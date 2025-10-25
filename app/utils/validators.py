from functools import wraps
from flask import request, jsonify
import re
from datetime import datetime

class APIValidator:
    """API request validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_priority(priority: str) -> bool:
        """Validate ticket priority"""
        valid_priorities = ['Critical', 'High', 'Medium', 'Low']
        return priority in valid_priorities
    
    @staticmethod
    def validate_status(status: str) -> bool:
        """Validate ticket status"""
        valid_statuses = ['New', 'Open', 'Pending', 'Closed']
        return status in valid_statuses
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """Validate date range"""
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            return start <= end
        except:
            return False

def require_json(f):
    """Decorator to require JSON content type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function

def validate_ticket_data(f):
    """Decorator to validate ticket creation data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        
        required_fields = ['title', 'description', 'priority', 'category']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        if not APIValidator.validate_priority(data['priority']):
            return jsonify({'error': 'Invalid priority value'}), 400
        
        return f(*args, **kwargs)
    return decorated_function

def validate_user_data(f):
    """Decorator to validate user data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        
        if 'email' in data and not APIValidator.validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        return f(*args, **kwargs)
    return decorated_function