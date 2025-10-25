from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.models.ticket import Ticket
from app.models.user import User, Agent
from app import db
import uuid
import queue
import threading

class NotificationService:
    """Enhanced service for handling notifications with email and queue support"""
    
    def __init__(self):
        self.notification_queue = queue.Queue()
        self.email_templates = {
            'ticket_created': 'New ticket {ticket_id} has been created: {title}',
            'ticket_assigned': 'Ticket {ticket_id} has been assigned to you: {title}',
            'status_changed': 'Ticket {ticket_id} status changed to {status}',
            'sla_warning': 'SLA WARNING: Ticket {ticket_id} is approaching deadline',
            'sla_breach': 'SLA BREACH: Ticket {ticket_id} has violated SLA'
        }
    
    @staticmethod
    def notify_sla_violation(ticket: Ticket) -> bool:
        """Notify about SLA violation with email"""
        print(f"SLA VIOLATION ALERT: Ticket {ticket.id} has violated SLA")
        
        if ticket.assigned_to:
            agent = Agent.query.get(ticket.assigned_to)
            if agent:
                return NotificationService.send_email_notification(
                    agent.email,
                    f"SLA BREACH: {ticket.id}",
                    f"Ticket {ticket.id} has breached its SLA target!"
                )
        return True
    
    @staticmethod
    def notify_ticket_assignment(ticket: Ticket, agent: Agent) -> bool:
        """Notify agent about ticket assignment with email"""
        print(f"ASSIGNMENT: Ticket {ticket.id} assigned to {agent.name}")
        
        return NotificationService.send_email_notification(
            agent.email,
            f"New Ticket Assigned: {ticket.id}",
            f"You have been assigned ticket {ticket.id}: {ticket.title}"
        )
    
    @staticmethod
    def notify_status_change(ticket: Ticket, old_status: str, new_status: str) -> bool:
        """Notify stakeholders about status change with email"""
        print(f"STATUS CHANGE: Ticket {ticket.id} changed from {old_status} to {new_status}")
        
        # Notify ticket creator
        creator = User.query.get(ticket.created_by)
        if creator:
            return NotificationService.send_email_notification(
                creator.email,
                f"Ticket Status Updated: {ticket.id}",
                f"Your ticket {ticket.id} status changed from {old_status} to {new_status}"
            )
        return True
    
    @staticmethod
    def send_email_notification(recipient_email: str, subject: str, message: str) -> bool:
        """Send email notification with logging"""
        try:
            # Simulate email sending (replace with actual SMTP)
            print(f"EMAIL: To={recipient_email}, Subject={subject}, Message={message}")
            
            # Log email attempt (if EmailLog model exists)
            try:
                from app.models.email_log import EmailLog
                log_entry = EmailLog(
                    id=str(uuid.uuid4()),
                    recipient=recipient_email,
                    subject=subject,
                    template='notification',
                    status='sent',
                    sent_at=datetime.utcnow()
                )
                db.session.add(log_entry)
                db.session.commit()
            except ImportError:
                pass  # EmailLog model not available
            
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def queue_notification(self, notification_type: str, recipient: str, data: Dict) -> bool:
        """Queue notification for async processing"""
        notification = {
            'id': str(uuid.uuid4()),
            'type': notification_type,
            'recipient': recipient,
            'data': data,
            'created_at': datetime.utcnow(),
            'status': 'queued'
        }
        
        self.notification_queue.put(notification)
        print(f"QUEUED: {notification_type} for {recipient}")
        return True
    
    def process_notification_queue(self):
        """Process queued notifications"""
        while not self.notification_queue.empty():
            try:
                notification = self.notification_queue.get()
                
                # Process based on type
                if notification['type'] == 'email':
                    self.send_email_notification(
                        notification['recipient'],
                        notification['data']['subject'],
                        notification['data']['message']
                    )
                
                notification['status'] = 'processed'
                print(f"Processed notification {notification['id']}")
                
            except Exception as e:
                print(f"Failed to process notification: {str(e)}")
    
    @staticmethod
    def get_notification_preferences(user_id: str) -> Dict:
        """Get user notification preferences"""
        return {
            'email_enabled': True,
            'sms_enabled': False,
            'push_enabled': True,
            'frequency': 'immediate',
            'types': {
                'ticket_assigned': True,
                'status_change': True,
                'sla_warning': True,
                'new_message': True
            }
        }
    
    @staticmethod
    def send_daily_digest(user_id: str) -> bool:
        """Send daily digest of tickets"""
        user = User.query.get(user_id)
        if not user:
            return False
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_tickets = Ticket.query.filter(
            Ticket.created_by == user_id,
            Ticket.created_at >= yesterday
        ).all()
        
        if recent_tickets:
            digest_content = f"Daily Digest: You have {len(recent_tickets)} tickets from the last 24 hours"
            return NotificationService.send_email_notification(
                user.email,
                "Daily Ticket Digest",
                digest_content
            )
        
        return True