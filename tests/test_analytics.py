import unittest
import json
from app import create_app, db
from app.models.ticket import Ticket
from app.models.user import Agent
from datetime import datetime, timedelta

class TestAnalyticsAPI(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
        
        # Create test data
        self.create_test_data()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_data(self):
        """Create test tickets and agents"""
        # Create test agent
        agent = Agent(
            id='agent1',
            name='Test Agent',
            email='agent@test.com'
        )
        db.session.add(agent)
        
        # Create test tickets
        for i in range(5):
            ticket = Ticket(
                id=f'TKT-{i+1}',
                title=f'Test Ticket {i+1}',
                description='Test description',
                priority='High' if i < 2 else 'Medium',
                status='Open' if i < 3 else 'Closed',
                category='Technical',
                created_by='user1',
                assigned_to='agent1' if i < 4 else None,
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            db.session.add(ticket)
        
        db.session.commit()
    
    def test_dashboard_analytics(self):
        """Test dashboard analytics endpoint"""
        response = self.client.get('/api/analytics/dashboard')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('total_tickets', data)
        self.assertIn('open_tickets', data)
        self.assertIn('closed_tickets', data)
        self.assertEqual(data['total_tickets'], 5)
    
    def test_ticket_status_counts(self):
        """Test ticket status counts endpoint"""
        response = self.client.get('/api/analytics/ticket-status-counts')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('Open', data)
        self.assertIn('Closed', data)
    
    def test_agent_workload(self):
        """Test agent workload endpoint"""
        response = self.client.get('/api/analytics/agent-workload')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIsInstance(data, list)
        if data:
            self.assertIn('agent_id', data[0])
            self.assertIn('active_tickets', data[0])

if __name__ == '__main__':
    unittest.main()