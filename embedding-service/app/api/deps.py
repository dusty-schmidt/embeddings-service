# app/api/deps.py

from fastapi import Depends
from app.config import get_settings, Settings
from app.core.cache import CacheManager
from app.core.providers.manager import ProviderManager
from app.core.rate_limiter import RateLimiter
from app.core.auth import verify_api_key, verify_admin_key
from functools import lru_cache


# Cached instances
_cache_manager = None
_provider_manager = None
_rate_limiter = None


@lru_cache()
def get_cache_manager() -> CacheManager:
    """Get cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        settings = get_settings()
        _cache_manager = CacheManager(settings)
    return _cache_manager


@lru_cache()
def get_provider_manager() -> ProviderManager:
    """Get provider manager instance"""
    global _provider_manager
    if _provider_manager is None:
        settings = get_settings()
        _provider_manager = ProviderManager(settings)
    return _provider_manager


@lru_cache()
def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        settings = get_settings()
        _rate_limiter = RateLimiter(settings)
    return _rate_limiter


# Export auth functions
__all__ = [
    "get_cache_manager",
    "get_provider_manager",
    "get_rate_limiter",
    "verify_api_key",
    "verify_admin_key",
]