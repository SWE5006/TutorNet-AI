"""
Streaming response handlers for TutorNet-AI conversation API.

This module contains functions for creating streaming responses for both
agent-based conversations (with tools) and regular LLM conversations.
Supports optional reflection-based response validation and improvement.
"""

import json
import logging
from typing import List, AsyncGenerator, Optional

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from fastapi import Header
from fastapi.responses import StreamingResponse

from src.core.utils.system_prompts import get_regular_system_prompt_for_workflow
from src.core.utils.models import ConversationRequest
from src.core.utils.agents.reflection_graph import reflect_on_response_with_agent
from src.core.utils.agents.react_agent import create_react_agent
from src.core.utils.langfuse_config import get_langfuse_handler_with_trace
from src.core.utils.memory_manager import save_conversation_context
from src.core.utils.api_utils import get_error_fallback_message, validate_and_get_tools


logger = logging.getLogger(__name__)

# Streaming headers for SSE (Server-Sent Events)
STREAMING_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "text/event-stream",
    "X-Accel-Buffering": "no",
}


async def create_agent_response_stream(
    graph,
    messages: List[BaseMessage],
    session_memory: ConversationBufferMemory,
    user_message: str,
    llm_instance,
    session_id: str = None,
    workflow: str = "general",
    enable_reflection: bool = False,
    request: ConversationRequest = None
) -> AsyncGenerator[str, None]:
    """
    Create streaming response for agent-based conversation.

    Args:
        graph: LangGraph instance with agent and tools
        messages: List of conversation messages
        session_memory: Session memory for conversation context
        user_message: Current user message
        llm_instance: LLM instance for reflection
        session_id: Session identifier
        workflow: Workflow type (e.g., "general", "assistant")
        enable_reflection: Whether to apply reflection validation
        request: Original conversation request

    Yields:
        JSON-formatted streaming data chunks
    """
    full_response_content = ""
    agent_messages = []  # Collect AIMessages with tool_calls and ToolMessages for memory
    tool_outputs = []  # Collect tool outputs for reflection

    try:
        logger.debug(f"Starting agent stream with messages: {len(messages)}")

        # Prepare config with Langfuse callback if available
        config = {}
        trace_handler = get_langfuse_handler_with_trace(session_id or "unknown", workflow, user_message)
        if trace_handler:
            config["callbacks"] = [trace_handler]

        async for chunk in graph.astream({"messages": messages}, stream_mode="messages", config=config):
            logger.debug(f"Received chunk: {type(chunk)}, content: {chunk}")

            # Handle the chunk structure from LangGraph's astream with stream_mode="messages"
            if isinstance(chunk, tuple) and len(chunk) >= 1:
                message = chunk[0]
                metadata = chunk[1] if len(chunk) > 1 else {}

                logger.debug(f"Processing message: {type(message)}, metadata: {metadata}")

                # Collect AIMessages with valid tool_calls and ToolMessages for memory
                if isinstance(message, AIMessage) and hasattr(message, 'tool_calls') and message.tool_calls:
                    # Only collect if tool_calls have valid name (not empty chunks)
                    valid_tool_calls = [tc for tc in message.tool_calls if tc.get('name')]
                    if valid_tool_calls:
                        agent_messages.append(message)
                        logger.debug(f"Collected AIMessage with {len(valid_tool_calls)} valid tool call(s)")
                elif isinstance(message, ToolMessage):
                    agent_messages.append(message)
                    # Collect tool output for reflection
                    tool_outputs.append({
                        "tool": message.name if hasattr(message, 'name') else "unknown",
                        "output": message.content
                    })
                    logger.debug(f"Collected ToolMessage: {message.content[:100]}...")

                # Check if this is an AI message chunk with content
                if hasattr(message, 'content') and message.content:
                    # Check if it's from the agent node (not tool calls)
                    if metadata.get('langgraph_node') == 'agent':
                        content_delta = message.content
                        full_response_content += content_delta
                        logger.debug(f"Agent content: {content_delta}")
                        yield f"data: {json.dumps({'chunk': content_delta})}\n\n"
                    elif metadata.get('langgraph_node') == 'tools':
                        # Tool output is not sent to client but logged for debugging
                        logger.info(f"Tool execution: {message.content}")
                        # Optionally yield tool execution info
                        yield f"data: {json.dumps({'tool_output': message.content, 'chunk': ''})}\n\n"
            else:
                # Fallback for other chunk structures
                logger.debug(f"Fallback chunk processing: {chunk}")
                if hasattr(chunk, 'content') and chunk.content:
                    content_delta = chunk.content
                    full_response_content += content_delta
                    yield f"data: {json.dumps({'chunk': content_delta})}\n\n"

        yield f"data: {json.dumps({'chunk': ''})}\n\n"

        # Reflect on response if enabled
        if enable_reflection and request and full_response_content:
            logger.debug(f"Running reflection on streamed response with {len(tool_outputs)} tool outputs")
            # Format tool outputs for reflection
            tool_outputs_str = None
            if tool_outputs:
                tool_outputs_str = "\n\n".join([
                    f"TOOL: {output['tool']}\nOUTPUT: {output['output']}"
                    for output in tool_outputs
                ])

            improved_response, reflection_notes = await reflect_on_response_with_agent(
                full_response_content,
                request,
                llm_instance,
                tool_outputs=tool_outputs_str
            )

            # Only update if the response was actually improved (changed)
            if improved_response != full_response_content:
                logger.info("Response was improved by reflection agent")
                full_response_content = improved_response
                yield f"data: {json.dumps({'reflection': {'improved': True, 'notes': reflection_notes}})}\n\n"
                yield f"data: {json.dumps({'chunk': '\n\n[Improved by reflection agent]'})}\n\n"
            else:
                logger.info("Response passed reflection validation without changes")
                yield f"data: {json.dumps({'reflection': {'improved': False, 'passed': True, 'notes': reflection_notes}})}\n\n"

    except Exception as e:
        error_msg = f"Agent streaming error: {str(e)}"
        logger.error(f"Agent streaming exception: {e}")
        fallback_msg = get_error_fallback_message(str(e))
        yield f"data: {json.dumps({'error': error_msg, 'chunk': fallback_msg})}\n\n"
    finally:
        if full_response_content:
            save_conversation_context(session_memory, user_message, full_response_content)

        # Add agent messages (AIMessage with tool_calls and ToolMessages) to memory
        if agent_messages:
            logger.debug(f"Adding {len(agent_messages)} agent messages to memory")
            for msg in agent_messages:
                session_memory.chat_memory.add_message(msg)


