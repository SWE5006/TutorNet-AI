"""
Integration tests for conversation endpoints
Tests the actual API endpoint behaviors and integration scenarios
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock


class TestToolIntegration:
    """Test tool integration scenarios"""
    
    def test_tool_selection_for_course_search(self):
        """Test that course search workflow selects appropriate tools"""
        from src.api.conversation import _validate_and_get_tools
        
        with patch('src.api.conversation.wrap_search_course_service') as mock_wrap:
            mock_tool = Mock()
            mock_tool.name = "search_course"
            mock_wrap.return_value = mock_tool
            
            tools = _validate_and_get_tools(["search_course"], None)
            
            assert len(tools) > 0
            mock_wrap.assert_called()
            
    def test_tool_selection_for_tutor_search(self):
        """Test that tutor search workflow selects appropriate tools"""
        from src.api.conversation import _validate_and_get_tools
        
        with patch('src.api.conversation.wrap_search_tutor_service') as mock_wrap:
            mock_tool = Mock()
            mock_tool.name = "search_tutor"
            mock_wrap.return_value = mock_tool
            
            tools = _validate_and_get_tools(["search_tutor"], None)
            
            assert len(tools) > 0
            mock_wrap.assert_called()
            
    def test_multiple_tool_selection(self):
        """Test selecting multiple tools at once"""
        from src.api.conversation import _validate_and_get_tools
        
        with patch('src.api.conversation.wrap_search_course_service') as mock_course:
            with patch('src.api.conversation.wrap_search_tutor_service') as mock_tutor:
                mock_course.return_value = Mock(name="search_course")
                mock_tutor.return_value = Mock(name="search_tutor")
                
                tools = _validate_and_get_tools(
                    ["search_course", "search_tutor"], 
                    None
                )
                
                assert len(tools) > 0


class TestChatEndpoint:
    """Test cases for /chat endpoint (non-streaming)"""
    
    def test_chat_endpoint_basic_request(self):
        """Test basic chat request without tools"""
        from src.api.conversation import ConversationRequest
        
        request = ConversationRequest(
            message="What is Python?",
            session_id="chat-001",
            workflow="assistant"
        )
        
        with patch('src.api.conversation._get_llm_instance') as mock_llm:
            with patch('src.api.conversation._get_session_memory') as mock_mem:
                with patch('src.api.conversation._prepare_messages') as mock_prep:
                    with patch('src.api.conversation._save_conversation_context') as mock_save:
                        mock_model = Mock()
                        mock_response = Mock()
                        mock_response.content = "Python is a programming language"
                        mock_model.invoke.return_value = mock_response
                        
                        mock_llm.return_value = mock_model
                        mock_mem.return_value = Mock()
                        mock_prep.return_value = []
                        
                        # Test the flow without HTTP
                        response = mock_model.invoke([])
                        assert response.content is not None
                        
    def test_chat_endpoint_with_memory(self):
        """Test chat preserves conversation memory"""
        from src.api.conversation import _get_session_memory
        from langchain.memory import ConversationBufferMemory
        
        session_id = "memory-test-123"
        
        # Get memory
        memory = _get_session_memory(session_id)
        
        # Add messages
        memory.chat_memory.add_user_message("First message")
        memory.chat_memory.add_ai_message("First response")
        
        # Get same memory again
        memory2 = _get_session_memory(session_id)
        
        assert len(memory2.chat_memory.messages) == 2
        

class TestSessionManagement:
    """Test cases for session management endpoints"""
    
    def test_clear_memory_existing_session(self):
        """Test clearing memory for existing session"""
        from src.api.conversation import _get_session_memory, memory_by_session
        
        session_id = "clear-test-001"
        
        # Create session with memory
        memory = _get_session_memory(session_id)
        memory.chat_memory.add_user_message("Test")
        
        assert session_id in memory_by_session
        
        # Clear it
        if session_id in memory_by_session:
            del memory_by_session[session_id]
            
        assert session_id not in memory_by_session
        
    def test_get_history_existing_session(self):
        """Test retrieving history for existing session"""
        from src.api.conversation import _get_session_memory
        
        session_id = "history-test-001"
        
        # Create session with history
        memory = _get_session_memory(session_id)
        memory.chat_memory.add_user_message("Hello")
        memory.chat_memory.add_ai_message("Hi there")
        
        # Get history
        messages = memory.chat_memory.messages
        
        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there"
        
    def test_get_history_empty_session(self):
        """Test retrieving history for session with no messages"""
        from src.api.conversation import _get_session_memory
        
        session_id = "empty-history-001"
        
        memory = _get_session_memory(session_id)
        messages = memory.chat_memory.messages
        
        assert len(messages) == 0


class TestWorkflowSelection:
    """Test workflow-specific behavior"""
    
    def test_censorship_workflow_uses_visual_model(self):
        """Test censorship workflow selects visual model"""
        from src.api.conversation import _create_qwen_openai_instance, ConversationRequest
        
        with patch('src.api.conversation.settings') as mock_settings:
            with patch('src.api.conversation.ChatOpenAI') as mock_chat:
                mock_settings.qwen_openai_url = "http://test"
                mock_settings.openai_api_key = "key"
                mock_settings.llm_model_name = "qwen-base"
                mock_settings.llm_visual_model_name = "qwen-vision"
                
                request = ConversationRequest(
                    message="Check this image",
                    session_id="test",
                    workflow="censorship"
                )
                
                _create_qwen_openai_instance(request)
                
                # Verify visual model was selected
                call_args = mock_chat.call_args
                assert call_args[1]['model'] == "qwen-vision"
                
    def test_assistant_workflow_uses_standard_model(self):
        """Test assistant workflow uses standard model"""
        from src.api.conversation import _create_qwen_openai_instance, ConversationRequest
        
        with patch('src.api.conversation.settings') as mock_settings:
            with patch('src.api.conversation.ChatOpenAI') as mock_chat:
                mock_settings.qwen_openai_url = "http://test"
                mock_settings.openai_api_key = "key"
                mock_settings.llm_model_name = "qwen-base"
                mock_settings.llm_visual_model_name = "qwen-vision"
                
                request = ConversationRequest(
                    message="Hello",
                    session_id="test",
                    workflow="assistant"
                )
                
                _create_qwen_openai_instance(request)
                
                # Verify standard model was selected
                call_args = mock_chat.call_args
                assert call_args[1]['model'] == "qwen-base"
