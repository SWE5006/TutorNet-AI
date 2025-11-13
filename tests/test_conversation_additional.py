"""
Additional unit tests for conversation module to improve coverage
Tests additional helper functions and edge cases
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from src.core.utils.api_utils import validate_and_get_tools, get_error_fallback_message
from src.core.utils.agents.react_agent import create_react_agent
from src.core.utils.memory_manager import get_session_memory, prepare_messages, save_conversation_context, memory_by_session
from src.core.utils.llm_factory import create_common_llm_params, create_qwen_openai_instance, create_openai_instance
from src.core.utils.models import ConversationRequest


class TestAdditionalConversationFunctions:
    """Additional test cases to improve coverage"""
    
    def testvalidate_and_get_tools_with_authorization(self):
        """Test tool validation with authorization token"""
        # Imported at top: validate_and_get_tools
        
        with patch('src.core.utils.api_utils.wrap_search_course_service') as mock_wrap:
            mock_tool = Mock()
            mock_tool.name = "search_course"
            mock_wrap.return_value = mock_tool
            
            tools = validate_and_get_tools(["search_course"], "Bearer token-123")
            
            assert len(tools) > 0
            mock_wrap.assert_called_once()
            
    def testvalidate_and_get_tools_multiple_tools(self):
        """Test validation of multiple tools"""
        # Imported at top: validate_and_get_tools
        
        with patch('src.core.utils.api_utils.wrap_search_course_service') as mock_course:
            with patch('src.core.utils.api_utils.wrap_search_tutor_service') as mock_tutor:
                mock_course.return_value = Mock(name="search_course")
                mock_tutor.return_value = Mock(name="search_tutor")
                
                tools = validate_and_get_tools(["search_course", "search_tutor"], "Bearer token")
                
                assert len(tools) > 0
                
    def testcreate_react_agent_with_langfuse_callback(self):
        """Test creating agent with Langfuse callback"""
        # Imported at top: create_react_agent
        
        with patch('src.core.utils.agents.react_agent.langgraph_create_react_agent') as mock_langgraph:
            with patch('src.core.utils.system_prompts.get_agent_system_prompt_for_workflow') as mock_prompt:
                mock_graph = Mock()
                mock_langgraph.return_value = mock_graph
                mock_prompt.return_value = "Prompt"
                
                mock_llm = Mock()
                mock_llm.callbacks = []
                
                result = create_react_agent(mock_llm, [], "assistant", "session-123", "Hello")
                
                # Should have set callbacks on LLM (check that callback was added, not exact object)
                assert len(mock_llm.callbacks) > 0
                assert result == mock_graph
                    
    def testcreate_react_agent_error_handling(self):
        """Test error handling in agent creation"""
        # Imported at top: create_react_agent
        
        with patch('src.core.utils.agents.react_agent.langgraph_create_react_agent') as mock_langgraph:
            with patch('src.core.utils.system_prompts.get_agent_system_prompt_for_workflow') as mock_prompt:
                mock_langgraph.side_effect = Exception("Agent creation failed")
                mock_prompt.return_value = "Prompt"
                
                mock_llm = Mock()
                
                with pytest.raises(HTTPException) as exc_info:
                    create_react_agent(mock_llm, [], "assistant")
                
                assert exc_info.value.status_code == 500
                assert "Failed to create ReAct agent" in str(exc_info.value.detail)
                    
    def testget_error_fallback_message_connection_error(self):
        """Test specific error fallback for connection errors"""
        # Imported at top: get_error_fallback_message
        
        result = get_error_fallback_message("Connection refused")
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def testget_error_fallback_message_timeout_error(self):
        """Test specific error fallback for timeout errors"""
        # Imported at top: get_error_fallback_message
        
        result = get_error_fallback_message("Request timed out after 30 seconds")
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def testget_error_fallback_message_rate_limit(self):
        """Test specific error fallback for rate limit errors"""
        # Imported at top: get_error_fallback_message
        
        result = get_error_fallback_message("Rate limit exceeded. Please try again later.")
        
        assert isinstance(result, str)
        assert len(result) > 0
        
    def testsave_conversation_context_error_handling(self):
        """Test error handling in save conversation context"""
        # Imported at top: save_conversation_context
        
        # Mock memory that raises error
        mock_memory = Mock()
        mock_memory.chat_memory.add_user_message.side_effect = Exception("Memory error")
        
        # Should not raise error (logs warning instead)
        save_conversation_context(mock_memory, "User input", "AI output")
        
    def testget_session_memory_creates_new_memory(self):
        """Test that new memory is created for new sessions"""
        # Imported at top: get_session_memory, memory_by_session
        
        # Clear any existing memory
        test_session_id = "new-test-session-unique-id-123"
        if test_session_id in memory_by_session:
            del memory_by_session[test_session_id]
        
        memory = get_session_memory(test_session_id)
        
        assert memory is not None
        assert test_session_id in memory_by_session
        
    def testget_session_memory_returns_existing_memory(self):
        """Test that existing memory is returned for existing sessions"""
        # Imported at top: get_session_memory, memory_by_session
        
        test_session_id = "existing-session-unique-123"
        
        # Get memory first time
        memory1 = get_session_memory(test_session_id)
        memory1.chat_memory.add_user_message("Test message")
        
        # Get memory second time
        memory2 = get_session_memory(test_session_id)
        
        # Should be same instance
        assert memory1 is memory2
        assert len(memory2.chat_memory.messages) == 1
        
    def testprepare_messages_with_history(self):
        """Test message preparation with existing history"""
        # Imported at top: prepare_messages
        from langchain.memory import ConversationBufferMemory
        
        memory = ConversationBufferMemory(return_messages=True)
        memory.chat_memory.add_user_message("Previous user message")
        memory.chat_memory.add_ai_message("Previous AI response")
        
        messages = prepare_messages(memory, "New user message")
        
        assert len(messages) == 3
        assert messages[0].content == "Previous user message"
        assert messages[1].content == "Previous AI response"
        assert messages[2].content == "New user message"
