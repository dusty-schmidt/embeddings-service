# app/models/requests.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List


class EmbedRequest(BaseModel):
    """Request to generate a single embedding"""
    
    text: str = Field(
        ...,
        description="Text to embed",
        min_length=1,
        max_length=8000
    )
    model: Optional[str] = Field(
        None,
        description="Model to use (provider-specific)"
    )
    provider: Optional[str] = Field(
        None,
        description="Provider to use (ollama, huggingface)"
    )
    use_cache: bool = Field(
        True,
        description="Whether to use cached embeddings"
    )
    
    @validator('text')
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()
    
    @validator('provider')
    def valid_provider(cls, v):
        if v and v not in ['ollama', 'huggingface']:
            raise ValueError('Provider must be ollama or huggingface')
        return v


class BatchEmbedRequest(BaseModel):
    """Request to generate multiple embeddings"""
    
    texts: List[str] = Field(
        ...,
        description="List of texts to embed",
        min_items=1,
        max_items=100
    )
    model: Optional[str] = Field(
        None,
        description="Model to use (provider-specific)"
    )
    provider: Optional[str] = Field(
        None,
        description="Provider to use (ollama, huggingface)"
    )
    use_cache: bool = Field(
        True,
        description="Whether to use cached embeddings"
    )
    
    @validator('texts')
    def validate_texts(cls, v):
        if not v:
            raise ValueError('Texts list cannot be empty')
        
        # Check each text
        cleaned = []
        for i, text in enumerate(v):
            if not text or not text.strip():
                raise ValueError(f'Text at index {i} is empty')
            if len(text) > 8000:
                raise ValueError(f'Text at index {i} exceeds maximum length')
            cleaned.append(text.strip())
        
        return cleaned
    
    @validator('provider')
    def valid_provider(cls, v):
        if v and v not in ['ollama', 'huggingface']:
            raise ValueError('Provider must be ollama or huggingface')
        return v