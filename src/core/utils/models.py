"""
Pydantic models and type definitions for the conversation API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage

# Constants
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2
DEFAULT_TEMPERATURE = 0.7

# Streaming response headers
STREAMING_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
}


class ConversationRequest(BaseModel):
    """Request model for conversation endpoints."""
    message: str = Field(..., description="The message from the user.")
    tool_names: Optional[List[str]] = Field(None, description="A list of tool names to use.")
    session_id: str = Field(..., description="The ID for the chat session.")
    workflow: Optional[str] = Field("general", description="The workflow type (course, translator, chat, conversation, general).")
    temperature: float = Field(
        DEFAULT_TEMPERATURE, ge=0.0, le=1.0, description="The sampling temperature for the LLM."
    )
    reflection: bool = Field(False, description="Whether to reflect on the response with the reflection agent for quality improvement.")


class SessionManagementRequest(BaseModel):
    """Request model for session management endpoints."""
    session_id: str = Field(..., description="The ID for the chat session.")


# State definition for reflection graph
class ReflectionState(TypedDict):
    """State for the reflection agent graph."""
    user_message: str
    original_response: str
    tool_outputs: Optional[str]
    current_response: str
    validation_result: str
    is_approved: bool
    retry_count: int
    max_retries: int
    final_response: str
    workflow: str
