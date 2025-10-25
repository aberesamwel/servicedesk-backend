from flask import Blueprint, request, jsonify
from app import db
from app.models.ticket import Ticket
from app.models.user import Agent
from sqlalchemy import func, case
from datetime import datetime, timedelta
import redis

analytics_bp = Blueprint('analytics', __name__)

# Redis cache for expensive queries
try:
    cache = redis.Redis(host='localhost', port=6379, db=0)
except:
    cache = None

@analytics_bp.route('/ticket-status-counts', methods=['GET'])
def get_ticket_status_counts():
    """Get count of tickets by status"""
    status_counts = db.session.query(
        Ticket.status,
        func.count(Ticket.id).label('count')
    ).group_by(Ticket.status).all()
    
    result = {status: count for status, count in status_counts}
    return jsonify(result)

@analytics_bp.route('/agent-workload', methods=['GET'])
def get_agent_workload():
    """Get current workload distribution across agents"""
    workload = db.session.query(
        Agent.id,
        Agent.name,
        Agent.email,
        func.count(case((Ticket.status != 'Closed', Ticket.id))).label('active_tickets'),
        func.count(case((Ticket.status == 'Closed', Ticket.id))).label('closed_tickets')
    ).outerjoin(Ticket, Agent.id == Ticket.assigned_to)\
     .group_by(Agent.id, Agent.name, Agent.email)\
     .all()
    
    result = []
    for agent_id, name, email, active, closed in workload:
        result.append({
            'agent_id': agent_id,
            'name': name,
            'email': email,
            'active_tickets': active or 0,
            'closed_tickets': closed or 0
        })
    
    return jsonify(result)

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get dashboard analytics"""
    total_tickets = Ticket.query.count()
    open_tickets = Ticket.query.filter(Ticket.status.in_(['New', 'Open', 'Pending'])).count()
    closed_tickets = Ticket.query.filter_by(status='Closed').count()
    
    priority_counts = db.session.query(
        Ticket.priority, 
        func.count(Ticket.id)
    ).group_by(Ticket.priority).all()
    
    sla_violations = Ticket.query.filter_by(sla_violated=True).count()
    
    return jsonify({
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'closed_tickets': closed_tickets,
        'sla_violations': sla_violations,
        'priority_breakdown': dict(priority_counts)
    })

@analytics_bp.route('/trends', methods=['GET'])
def get_trends():
    """Get ticket trends and forecasting"""
    days = request.args.get('days', 30, type=int)
    
    # Check cache first
    cache_key = f"trends_{days}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return jsonify(eval(cached_result))
    
    # Daily ticket creation trend
    daily_tickets = db.session.query(
        func.date(Ticket.created_at).label('date'),
        func.count(Ticket.id).label('count')
    ).filter(
        Ticket.created_at >= datetime.utcnow() - timedelta(days=days)
    ).group_by(func.date(Ticket.created_at)).all()
    
    result = [{
        'date': str(day.date),
        'tickets': day.count
    } for day in daily_tickets]
    
    # Cache for 1 hour
    if cache:
        cache.setex(cache_key, 3600, str(result))
    
    return jsonify(result)

@analytics_bp.route('/forecasting', methods=['GET'])
def get_forecasting():
    """Get ticket volume forecasting"""
    cache_key = "forecasting"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result:
            return jsonify(eval(cached_result))
    
    # Simple 7-day moving average forecast
    recent_tickets = Ticket.query.filter(
        Ticket.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    daily_avg = recent_tickets / 7
    forecast = {
        'daily_average': round(daily_avg, 1),
        'weekly_forecast': round(daily_avg * 7),
        'monthly_forecast': round(daily_avg * 30),
        'trend': 'increasing' if daily_avg > 5 else 'stable'
    }
    
    # Cache for 30 minutes
    if cache:
        cache.setex(cache_key, 1800, str(forecast))
    
    return jsonify(forecast)

@analytics_bp.route('/performance-metrics', methods=['GET'])
def get_performance_metrics():
    """Get advanced performance metrics"""
    days = request.args.get('days', 30, type=int)
    
    # Resolution time by priority
    resolution_times = db.session.query(
        Ticket.priority,
        func.avg(Ticket.resolution_time_hours).label('avg_time')
    ).filter(
        Ticket.status == 'Closed',
        Ticket.created_at >= datetime.utcnow() - timedelta(days=days)
    ).group_by(Ticket.priority).all()
    
    # First response time
    first_response = db.session.query(
        func.avg(func.extract('epoch', Ticket.updated_at - Ticket.created_at) / 3600).label('avg_hours')
    ).filter(
        Ticket.created_at >= datetime.utcnow() - timedelta(days=days)
    ).scalar()
    
    return jsonify({
        'resolution_times': {priority: round(float(avg_time), 2) for priority, avg_time in resolution_times},
        'first_response_time': round(float(first_response or 0), 2),
        'period_days': days
    })