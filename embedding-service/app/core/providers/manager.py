# app/core/providers/manager.py

from typing import Optional, List, Dict
from .base import BaseEmbeddingProvider, EmbeddingResult
from .ollama import OllamaProvider
from .huggingface import HuggingFaceProvider


class ProviderManager:
    """Manages embedding providers and handles fallback"""
    
    def __init__(self, config):
        self.config = config
        self.providers: Dict[str, BaseEmbeddingProvider] = {}
        self.default_provider_name = config.DEFAULT_PROVIDER
        self.fallback_enabled = config.FALLBACK_ENABLED
        
        # Initialize providers
        self._init_providers()
    
    def _init_providers(self):
        """Initialize all configured providers"""
        # Ollama
        ollama_config = self.config.get_provider_config("ollama")
        self.providers["ollama"] = OllamaProvider(ollama_config)
        
        # HuggingFace
        if self.config.HUGGINGFACE_API_KEY:
            hf_config = self.config.get_provider_config("huggingface")
            self.providers["huggingface"] = HuggingFaceProvider(hf_config)
    
    def get_provider(self, name: Optional[str] = None) -> BaseEmbeddingProvider:
        """
        Get a provider by name
        
        Args:
            name: Provider name (ollama, huggingface). If None, returns default.
            
        Returns:
            Provider instance
            
        Raises:
            ValueError if provider not found
        """
        provider_name = name or self.default_provider_name
        
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not available")
        
        return self.providers[provider_name]
    
    async def embed(
        self, 
        text: str, 
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> EmbeddingResult:
        """
        Generate embedding with automatic fallback
        
        Args:
            text: Text to embed
            model: Optional model name
            provider: Optional provider name
            
        Returns:
            EmbeddingResult
        """
        primary_provider = self.get_provider(provider)
        
        try:
            return await primary_provider.embed(text, model)
        except Exception as e:
            # Try fallback if enabled
            if self.fallback_enabled and len(self.providers) > 1:
                # Get alternative provider
                fallback_name = self._get_fallback_provider(
                    primary_provider.name
                )
                
                if fallback_name:
                    fallback_provider = self.providers[fallback_name]
                    try:
                        result = await fallback_provider.embed(text, model)
                        # Add fallback info to metadata
                        result.metadata["fallback"] = True
                        result.metadata["primary_provider"] = primary_provider.name
                        result.metadata["primary_error"] = str(e)
                        return result
                    except Exception as fallback_error:
                        raise RuntimeError(
                            f"Primary provider failed: {str(e)}. "
                            f"Fallback also failed: {str(fallback_error)}"
                        )
            
            # No fallback or fallback disabled
            raise
    
    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> List[EmbeddingResult]:
        """
        Generate batch embeddings with automatic fallback
        
        Args:
            texts: List of texts to embed
            model: Optional model name
            provider: Optional provider name
            
        Returns:
            List of EmbeddingResult
        """
        primary_provider = self.get_provider(provider)
        
        try:
            return await primary_provider.embed_batch(texts, model)
        except Exception as e:
            # Try fallback if enabled
            if self.fallback_enabled and len(self.providers) > 1:
                fallback_name = self._get_fallback_provider(
                    primary_provider.name
                )
                
                if fallback_name:
                    fallback_provider = self.providers[fallback_name]
                    try:
                        results = await fallback_provider.embed_batch(texts, model)
                        # Add fallback info to all results
                        for result in results:
                            result.metadata["fallback"] = True
                            result.metadata["primary_provider"] = primary_provider.name
                            result.metadata["primary_error"] = str(e)
                        return results
                    except Exception as fallback_error:
                        raise RuntimeError(
                            f"Primary provider failed: {str(e)}. "
                            f"Fallback also failed: {str(fallback_error)}"
                        )
            
            # No fallback or fallback disabled
            raise
    
    def _get_fallback_provider(self, primary_name: str) -> Optional[str]:
        """Get fallback provider name"""
        # Simple strategy: use the other provider
        available = [name for name in self.providers.keys() if name != primary_name]
        return available[0] if available else None
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers"""
        health = {}
        for name, provider in self.providers.items():
            try:
                health[name] = await provider.health_check()
            except Exception:
                health[name] = False
        return health
    
    def get_all_models(self) -> Dict[str, List[Dict]]:
        """Get all available models from all providers"""
        models = {}
        for name, provider in self.providers.items():
            models[name] = provider.get_available_models()
        return models
    
    async def close_all(self):
        """Close all provider connections"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()