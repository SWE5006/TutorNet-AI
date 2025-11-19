"""
Comprehensive tests for conversation API endpoints.

Tests cover the main endpoints: /chat, /conversation, /clear_memory, /get_history
with various scenarios including tools, reflection, error handling, and streaming.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from src.main import app
from src.core.utils.memory_manager import memory_by_session
from src.core.utils.models import ConversationRequest


@pytest.fixture
def client():
    """Create a test client for FastAPI."""
    return TestClient(app)


@pytest.fixture
def mock_llm():
    """Create a mock LLM instance."""
    llm = Mock()
    llm.astream = AsyncMock()
    llm.invoke = Mock()
    return llm


@pytest.fixture
def sample_request():
    """Sample conversation request."""
    return {
        "session_id": "test-session-chat",
        "message": "Hello, how are you?",
        "temperature": 0.7,
        "workflow": "chat"
    }


class TestChatEndpoint:
    """Test the /api/conversation/chat endpoint (non-streaming)."""

    @pytest.mark.asyncio
    async def test_chat_basic_response(self, client, sample_request):
        """Test basic chat response without tools."""
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_regular_system_prompt_for_workflow') as mock_prompt:
            
            # Setup mocks
            mock_llm = Mock()
            async def mock_astream(*args, **kwargs):
                yield Mock(content="Hello! I'm doing great.")
            mock_llm.astream = mock_astream
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            mock_prompt.return_value = "You are a helpful assistant."
            
            # Make request
            response = client.post("/foundation/api/conversation/chat", json=sample_request)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test-session-chat"
            assert data["message"] == "Hello, how are you?"
            assert data["response"] == "Hello! I'm doing great."
            assert data["workflow"] == "chat"
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_tools(self, client):
        """Test chat endpoint with tool usage."""
        request_data = {
            "session_id": "test-session-tools",
            "message": "Search for Python courses",
            "tool_names": ["search_courses"],
            "temperature": 0.7,
            "workflow": "assistant"
        }
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.validate_and_get_tools') as mock_validate, \
             patch('src.api.conversation.create_react_agent') as mock_create_agent, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_langfuse_handler_with_trace') as mock_langfuse:
            
            # Setup mocks
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            
            # Mock tool validation
            mock_tool = Mock()
            mock_tool.name = "search_courses"
            mock_validate.return_value = [mock_tool]
            
            # Mock agent with tool calls and responses
            mock_graph = Mock()
            async def mock_astream(*args, **kwargs):
                # Simulate AI message with tool call
                ai_msg = AIMessage(content="", tool_calls=[{"name": "search_courses", "args": {}, "id": "call_123"}])
                ai_msg.tool_calls = [{"name": "search_courses", "args": {}, "id": "call_123"}]
                yield (ai_msg, {"langgraph_node": "agent"})
                
                # Simulate tool response
                tool_msg = ToolMessage(content="Found 5 Python courses", name="search_courses", tool_call_id="call_123")
                yield (tool_msg, {"langgraph_node": "tools"})
                
                # Simulate final AI response
                final_msg = AIMessage(content="Here are the Python courses I found")
                yield (final_msg, {"langgraph_node": "agent"})
            
            mock_graph.astream = mock_astream
            mock_create_agent.return_value = mock_graph
            mock_langfuse.return_value = None
            
            # Make request
            response = client.post("/foundation/api/conversation/chat", json=request_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test-session-tools"
            assert "Here are the Python courses I found" in data["response"]
            assert data["tool_names"] == ["search_courses"]
            mock_validate.assert_called_once()
            mock_create_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_reflection_improvement(self, client, sample_request):
        """Test chat with reflection that improves the response."""
        sample_request["reflection"] = True
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_regular_system_prompt_for_workflow') as mock_prompt, \
             patch('src.api.conversation.reflect_on_response_with_agent') as mock_reflect:
            
            # Setup mocks
            mock_llm = Mock()
            async def mock_astream(*args, **kwargs):
                yield Mock(content="Initial response")
            mock_llm.astream = mock_astream
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            mock_prompt.return_value = "You are a helpful assistant."
            
            # Mock reflection that improves the response
            mock_reflect.return_value = ("Improved response", "Made more concise")
            
            # Make request
            response = client.post("/foundation/api/conversation/chat", json=sample_request)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Improved response"
            assert "reflection" in data
            assert data["reflection"]["improved"] == True
            assert data["reflection"]["original_response"] == "Initial response"
            assert data["reflection"]["improved_response"] == "Improved response"
            mock_reflect.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_reflection_no_improvement(self, client, sample_request):
        """Test chat with reflection that approves the response without changes."""
        sample_request["reflection"] = True
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_regular_system_prompt_for_workflow') as mock_prompt, \
             patch('src.api.conversation.reflect_on_response_with_agent') as mock_reflect:
            
            # Setup mocks
            mock_llm = Mock()
            async def mock_astream(*args, **kwargs):
                yield Mock(content="Good response")
            mock_llm.astream = mock_astream
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            mock_prompt.return_value = "You are a helpful assistant."
            
            # Mock reflection that returns the same response
            mock_reflect.return_value = ("Good response", "Response approved")
            
            # Make request
            response = client.post("/foundation/api/conversation/chat", json=sample_request)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Good response"
            assert "reflection" in data
            assert data["reflection"]["improved"] == False
            assert data["reflection"]["passed"] == True
            assert data["reflection"]["reflection_notes"] == "Response approved"

    @pytest.mark.asyncio
    async def test_chat_with_tools_and_reflection(self, client):
        """Test chat with both tools and reflection enabled."""
        request_data = {
            "session_id": "test-session-tools-reflect",
            "message": "Find Python courses",
            "tool_names": ["search_courses"],
            "reflection": True,
            "temperature": 0.7,
            "workflow": "assistant"
        }
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.validate_and_get_tools') as mock_validate, \
             patch('src.api.conversation.create_react_agent') as mock_create_agent, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_langfuse_handler_with_trace') as mock_langfuse, \
             patch('src.api.conversation.reflect_on_response_with_agent') as mock_reflect:
            
            # Setup mocks
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            
            mock_tool = Mock()
            mock_tool.name = "search_courses"
            mock_validate.return_value = [mock_tool]
            
            # Mock agent response with tools
            mock_graph = Mock()
            async def mock_astream(*args, **kwargs):
                # Tool call
                ai_msg = AIMessage(content="", tool_calls=[{"name": "search_courses", "args": {}, "id": "call_123"}])
                ai_msg.tool_calls = [{"name": "search_courses", "args": {}, "id": "call_123"}]
                yield (ai_msg, {"langgraph_node": "agent"})
                
                # Tool result
                tool_msg = ToolMessage(content="Course results", name="search_courses", tool_call_id="call_123")
                yield (tool_msg, {"langgraph_node": "tools"})
                
                # Final response
                final_msg = AIMessage(content="Found courses")
                yield (final_msg, {"langgraph_node": "agent"})
            
            mock_graph.astream = mock_astream
            mock_create_agent.return_value = mock_graph
            mock_langfuse.return_value = None
            
            # Mock reflection
            mock_reflect.return_value = ("Improved course list", "Added details")
            
            # Make request
            response = client.post("/foundation/api/conversation/chat", json=request_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Improved course list"
            assert "reflection" in data
            assert data["reflection"]["improved"] == True
            # Verify tool outputs were passed to reflection
            mock_reflect.assert_called_once()
            call_kwargs = mock_reflect.call_args[1]
            assert call_kwargs["tool_outputs"] is not None
            assert "search_courses" in call_kwargs["tool_outputs"]

    @pytest.mark.asyncio
    async def test_chat_error_handling(self, client, sample_request):
        """Test chat endpoint error handling."""
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_error_fallback_message') as mock_error:
            
            # Simulate an error
            mock_get_llm.side_effect = Exception("LLM service unavailable")
            mock_error.return_value = "I apologize, but I'm experiencing technical difficulties."
            
            # Make request
            response = client.post("/foundation/api/conversation/chat", json=sample_request)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data
            assert data["endpoint"] == "chat"
            mock_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_authorization_header(self, client, sample_request):
        """Test chat endpoint with authorization header."""
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_regular_system_prompt_for_workflow') as mock_prompt:
            
            # Setup mocks
            mock_llm = Mock()
            async def mock_astream(*args, **kwargs):
                yield Mock(content="Authorized response")
            mock_llm.astream = mock_astream
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            mock_prompt.return_value = "You are a helpful assistant."
            
            # Make request with auth header
            response = client.post(
                "/foundation/api/conversation/chat",
                json=sample_request,
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Authorized response"

    @pytest.mark.asyncio
    async def test_chat_collects_agent_messages(self, client):
        """Test that chat endpoint collects AIMessages with tool_calls and ToolMessages."""
        request_data = {
            "session_id": "test-session-collect",
            "message": "Use a tool",
            "tool_names": ["test_tool"],
            "temperature": 0.7,
            "workflow": "assistant"
        }
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.validate_and_get_tools') as mock_validate, \
             patch('src.api.conversation.create_react_agent') as mock_create_agent, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_langfuse_handler_with_trace') as mock_langfuse:
            
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            
            mock_tool = Mock()
            mock_tool.name = "test_tool"
            mock_validate.return_value = [mock_tool]
            
            # Mock agent with multiple messages
            mock_graph = Mock()
            async def mock_astream(*args, **kwargs):
                # AI message with empty tool calls (should be skipped)
                empty_ai = AIMessage(content="", tool_calls=[{"name": "", "args": {}, "id": ""}])
                empty_ai.tool_calls = [{"name": "", "args": {}, "id": ""}]
                yield (empty_ai, {"langgraph_node": "agent"})
                
                # AI message with valid tool call (should be collected)
                valid_ai = AIMessage(content="", tool_calls=[{"name": "test_tool", "args": {}, "id": "call_123"}])
                valid_ai.tool_calls = [{"name": "test_tool", "args": {}, "id": "call_123"}]
                yield (valid_ai, {"langgraph_node": "agent"})
                
                # Tool message (should be collected)
                tool_msg = ToolMessage(content="Tool result", name="test_tool", tool_call_id="call_123")
                yield (tool_msg, {"langgraph_node": "tools"})
                
                # Final response
                final_msg = AIMessage(content="Done")
                yield (final_msg, {"langgraph_node": "agent"})
            
            mock_graph.astream = mock_astream
            mock_create_agent.return_value = mock_graph
            mock_langfuse.return_value = None
            
            # Make request
            response = client.post("/foundation/api/conversation/chat", json=request_data)
            
            # Assertions
            assert response.status_code == 200
            # Verify that agent messages were added to memory
            # Should have 1 valid AIMessage and 1 ToolMessage = 2 messages
            assert mock_memory.chat_memory.add_message.call_count == 2


class TestConversationEndpoint:
    """Test the /api/conversation endpoint (streaming)."""

    @pytest.mark.asyncio
    async def test_conversation_without_tools(self, client, sample_request):
        """Test conversation endpoint without tools (delegates to handle_regular_conversation)."""
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.handle_regular_conversation') as mock_handle:
            
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            
            # Mock the streaming handler
            from fastapi.responses import StreamingResponse
            async def mock_stream():
                yield b"data: test\n\n"
            mock_handle.return_value = StreamingResponse(mock_stream())
            
            # Make request
            response = client.post("/foundation/api/conversation", json=sample_request)
            
            # Assertions
            assert response.status_code == 200
            mock_handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_conversation_with_tools(self, client):
        """Test conversation endpoint with tools (delegates to handle_tool_conversation)."""
        request_data = {
            "session_id": "test-session-conv-tools",
            "message": "Search courses",
            "tool_names": ["search_courses"],
            "temperature": 0.7,
            "workflow": "assistant"
        }
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.handle_tool_conversation') as mock_handle:
            
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            
            # Mock the streaming handler
            from fastapi.responses import StreamingResponse
            async def mock_stream():
                yield b"data: test\n\n"
            mock_handle.return_value = StreamingResponse(mock_stream())
            
            # Make request
            response = client.post("/foundation/api/conversation", json=request_data)
            
            # Assertions
            assert response.status_code == 200
            mock_handle.assert_called_once()
            # Just verify it was called, the authorization is passed as None when not provided

    @pytest.mark.asyncio
    async def test_conversation_with_authorization(self, client, sample_request):
        """Test conversation endpoint with authorization header."""
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.handle_regular_conversation') as mock_handle:
            
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            
            # Mock the streaming handler
            from fastapi.responses import StreamingResponse
            async def mock_stream():
                yield b"data: test\n\n"
            mock_handle.return_value = StreamingResponse(mock_stream())
            
            # Make request with auth
            response = client.post(
                "/foundation/api/conversation",
                json=sample_request,
                headers={"Authorization": "Bearer test-token"}
            )
            
            # Assertions
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_conversation_error_handling(self, client, sample_request):
        """Test conversation endpoint error handling."""
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm:
            
            # Simulate an error
            mock_get_llm.side_effect = Exception("Service error")
            
            # Make request
            response = client.post("/foundation/api/conversation", json=sample_request)
            
            # Assertions
            assert response.status_code == 500
            # Error handler wraps the error, so just check status code

    @pytest.mark.asyncio
    async def test_conversation_http_exception_propagation(self, client, sample_request):
        """Test that HTTPException is properly propagated."""
        from fastapi import HTTPException
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm:
            
            # Simulate HTTPException
            mock_get_llm.side_effect = HTTPException(status_code=401, detail="Unauthorized")
            
            # Make request
            response = client.post("/foundation/api/conversation", json=sample_request)
            
            # Assertions
            assert response.status_code == 401
            # Error handler wraps HTTPException


class TestClearMemoryEndpoint:
    """Test the /api/conversation/clear_memory endpoint."""

    def test_clear_memory_success(self, client):
        """Test clearing memory for an existing session."""
        # Create a session first
        session_id = "test-session-clear"
        from langchain.memory import ConversationBufferMemory
        memory_by_session[session_id] = ConversationBufferMemory(return_messages=True)
        
        # Clear the memory
        response = client.post(
            "/foundation/api/conversation/clear_memory",
            json={"session_id": session_id}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert f"Memory for session {session_id} cleared successfully" in data["message"]
        assert session_id not in memory_by_session

    def test_clear_memory_not_found(self, client):
        """Test clearing memory for a non-existent session."""
        response = client.post(
            "/foundation/api/conversation/clear_memory",
            json={"session_id": "non-existent-session"}
        )
        
        # Assertions
        assert response.status_code == 404
        # Error handler wraps the detail

    def test_clear_memory_with_authorization(self, client):
        """Test clear_memory endpoint with authorization header."""
        # Create a session
        session_id = "test-session-auth-clear"
        from langchain.memory import ConversationBufferMemory
        memory_by_session[session_id] = ConversationBufferMemory(return_messages=True)
        
        # Clear with auth header
        response = client.post(
            "/foundation/api/conversation/clear_memory",
            json={"session_id": session_id},
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Assertions
        assert response.status_code == 200


class TestGetHistoryEndpoint:
    """Test the /api/conversation/get_history endpoint."""

    def test_get_history_success(self, client):
        """Test getting history for an existing session."""
        # Create a session with history
        session_id = "test-session-history"
        from langchain.memory import ConversationBufferMemory
        memory = ConversationBufferMemory(return_messages=True)
        memory.save_context({"input": "Hello"}, {"output": "Hi there!"})
        memory.save_context({"input": "How are you?"}, {"output": "I'm doing well!"})
        memory_by_session[session_id] = memory
        
        # Get the history
        response = client.post(
            "/foundation/api/conversation/get_history",
            json={"session_id": session_id}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "Hello" in data["history"]
        assert "Hi there!" in data["history"]

    def test_get_history_not_found(self, client):
        """Test getting history for a non-existent session."""
        response = client.post(
            "/foundation/api/conversation/get_history",
            json={"session_id": "non-existent-session"}
        )
        
        # Assertions
        assert response.status_code == 404
        # Error handler wraps the detail

    def test_get_history_with_authorization(self, client):
        """Test get_history endpoint with authorization header."""
        # Create a session
        session_id = "test-session-auth-history"
        from langchain.memory import ConversationBufferMemory
        memory = ConversationBufferMemory(return_messages=True)
        memory.save_context({"input": "Test"}, {"output": "Response"})
        memory_by_session[session_id] = memory
        
        # Get history with auth header
        response = client.post(
            "/foundation/api/conversation/get_history",
            json={"session_id": session_id},
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Assertions
        assert response.status_code == 200
        assert "Test" in response.json()["history"]


class TestEdgeCases:
    """Test edge cases and specific scenarios."""

    @pytest.mark.asyncio
    async def test_chat_empty_tool_names(self, client):
        """Test chat with empty tool_names list."""
        request_data = {
            "session_id": "test-empty-tools",
            "message": "Hello",
            "tool_names": [],
            "temperature": 0.7,
            "workflow": "chat"
        }
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_regular_system_prompt_for_workflow') as mock_prompt:
            
            mock_llm = Mock()
            async def mock_astream(*args, **kwargs):
                yield Mock(content="Response without tools")
            mock_llm.astream = mock_astream
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            mock_prompt.return_value = "You are a helpful assistant."
            
            response = client.post("/foundation/api/conversation/chat", json=request_data)
            
            assert response.status_code == 200
            assert response.json()["tool_names"] == []

    @pytest.mark.asyncio
    async def test_chat_none_tool_names(self, client):
        """Test chat with None tool_names (should default to empty list)."""
        request_data = {
            "session_id": "test-none-tools",
            "message": "Hello",
            "tool_names": None,
            "temperature": 0.7,
            "workflow": "chat"
        }
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_regular_system_prompt_for_workflow') as mock_prompt:
            
            mock_llm = Mock()
            async def mock_astream(*args, **kwargs):
                yield Mock(content="Response")
            mock_llm.astream = mock_astream
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            mock_prompt.return_value = "You are a helpful assistant."
            
            response = client.post("/foundation/api/conversation/chat", json=request_data)
            
            assert response.status_code == 200
            # None should be converted to []
            assert response.json()["tool_names"] == []

    @pytest.mark.asyncio
    async def test_chat_reflection_without_response(self, client):
        """Test chat with reflection enabled but empty response (should skip reflection)."""
        request_data = {
            "session_id": "test-no-response",
            "message": "Hello",
            "reflection": True,
            "temperature": 0.7,
            "workflow": "chat"
        }
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_regular_system_prompt_for_workflow') as mock_prompt, \
             patch('src.api.conversation.reflect_on_response_with_agent') as mock_reflect:
            
            mock_llm = Mock()
            async def mock_astream(*args, **kwargs):
                # Yield nothing (empty response)
                return
                yield  # This makes it an async generator
            mock_llm.astream = mock_astream
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            mock_prompt.return_value = "You are a helpful assistant."
            
            response = client.post("/foundation/api/conversation/chat", json=request_data)
            
            assert response.status_code == 200
            # Reflection should not be called for empty response
            mock_reflect.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_fallback_chunk_structure(self, client):
        """Test chat handling of non-tuple chunk structures."""
        request_data = {
            "session_id": "test-fallback",
            "message": "Test fallback",
            "tool_names": ["test_tool"],
            "temperature": 0.7,
            "workflow": "assistant"
        }
        
        with patch('src.api.conversation.get_llm_instance') as mock_get_llm, \
             patch('src.api.conversation.get_session_memory') as mock_get_memory, \
             patch('src.api.conversation.prepare_messages') as mock_prepare, \
             patch('src.api.conversation.validate_and_get_tools') as mock_validate, \
             patch('src.api.conversation.create_react_agent') as mock_create_agent, \
             patch('src.api.conversation.save_conversation_context') as mock_save, \
             patch('src.api.conversation.get_langfuse_handler_with_trace') as mock_langfuse:
            
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            
            mock_memory = Mock()
            mock_memory.chat_memory.add_message = Mock()
            mock_get_memory.return_value = mock_memory
            mock_prepare.return_value = []
            
            mock_tool = Mock()
            mock_tool.name = "test_tool"
            mock_validate.return_value = [mock_tool]
            
            # Mock agent that returns non-tuple chunks (fallback case)
            mock_graph = Mock()
            async def mock_astream(*args, **kwargs):
                # Return a message object directly (not in tuple)
                chunk = Mock()
                chunk.content = "Fallback response"
                yield chunk
            
            mock_graph.astream = mock_astream
            mock_create_agent.return_value = mock_graph
            mock_langfuse.return_value = None
            
            response = client.post("/foundation/api/conversation/chat", json=request_data)
            
            assert response.status_code == 200
            # Should use fallback content extraction
            assert response.json()["response"] == "Fallback response"
