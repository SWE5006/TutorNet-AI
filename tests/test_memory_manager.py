"""
Tests for memory manager functions
"""
import pytest
from unittest.mock import Mock, patch
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from src.core.utils.memory_manager import (
    get_session_memory,
    clear_session_memory,
    prepare_messages,
    save_conversation_context,
    get_session_history,
    memory_by_session
)


class TestGetSessionMemory:
    """Test cases for get_session_memory function"""
    
    def setup_method(self):
        """Clear memory before each test"""
        memory_by_session.clear()
    
    def test_get_new_session_memory(self):
        """Test getting memory for a new session"""
        session_id = "new-session-001"
        memory = get_session_memory(session_id)
        
        assert isinstance(memory, ConversationBufferMemory)
        assert session_id in memory_by_session
        assert memory.return_messages is True
    
    def test_get_existing_session_memory(self):
        """Test getting memory for an existing session"""
        session_id = "existing-session-001"
        
        # Create initial memory
        memory1 = get_session_memory(session_id)
        memory1.save_context({"input": "Hello"}, {"output": "Hi there"})
        
        # Get the same memory again
        memory2 = get_session_memory(session_id)
        
        assert memory1 is memory2
        assert len(memory2.chat_memory.messages) == 2
    
    def test_multiple_sessions_isolated(self):
        """Test that multiple sessions maintain separate memories"""
        session1 = "session-001"
        session2 = "session-002"
        
        memory1 = get_session_memory(session1)
        memory2 = get_session_memory(session2)
        
        memory1.save_context({"input": "Message 1"}, {"output": "Response 1"})
        memory2.save_context({"input": "Message 2"}, {"output": "Response 2"})
        
        assert len(memory1.chat_memory.messages) == 2
        assert len(memory2.chat_memory.messages) == 2
        assert memory1 is not memory2


class TestClearSessionMemory:
    """Test cases for clear_session_memory function"""
    
    def setup_method(self):
        """Clear memory before each test"""
        memory_by_session.clear()
    
    def test_clear_existing_session(self):
        """Test clearing an existing session"""
        session_id = "clear-test-001"
        
        # Create session with data
        memory = get_session_memory(session_id)
        memory.save_context({"input": "Test"}, {"output": "Response"})
        
        assert session_id in memory_by_session
        
        # Clear the session
        result = clear_session_memory(session_id)
        
        assert result is True
        assert session_id not in memory_by_session
    
    def test_clear_nonexistent_session(self):
        """Test clearing a session that doesn't exist"""
        session_id = "nonexistent-session"
        
        result = clear_session_memory(session_id)
        
        assert result is False
    
    def test_clear_multiple_times(self):
        """Test clearing the same session multiple times"""
        session_id = "multi-clear-001"
        
        memory = get_session_memory(session_id)
        
        # First clear should succeed
        result1 = clear_session_memory(session_id)
        assert result1 is True
        
        # Second clear should fail (already cleared)
        result2 = clear_session_memory(session_id)
        assert result2 is False


class TestPrepareMessages:
    """Test cases for prepare_messages function"""
    
    def test_prepare_messages_empty_history(self):
        """Test preparing messages with empty history"""
        memory = ConversationBufferMemory(return_messages=True)
        user_message = "Hello, world!"
        
        messages = prepare_messages(memory, user_message)
        
        assert len(messages) == 1
        assert isinstance(messages[0], HumanMessage)
        assert messages[0].content == "Hello, world!"
    
    def test_prepare_messages_with_history(self):
        """Test preparing messages with conversation history"""
        memory = ConversationBufferMemory(return_messages=True)
        memory.save_context({"input": "Previous message"}, {"output": "Previous response"})
        
        messages = prepare_messages(memory, "New message")
        
        assert len(messages) == 3
        assert messages[0].content == "Previous message"
        assert messages[1].content == "Previous response"
        assert messages[2].content == "New message"
        assert isinstance(messages[2], HumanMessage)
    
    def test_prepare_messages_preserves_order(self):
        """Test that message order is preserved"""
        memory = ConversationBufferMemory(return_messages=True)
        memory.save_context({"input": "First"}, {"output": "First response"})
        memory.save_context({"input": "Second"}, {"output": "Second response"})
        
        messages = prepare_messages(memory, "Third")
        
        assert len(messages) == 5
        assert messages[0].content == "First"
        assert messages[2].content == "Second"
        assert messages[4].content == "Third"
    
    def test_prepare_messages_multiple_history_entries(self):
        """Test preparing messages with multiple history entries"""
        memory = ConversationBufferMemory(return_messages=True)
        
        # Add multiple conversation turns
        for i in range(3):
            memory.save_context({"input": f"Message {i}"}, {"output": f"Response {i}"})
        
        messages = prepare_messages(memory, "Final message")
        
        # 3 conversations * 2 messages each + 1 new message = 7
        assert len(messages) == 7
        assert messages[-1].content == "Final message"


