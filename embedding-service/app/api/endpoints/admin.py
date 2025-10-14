# app/api/endpoints/admin.py

from fastapi import APIRouter, Depends

from app.models.responses import StatsResponse, CacheInfoResponse, MessageResponse
from app.api.deps import get_cache_manager, verify_admin_key
from app.utils.metrics import metrics_collector

router = APIRouter()


@router.get("/admin/stats", response_model=StatsResponse)
async def get_stats(
    admin_key: str = Depends(verify_admin_key),
    cache_manager = Depends(get_cache_manager)
):
    """
    Get detailed service statistics (admin only)
    
    Requires admin API key
    """
    metrics = metrics_collector.get_all_metrics()
    cache_stats = cache_manager.get_stats()
    
    return StatsResponse(
        total_requests=metrics["total_requests"],
        total_embeddings=metrics["total_embeddings"],
        cache_hits=metrics["cache_hits"],
        cache_misses=metrics["cache_misses"],
        cache_hit_rate=metrics["cache_hit_rate"],
        provider_usage=metrics["provider_usage"],
        uptime=metrics["uptime_seconds"],
        cache_info=cache_stats
    )


@router.get("/admin/cache/info", response_model=CacheInfoResponse)
async def get_cache_info(
    admin_key: str = Depends(verify_admin_key),
    cache_manager = Depends(get_cache_manager)
):
    """
    Get cache information (admin only)
    
    Requires admin API key
    """
    stats = cache_manager.get_stats()
    
    return CacheInfoResponse(
        enabled=cache_manager.enabled,
        backend=stats.get("backend", "unknown"),
        ttl=cache_manager.ttl,
        available=cache_manager.is_available(),
        stats=stats
    )


@router.post("/admin/cache/clear", response_model=MessageResponse)
async def clear_cache(
    admin_key: str = Depends(verify_admin_key),
    cache_manager = Depends(get_cache_manager)
):
    """
    Clear all cached embeddings (admin only)
    
    Requires admin API key
    """
    cache_manager.clear_all()
    
    return MessageResponse(
        message="Cache cleared successfully",
        success=True
    )