"""
Session memory management for conversations.
"""

from typing import Dict, List
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import BaseMessage, HumanMessage
import logging

logger = logging.getLogger(__name__)

# Global session memory storage
memory_by_session: Dict[str, ConversationBufferMemory] = {}


def get_session_memory(session_id: str) -> ConversationBufferMemory:
    """Get or create session-specific memory."""
    if session_id not in memory_by_session:
        memory_by_session[session_id] = ConversationBufferMemory(return_messages=True)
    return memory_by_session[session_id]


def clear_session_memory(session_id: str) -> bool:
    """Clear memory for a specific session."""
    if session_id in memory_by_session:
        del memory_by_session[session_id]
        return True
    return False


def prepare_messages(session_memory: ConversationBufferMemory, user_message: str) -> List[BaseMessage]:
    """Prepare messages for LLM processing."""
    # Get conversation history
    history = session_memory.chat_memory.messages
    messages = []
    
    # Add conversation history
    for message in history:
        messages.append(message)
    
    # Add current user message
    messages.append(HumanMessage(content=user_message))
    
    return messages


def save_conversation_context(session_memory: ConversationBufferMemory, user_input: str, ai_output: str) -> None:
    """Save conversation context to session memory with error handling."""
    try:
        session_memory.save_context({"input": user_input}, {"output": ai_output})
        logger.debug(f"Saved conversation context for session")
    except Exception as e:
        logger.error(f"Failed to save conversation context: {e}")


def get_session_history(session_id: str) -> str:
    """Get conversation history for a session."""
    if session_id in memory_by_session:
        return memory_by_session[session_id].buffer_as_str
    return None