class TestSaveConversationContext:
    """Test cases for save_conversation_context function"""
    
    def test_save_context_success(self):
        """Test successfully saving conversation context"""
        memory = ConversationBufferMemory(return_messages=True)
        
        save_conversation_context(memory, "User input", "AI output")
        
        messages = memory.chat_memory.messages
        assert len(messages) == 2
        assert messages[0].content == "User input"
        assert messages[1].content == "AI output"
    
    def test_save_context_multiple_times(self):
        """Test saving context multiple times"""
        memory = ConversationBufferMemory(return_messages=True)
        
        save_conversation_context(memory, "Input 1", "Output 1")
        save_conversation_context(memory, "Input 2", "Output 2")
        
        messages = memory.chat_memory.messages
        assert len(messages) == 4
    
    def test_save_context_with_exception(self):
        """Test save context handles exceptions gracefully"""
        mock_memory = Mock()
        mock_memory.save_context.side_effect = Exception("Save error")
        
        # Should not raise exception
        save_conversation_context(mock_memory, "Input", "Output")
        
        # Verify it tried to save
        mock_memory.save_context.assert_called_once()
    
    def test_save_context_empty_strings(self):
        """Test saving empty strings"""
        memory = ConversationBufferMemory(return_messages=True)
        
        save_conversation_context(memory, "", "")
        
        messages = memory.chat_memory.messages
        assert len(messages) == 2
        assert messages[0].content == ""
        assert messages[1].content == ""
    
    def test_save_context_special_characters(self):
        """Test saving context with special characters"""
        memory = ConversationBufferMemory(return_messages=True)
        
        user_input = "Hello! How are you? 🎉"
        ai_output = "I'm great! Thanks for asking 😊"
        
        save_conversation_context(memory, user_input, ai_output)
        
        messages = memory.chat_memory.messages
        assert messages[0].content == user_input
        assert messages[1].content == ai_output


class TestGetSessionHistory:
    """Test cases for get_session_history function"""
    
    def setup_method(self):
        """Clear memory before each test"""
        memory_by_session.clear()
    
    def test_get_history_existing_session(self):
        """Test getting history for existing session"""
        session_id = "history-test-001"
        
        memory = get_session_memory(session_id)
        memory.save_context({"input": "Hello"}, {"output": "Hi"})
        
        history = get_session_history(session_id)
        
        assert history is not None
        assert "Hello" in history
        assert "Hi" in history
    
    def test_get_history_nonexistent_session(self):
        """Test getting history for non-existent session"""
        session_id = "nonexistent-history"
        
        history = get_session_history(session_id)
        
        assert history is None
    
    def test_get_history_empty_session(self):
        """Test getting history for empty session"""
        session_id = "empty-history-001"
        
        # Create session but don't add any messages
        get_session_memory(session_id)
        
        history = get_session_history(session_id)
        
        # Should return empty string or similar
        assert history is not None
        assert len(history) == 0 or history == ""
    
    def test_get_history_multiple_messages(self):
        """Test getting history with multiple messages"""
        session_id = "multi-message-history"
        
        memory = get_session_memory(session_id)
        memory.save_context({"input": "First"}, {"output": "First response"})
        memory.save_context({"input": "Second"}, {"output": "Second response"})
        
        history = get_session_history(session_id)
        
        assert "First" in history
        assert "First response" in history
        assert "Second" in history
        assert "Second response" in history


class TestMemoryIntegration:
    """Integration tests for memory functions"""
    
    def setup_method(self):
        """Clear memory before each test"""
        memory_by_session.clear()
    
    def test_full_conversation_flow(self):
        """Test complete conversation flow"""
        session_id = "integration-test-001"
        
        # Get memory
        memory = get_session_memory(session_id)
        
        # First turn
        messages1 = prepare_messages(memory, "Hello")
        save_conversation_context(memory, "Hello", "Hi there!")
        
        # Second turn
        messages2 = prepare_messages(memory, "How are you?")
        save_conversation_context(memory, "How are you?", "I'm doing well!")
        
        # Check history
        history = get_session_history(session_id)
        
        assert len(messages2) == 3  # Previous message + response + new message
        assert "Hello" in history
        assert "Hi there!" in history
        assert "How are you?" in history
        
        # Clear session
        result = clear_session_memory(session_id)
        assert result is True
        
        # History should be gone
        history_after = get_session_history(session_id)
        assert history_after is None
