from flask import Blueprint, request, jsonify
from app.services.sla_service import SLAService
from app.models.ticket import Ticket
from datetime import datetime

sla_bp = Blueprint('sla', __name__)

@sla_bp.route('/dashboard', methods=['GET'])
def get_sla_dashboard():
    """Get SLA dashboard metrics"""
    sla_service = SLAService()
    dashboard_data = sla_service.get_sla_dashboard()
    return jsonify(dashboard_data)

@sla_bp.route('/violations', methods=['GET'])
def get_sla_violations():
    """Get current SLA violations"""
    sla_service = SLAService()
    violations = sla_service.check_sla_violations()
    
    result = [{
        'ticket_id': ticket.id,
        'title': ticket.title,
        'priority': ticket.priority,
        'hours_open': ticket.hours_open,
        'violation_time': datetime.utcnow().isoformat()
    } for ticket in violations]
    
    return jsonify(result)

@sla_bp.route('/forecast', methods=['GET'])
def get_sla_forecast():
    """Get SLA violation forecast"""
    hours_ahead = request.args.get('hours', 24, type=int)
    sla_service = SLAService()
    at_risk_tickets = sla_service.get_violation_forecast(hours_ahead)
    
    result = [{
        'ticket_id': ticket.id,
        'title': ticket.title,
        'priority': ticket.priority,
        'risk_level': sla_service.calculate_violation_risk(ticket),
        'estimated_violation': 'within_24h' if hours_ahead <= 24 else 'later'
    } for ticket in at_risk_tickets]
    
    return jsonify(result)

@sla_bp.route('/trends', methods=['GET'])
def get_sla_trends():
    """Get SLA adherence trends"""
    days = request.args.get('days', 30, type=int)
    sla_service = SLAService()
    trends = sla_service.get_sla_trends(days)
    return jsonify(trends)