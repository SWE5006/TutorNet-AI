"""
Additional unit tests for conversation module to improve coverage
Tests additional helper functions and edge cases
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class TestAdditionalConversationFunctions:
    """Additional test cases to improve coverage"""
    
    def test_validate_and_get_tools_with_authorization(self):
        """Test tool validation with authorization token"""
        from src.api.conversation import _validate_and_get_tools
        
        with patch('src.api.conversation.wrap_search_course_service') as mock_wrap:
            mock_tool = Mock()
            mock_tool.name = "search_course"
            mock_wrap.return_value = mock_tool
            
            tools = _validate_and_get_tools(["search_course"], "Bearer token-123")
            
            assert len(tools) > 0
            mock_wrap.assert_called_once()
            
    def test_validate_and_get_tools_multiple_tools(self):
        """Test validation of multiple tools"""
        from src.api.conversation import _validate_and_get_tools
        
        with patch('src.api.conversation.wrap_search_course_service') as mock_course:
            with patch('src.api.conversation.wrap_search_tutor_service') as mock_tutor:
                mock_course.return_value = Mock(name="search_course")
                mock_tutor.return_value = Mock(name="search_tutor")
                
                tools = _validate_and_get_tools(["search_course", "search_tutor"], "Bearer token")
                
                assert len(tools) > 0
                
    def test_create_react_agent_with_langfuse_callback(self):
        """Test creating agent with Langfuse callback"""
        from src.api.conversation import _create_react_agent
        
        with patch('src.api.conversation.create_react_agent') as mock_create:
            with patch('src.api.conversation.get_agent_system_prompt_for_workflow') as mock_prompt:
                with patch('src.api.conversation._get_langfuse_handler_with_trace') as mock_langfuse:
                    mock_graph = Mock()
                    mock_create.return_value = mock_graph
                    mock_prompt.return_value = "Prompt"
                    
                    # Mock Langfuse handler
                    mock_handler = Mock()
                    mock_langfuse.return_value = mock_handler
                    
                    mock_llm = Mock()
                    mock_llm.callbacks = []
                    
                    result = _create_react_agent(mock_llm, [], "assistant", "session-123", "Hello")
                    
                    # Should have set callbacks on LLM
                    assert mock_llm.callbacks == [mock_handler]
                    assert result == mock_graph
                    
    def test_create_react_agent_error_handling(self):
        """Test error handling in agent creation"""
        from src.api.conversation import _create_react_agent
        
        with patch('src.api.conversation.create_react_agent') as mock_create:
            with patch('src.api.conversation.get_agent_system_prompt_for_workflow') as mock_prompt:
                mock_create.side_effect = Exception("Agent creation failed")
                mock_prompt.return_value = "Prompt"
                
                mock_llm = Mock()
                
                with pytest.raises(Exception):
                    _create_react_agent(mock_llm, [], "assistant")
                    
    def test_get_error_fallback_message_connection_error(self):
        """Test specific error fallback for connection errors"""
        from src.api.conversation import _get_error_fallback_message
        
        result = _get_error_fallback_message("Connection refused")
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def test_get_error_fallback_message_timeout_error(self):
        """Test specific error fallback for timeout errors"""
        from src.api.conversation import _get_error_fallback_message
        
        result = _get_error_fallback_message("Request timed out after 30 seconds")
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def test_get_error_fallback_message_rate_limit(self):
        """Test specific error fallback for rate limit errors"""
        from src.api.conversation import _get_error_fallback_message
        
        result = _get_error_fallback_message("Rate limit exceeded. Please try again later.")
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def test_save_conversation_context_error_handling(self):
        """Test error handling in save conversation context"""
        from src.api.conversation import _save_conversation_context
        
        # Mock memory that raises error
        mock_memory = Mock()
        mock_memory.chat_memory.add_user_message.side_effect = Exception("Memory error")
        
        # Should not raise error (logs warning instead)
        _save_conversation_context(mock_memory, "User input", "AI output")
        
    def test_get_session_memory_creates_new_memory(self):
        """Test that new memory is created for new sessions"""
        from src.api.conversation import _get_session_memory, memory_by_session
        
        # Clear any existing memory
        test_session_id = "new-test-session-unique-id-123"
        if test_session_id in memory_by_session:
            del memory_by_session[test_session_id]
        
        memory = _get_session_memory(test_session_id)
        
        assert memory is not None
        assert test_session_id in memory_by_session
        
    def test_get_session_memory_returns_existing_memory(self):
        """Test that existing memory is returned for existing sessions"""
        from src.api.conversation import _get_session_memory, memory_by_session
        
        test_session_id = "existing-session-unique-123"
        
        # Get memory first time
        memory1 = _get_session_memory(test_session_id)
        memory1.chat_memory.add_user_message("Test message")
        
        # Get memory second time
        memory2 = _get_session_memory(test_session_id)
        
        # Should be same instance
        assert memory1 is memory2
        assert len(memory2.chat_memory.messages) == 1
        
    def test_prepare_messages_with_history(self):
        """Test message preparation with existing history"""
        from src.api.conversation import _prepare_messages
        from langchain.memory import ConversationBufferMemory
        
        memory = ConversationBufferMemory(return_messages=True)
        memory.chat_memory.add_user_message("Previous user message")
        memory.chat_memory.add_ai_message("Previous AI response")
        
        messages = _prepare_messages(memory, "New user message")
        
        assert len(messages) == 3
        assert messages[0].content == "Previous user message"
        assert messages[1].content == "Previous AI response"
        assert messages[2].content == "New user message"
        
    def test_create_qwen_instance_with_censorship_workflow(self):
        """Test Qwen instance creation for censorship workflow"""
        from src.api.conversation import _create_qwen_openai_instance, ConversationRequest
        
        with patch('src.api.conversation.settings') as mock_settings:
            with patch('src.api.conversation.ChatOpenAI') as mock_chat:
                mock_settings.qwen_openai_url = "http://test.com"
                mock_settings.openai_api_key = "key"
                mock_settings.llm_model_name = "qwen-model"
                mock_settings.llm_visual_model_name = "qwen-visual"
                
                mock_chat.return_value = Mock()
                
                request = ConversationRequest(
                    message="Test",
                    session_id="test",
                    workflow="censorship"
                )
                
                _create_qwen_openai_instance(request)
                
                # Should use visual model
                call_args = mock_chat.call_args
                assert call_args[1]['model'] == "qwen-visual"
                
    def test_create_openai_instance_with_censorship_workflow(self):
        """Test OpenAI instance creation for censorship workflow"""
        from src.api.conversation import _create_openai_instance, ConversationRequest
        
        with patch('src.api.conversation.settings') as mock_settings:
            with patch('src.api.conversation.ChatOpenAI') as mock_chat:
                mock_settings.openai_api_key = "key"
                mock_settings.llm_model_name = "gpt-4"
                mock_settings.llm_visual_model_name = "gpt-4-vision"
                
                mock_chat.return_value = Mock()
                
                request = ConversationRequest(
                    message="Test",
                    session_id="test",
                    workflow="censorship"
                )
                
                _create_openai_instance(request)
                
                # Should use visual model
                call_args = mock_chat.call_args
                assert call_args[1]['model'] == "gpt-4-vision"
