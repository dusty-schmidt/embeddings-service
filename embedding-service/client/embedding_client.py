# client/embedding_client.py

import requests
from typing import List, Dict, Optional, Any


class EmbeddingClient:
    """Client for the centralized embedding service"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def embed(self, text: str, model: Optional[str] = None, provider: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            model: Optional model override
            provider: Optional provider (ollama, huggingface)
            use_cache: Whether to use cached embeddings
            
        Returns:
            dict with embedding, dimensions, tokens, etc.
        """
        payload = {
            "text": text,
            "use_cache": use_cache
        }
        
        if model:
            payload["model"] = model
        if provider:
            payload["provider"] = provider
        
        response = requests.post(
            f"{self.base_url}/api/embed",
            headers=self.headers,
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
    
    def embed_batch(self, texts: List[str], model: Optional[str] = None, provider: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            model: Optional model override
            provider: Optional provider (ollama, huggingface)
            use_cache: Whether to use cached embeddings
            
        Returns:
            dict with embeddings list, total tokens, cached count, etc.
        """
        payload = {
            "texts": texts,
            "use_cache": use_cache
        }
        
        if model:
            payload["model"] = model
        if provider:
            payload["provider"] = provider
        
        response = requests.post(
            f"{self.base_url}/api/embed/batch",
            headers=self.headers,
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
    
    def search_knowledge(self, query: str, limit: int = 5, score_threshold: Optional[float] = None, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search the knowledge base
        
        Args:
            query: Search query
            limit: Max number of results
            score_threshold: Minimum similarity score
            filters: Metadata filters
            
        Returns:
            dict with search results
        """
        payload = {
            "query": query,
            "limit": limit
        }
        
        if score_threshold is not None:
            payload["score_threshold"] = score_threshold
        if filters:
            payload["filters"] = filters
        
        response = requests.post(
            f"{self.base_url}/knowledge/search",
            headers=self.headers,
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        response = requests.get(
            f"{self.base_url}/knowledge/stats",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_providers(self) -> Dict[str, Any]:
        """Get available embedding providers"""
        response = requests.get(
            f"{self.base_url}/providers",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        response = requests.get(f"{self.base_url}/metrics")
        response.raise_for_status()
        return response.json()