# app/models/responses.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class EmbedResponse(BaseModel):
    """Response for single embedding"""
    
    embedding: List[float] = Field(..., description="The embedding vector")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider used")
    dimensions: int = Field(..., description="Embedding dimensions")
    tokens: Optional[int] = Field(None, description="Token count (if available)")
    cached: bool = Field(..., description="Whether result was cached")
    timestamp: str = Field(..., description="Request timestamp")
    request_id: str = Field(..., description="Unique request identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchEmbedResponse(BaseModel):
    """Response for batch embeddings"""
    
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider used")
    dimensions: int = Field(..., description="Embedding dimensions")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")
    count: int = Field(..., description="Number of embeddings")
    cached_count: int = Field(..., description="Number of cached results")
    timestamp: str = Field(..., description="Request timestamp")
    request_id: str = Field(..., description="Unique request identifier")


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Current timestamp")
    cache_available: bool = Field(..., description="Whether cache is available")
    providers: Dict[str, bool] = Field(..., description="Provider health status")


class MetricsResponse(BaseModel):
    """Metrics response"""
    
    total_requests: int = Field(..., description="Total requests processed")
    cache_hits: int = Field(..., description="Cache hits")
    cache_misses: int = Field(..., description="Cache misses")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")
    provider_usage: Dict[str, int] = Field(..., description="Usage per provider")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


class StatsResponse(BaseModel):
    """Admin statistics response"""
    
    total_requests: int
    total_embeddings: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    provider_usage: Dict[str, int]
    uptime: float
    cache_info: Dict[str, Any]


class ProviderInfo(BaseModel):
    """Information about a provider"""
    
    name: str = Field(..., description="Provider name")
    available: bool = Field(..., description="Whether provider is available")
    default_model: str = Field(..., description="Default model")
    models: List[Dict[str, Any]] = Field(..., description="Available models")


class ProvidersResponse(BaseModel):
    """Response listing all providers"""
    
    default_provider: str = Field(..., description="Default provider name")
    providers: List[ProviderInfo] = Field(..., description="List of providers")


class CacheInfoResponse(BaseModel):
    """Cache information response"""
    
    enabled: bool
    backend: str
    ttl: int
    available: bool
    stats: Dict[str, Any]


class MessageResponse(BaseModel):
    """Generic message response"""
    
    message: str = Field(..., description="Response message")
    success: bool = Field(True, description="Whether operation was successful")


class SearchResult(BaseModel):
    """Single search result"""
    text: str = Field(..., description="Matched text")
    score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(..., description="Result metadata")


class SearchResponse(BaseModel):
    """Response from knowledge search"""
    query: str
    results: List[SearchResult]
    count: int


class CollectionStats(BaseModel):
    """Knowledge base collection statistics"""
    collection_name: str
    total_vectors: int
    total_points: int
    status: str