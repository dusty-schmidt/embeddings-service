# app/core/cache.py

import redis
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime


class CacheManager:
    """Redis cache manager with in-memory fallback"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.CACHE_ENABLED
        self.ttl = config.CACHE_TTL
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, tuple] = {}  # (data, expiry)
        self.use_redis = True
        
        if self.enabled:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                password=self.config.REDIS_PASSWORD if self.config.REDIS_PASSWORD else None,
                db=self.config.REDIS_DB,
                decode_responses=False,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            print(f"✓ Redis connected: {self.config.REDIS_HOST}:{self.config.REDIS_PORT}")
            self.use_redis = True
        except Exception as e:
            print(f"✗ Redis connection failed: {e}")
            print("  Using in-memory cache as fallback")
            self.redis_client = None
            self.use_redis = False
    
    def generate_key(self, text: str, model: str, provider: str) -> str:
        """Generate cache key from text, model, and provider"""
        content = f"{provider}:{model}:{text}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()
        return f"emb:{hash_value}"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve value from cache"""
        if not self.enabled:
            return None
        
        # Try Redis first
        if self.use_redis and self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                print(f"Redis read error: {e}")
                # Fall through to memory cache
        
        # Try memory cache
        if key in self.memory_cache:
            data, expiry = self.memory_cache[key]
            if datetime.now().timestamp() < expiry:
                return data
            else:
                # Expired, remove it
                del self.memory_cache[key]
        
        return None
    
    def set(self, key: str, value: Dict[str, Any]):
        """Store value in cache"""
        if not self.enabled:
            return
        
        serialized = json.dumps(value)
        
        # Try Redis first
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(key, self.ttl, serialized)
                return
            except Exception as e:
                print(f"Redis write error: {e}")
                # Fall through to memory cache
        
        # Store in memory cache
        expiry = datetime.now().timestamp() + self.ttl
        self.memory_cache[key] = (value, expiry)
        
        # Clean up old entries if cache gets too large
        if len(self.memory_cache) > 10000:
            self._cleanup_memory_cache()
    
    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache"""
        now = datetime.now().timestamp()
        expired_keys = [
            key for key, (_, expiry) in self.memory_cache.items()
            if now >= expiry
        ]
        for key in expired_keys:
            del self.memory_cache[key]
    
    def delete(self, key: str):
        """Delete a key from cache"""
        if not self.enabled:
            return
        
        # Delete from Redis
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass
        
        # Delete from memory
        if key in self.memory_cache:
            del self.memory_cache[key]
    
    def clear_all(self):
        """Clear entire cache"""
        if not self.enabled:
            return
        
        # Clear Redis
        if self.use_redis and self.redis_client:
            try:
                # Only delete keys matching our pattern
                for key in self.redis_client.scan_iter("emb:*"):
                    self.redis_client.delete(key)
            except Exception as e:
                print(f"Redis clear error: {e}")
        
        # Clear memory cache
        self.memory_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "enabled": self.enabled,
            "backend": "redis" if self.use_redis else "memory",
            "ttl": self.ttl
        }
        
        if self.use_redis and self.redis_client:
            try:
                info = self.redis_client.info()
                stats["redis"] = {
                    "connected": True,
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "total_keys": self.redis_client.dbsize()
                }
            except Exception:
                stats["redis"] = {"connected": False}
        else:
            stats["memory"] = {
                "keys": len(self.memory_cache)
            }
        
        return stats
    
    def is_available(self) -> bool:
        """Check if cache is available"""
        if not self.enabled:
            return False
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.ping()
                return True
            except Exception:
                return False
        
        # Memory cache is always available
        return True