# app/core/providers/huggingface.py

import aiohttp
from typing import List, Optional, Dict
from .base import BaseEmbeddingProvider, EmbeddingResult


class HuggingFaceProvider(BaseEmbeddingProvider):
    """HuggingFace embedding provider - cloud-based, reliable"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.timeout = config.get("timeout", 30)
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        return self.session
    
    async def embed(self, text: str, model: Optional[str] = None) -> EmbeddingResult:
        """Generate embedding using HuggingFace"""
        model = model or self.get_default_model()
        session = await self._get_session()
        
        url = f"{self.api_url}/{model}"
        payload = {
            "inputs": text
        }
        
        try:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                # HuggingFace returns embeddings directly
                # Handle both single vector and batched responses
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], list):
                        # Batched response, take first
                        embedding = data[0]
                    else:
                        # Single vector
                        embedding = data
                else:
                    raise ValueError("Unexpected response format from HuggingFace")
                
                return EmbeddingResult(
                    embedding=embedding,
                    model=model,
                    dimensions=len(embedding),
                    provider="huggingface",
                    tokens=None,  # HF doesn't return token count in free tier
                    metadata={
                        "model": model
                    }
                )
                
        except aiohttp.ClientError as e:
            raise ConnectionError(f"HuggingFace API error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"HuggingFace embedding failed: {str(e)}")
    
    async def embed_batch(
        self, 
        texts: List[str], 
        model: Optional[str] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts"""
        model = model or self.get_default_model()
        session = await self._get_session()
        
        url = f"{self.api_url}/{model}"
        payload = {
            "inputs": texts
        }
        
        try:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                # HuggingFace returns list of embeddings for batch
                results = []
                for embedding in data:
                    results.append(EmbeddingResult(
                        embedding=embedding,
                        model=model,
                        dimensions=len(embedding),
                        provider="huggingface",
                        tokens=None,
                        metadata={"model": model}
                    ))
                
                return results
                
        except aiohttp.ClientError as e:
            raise ConnectionError(f"HuggingFace API error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"HuggingFace batch embedding failed: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if HuggingFace API is available"""
        if not self.api_key:
            return False
        
        try:
            # Try a simple embedding to check health
            await self.embed("test", self.get_default_model())
            return True
        except Exception:
            return False
    
    def get_available_models(self) -> List[Dict[str, any]]:
        """Get available HuggingFace models"""
        return [
            {
                "name": "sentence-transformers/all-MiniLM-L6-v2",
                "dimensions": 384,
                "description": "Fast and efficient, good for most tasks"
            },
            {
                "name": "sentence-transformers/all-mpnet-base-v2",
                "dimensions": 768,
                "description": "High quality, balanced performance"
            },
            {
                "name": "BAAI/bge-small-en-v1.5",
                "dimensions": 384,
                "description": "Optimized for retrieval tasks"
            },
            {
                "name": "BAAI/bge-base-en-v1.5",
                "dimensions": 768,
                "description": "Larger retrieval model"
            }
        ]
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()