from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.schemas.user_schema import user_schema, users_schema
from app.services.notification_service import NotificationService
from datetime import datetime

users_bp = Blueprint('users', __name__)

@users_bp.route('/', methods=['GET'])
def get_users():
    """Get all users"""
    role = request.args.get('role')
    
    query = User.query
    if role:
        query = query.filter(User.role == role)
    
    users = query.order_by(User.name).all()
    return jsonify(users_schema.dump(users))

@users_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user"""
    user = User.query.get_or_404(user_id)
    return jsonify(user_schema.dump(user))

@users_bp.route('/', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    user = User(
        id=data['id'],
        name=data['name'],
        email=data['email'],
        role=data['role']
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user_schema.dump(user)), 201

@users_bp.route('/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update a user"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    for field in ['name', 'email', 'role']:
        if field in data:
            setattr(user, field, data[field])
    
    db.session.commit()
    return jsonify(user_schema.dump(user))

@users_bp.route('/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    return '', 204

@users_bp.route('/<user_id>/notifications/preferences', methods=['GET'])
def get_notification_preferences(user_id):
    """Get user notification preferences"""
    user = User.query.get_or_404(user_id)
    
    preferences = NotificationService.get_notification_preferences(user_id)
    preferences['user_id'] = user_id
    preferences['user_email'] = user.email
    
    return jsonify(preferences)

@users_bp.route('/<user_id>/notifications/preferences', methods=['PUT'])
def update_notification_preferences(user_id):
    """Update user notification preferences"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    updated_preferences = {
        'user_id': user_id,
        'email_enabled': data.get('email_enabled', True),
        'sms_enabled': data.get('sms_enabled', False),
        'push_enabled': data.get('push_enabled', True),
        'frequency': data.get('frequency', 'immediate'),
        'types': data.get('types', {}),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    return jsonify(updated_preferences)

@users_bp.route('/<user_id>/notifications/test', methods=['POST'])
def send_test_notification(user_id):
    """Send test notification to user"""
    user = User.query.get_or_404(user_id)
    
    success = NotificationService.send_email_notification(
        user.email,
        "Test Notification - IT ServiceDesk",
        "This is a test notification from IT ServiceDesk platform. Your notifications are working correctly!"
    )
    
    return jsonify({
        'success': success,
        'message': 'Test notification sent successfully' if success else 'Failed to send test notification',
        'recipient': user.email,
        'timestamp': datetime.utcnow().isoformat()
    })