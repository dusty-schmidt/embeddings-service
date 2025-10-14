# app/core/auth.py

from fastapi import Header, HTTPException, status
from typing import Optional
from app.config import get_settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key from request header
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    settings = get_settings()
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_api_key not in settings.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return x_api_key


async def verify_admin_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify admin API key from request header
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        The validated admin API key
        
    Raises:
        HTTPException: If API key is missing or not an admin key
    """
    settings = get_settings()
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if x_api_key not in settings.ADMIN_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return x_api_key


def get_api_key_hash(api_key: str) -> str:
    """Get a hash of the API key for logging/metrics (never log the actual key)"""
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()[:8]