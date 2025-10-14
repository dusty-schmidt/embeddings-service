# app/core/providers/ollama.py

import aiohttp
from typing import List, Optional, Dict
from .base import BaseEmbeddingProvider, EmbeddingResult


class OllamaProvider(BaseEmbeddingProvider):
    """Ollama embedding provider - local, fast, free"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.timeout = config.get("timeout", 30)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def embed(self, text: str, model: Optional[str] = None) -> EmbeddingResult:
        """Generate embedding using Ollama"""
        model = model or self.get_default_model()
        session = await self._get_session()
        
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": model,
            "prompt": text
        }
        
        try:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                embedding = data.get("embedding", [])
                
                return EmbeddingResult(
                    embedding=embedding,
                    model=model,
                    dimensions=len(embedding),
                    provider="ollama",
                    tokens=None,  # Ollama doesn't return token count
                    metadata={
                        "model": model,
                        "base_url": self.base_url
                    }
                )
                
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Ollama API error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Ollama embedding failed: {str(e)}")
    
    async def embed_batch(
        self, 
        texts: List[str], 
        model: Optional[str] = None
    ) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts"""
        # Ollama doesn't have native batch support, so we do sequential
        results = []
        for text in texts:
            result = await self.embed(text, model)
            results.append(result)
        return results
    
    async def health_check(self) -> bool:
        """Check if Ollama is available"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/tags"
            
            async with session.get(url) as response:
                return response.status == 200
                
        except Exception:
            return False
    
    def get_available_models(self) -> List[Dict[str, any]]:
        """Get available Ollama models"""
        # Common Ollama embedding models
        return [
            {
                "name": "nomic-embed-text",
                "dimensions": 768,
                "description": "High-quality text embeddings"
            },
            {
                "name": "mxbai-embed-large",
                "dimensions": 1024,
                "description": "Large embedding model"
            },
            {
                "name": "all-minilm",
                "dimensions": 384,
                "description": "Fast and efficient"
            }
        ]
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()