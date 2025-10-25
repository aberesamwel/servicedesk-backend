from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from app.models.ticket import Ticket
from app import db
from sqlalchemy import func

class AnalyticsHelper:
    """Helper class for analytics calculations"""
    
    @staticmethod
    def calculate_resolution_rate(days: int = 30) -> float:
        """Calculate ticket resolution rate"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total_tickets = Ticket.query.filter(Ticket.created_at >= start_date).count()
        resolved_tickets = Ticket.query.filter(
            Ticket.created_at >= start_date,
            Ticket.status == 'Closed'
        ).count()
        
        return (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
    
    @staticmethod
    def get_peak_hours() -> List[Dict]:
        """Get peak ticket creation hours"""
        peak_data = db.session.query(
            func.extract('hour', Ticket.created_at).label('hour'),
            func.count(Ticket.id).label('count')
        ).group_by(func.extract('hour', Ticket.created_at)).all()
        
        return [{'hour': int(hour), 'count': count} for hour, count in peak_data]
    
    @staticmethod
    def calculate_avg_response_time(priority: str = None) -> float:
        """Calculate average first response time"""
        query = db.session.query(
            func.avg(func.extract('epoch', Ticket.updated_at - Ticket.created_at) / 3600)
        )
        
        if priority:
            query = query.filter(Ticket.priority == priority)
        
        result = query.scalar()
        return round(float(result or 0), 2)
    
    @staticmethod
    def get_category_distribution() -> Dict[str, int]:
        """Get ticket distribution by category"""
        categories = db.session.query(
            Ticket.category,
            func.count(Ticket.id).label('count')
        ).group_by(Ticket.category).all()
        
        return {category: count for category, count in categories}