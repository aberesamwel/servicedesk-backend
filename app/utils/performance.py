import time
from functools import wraps
from flask import request, g
from app.utils.logger import Logger

class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    @staticmethod
    def monitor_endpoint(f):
        """Decorator to monitor endpoint performance"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log performance
                Logger.log_performance(
                    f"{request.method} {request.endpoint}",
                    duration
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                Logger.log_error(e, f"{request.method} {request.endpoint}")
                raise
        
        return decorated_function
    
    @staticmethod
    def track_database_queries():
        """Track database query performance"""
        g.query_start_time = time.time()
    
    @staticmethod
    def log_slow_queries(duration_threshold: float = 1.0):
        """Log slow database queries"""
        if hasattr(g, 'query_start_time'):
            duration = time.time() - g.query_start_time
            if duration > duration_threshold:
                Logger.log_performance("SLOW_QUERY", duration)

def measure_time(operation_name: str):
    """Context manager for measuring operation time"""
    class TimeContext:
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            Logger.log_performance(operation_name, duration)
    
    return TimeContext()