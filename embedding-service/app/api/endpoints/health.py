# app/api/endpoints/embeddings.py

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import hashlib
import time

from app.models.requests import EmbedRequest, BatchEmbedRequest
from app.models.responses import EmbedResponse, BatchEmbedResponse
from app.api.deps import (
    get_cache_manager,
    get_provider_manager,
    get_rate_limiter,
    verify_api_key
)
from app.core.auth import get_api_key_hash
from app.utils.metrics import metrics_collector
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/embed", response_model=EmbedResponse)
async def create_embedding(
    request: EmbedRequest,
    api_key: str = Depends(verify_api_key),
    cache_manager = Depends(get_cache_manager),
    provider_manager = Depends(get_provider_manager),
    rate_limiter = Depends(get_rate_limiter)
):
    """
    Generate embedding for a single text
    
    - **text**: Text to embed
    - **model**: Optional model name (provider-specific)
    - **provider**: Optional provider (ollama, huggingface)
    - **use_cache**: Whether to use cached results
    """
    start_time = time.time()
    
    # Rate limiting
    rate_limiter.check_rate_limit(api_key)
    
    # Generate request ID
    request_id = hashlib.sha256(
        f"{request.text[:50]}{datetime.utcnow()}".encode()
    ).hexdigest()[:16]
    
    # Record request
    metrics_collector.record_request()
    metrics_collector.record_embeddings(1)
    
    cached = False
    result = None
    
    # Try cache first
    if request.use_cache:
        provider = request.provider or provider_manager.default_provider_name
        model = request.model or provider_manager.get_provider(provider).get_default_model()
        cache_key = cache_manager.generate_key(request.text, model, provider)
        
        cached_data = cache_manager.get(cache_key)
        if cached_data:
            cached = True
            metrics_collector.record_cache_hit()
            
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                "Embedding request (cached)",
                extra={
                    "request_id": request_id,
                    "api_key_hash": get_api_key_hash(api_key),
                    "provider": provider,
                    "model": model,
                    "cached": True,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            
            return EmbedResponse(
                embedding=cached_data["embedding"],
                model=cached_data["model"],
                provider=cached_data["provider"],
                dimensions=cached_data["dimensions"],
                tokens=cached_data.get("tokens"),
                cached=True,
                timestamp=datetime.utcnow().isoformat(),
                request_id=request_id,
                metadata=cached_data.get("metadata")
            )
    
    # Generate new embedding
    try:
        metrics_collector.record_cache_miss()
        
        result = await provider_manager.embed(
            text=request.text,
            model=request.model,
            provider=request.provider
        )
        
        metrics_collector.record_provider_usage(result.provider)
        
        # Cache the result
        if request.use_cache:
            cache_key = cache_manager.generate_key(
                request.text, 
                result.model, 
                result.provider
            )
            cache_manager.set(cache_key, {
                "embedding": result.embedding,
                "model": result.model,
                "provider": result.provider,
                "dimensions": result.dimensions,
                "tokens": result.tokens,
                "metadata": result.metadata
            })
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "Embedding request (generated)",
            extra={
                "request_id": request_id,
                "api_key_hash": get_api_key_hash(api_key),
                "provider": result.provider,
                "model": result.model,
                "cached": False,
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        return EmbedResponse(
            embedding=result.embedding,
            model=result.model,
            provider=result.provider,
            dimensions=result.dimensions,
            tokens=result.tokens,
            cached=False,
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id,
            metadata=result.metadata
        )
        
    except Exception as e:
        metrics_collector.record_error()
        logger.error(
            f"Embedding generation failed: {str(e)}",
            extra={
                "request_id": request_id,
                "api_key_hash": get_api_key_hash(api_key)
            }
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embed/batch", response_model=BatchEmbedResponse)
async def create_batch_embeddings(
    request: BatchEmbedRequest,
    api_key: str = Depends(verify_api_key),
    cache_manager = Depends(get_cache_manager),
    provider_manager = Depends(get_provider_manager),
    rate_limiter = Depends(get_rate_limiter)
):
    """
    Generate embeddings for multiple texts
    
    - **texts**: List of texts to embed (max 100)
    - **model**: Optional model name (provider-specific)
    - **provider**: Optional provider (ollama, huggingface)
    - **use_cache**: Whether to use cached results
    """
    start_time = time.time()
    
    # Rate limiting
    rate_limiter.check_rate_limit(api_key)
    
    # Generate request ID
    request_id = hashlib.sha256(
        f"{len(request.texts)}{datetime.utcnow()}".encode()
    ).hexdigest()[:16]
    
    # Record request
    metrics_collector.record_request()
    metrics_collector.record_embeddings(len(request.texts))
    
    provider = request.provider or provider_manager.default_provider_name
    model = request.model or provider_manager.get_provider(provider).get_default_model()
    
    embeddings = []
    cached_count = 0
    total_tokens = 0
    
    # Process each text
    for text in request.texts:
        # Try cache
        if request.use_cache:
            cache_key = cache_manager.generate_key(text, model, provider)
            cached_data = cache_manager.get(cache_key)
            
            if cached_data:
                embeddings.append(cached_data["embedding"])
                cached_count += 1
                metrics_collector.record_cache_hit()
                if cached_data.get("tokens"):
                    total_tokens += cached_data["tokens"]
                continue
        
        # Generate new embedding
        try:
            metrics_collector.record_cache_miss()
            
            result = await provider_manager.embed(
                text=text,
                model=request.model,
                provider=request.provider
            )
            
            embeddings.append(result.embedding)
            if result.tokens:
                total_tokens += result.tokens
            
            # Cache it
            if request.use_cache:
                cache_key = cache_manager.generate_key(text, result.model, result.provider)
                cache_manager.set(cache_key, {
                    "embedding": result.embedding,
                    "model": result.model,
                    "provider": result.provider,
                    "dimensions": result.dimensions,
                    "tokens": result.tokens,
                    "metadata": result.metadata
                })
                
        except Exception as e:
            metrics_collector.record_error()
            logger.error(
                f"Batch embedding failed for text: {str(e)}",
                extra={"request_id": request_id}
            )
            raise HTTPException(status_code=500, detail=f"Failed on text: {str(e)}")
    
    metrics_collector.record_provider_usage(provider)
    
    duration_ms = (time.time() - start_time) * 1000
    
    logger.info(
        "Batch embedding request",
        extra={
            "request_id": request_id,
            "api_key_hash": get_api_key_hash(api_key),
            "provider": provider,
            "model": model,
            "count": len(embeddings),
            "cached_count": cached_count,
            "duration_ms": round(duration_ms, 2)
        }
    )
    
    return BatchEmbedResponse(
        embeddings=embeddings,
        model=model,
        provider=provider,
        dimensions=len(embeddings[0]) if embeddings else 0,
        total_tokens=total_tokens if total_tokens > 0 else None,
        count=len(embeddings),
        cached_count=cached_count,
        timestamp=datetime.utcnow().isoformat(),
        request_id=request_id
    )