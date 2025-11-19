"""
Utility functions for conversation handling.
"""

from typing import List, Any
from fastapi import HTTPException
from src.core.function_tools import (
    wrap_search_tutor_service,
    wrap_search_course_service,
    wrap_get_course_by_userid_service,
    wrap_get_course_details_service,
    wrap_place_order_service,
)
import logging

logger = logging.getLogger(__name__)


def validate_and_get_tools(tool_names: List[str], authorization: str = None) -> List[Any]:
    """Validate requested tools and return available tools."""
    try:
        # Create wrapper config with authorization token
        wrapper_config = {"authorization": authorization or ""}
        
        # Map of available function tools
        available_tools = {
            "search_tutor": wrap_search_tutor_service(wrapper_config),
            "search_course": wrap_search_course_service(wrapper_config),
            "get_course_by_userid": wrap_get_course_by_userid_service(wrapper_config),
            "get_course_details": wrap_get_course_details_service(wrapper_config),
            "place_order": wrap_place_order_service(wrapper_config),
        }
        
        tools = []
        missing_tools = []
        
        for tool_name in tool_names:
            if tool_name in available_tools:
                tools.append(available_tools[tool_name])
            else:
                missing_tools.append(tool_name)
        
        if missing_tools:
            logger.error(f"Tools not found: {', '.join(missing_tools)}")
            raise HTTPException(status_code=404, detail=f"Tools not found: {', '.join(missing_tools)}")
        
        return tools
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get function tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load function tools: {e}")


def get_error_fallback_message(error_str: str) -> str:
    """Generate appropriate fallback message based on error type."""
    error_lower = error_str.lower()
    if "connection" in error_lower:
        return "I'm experiencing connection issues right now. Please try again in a moment."
    elif "timeout" in error_lower:
        return "The request is taking longer than expected. Please try again."
    else:
        return "I'm currently experiencing technical difficulties. Please try again later."


def extract_regeneration_instructions(validation_result: str) -> str:
    """Extract regeneration instructions from validation result."""
    try:
        # Look for REGENERATION_INSTRUCTIONS section
        if "REGENERATION_INSTRUCTIONS:" in validation_result:
            parts = validation_result.split("REGENERATION_INSTRUCTIONS:")
            if len(parts) > 1:
                instructions = parts[1].split("REQUIRED_CORRECTIONS:")[0].strip()
                return instructions
        
        # Fallback: return the whole validation result
        return validation_result
    except Exception as e:
        logger.error(f"Error extracting regeneration instructions: {e}")
        return validation_result
