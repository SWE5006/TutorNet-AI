from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, AsyncGenerator, Tuple, Any
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, ToolMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from src.core.function_tools import (
    wrap_search_tutor_service,
    wrap_search_course_service,
    wrap_get_course_by_userid_service,
    wrap_get_course_details_service,
    wrap_place_order_service,
    
)
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from src.core.utils.settings import get_settings
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from src.core.utils.system_prompts import (
    get_agent_system_prompt_for_workflow,
    get_regular_system_prompt_for_workflow
)

import json
import uuid
import logging

router = APIRouter(prefix="/api/conversation")
settings = get_settings()
memory_by_session: Dict[str, ConversationBufferMemory] = {}
logger = logging.getLogger(__name__)

# Constants
REQUEST_TIMEOUT = 60  # Increased timeout for international network access
MAX_RETRIES = 3  # Increased retries for better reliability
DEFAULT_TEMPERATURE = 0.7

# Streaming response headers
STREAMING_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
}

# Initialize Langfuse for tracing and observability
langfuse = None
langfuse_handler = None

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

# System prompts now managed in src/core/utils/system_prompts.py

class ConversationRequest(BaseModel):
    message: str = Field(..., description="The message from the user.")
    tool_names: Optional[List[str]] = Field(None, description="A list of tool names to use.")
    session_id: str = Field(..., description="The ID for the chat session.")
    workflow: Optional[str] = Field("general", description="The workflow type (course, translator, chat, conversation, general).")
    temperature: float = Field(
        DEFAULT_TEMPERATURE, ge=0.0, le=1.0, description="The sampling temperature for the LLM."
    )


class SessionManagementRequest(BaseModel):
    session_id: str = Field(..., description="The ID for the chat session.")


def _create_common_llm_params(request: ConversationRequest) -> Dict[str, Any]:
    """Create common LLM parameters used across all providers."""
    return {
        "temperature": request.temperature,
        "streaming": True,
        "request_timeout": REQUEST_TIMEOUT,
        "max_retries": MAX_RETRIES,
    }


def _create_qwen_openai_instance(request: ConversationRequest) -> ChatOpenAI:
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
        **_create_common_llm_params(request)
    )


def _create_openai_instance(request: ConversationRequest) -> ChatOpenAI:
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
        **_create_common_llm_params(request)
    )


def _get_llm_instance(request: ConversationRequest):
    """Get the appropriate LLM instance based on settings with fallback logic."""
    try:
        # Try Qwen OpenAI first if configured
        if settings.qwen_openai_enabled:
            return _create_qwen_openai_instance(request)
        # Fallback to OpenAI
        else:
            return _create_openai_instance(request)
    except Exception as e:
        logger.error(f"Failed to create LLM instance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize LLM: {e}")


def _get_session_memory(session_id: str) -> ConversationBufferMemory:
    """Get or create session-specific memory."""
    if session_id not in memory_by_session:
        memory_by_session[session_id] = ConversationBufferMemory(return_messages=True)
    return memory_by_session[session_id]


def _get_langfuse_handler_with_trace(session_id: str, workflow: str, user_message: str) -> Optional[CallbackHandler]:
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


def _prepare_messages(session_memory: ConversationBufferMemory, user_message: str) -> List[BaseMessage]:
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


def _validate_and_get_tools(tool_names: List[str], authorization: str = None) -> List[Any]:
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


def _create_react_agent(llm_instance, tools: List[Any], workflow: str = "general", session_id: str = None, user_message: str = None):
    """Create a ReAct agent with the given LLM and tools."""
    try:
        agent_system_prompt = get_agent_system_prompt_for_workflow(workflow)
        system_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=agent_system_prompt),
            ("placeholder", "{messages}"),
        ])
        logger.debug(f"Creating ReAct agent with {len(tools)} tools: {[t.name for t in tools]} for workflow: {workflow}")
        
        # Add Langfuse callback to LLM if available
        trace_handler = _get_langfuse_handler_with_trace(session_id or "unknown", workflow, user_message or "")
        if trace_handler:
            # Update LLM instance with Langfuse callback
            llm_instance.callbacks = [trace_handler]
            
        return create_react_agent(model=llm_instance, tools=tools, prompt=system_prompt)
    except Exception as e:
        logger.error(f"Failed to create ReAct agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create ReAct agent: {e}")


def _get_error_fallback_message(error_str: str) -> str:
    """Generate appropriate fallback message based on error type."""
    error_lower = error_str.lower()
    if "connection" in error_lower:
        return "I'm experiencing connection issues right now. Please try again in a moment."
    elif "timeout" in error_lower:
        return "The request is taking longer than expected. Please try again."
    else:
        return "I'm currently experiencing technical difficulties. Please try again later."


def _save_conversation_context(session_memory: ConversationBufferMemory, user_input: str, ai_output: str) -> None:
    """Save conversation context to session memory with error handling."""
    try:
        session_memory.save_context({"input": user_input}, {"output": ai_output})
        logger.debug(f"Saved conversation context for session")
    except Exception as e:
        logger.error(f"Failed to save conversation context: {e}")


