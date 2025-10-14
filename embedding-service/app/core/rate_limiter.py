# app/core/rate_limiter.py

from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.RATE_LIMIT_ENABLED
        self.per_minute = config.RATE_LIMIT_PER_MINUTE
        self.per_hour = config.RATE_LIMIT_PER_HOUR
        
        # Storage: {api_key: [(timestamp, count), ...]}
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
    
    def _cleanup_old_requests(self, requests: list, window: timedelta):
        """Remove requests outside the time window"""
        cutoff = datetime.now() - window
        return [ts for ts in requests if ts > cutoff]
    
    def check_rate_limit(self, api_key: str):
        """
        Check if request is within rate limits
        
        Args:
            api_key: The API key making the request
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        if not self.enabled:
            return
        
        now = datetime.now()
        
        # Clean up old requests
        self.minute_requests[api_key] = self._cleanup_old_requests(
            self.minute_requests[api_key],
            timedelta(minutes=1)
        )
        self.hour_requests[api_key] = self._cleanup_old_requests(
            self.hour_requests[api_key],
            timedelta(hours=1)
        )
        
        # Check per-minute limit
        minute_count = len(self.minute_requests[api_key])
        if minute_count >= self.per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.per_minute} requests per minute",
                headers={
                    "X-RateLimit-Limit": str(self.per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((now + timedelta(minutes=1)).timestamp()))
                }
            )
        
        # Check per-hour limit
        hour_count = len(self.hour_requests[api_key])
        if hour_count >= self.per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.per_hour} requests per hour",
                headers={
                    "X-RateLimit-Limit": str(self.per_hour),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((now + timedelta(hours=1)).timestamp()))
                }
            )
        
        # Record this request
        self.minute_requests[api_key].append(now)
        self.hour_requests[api_key].append(now)
    
    def get_usage(self, api_key: str) -> Dict[str, int]:
        """Get current usage for an API key"""
        if not self.enabled:
            return {
                "minute": 0,
                "hour": 0,
                "minute_limit": self.per_minute,
                "hour_limit": self.per_hour
            }
        
        # Clean up first
        now = datetime.now()
        self.minute_requests[api_key] = self._cleanup_old_requests(
            self.minute_requests[api_key],
            timedelta(minutes=1)
        )
        self.hour_requests[api_key] = self._cleanup_old_requests(
            self.hour_requests[api_key],
            timedelta(hours=1)
        )
        
        return {
            "minute": len(self.minute_requests[api_key]),
            "hour": len(self.hour_requests[api_key]),
            "minute_limit": self.per_minute,
            "hour_limit": self.per_hour,
            "minute_remaining": max(0, self.per_minute - len(self.minute_requests[api_key])),
            "hour_remaining": max(0, self.per_hour - len(self.hour_requests[api_key]))
        }