async def create_regular_response_stream(
    llm_instance,
    messages: List[BaseMessage],
    session_memory: ConversationBufferMemory,
    user_message: str,
    workflow: str = "general",
    session_id: str = None,
    enable_reflection: bool = False,
    request: ConversationRequest = None
) -> AsyncGenerator[str, None]:
    """
    Create streaming response for regular conversation without tools.

    Args:
        llm_instance: LLM instance for generation
        messages: List of conversation messages
        session_memory: Session memory for conversation context
        user_message: Current user message
        workflow: Workflow type (e.g., "general", "assistant")
        session_id: Session identifier
        enable_reflection: Whether to apply reflection validation
        request: Original conversation request

    Yields:
        JSON-formatted streaming data chunks
    """
    regular_system_prompt = get_regular_system_prompt_for_workflow(workflow)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=regular_system_prompt),
        *messages
    ])

    full_response_content = ""
    try:
        # Prepare config with Langfuse callback if available
        config = {}
        trace_handler = get_langfuse_handler_with_trace(session_id or "unknown", workflow, user_message)
        if trace_handler:
            config["callbacks"] = [trace_handler]

        async for chunk in llm_instance.astream(prompt.invoke({}), config=config):
            if chunk.content:
                content = chunk.content
                full_response_content += content
                yield f"data: {json.dumps({'chunk': content})}\n\n"

        yield f"data: {json.dumps({'chunk': ''})}\n\n"

        # Reflect on response if enabled
        if enable_reflection and request and full_response_content:
            logger.debug("Running reflection on streamed response")
            improved_response, reflection_notes = await reflect_on_response_with_agent(
                full_response_content,
                request,
                llm_instance
            )

            # Only update if the response was actually improved (changed)
            if improved_response != full_response_content:
                logger.info("Response was improved by reflection agent")
                full_response_content = improved_response
                yield f"data: {json.dumps({'reflection': {'improved': True, 'notes': reflection_notes}})}\n\n"
                yield f"data: {json.dumps({'chunk': '\n\n[Improved by reflection agent]'})}\n\n"
            else:
                logger.info("Response passed reflection validation without changes")
                yield f"data: {json.dumps({'reflection': {'improved': False, 'passed': True, 'notes': reflection_notes}})}\n\n"

    except Exception as e:
        error_msg = f"Regular streaming error: {str(e)}"
        logger.error(f"Regular streaming exception: {e}")
        fallback_msg = get_error_fallback_message(str(e))
        yield f"data: {json.dumps({'error': error_msg, 'chunk': fallback_msg})}\n\n"
    finally:
        if full_response_content:
            save_conversation_context(session_memory, user_message, full_response_content)


async def handle_tool_conversation(
    request: ConversationRequest,
    llm_instance,
    session_memory: ConversationBufferMemory,
    messages: List[BaseMessage],
    authorization: str = None
) -> StreamingResponse:
    """
    Handle conversation with tools using ReAct agent.

    Args:
        request: Conversation request with tool configuration
        llm_instance: LLM instance for agent
        session_memory: Session memory for conversation context
        messages: List of conversation messages
        authorization: Authorization header for tool access

    Returns:
        StreamingResponse with agent-generated content
    """
    logger.debug(f"Tools requested: {request.tool_names}")
    tools = validate_and_get_tools(request.tool_names, authorization)
    graph = create_react_agent(llm_instance, tools, request.workflow, request.session_id, request.message)

    return StreamingResponse(
        create_agent_response_stream(
            graph, messages, session_memory, request.message,
            llm_instance, request.session_id, request.workflow, False, request
        ),
        media_type="text/event-stream",
        headers=STREAMING_HEADERS
    )


async def handle_regular_conversation(
    request: ConversationRequest,
    llm_instance,
    session_memory: ConversationBufferMemory,
    messages: List[BaseMessage]
) -> StreamingResponse:
    """
    Handle regular conversation without tools.

    Args:
        request: Conversation request
        llm_instance: LLM instance for generation
        session_memory: Session memory for conversation context
        messages: List of conversation messages

    Returns:
        StreamingResponse with LLM-generated content
    """
    return StreamingResponse(
        create_regular_response_stream(
            llm_instance, messages, session_memory, request.message,
            request.workflow, request.session_id, False, request
        ),
        media_type="text/event-stream",
        headers=STREAMING_HEADERS
    )
