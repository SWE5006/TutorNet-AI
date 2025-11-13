"""
ReAct agent creation for tool-based conversations.
"""

from typing import List, Any, Optional
from fastapi import HTTPException
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent as langgraph_create_react_agent
from src.core.utils.system_prompts import get_agent_system_prompt_for_workflow
from src.core.utils.langfuse_config import get_langfuse_handler_with_trace
import logging

logger = logging.getLogger(__name__)


def create_react_agent(
    llm_instance,
    tools: List[Any],
    workflow: str = "general",
    session_id: Optional[str] = None,
    user_message: Optional[str] = None
):
    """
    Create a ReAct agent with the given LLM and tools.
    
    Args:
        llm_instance: The LLM instance to use
        tools: List of tools available to the agent
        workflow: The workflow type (general, assistant, etc.)
        session_id: Session ID for tracing
        user_message: User message for tracing context
        
    Returns:
        Compiled ReAct agent graph
        
    Raises:
        HTTPException: If agent creation fails
    """
    try:
        agent_system_prompt = get_agent_system_prompt_for_workflow(workflow)
        system_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=agent_system_prompt),
            ("placeholder", "{messages}"),
        ])
        logger.debug(
            f"Creating ReAct agent with {len(tools)} tools: "
            f"{[t.name for t in tools]} for workflow: {workflow}"
        )
        
        # Add Langfuse callback to LLM if available
        trace_handler = get_langfuse_handler_with_trace(
            session_id or "unknown",
            workflow,
            user_message or ""
        )
        if trace_handler:
            # Update LLM instance with Langfuse callback
            llm_instance.callbacks = [trace_handler]
            
        return langgraph_create_react_agent(
            model=llm_instance,
            tools=tools,
            prompt=system_prompt
        )
    except Exception as e:
        logger.error(f"Failed to create ReAct agent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ReAct agent: {e}"
        )
