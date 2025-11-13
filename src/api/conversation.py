"""
TutorNet-AI Conversation API

Main API endpoints for conversational interactions with optional tool usage
and reflection-based quality validation.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header

from src.core.utils.models import ConversationRequest, SessionManagementRequest
from src.core.utils.llm_factory import get_llm_instance
from src.core.utils.memory_manager import get_session_memory, prepare_messages, save_conversation_context, memory_by_session
from src.core.utils.streaming_handlers import handle_tool_conversation, handle_regular_conversation
from src.core.utils.agents.reflection_graph import reflect_on_response_with_agent
from src.core.utils.agents.react_agent import create_react_agent
from src.core.utils.langfuse_config import get_langfuse_handler_with_trace
from src.core.utils.api_utils import validate_and_get_tools, get_error_fallback_message
from src.core.utils.system_prompts import get_regular_system_prompt_for_workflow
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

# Initialize router and logger
router = APIRouter(prefix="/api/conversation")
logger = logging.getLogger(__name__)


@router.post("/chat")
async def chat(
    request: ConversationRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    Chat endpoint that returns a complete JSON response after getting the full response from LLM.
    Non-streaming version of the conversation endpoint.
    Accepts both request body and headers.
    """
    try:
        llm_instance = get_llm_instance(request)
        session_memory = get_session_memory(request.session_id)
        messages = prepare_messages(session_memory, request.message)

        # Ensure tool_names is always a list, even if None is provided in the request
        tool_names = request.tool_names or []

        full_response = ""
        agent_messages = []  # Collect AIMessages with tool_calls and ToolMessages for memory
        tool_outputs = []  # Collect tool outputs for reflection

        if tool_names:
            # Handle conversation with tools using ReAct agent
            logger.debug(f"Tools requested: {tool_names}")
            tools = validate_and_get_tools(tool_names, authorization)
            logger.debug(f"Validated tools: {[t.name for t in tools]}")
            graph = create_react_agent(llm_instance, tools, request.workflow or "chat", request.session_id, request.message)

            # Collect full response from agent
            trace_handler = get_langfuse_handler_with_trace(request.session_id, request.workflow or "chat", request.message)
            config = {}
            if trace_handler:
                config["callbacks"] = [trace_handler]

            async for chunk in graph.astream({"messages": messages}, stream_mode="messages", config=config):
                logger.debug(f"Chat endpoint received chunk: {type(chunk)}, content: {chunk}")
                if isinstance(chunk, tuple) and len(chunk) >= 1:
                    message = chunk[0]
                    metadata = chunk[1] if len(chunk) > 1 else {}

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
                            full_response += message.content
                        elif metadata.get('langgraph_node') == 'tools':
                            # Tool output is logged but not included in response
                            logger.info(f"Tool execution: {message.content}")
                else:
                    # Fallback for other chunk structures
                    if hasattr(chunk, 'content') and chunk.content:
                        full_response += chunk.content
        else:
            # Handle regular conversation without tools
            regular_system_prompt = get_regular_system_prompt_for_workflow(request.workflow or "chat")
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=regular_system_prompt),
                *messages
            ])

            # Collect full response from LLM
            trace_handler = get_langfuse_handler_with_trace(request.session_id, request.workflow or "chat", request.message)
            config = {}
            if trace_handler:
                config["callbacks"] = [trace_handler]

            async for chunk in llm_instance.astream(prompt.invoke({}), config=config):
                if chunk.content:
                    full_response += chunk.content

        # Reflect on response if enabled
        reflection_result = None
        if request.reflection and full_response:
            logger.debug(f"Running reflection with {len(tool_outputs)} tool outputs")
            # Format tool outputs for reflection
            tool_outputs_str = None
            if tool_outputs:
                tool_outputs_str = "\n\n".join([
                    f"TOOL: {output['tool']}\nOUTPUT: {output['output']}"
                    for output in tool_outputs
                ])

            improved_response, reflection_notes = await reflect_on_response_with_agent(
                full_response,
                request,
                llm_instance,
                tool_outputs=tool_outputs_str
            )

            # Only update if the response was actually improved (changed)
            if improved_response != full_response:
                logger.info("Response was improved by reflection agent")
                reflection_result = {
                    "original_response": full_response,
                    "improved_response": improved_response,
                    "reflection_notes": reflection_notes,
                    "improved": True
                }
                # Use the improved response
                full_response = improved_response
                logger.info(f"Reflection completed with improvements: {reflection_notes[:100]}...")
            else:
                logger.info("Response passed reflection validation without changes")
                reflection_result = {
                    "response": full_response,
                    "reflection_notes": reflection_notes,
                    "improved": False,
                    "passed": True
                }

        # Save conversation context
        save_conversation_context(session_memory, request.message, full_response)

        # Add agent messages (AIMessage with tool_calls and ToolMessages) to memory if tools were used
        if agent_messages:
            logger.debug(f"Adding {len(agent_messages)} agent messages to memory")
            for msg in agent_messages:
                session_memory.chat_memory.add_message(msg)

        response_data = {
            "session_id": request.session_id,
            "message": request.message,
            "response": full_response,
            "tool_names": tool_names,
            "temperature": request.temperature,
            "workflow": request.workflow
        }

        # Add reflection result if performed
        if reflection_result:
            response_data["reflection"] = reflection_result

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        error_response = get_error_fallback_message(str(e))
        return {
            "message": error_response,
            "session_id": request.session_id,
            "endpoint": "chat",
            "status": "error",
            "error": str(e)
        }


@router.post("")
async def conversation(
    request: ConversationRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """
    General conversation endpoint with session history managed by Langchain's ConversationBufferMemory.
    Uses streaming for responses.
    Accepts both request body and headers.
    """
    try:
        llm_instance = get_llm_instance(request)
        session_memory = get_session_memory(request.session_id)
        messages = prepare_messages(session_memory, request.message)

        logger.debug(f"Request session_id: {request.session_id}")

        # Ensure tool_names is always a list, even if None is provided in the request
        tool_names = request.tool_names or []

        if tool_names:
            return await handle_tool_conversation(request, llm_instance, session_memory, messages, authorization)
        else:
            return await handle_regular_conversation(request, llm_instance, session_memory, messages)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during conversation processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error during LLM invocation: {e}")


@router.post("/clear_memory")
async def clear_memory(
    request: SessionManagementRequest,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Clears the conversation memory for a specific session.
    Accepts both request body and headers.
    """
    logger.debug(f"Authorization header provided: {bool(authorization)}")

    session_id = request.session_id
    if session_id in memory_by_session:
        del memory_by_session[session_id]
        return {"message": f"Memory for session {session_id} cleared successfully."}
    raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")


@router.post("/get_history")
async def get_history(
    request: SessionManagementRequest,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Retrieves the full conversation history for a specific session.
    Accepts both request body and headers.
    """

    session_id = request.session_id
    if session_id in memory_by_session:
        session_memory = memory_by_session[session_id]
        history = session_memory.buffer_as_str
        return {"session_id": session_id, "history": history}
    raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
