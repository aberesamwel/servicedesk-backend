from flask import Blueprint, request, jsonify
from app.services.notification_service import NotificationService
from datetime import datetime

users_bp = Blueprint('users', __name__)
notification_service = NotificationService()

@users_bp.route('/<int:user_id>/notification-preferences', methods=['GET'])
def get_notification_preferences(user_id):
    """Get user notification preferences"""
    preferences = {
        'user_id': user_id,
        'email_notifications': True,
        'sms_notifications': False,
        'notification_types': {
            'ticket_created': True,
            'ticket_updated': True,
            'sla_violation': True,
            'ticket_resolved': False
        },
        'quiet_hours': {
            'enabled': True,
            'start': '22:00',
            'end': '08:00'
        }
    }
    
    return jsonify(preferences)

@users_bp.route('/<int:user_id>/notification-preferences', methods=['PUT'])
def update_notification_preferences(user_id):
    """Update user notification preferences"""
    data = request.get_json()
    
    updated_preferences = {
        'user_id': user_id,
        'updated_at': datetime.utcnow().isoformat(),
        'preferences': data
    }
    
    return jsonify({
        'message': 'Notification preferences updated',
        'data': updated_preferences
    })

@users_bp.route('/<int:user_id>/send-test-notification', methods=['POST'])
def send_test_notification(user_id):
    """Send test notification to user"""
    data = request.get_json()
    template_name = data.get('template', 'ticket_created')
    
    user_email = f"user{user_id}@example.com"
    
    context = {
        'ticket_id': 123,
        'title': 'Test Notification',
        'priority': 'medium',
        'status': 'open'
    }
    
    success = notification_service.send_notification(user_email, template_name, context)
    
    return jsonify({
        'message': 'Test notification sent' if success else 'Failed to send notification',
        'template': template_name,
        'recipient': user_email
    })

@users_bp.route('/notification-queue-status', methods=['GET'])
def get_notification_queue_status():
    """Get notification queue status"""
    status = notification_service.get_queue_status()
    return jsonify(status)