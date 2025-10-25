import unittest
from app import create_app, db
from app.models.ticket import Ticket
from app.services.sla_service import SLAService
from datetime import datetime, timedelta

class TestSLAService(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.sla_service = SLAService()
        self.create_test_tickets()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_tickets(self):
        """Create test tickets with different SLA scenarios"""
        # Critical ticket - should violate SLA after 4 hours
        critical_ticket = Ticket(
            id='TKT-CRITICAL',
            title='Critical Issue',
            priority='Critical',
            status='Open',
            category='Technical',
            created_by='user1',
            created_at=datetime.utcnow() - timedelta(hours=5),  # 5 hours old
            sla_violated=False
        )
        
        # High priority ticket - within SLA
        high_ticket = Ticket(
            id='TKT-HIGH',
            title='High Priority Issue',
            priority='High',
            status='Open',
            category='Technical',
            created_by='user1',
            created_at=datetime.utcnow() - timedelta(hours=6),  # 6 hours old
            sla_violated=False
        )
        
        # Closed ticket
        closed_ticket = Ticket(
            id='TKT-CLOSED',
            title='Closed Ticket',
            priority='Medium',
            status='Closed',
            category='Technical',
            created_by='user1',
            created_at=datetime.utcnow() - timedelta(days=1),
            sla_violated=False
        )
        
        db.session.add_all([critical_ticket, high_ticket, closed_ticket])
        db.session.commit()
    
    def test_get_sla_target(self):
        """Test SLA target calculation"""
        self.assertEqual(SLAService.get_sla_target('Critical'), 4)
        self.assertEqual(SLAService.get_sla_target('High'), 8)
        self.assertEqual(SLAService.get_sla_target('Medium'), 24)
        self.assertEqual(SLAService.get_sla_target('Low'), 72)
    
    def test_calculate_violation_risk(self):
        """Test SLA violation risk calculation"""
        critical_ticket = Ticket.query.filter_by(id='TKT-CRITICAL').first()
        risk = SLAService.calculate_violation_risk(critical_ticket)
        
        # 5 hours old critical ticket should have risk > 1.0
        self.assertGreater(risk, 1.0)
        
        closed_ticket = Ticket.query.filter_by(id='TKT-CLOSED').first()
        closed_risk = SLAService.calculate_violation_risk(closed_ticket)
        
        # Closed tickets should have 0 risk
        self.assertEqual(closed_risk, 0.0)
    
    def test_check_sla_violations(self):
        """Test SLA violation detection"""
        violations = self.sla_service.check_sla_violations()
        
        # Should detect the critical ticket as violation
        violation_ids = [v.id for v in violations]
        self.assertIn('TKT-CRITICAL', violation_ids)
    
    def test_get_violation_forecast(self):
        """Test SLA violation forecasting"""
        at_risk_tickets = self.sla_service.get_violation_forecast(hours_ahead=24)
        
        # Should include tickets that will violate SLA in next 24 hours
        self.assertIsInstance(at_risk_tickets, list)
    
    def test_sla_dashboard(self):
        """Test SLA dashboard metrics"""
        dashboard = SLAService.get_sla_dashboard()
        
        self.assertIn('adherence_rate', dashboard)
        self.assertIn('total_tickets', dashboard)
        self.assertIn('violations', dashboard)
        self.assertIn('by_priority', dashboard)

if __name__ == '__main__':
    unittest.main()