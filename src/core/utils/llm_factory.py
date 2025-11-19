"""
LLM instance creation and management.
"""

from typing import Dict, Any
from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from src.core.utils.settings import get_settings
from src.core.utils.models import ConversationRequest, REQUEST_TIMEOUT, MAX_RETRIES
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def create_common_llm_params(request: ConversationRequest) -> Dict[str, Any]:
    """Create common LLM parameters used across all providers."""
    return {
        "temperature": request.temperature,
        "streaming": True,
        "request_timeout": REQUEST_TIMEOUT,
        "max_retries": MAX_RETRIES,
    }


def create_qwen_openai_instance(request: ConversationRequest) -> ChatOpenAI:
    """Create Qwen OpenAI compatible instance with proper validation."""
    if not (settings.qwen_openai_url and settings.openai_api_key and settings.llm_model_name):
        logger.error("Qwen OpenAI settings are incomplete")
        raise HTTPException(status_code=500, detail="Qwen OpenAI settings are incomplete.")
    
    # Use visual model for censorship workflow, otherwise use regular model
    if request.workflow == "censorship" and settings.llm_visual_model_name:
        model_to_use = settings.llm_visual_model_name
        logger.debug(f"Initializing Qwen OpenAI Visual LLM for censorship: {model_to_use}")
    else:
        model_to_use = settings.llm_model_name
        logger.debug(f"Initializing Qwen OpenAI LLM: {model_to_use}")

    return ChatOpenAI(
        base_url=settings.qwen_openai_url,
        api_key=settings.openai_api_key,
        model=model_to_use,
        **create_common_llm_params(request)
    )


def create_openai_instance(request: ConversationRequest) -> ChatOpenAI:
    """Create OpenAI instance with proper validation."""
    if not (settings.openai_api_key and settings.llm_model_name):
        logger.error("OpenAI settings are incomplete")
        raise HTTPException(status_code=500, detail="OpenAI settings are incomplete.")
    
    # Use visual model for censorship workflow, otherwise use regular model
    if request.workflow == "censorship" and settings.llm_visual_model_name:
        model_to_use = settings.llm_visual_model_name
        logger.debug(f"Initializing OpenAI Visual LLM for censorship: {model_to_use}")
    else:
        model_to_use = settings.llm_model_name
        logger.debug(f"Initializing OpenAI LLM: {model_to_use}")

    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=model_to_use,
        **create_common_llm_params(request)
    )


def get_llm_instance(request: ConversationRequest) -> ChatOpenAI:
    """Get the appropriate LLM instance based on settings with fallback logic."""
    try:
        # Try Qwen OpenAI first if configured
        if settings.qwen_openai_enabled:
            return create_qwen_openai_instance(request)
        # Fallback to OpenAI
        else:
            return create_openai_instance(request)
    except Exception as e:
        logger.error(f"Failed to create LLM instance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize LLM: {e}")
