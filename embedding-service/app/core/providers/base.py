# app/core/providers/base.py

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Result from an embedding operation"""
    embedding: List[float]
    model: str
    dimensions: int
    provider: str
    tokens: Optional[int] = None
    metadata: Optional[Dict] = None


class BaseEmbeddingProvider(ABC):
    """Base class for all embedding providers"""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = self.__class__.__name__.replace("Provider", "").lower()
    
    @abstractmethod
    async def embed(self, text: str, model: Optional[str] = None) -> EmbeddingResult:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            model: Optional model override
            
        Returns:
            EmbeddingResult with embedding and metadata
        """
        pass
    
    @abstractmethod
    async def embed_batch(
        self, 
        texts: List[str], 
        model: Optional[str] = None
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            model: Optional model override
            
        Returns:
            List of EmbeddingResult
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if provider is available
        
        Returns:
            True if provider is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[Dict[str, any]]:
        """
        Get list of available models
        
        Returns:
            List of model information dicts
        """
        pass
    
    def get_default_model(self) -> str:
        """Get the default model for this provider"""
        return self.config.get("default_model", "")
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"