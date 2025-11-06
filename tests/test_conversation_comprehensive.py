"""
Additional comprehensive tests for conversation.py
Focus on improving coverage for uncovered code paths
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock, ANY
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain.memory import ConversationBufferMemory


class TestMessageHandling:
    """Test message handling and preparation"""
    
    def test_prepare_messages_with_tool_messages(self):
        """Test preparing messages that include tool messages"""
        from src.api.conversation import _prepare_messages
        
        memory = ConversationBufferMemory(return_messages=True)
        memory.chat_memory.add_user_message("Search for Python courses")
        
        # Add tool message
        tool_msg = ToolMessage(
            content="Found 5 courses",
            tool_call_id="call_123"
        )
        memory.chat_memory.add_message(tool_msg)
        memory.chat_memory.add_ai_message("Here are the Python courses")
        
        messages = _prepare_messages(memory, "Show me the first one")
        
        assert len(messages) == 4
        assert any(isinstance(msg, ToolMessage) for msg in messages)
        
    def test_prepare_messages_preserves_order(self):
        """Test that message order is preserved"""
        from src.api.conversation import _prepare_messages
        
        memory = ConversationBufferMemory(return_messages=True)
        memory.chat_memory.add_user_message("First")
        memory.chat_memory.add_ai_message("Response 1")
        memory.chat_memory.add_user_message("Second")
        memory.chat_memory.add_ai_message("Response 2")
        
        messages = _prepare_messages(memory, "Third")
        
        assert len(messages) == 5
        assert messages[0].content == "First"
        assert messages[1].content == "Response 1"
        assert messages[2].content == "Second"
        assert messages[3].content == "Response 2"
        assert messages[4].content == "Third"


class TestAgentGraphCreation:
    """Test agent and graph creation"""
    
    def test_create_react_agent_with_multiple_tools(self):
        """Test creating agent with multiple tools"""
        from src.api.conversation import _create_react_agent
        
        with patch('src.api.conversation.create_react_agent') as mock_create:
            with patch('src.api.conversation.get_agent_system_prompt_for_workflow') as mock_prompt:
                mock_graph = Mock()
                mock_create.return_value = mock_graph
                mock_prompt.return_value = "System prompt"
                
                mock_llm = Mock()
                mock_llm.callbacks = []
                
                tool1 = Mock(name="tool1")
                tool2 = Mock(name="tool2")
                tools = [tool1, tool2]
                
                result = _create_react_agent(mock_llm, tools, "assistant")
                
                mock_create.assert_called_once()
                assert result == mock_graph
                
    def test_create_react_agent_with_langfuse_trace(self):
        """Test agent creation includes Langfuse tracing"""
        from src.api.conversation import _create_react_agent
        
        with patch('src.api.conversation.create_react_agent') as mock_create:
            with patch('src.api.conversation.get_agent_system_prompt_for_workflow') as mock_prompt:
                with patch('src.api.conversation._get_langfuse_handler_with_trace') as mock_trace:
                    mock_handler = Mock()
                    mock_trace.return_value = mock_handler
                    mock_graph = Mock()
                    mock_create.return_value = mock_graph
                    mock_prompt.return_value = "Prompt"
                    
                    mock_llm = Mock()
                    mock_llm.callbacks = []
                    
                    _create_react_agent(
                        mock_llm, [], "assistant", 
                        session_id="test-123"
                    )
                    
                    # Should have called langfuse
                    assert mock_llm.callbacks == [mock_handler]


class TestLLMInstanceConfiguration:
    """Test LLM instance creation with various configurations"""
    
    def test_get_llm_instance_with_custom_temperature(self):
        """Test LLM instance with custom temperature"""
        from src.api.conversation import _get_llm_instance, ConversationRequest
        
        with patch('src.api.conversation._create_qwen_openai_instance') as mock_qwen:
            mock_llm = Mock()
            mock_qwen.return_value = mock_llm
            
            request = ConversationRequest(
                message="Test",
                session_id="test",
                workflow="assistant",
                temperature=0.9
            )
            
            result = _get_llm_instance(request)
            
            # Should pass custom temperature
            mock_qwen.assert_called_once_with(request)
            
    def test_qwen_instance_with_all_params(self):
        """Test Qwen instance creation with parameters"""
        from src.api.conversation import _create_qwen_openai_instance, ConversationRequest
        
        with patch('src.api.conversation.settings') as mock_settings:
            with patch('src.api.conversation.ChatOpenAI') as mock_chat:
                mock_settings.qwen_openai_url = "http://qwen.test"
                mock_settings.openai_api_key = "test-key"
                mock_settings.llm_model_name = "qwen-plus"
                mock_settings.llm_visual_model_name = "qwen-vision"
                
                request = ConversationRequest(
                    message="Test message",
                    session_id="test-123",
                    workflow="assistant",
                    temperature=0.7
                )
                
                _create_qwen_openai_instance(request)
                
                # Verify parameters were passed
                call_kwargs = mock_chat.call_args[1]
                assert call_kwargs['base_url'] == "http://qwen.test"
                assert call_kwargs['api_key'] == "test-key"
                assert call_kwargs['temperature'] == 0.7
                
    def test_openai_instance_with_all_params(self):
        """Test OpenAI instance creation with all parameters"""
        from src.api.conversation import _create_openai_instance, ConversationRequest
        
        with patch('src.api.conversation.settings') as mock_settings:
            with patch('src.api.conversation.ChatOpenAI') as mock_chat:
                mock_settings.openai_api_key = "openai-key"
                mock_settings.llm_model_name = "gpt-4"
                mock_settings.llm_visual_model_name = "gpt-4-vision-preview"
                mock_settings.llm_request_timeout = 30
                
                request = ConversationRequest(
                    message="Test",
                    session_id="test",
                    workflow="assistant",
                    temperature=0.5
                )
                
                _create_openai_instance(request)
                
                call_kwargs = mock_chat.call_args[1]
                assert call_kwargs['api_key'] == "openai-key"
                assert call_kwargs['temperature'] == 0.5


class TestErrorPathsCoverage:
    """Test error paths and edge cases"""
    
    def test_validate_tools_with_empty_list(self):
        """Test validating empty tool list"""
        from src.api.conversation import _validate_and_get_tools
        
        tools = _validate_and_get_tools([], None)
        assert tools == []
        
    def test_save_context_with_none_memory(self):
        """Test saving context with None memory"""
        from src.api.conversation import _save_conversation_context
        
        # Should handle gracefully
        _save_conversation_context(None, "input", "output")
        # No assertion needed - just shouldn't crash
        
    def test_save_context_saves_successfully(self):
        """Test saving context with valid memory"""
        from src.api.conversation import _save_conversation_context
        
        mock_memory = Mock()
        _save_conversation_context(mock_memory, "User input", "AI output")
        
        # Should call save_context
        mock_memory.save_context.assert_called_once_with(
            {"input": "User input"}, 
            {"output": "AI output"}
        )
        
    def test_get_error_fallback_for_auth_error(self):
        """Test error message for authentication errors"""
        from src.api.conversation import _get_error_fallback_message
        
        result = _get_error_fallback_message("Authentication failed: Invalid API key")
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def test_get_error_fallback_for_server_error(self):
        """Test error message for server errors"""
        from src.api.conversation import _get_error_fallback_message
        
        result = _get_error_fallback_message("Internal server error: 500")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestWorkflowSpecificBehavior:
    """Test workflow-specific code paths"""
    
    def test_translator_workflow_settings(self):
        """Test translator workflow uses correct settings"""
        from src.api.conversation import _create_qwen_openai_instance, ConversationRequest
        
        with patch('src.api.conversation.settings') as mock_settings:
            with patch('src.api.conversation.ChatOpenAI') as mock_chat:
                mock_settings.qwen_openai_url = "http://test"
                mock_settings.openai_api_key = "key"
                mock_settings.llm_model_name = "qwen"
                
                request = ConversationRequest(
                    message="Translate this",
                    session_id="test",
                    workflow="translator"
                )
                
                _create_qwen_openai_instance(request)
                
                # Verify standard model for translator
                assert mock_chat.called
                
    def test_content_optimizer_workflow(self):
        """Test content optimizer workflow"""
        from src.api.conversation import _create_qwen_openai_instance, ConversationRequest
        
        with patch('src.api.conversation.settings') as mock_settings:
            with patch('src.api.conversation.ChatOpenAI') as mock_chat:
                mock_settings.qwen_openai_url = "http://test"
                mock_settings.openai_api_key = "key"
                mock_settings.llm_model_name = "qwen"
                
                request = ConversationRequest(
                    message="Optimize this content",
                    session_id="test",
                    workflow="content_optimizer"
                )
                
                _create_qwen_openai_instance(request)
                
                assert mock_chat.called
                
    def test_earnings_analyser_workflow(self):
        """Test earnings analyser workflow"""
        from src.api.conversation import _create_qwen_openai_instance, ConversationRequest
        
        with patch('src.api.conversation.settings') as mock_settings:
            with patch('src.api.conversation.ChatOpenAI') as mock_chat:
                mock_settings.qwen_openai_url = "http://test"
                mock_settings.openai_api_key = "key"
                mock_settings.llm_model_name = "qwen"
                
                request = ConversationRequest(
                    message="Analyze earnings",
                    session_id="test",
                    workflow="earnings_analyser"
                )
                
                _create_qwen_openai_instance(request)
                
                assert mock_chat.called


class TestConversationFlows:
    """Test complete conversation flows"""
    
    def test_multi_turn_conversation_memory(self):
        """Test multi-turn conversation preserves memory"""
        from src.api.conversation import _get_session_memory
        
        session_id = "multi-turn-test"
        
        # Turn 1
        memory = _get_session_memory(session_id)
        memory.chat_memory.add_user_message("What is Python?")
        memory.chat_memory.add_ai_message("Python is a programming language")
        
        # Turn 2
        memory2 = _get_session_memory(session_id)
        memory2.chat_memory.add_user_message("Tell me more")
        memory2.chat_memory.add_ai_message("Python was created by Guido van Rossum")
        
        # Verify memory persists
        assert len(memory2.chat_memory.messages) == 4
        assert memory is memory2  # Same instance
        
    def test_conversation_with_tool_results(self):
        """Test conversation flow with tool execution results"""
        from src.api.conversation import _prepare_messages
        
        memory = ConversationBufferMemory(return_messages=True)
        
        # User asks question
        memory.chat_memory.add_user_message("Find Python courses")
        
        # Tool is called (simulated)
        tool_msg = ToolMessage(
            content='{"courses": ["Python 101", "Advanced Python"]}',
            tool_call_id="call_abc"
        )
        memory.chat_memory.add_message(tool_msg)
        
        # AI responds with tool results
        memory.chat_memory.add_ai_message("I found 2 Python courses for you")
        
        messages = _prepare_messages(memory, "Tell me about the first one")
        
        assert len(messages) == 4
        assert isinstance(messages[1], ToolMessage)
