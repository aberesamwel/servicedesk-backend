from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app import db
from app.models.ticket import Ticket
from sqlalchemy import func, case
import redis

class SLAService:
    """Service for SLA management and monitoring"""
    
    def __init__(self):
        try:
            self.cache = redis.Redis(host='localhost', port=6379, db=0)
        except:
            self.cache = None
    
    @staticmethod
    def get_sla_target(priority: str) -> int:
        """Get SLA target hours for priority"""
        targets = {
            'Critical': 4,
            'High': 8, 
            'Medium': 24,
            'Low': 72
        }
        return targets.get(priority, 24)
    
    @staticmethod
    def calculate_violation_risk(ticket: Ticket) -> float:
        """Calculate SLA violation risk (0.0 to 1.0)"""
        if ticket.status == 'Closed':
            return 0.0
            
        target_hours = SLAService.get_sla_target(ticket.priority)
        elapsed_hours = (datetime.utcnow() - ticket.created_at).total_seconds() / 3600
        
        risk = elapsed_hours / target_hours
        return min(risk, 1.0)
    
    def check_sla_violations(self) -> List[Ticket]:
        """Enhanced SLA violation detection with caching"""
        cache_key = "sla_violations_check"
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                violation_ids = eval(cached_result)
                return Ticket.query.filter(Ticket.id.in_(violation_ids)).all()
        
        violations = []
        open_tickets = Ticket.query.filter(Ticket.status != 'Closed').all()
        
        for ticket in open_tickets:
            risk = self.calculate_violation_risk(ticket)
            if risk >= 1.0 and not ticket.sla_violated:
                ticket.sla_violated = True
                violations.append(ticket)
        
        if violations:
            db.session.commit()
            if self.cache:
                violation_ids = [t.id for t in violations]
                self.cache.setex(cache_key, 300, str(violation_ids))
        
        return violations
    
    def get_violation_forecast(self, hours_ahead: int = 24) -> List[Ticket]:
        """Forecast tickets likely to violate SLA in next X hours"""
        future_time = datetime.utcnow() + timedelta(hours=hours_ahead)
        at_risk_tickets = []
        
        open_tickets = Ticket.query.filter(Ticket.status != 'Closed').all()
        
        for ticket in open_tickets:
            target_hours = self.get_sla_target(ticket.priority)
            deadline = ticket.created_at + timedelta(hours=target_hours)
            
            if deadline <= future_time and not ticket.sla_violated:
                at_risk_tickets.append(ticket)
        
        return at_risk_tickets
    
    def get_sla_trends(self, days: int = 30) -> List[Dict]:
        """Get SLA adherence trends over time with caching"""
        cache_key = f"sla_trends_{days}"
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return eval(cached_result)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        daily_sla = db.session.query(
            func.date(Ticket.created_at).label('date'),
            func.count(Ticket.id).label('total'),
            func.count(case((Ticket.sla_violated == False, Ticket.id))).label('met_sla')
        ).filter(
            Ticket.created_at >= start_date,
            Ticket.status == 'Closed'
        ).group_by(func.date(Ticket.created_at)).all()
        
        result = [{
            'date': str(day.date),
            'adherence_rate': (day.met_sla / day.total * 100) if day.total > 0 else 0
        } for day in daily_sla]
        
        # Cache for 1 hour
        if self.cache:
            self.cache.setex(cache_key, 3600, str(result))
        
        return result
    
    @staticmethod
    def get_sla_dashboard() -> Dict:
        """Get SLA dashboard metrics"""
        closed_tickets = Ticket.query.filter(Ticket.status == 'Closed').all()
        
        if not closed_tickets:
            return {
                'adherence_rate': 0,
                'total_tickets': 0,
                'violations': 0,
                'by_priority': {}
            }
        
        violations = len([t for t in closed_tickets if t.sla_violated])
        adherence_rate = ((len(closed_tickets) - violations) / len(closed_tickets)) * 100
        
        # By priority breakdown
        by_priority = {}
        for priority in ['Critical', 'High', 'Medium', 'Low']:
            priority_tickets = [t for t in closed_tickets if t.priority == priority]
            if priority_tickets:
                priority_violations = len([t for t in priority_tickets if t.sla_violated])
                priority_adherence = ((len(priority_tickets) - priority_violations) / len(priority_tickets)) * 100
                by_priority[priority] = {
                    'total': len(priority_tickets),
                    'violations': priority_violations,
                    'adherence_rate': round(priority_adherence, 2)
                }
        
        return {
            'adherence_rate': round(adherence_rate, 2),
            'total_tickets': len(closed_tickets),
            'violations': violations,
            'by_priority': by_priority
        }