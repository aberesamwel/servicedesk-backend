import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
import queue
import threading
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling email notifications"""
    
    def __init__(self):
        self.email_queue = queue.Queue()
        self.templates = self._load_templates()
        self._start_worker()
    
    def _load_templates(self) -> Dict:
        """Load email templates"""
        return {
            'ticket_created': {
                'subject': 'New Ticket Created: #{ticket_id}',
                'body': 'A new ticket has been created.\n\nTicket ID: {ticket_id}\nTitle: {title}\nPriority: {priority}'
            },
            'ticket_updated': {
                'subject': 'Ticket Updated: #{ticket_id}',
                'body': 'Your ticket has been updated.\n\nTicket ID: {ticket_id}\nStatus: {status}\nUpdated by: {updated_by}'
            },
            'sla_violation': {
                'subject': 'SLA Violation Alert: #{ticket_id}',
                'body': 'SLA violation detected.\n\nTicket ID: {ticket_id}\nPriority: {priority}\nElapsed Time: {elapsed_time}'
            }
        }
    
    def send_notification(self, recipient: str, template_name: str, context: Dict):
        """Queue email notification for sending"""
        template = self.templates.get(template_name)
        if not template:
            logger.error(f"Template {template_name} not found")
            return False
        
        email_data = {
            'recipient': recipient,
            'subject': template['subject'].format(**context),
            'body': template['body'].format(**context),
            'timestamp': datetime.utcnow()
        }
        
        self.email_queue.put(email_data)
        return True
    
    def _start_worker(self):
        """Start background worker for processing email queue"""
        def worker():
            while True:
                try:
                    email_data = self.email_queue.get(timeout=1)
                    self._send_email(email_data)
                    self.email_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Email sending failed: {e}")
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _send_email(self, email_data: Dict):
        """Send email (mock implementation)"""
        logger.info(f"Sending email to {email_data['recipient']}: {email_data['subject']}")
        return True
    
    def get_queue_status(self) -> Dict:
        """Get notification queue status"""
        return {
            'queue_size': self.email_queue.qsize(),
            'available_templates': list(self.templates.keys()),
            'status': 'active'
        }