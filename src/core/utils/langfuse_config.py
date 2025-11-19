"""
Langfuse initialization and tracing utilities.
"""

from typing import Optional
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from src.core.utils.settings import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Global Langfuse instances
langfuse: Optional[Langfuse] = None
langfuse_handler: Optional[CallbackHandler] = None


def initialize_langfuse():
    """Initialize Langfuse for tracing and observability."""
    global langfuse, langfuse_handler
    
    if settings.langfuse_enable:
        try:
            # Initialize Langfuse client with optional configuration
            langfuse_config = {}
            if hasattr(settings, 'langfuse_public_key') and settings.langfuse_public_key:
                langfuse_config['public_key'] = settings.langfuse_public_key
            if hasattr(settings, 'langfuse_secret_key') and settings.langfuse_secret_key:
                langfuse_config['secret_key'] = settings.langfuse_secret_key
            if hasattr(settings, 'langfuse_host') and settings.langfuse_host:
                langfuse_config['host'] = settings.langfuse_host
                
            langfuse = Langfuse(**langfuse_config) if langfuse_config else Langfuse()
            langfuse_handler = CallbackHandler()
            logger.info("Langfuse initialized successfully for conversation tracing")
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse: {e}. Continuing without tracing.")
            langfuse = None
            langfuse_handler = None
    else:
        logger.info("Langfuse tracing disabled")


def get_langfuse_handler_with_trace(session_id: str, workflow: str, user_message: str) -> Optional[CallbackHandler]:
    """Create a Langfuse handler with trace information for the current conversation."""
    if not langfuse or not langfuse_handler:
        return None
    
    try:
        # Create a new trace for this conversation
        trace = langfuse.api.trace(
            name=f"conversation_{workflow}",
            user_id=session_id,
            session_id=session_id,
            metadata={
                "workflow": workflow,
                "user_message": user_message[:100] + "..." if len(user_message) > 100 else user_message,
                "endpoint": "conversation_api"
            }
        )
        
        # Create a new handler with the trace
        handler = CallbackHandler(trace=trace)
        return handler
    except Exception as e:
        logger.warning(f"Failed to create Langfuse trace: {e}")
        return langfuse_handler  # Fallback to basic handler


# Initialize on module load
initialize_langfuse()
