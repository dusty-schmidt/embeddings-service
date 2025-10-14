# app/api/endpoints/knowledge.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.api.deps import get_provider_manager, verify_api_key
from app.core.vector_store import VectorStore
from app.config import get_settings

router = APIRouter()


# Request/Response Models
class SearchRequest(BaseModel):
    """Request to search knowledge base"""
    query: str = Field(..., description="Search query text")
    limit: int = Field(5, ge=1, le=50, description="Number of results")
    score_threshold: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Minimum similarity score (0-1)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata filters (e.g., {'source': 'article.txt'})"
    )


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


# Dependency to get vector store
def get_vector_store() -> VectorStore:
    """Get Qdrant vector store instance"""
    settings = get_settings()
    
    qdrant_host = getattr(settings, 'QDRANT_HOST', 'localhost')
    qdrant_port = getattr(settings, 'QDRANT_PORT', 6333)
    qdrant_api_key = getattr(settings, 'QDRANT_API_KEY', None)
    
    return VectorStore(
        host=qdrant_host,
        port=qdrant_port,
        api_key=qdrant_api_key
    )


@router.post("/knowledge/search", response_model=SearchResponse)
async def search_knowledge(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key),
    provider_manager = Depends(get_provider_manager),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Search the knowledge base with semantic search
    
    - **query**: Your search query
    - **limit**: Max number of results (1-50)
    - **score_threshold**: Minimum similarity score (optional)
    - **filters**: Metadata filters (optional)
    """
    settings = get_settings()
    collection_name = getattr(settings, 'QDRANT_COLLECTION', 'knowledge_base')
    
    try:
        # Get embedding for query
        query_result = await provider_manager.embed(
            text=request.query,
            model=None,
            provider=None
        )
        
        # Search in Qdrant
        results = vector_store.search(
            collection_name=collection_name,
            query_vector=query_result.embedding,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filter_conditions=request.filters
        )
        
        # Format results
        search_results = [
            SearchResult(
                text=r["text"],
                score=r["score"],
                metadata=r["metadata"]
            )
            for r in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            count=len(search_results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/knowledge/stats", response_model=CollectionStats)
async def get_knowledge_stats(
    api_key: str = Depends(verify_api_key),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Get statistics about the knowledge base
    
    Returns total number of vectors, points, and collection status
    """
    settings = get_settings()
    collection_name = getattr(settings, 'QDRANT_COLLECTION', 'knowledge_base')
    
    try:
        info = vector_store.get_collection_info(collection_name)
        
        return CollectionStats(
            collection_name=collection_name,
            total_vectors=info["vectors_count"],
            total_points=info["points_count"],
            status=info["status"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/knowledge/health")
async def check_knowledge_health(
    api_key: str = Depends(verify_api_key),
    vector_store: VectorStore = Depends(get_vector_store)
) -> Dict[str, Any]:
    """
    Check if Qdrant vector store is available
    """
    is_available = vector_store.is_available()
    
    return {
        "qdrant_available": is_available,
        "status": "healthy" if is_available else "unavailable"
    }