async def _create_agent_response_stream(
    graph, messages: List[BaseMessage], session_memory: ConversationBufferMemory, user_message: str, session_id: str = None, workflow: str = "general"
) -> AsyncGenerator[str, None]:
    """Create streaming response for agent-based conversation."""
    full_response_content = ""
    agent_messages = []  # Collect AIMessages with tool_calls and ToolMessages for memory
    
    try:
        logger.debug(f"Starting agent stream with messages: {len(messages)}")
        
        # Prepare config with Langfuse callback if available
        config = {}
        trace_handler = _get_langfuse_handler_with_trace(session_id or "unknown", workflow, user_message)
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
    except Exception as e:
        error_msg = f"Agent streaming error: {str(e)}"
        logger.error(f"Agent streaming exception: {e}")
        fallback_msg = _get_error_fallback_message(str(e))
        yield f"data: {json.dumps({'error': error_msg, 'chunk': fallback_msg})}\n\n"
    finally:
        if full_response_content:
            _save_conversation_context(session_memory, user_message, full_response_content)
        
        # Add agent messages (AIMessage with tool_calls and ToolMessages) to memory
        if agent_messages:
            logger.debug(f"Adding {len(agent_messages)} agent messages to memory")
            for msg in agent_messages:
                session_memory.chat_memory.add_message(msg)


async def _create_regular_response_stream(
    llm_instance, messages: List[BaseMessage], session_memory: ConversationBufferMemory, user_message: str, workflow: str = "general", session_id: str = None
) -> AsyncGenerator[str, None]:
    """Create streaming response for regular conversation."""
    regular_system_prompt = get_regular_system_prompt_for_workflow(workflow)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=regular_system_prompt),
        *messages
    ])
    
    full_response_content = ""
    try:
        # Prepare config with Langfuse callback if available
        config = {}
        trace_handler = _get_langfuse_handler_with_trace(session_id or "unknown", workflow, user_message)
        if trace_handler:
            config["callbacks"] = [trace_handler]
            
        async for chunk in llm_instance.astream(prompt.invoke({}), config=config):
            if chunk.content:
                content = chunk.content
                full_response_content += content
                yield f"data: {json.dumps({'chunk': content})}\n\n"
        
        yield f"data: {json.dumps({'chunk': ''})}\n\n"
    except Exception as e:
        error_msg = f"Regular streaming error: {str(e)}"
        logger.error(f"Regular streaming exception: {e}")
        fallback_msg = _get_error_fallback_message(str(e))
        yield f"data: {json.dumps({'error': error_msg, 'chunk': fallback_msg})}\n\n"
    finally:
        if full_response_content:
            _save_conversation_context(session_memory, user_message, full_response_content)


async def _handle_tool_conversation(request: ConversationRequest, llm_instance, session_memory: ConversationBufferMemory, messages: List[BaseMessage], authorization: str = None) -> StreamingResponse:
    """Handle conversation with tools using ReAct agent."""
    logger.debug(f"Tools requested: {request.tool_names}")
    tools = _validate_and_get_tools(request.tool_names, authorization)
    graph = _create_react_agent(llm_instance, tools, request.workflow, request.session_id, request.message)
    
    return StreamingResponse(
        _create_agent_response_stream(graph, messages, session_memory, request.message, request.session_id, request.workflow),
        media_type="text/event-stream",
        headers=STREAMING_HEADERS
    )


async def _handle_regular_conversation(request: ConversationRequest, llm_instance, session_memory: ConversationBufferMemory, messages: List[BaseMessage]) -> StreamingResponse:
    """Handle regular conversation without tools."""
    return StreamingResponse(
        _create_regular_response_stream(llm_instance, messages, session_memory, request.message, request.workflow, request.session_id),
        media_type="text/event-stream",
        headers=STREAMING_HEADERS
    )

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
        llm_instance = _get_llm_instance(request)
        session_memory = _get_session_memory(request.session_id)
        messages = _prepare_messages(session_memory, request.message)
        
        # Ensure tool_names is always a list, even if None is provided in the request
        tool_names = request.tool_names or []
        
        full_response = ""
        agent_messages = []  # Collect AIMessages with tool_calls and ToolMessages for memory
        
        if tool_names:
            # Handle conversation with tools using ReAct agent
            logger.debug(f"Tools requested: {tool_names}")
            tools = _validate_and_get_tools(tool_names, authorization)
            logger.debug(f"Validated tools: {[t.name for t in tools]}")
            graph = _create_react_agent(llm_instance, tools, request.workflow or "chat", request.session_id, request.message)
            
            # Collect full response from agent
            trace_handler = _get_langfuse_handler_with_trace(request.session_id, request.workflow or "chat", request.message)
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
            trace_handler = _get_langfuse_handler_with_trace(request.session_id, request.workflow or "chat", request.message)
            config = {}
            if trace_handler:
                config["callbacks"] = [trace_handler]
                
            async for chunk in llm_instance.astream(prompt.invoke({}), config=config):
                if chunk.content:
                    full_response += chunk.content
        
        # Save conversation context
        _save_conversation_context(session_memory, request.message, full_response)
        
        # Add agent messages (AIMessage with tool_calls and ToolMessages) to memory if tools were used
        if agent_messages:
            logger.debug(f"Adding {len(agent_messages)} agent messages to memory")
            for msg in agent_messages:
                session_memory.chat_memory.add_message(msg)
        
        return {
            "session_id": request.session_id,
            "message": request.message,
            "response": full_response,
            "tool_names": tool_names,
            "temperature": request.temperature,
            "workflow": request.workflow
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        error_response = _get_error_fallback_message(str(e))
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
        llm_instance = _get_llm_instance(request)
        session_memory = _get_session_memory(request.session_id)
        messages = _prepare_messages(session_memory, request.message)

        logger.debug(f"Request session_id: {request.session_id}")

        # Ensure tool_names is always a list, even if None is provided in the request
        tool_names = request.tool_names or []

        if tool_names:
            return await _handle_tool_conversation(request, llm_instance, session_memory, messages, authorization)
        else:
            return await _handle_regular_conversation(request, llm_instance, session_memory, messages)
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
