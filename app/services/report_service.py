from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.models.ticket import Ticket
from app.models.user import Agent
from app import db
from sqlalchemy import func, case

class ReportService:
    """Service for generating various reports"""
    
    @staticmethod
    def generate_summary_report(days: int = 30) -> Dict:
        """Generate summary report for specified period"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Basic metrics
        total_tickets = Ticket.query.filter(Ticket.created_at >= start_date).count()
        closed_tickets = Ticket.query.filter(
            Ticket.created_at >= start_date,
            Ticket.status == 'Closed'
        ).count()
        
        # Priority breakdown
        priority_stats = db.session.query(
            Ticket.priority,
            func.count(Ticket.id).label('count'),
            func.avg(Ticket.resolution_time_hours).label('avg_resolution')
        ).filter(
            Ticket.created_at >= start_date
        ).group_by(Ticket.priority).all()
        
        return {
            'period_days': days,
            'total_tickets': total_tickets,
            'closed_tickets': closed_tickets,
            'resolution_rate': (closed_tickets / total_tickets * 100) if total_tickets > 0 else 0,
            'priority_breakdown': {
                priority: {
                    'count': count,
                    'avg_resolution_hours': round(float(avg_res or 0), 2)
                } for priority, count, avg_res in priority_stats
            }
        }
    
    @staticmethod
    def generate_agent_performance_report(days: int = 30) -> List[Dict]:
        """Generate agent performance report"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        agent_stats = db.session.query(
            Agent.id,
            Agent.name,
            Agent.email,
            func.count(Ticket.id).label('total_assigned'),
            func.count(case((Ticket.status == 'Closed', Ticket.id))).label('resolved'),
            func.avg(Ticket.resolution_time_hours).label('avg_resolution')
        ).outerjoin(
            Ticket, Agent.id == Ticket.assigned_to
        ).filter(
            Ticket.created_at >= start_date
        ).group_by(Agent.id, Agent.name, Agent.email).all()
        
        return [{
            'agent_id': agent_id,
            'name': name,
            'email': email,
            'tickets_assigned': total_assigned or 0,
            'tickets_resolved': resolved or 0,
            'resolution_rate': (resolved / total_assigned * 100) if total_assigned > 0 else 0,
            'avg_resolution_hours': round(float(avg_res or 0), 2)
        } for agent_id, name, email, total_assigned, resolved, avg_res in agent_stats]
    
    @staticmethod
    def generate_sla_compliance_report(days: int = 30) -> Dict:
        """Generate SLA compliance report"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        tickets = Ticket.query.filter(
            Ticket.created_at >= start_date,
            Ticket.status == 'Closed'
        ).all()
        
        if not tickets:
            return {
                'period_days': days,
                'total_tickets': 0,
                'sla_met': 0,
                'sla_violated': 0,
                'compliance_rate': 0,
                'by_priority': {}
            }
        
        sla_met = len([t for t in tickets if not t.sla_violated])
        sla_violated = len([t for t in tickets if t.sla_violated])
        
        # By priority
        by_priority = {}
        for priority in ['Critical', 'High', 'Medium', 'Low']:
            priority_tickets = [t for t in tickets if t.priority == priority]
            if priority_tickets:
                priority_met = len([t for t in priority_tickets if not t.sla_violated])
                by_priority[priority] = {
                    'total': len(priority_tickets),
                    'met': priority_met,
                    'violated': len(priority_tickets) - priority_met,
                    'compliance_rate': (priority_met / len(priority_tickets) * 100)
                }
        
        return {
            'period_days': days,
            'total_tickets': len(tickets),
            'sla_met': sla_met,
            'sla_violated': sla_violated,
            'compliance_rate': (sla_met / len(tickets) * 100),
            'by_priority': by_priority
        }