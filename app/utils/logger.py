import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class Logger:
    """Application logger configuration"""
    
    @staticmethod
    def setup_logging(app):
        """Setup application logging"""
        if not app.debug and not app.testing:
            # Create logs directory if it doesn't exist
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            # Setup file handler
            file_handler = RotatingFileHandler(
                'logs/servicedesk.log',
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('ServiceDesk backend startup')
    
    @staticmethod
    def log_api_request(endpoint: str, method: str, user_id: str = None):
        """Log API request"""
        message = f"API {method} {endpoint}"
        if user_id:
            message += f" - User: {user_id}"
        
        logging.info(message)
    
    @staticmethod
    def log_error(error: Exception, context: str = ""):
        """Log application error"""
        message = f"ERROR in {context}: {str(error)}"
        logging.error(message)
    
    @staticmethod
    def log_performance(operation: str, duration: float):
        """Log performance metrics"""
        message = f"PERFORMANCE {operation}: {duration:.3f}s"
        logging.info(message)