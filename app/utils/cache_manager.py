import redis
import json
from typing import Any, Optional
from datetime import timedelta

class CacheManager:
    """Redis cache manager for application data"""
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            self.available = True
        except:
            self.available = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.available:
            return None
        
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except:
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration"""
        if not self.available:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, expire, serialized_value)
        except:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.available:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except:
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.available:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            return self.redis_client.delete(*keys) if keys else 0
        except:
            return 0
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.available:
            return {'available': False}
        
        try:
            info = self.redis_client.info()
            return {
                'available': True,
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
        except:
            return {'available': False}

# Global cache instance
cache_manager = CacheManager()