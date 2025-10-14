# app/api/endpoints/providers.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from app.models.responses import ProvidersResponse, ProviderInfo
from app.api.deps import get_provider_manager, verify_api_key
from app.config import get_settings

router = APIRouter()


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers(
    api_key: str = Depends(verify_api_key),
    provider_manager = Depends(get_provider_manager)
):
    """
    List all available providers and their models
    
    Returns information about each provider including:
    - Availability status
    - Default model
    - Available models with dimensions
    """
    settings = get_settings()
    
    # Get health status for all providers
    health_status = await provider_manager.health_check_all()
    
    # Get all models
    all_models = provider_manager.get_all_models()
    
    # Build provider info list
    providers_info = []
    for name, provider in provider_manager.providers.items():
        providers_info.append(ProviderInfo(
            name=name,
            available=health_status.get(name, False),
            default_model=provider.get_default_model(),
            models=all_models.get(name, [])
        ))
    
    return ProvidersResponse(
        default_provider=settings.DEFAULT_PROVIDER,
        providers=providers_info
    )


@router.get("/providers/{provider_name}/status")
async def check_provider_status(
    provider_name: str,
    api_key: str = Depends(verify_api_key),
    provider_manager = Depends(get_provider_manager)
) -> Dict[str, any]:
    """
    Check if a specific provider is available
    
    - **provider_name**: Name of the provider (ollama, huggingface)
    """
    try:
        provider = provider_manager.get_provider(provider_name)
        is_healthy = await provider.health_check()
        
        return {
            "provider": provider_name,
            "available": is_healthy,
            "default_model": provider.get_default_model()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))