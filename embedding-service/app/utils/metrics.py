# app/utils/metrics.py

from datetime import datetime
from typing import Dict
from collections import defaultdict


class MetricsCollector:
    """Simple in-memory metrics collector"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.total_requests = 0
        self.total_embeddings = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.provider_usage: Dict[str, int] = defaultdict(int)
        self.errors = 0
    
    def record_request(self):
        """Record a request"""
        self.total_requests += 1
    
    def record_embeddings(self, count: int):
        """Record number of embeddings generated"""
        self.total_embeddings += count
    
    def record_cache_hit(self):
        """Record a cache hit"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record a cache miss"""
        self.cache_misses += 1
    
    def record_provider_usage(self, provider: str):
        """Record provider usage"""
        self.provider_usage[provider] += 1
    
    def record_error(self):
        """Record an error"""
        self.errors += 1
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100
    
    def get_uptime(self) -> float:
        """Get uptime in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_all_metrics(self) -> dict:
        """Get all metrics"""
        return {
            "total_requests": self.total_requests,
            "total_embeddings": self.total_embeddings,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.get_cache_hit_rate(), 2),
            "provider_usage": dict(self.provider_usage),
            "errors": self.errors,
            "uptime_seconds": round(self.get_uptime(), 2)
        }
    
    def reset(self):
        """Reset all metrics"""
        self.start_time = datetime.now()
        self.total_requests = 0
        self.total_embeddings = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.provider_usage.clear()
        self.errors = 0


# Global metrics instance
metrics_collector = MetricsCollector()