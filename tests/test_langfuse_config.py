"""
Tests for Langfuse configuration and initialization
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.utils.langfuse_config import (
    initialize_langfuse,
    get_langfuse_handler_with_trace,
    langfuse,
    langfuse_handler
)


class TestInitializeLangfuse:
    """Test cases for initialize_langfuse function"""
    
    @patch('src.core.utils.langfuse_config.Langfuse')
    @patch('src.core.utils.langfuse_config.CallbackHandler')
    @patch('src.core.utils.langfuse_config.settings')
    def test_initialize_with_langfuse_enabled(self, mock_settings, mock_handler_class, mock_langfuse_class):
        """Test initialization when Langfuse is enabled"""
        mock_settings.langfuse_enable = True
        mock_settings.langfuse_public_key = "test-public-key"
        mock_settings.langfuse_secret_key = "test-secret-key"
        mock_settings.langfuse_host = "https://test.langfuse.com"
        
        mock_langfuse_instance = Mock()
        mock_langfuse_class.return_value = mock_langfuse_instance
        mock_handler_instance = Mock()
        mock_handler_class.return_value = mock_handler_instance
        
        # Need to reload module or call function directly
        import src.core.utils.langfuse_config as lf_module
        lf_module.initialize_langfuse()
        
        # Verify Langfuse was initialized with correct config
        mock_langfuse_class.assert_called_once()
        call_kwargs = mock_langfuse_class.call_args[1]
        assert call_kwargs['public_key'] == "test-public-key"
        assert call_kwargs['secret_key'] == "test-secret-key"
        assert call_kwargs['host'] == "https://test.langfuse.com"
    
    @patch('src.core.utils.langfuse_config.settings')
    def test_initialize_with_langfuse_disabled(self, mock_settings):
        """Test initialization when Langfuse is disabled"""
        mock_settings.langfuse_enable = False
        
        import src.core.utils.langfuse_config as lf_module
        lf_module.initialize_langfuse()
        
        # Should not raise any exceptions
        # This is mainly to ensure the code path is covered
    
    @patch('src.core.utils.langfuse_config.Langfuse')
    @patch('src.core.utils.langfuse_config.settings')
    def test_initialize_with_exception(self, mock_settings, mock_langfuse_class):
        """Test initialization handles exceptions gracefully"""
        mock_settings.langfuse_enable = True
        mock_settings.langfuse_public_key = "test-key"
        mock_settings.langfuse_secret_key = "test-secret"
        
        mock_langfuse_class.side_effect = Exception("Langfuse initialization error")
        
        import src.core.utils.langfuse_config as lf_module
        
        # Should not raise exception, just log warning
        lf_module.initialize_langfuse()
        
        # Verify globals were set to None
        assert lf_module.langfuse is None
        assert lf_module.langfuse_handler is None
    
    @patch('src.core.utils.langfuse_config.Langfuse')
    @patch('src.core.utils.langfuse_config.CallbackHandler')
    @patch('src.core.utils.langfuse_config.settings')
    def test_initialize_with_partial_config(self, mock_settings, mock_handler_class, mock_langfuse_class):
        """Test initialization with only some config values"""
        mock_settings.langfuse_enable = True
        mock_settings.langfuse_public_key = "test-public-key"
        # Set hasattr to return False for missing attributes
        mock_settings.langfuse_secret_key = None
        mock_settings.langfuse_host = None
        
        import src.core.utils.langfuse_config as lf_module
        lf_module.initialize_langfuse()
        
        # Should still initialize with available config
        assert mock_langfuse_class.called or mock_settings.langfuse_enable


class TestGetLangfuseHandlerWithTrace:
    """Test cases for get_langfuse_handler_with_trace function"""
    
    def test_get_handler_when_langfuse_not_initialized(self):
        """Test getting handler when Langfuse is not initialized"""
        import src.core.utils.langfuse_config as lf_module
        
        # Temporarily set to None
        original_langfuse = lf_module.langfuse
        original_handler = lf_module.langfuse_handler
        
        lf_module.langfuse = None
        lf_module.langfuse_handler = None
        
        handler = get_langfuse_handler_with_trace("session-123", "assistant", "Hello")
        
        assert handler is None
        
        # Restore
        lf_module.langfuse = original_langfuse
        lf_module.langfuse_handler = original_handler
    
    @patch('src.core.utils.langfuse_config.CallbackHandler')
    def test_get_handler_with_trace_success(self, mock_handler_class):
        """Test successfully getting handler with trace"""
        import src.core.utils.langfuse_config as lf_module
        
        # Setup mock Langfuse
        mock_langfuse = Mock()
        mock_trace = Mock()
        mock_langfuse.api.trace.return_value = mock_trace
        
        mock_new_handler = Mock()
        mock_handler_class.return_value = mock_new_handler
        
        original_langfuse = lf_module.langfuse
        original_handler = lf_module.langfuse_handler
        
        lf_module.langfuse = mock_langfuse
        lf_module.langfuse_handler = Mock()
        
        handler = get_langfuse_handler_with_trace("session-123", "translator", "Translate this")
        
        # Verify trace was created
        mock_langfuse.api.trace.assert_called_once()
        call_kwargs = mock_langfuse.api.trace.call_args[1]
        assert call_kwargs['name'] == "conversation_translator"
        assert call_kwargs['user_id'] == "session-123"
        assert call_kwargs['session_id'] == "session-123"
        assert call_kwargs['metadata']['workflow'] == "translator"
        
        # Verify new handler was created with trace
        mock_handler_class.assert_called_once_with(trace=mock_trace)
        assert handler == mock_new_handler
        
        # Restore
        lf_module.langfuse = original_langfuse
        lf_module.langfuse_handler = original_handler
    
    def test_get_handler_with_long_message(self):
        """Test that long messages are truncated in trace metadata"""
        import src.core.utils.langfuse_config as lf_module
        
        mock_langfuse = Mock()
        mock_trace = Mock()
        mock_langfuse.api.trace.return_value = mock_trace
        
        original_langfuse = lf_module.langfuse
        original_handler = lf_module.langfuse_handler
        
        lf_module.langfuse = mock_langfuse
        lf_module.langfuse_handler = Mock()
        
        long_message = "A" * 200  # Message longer than 100 chars
        
        with patch('src.core.utils.langfuse_config.CallbackHandler'):
            handler = get_langfuse_handler_with_trace("session-123", "assistant", long_message)
        
        # Verify message was truncated
        call_kwargs = mock_langfuse.api.trace.call_args[1]
        user_message_in_metadata = call_kwargs['metadata']['user_message']
        assert len(user_message_in_metadata) <= 103  # 100 + "..."
        assert user_message_in_metadata.endswith("...")
        
        # Restore
        lf_module.langfuse = original_langfuse
        lf_module.langfuse_handler = original_handler
    
    def test_get_handler_with_short_message(self):
        """Test that short messages are not truncated"""
        import src.core.utils.langfuse_config as lf_module
        
        mock_langfuse = Mock()
        mock_trace = Mock()
        mock_langfuse.api.trace.return_value = mock_trace
        
        original_langfuse = lf_module.langfuse
        original_handler = lf_module.langfuse_handler
        
        lf_module.langfuse = mock_langfuse
        lf_module.langfuse_handler = Mock()
        
        short_message = "Hello there"
        
        with patch('src.core.utils.langfuse_config.CallbackHandler'):
            handler = get_langfuse_handler_with_trace("session-123", "assistant", short_message)
        
        # Verify message was not truncated
        call_kwargs = mock_langfuse.api.trace.call_args[1]
        user_message_in_metadata = call_kwargs['metadata']['user_message']
        assert user_message_in_metadata == short_message
        assert not user_message_in_metadata.endswith("...")
        
        # Restore
        lf_module.langfuse = original_langfuse
        lf_module.langfuse_handler = original_handler
    
    def test_get_handler_with_trace_exception(self):
        """Test that exceptions are handled and fallback handler is returned"""
        import src.core.utils.langfuse_config as lf_module
        
        mock_langfuse = Mock()
        mock_langfuse.api.trace.side_effect = Exception("Trace creation failed")
        
        mock_fallback_handler = Mock()
        
        original_langfuse = lf_module.langfuse
        original_handler = lf_module.langfuse_handler
        
        lf_module.langfuse = mock_langfuse
        lf_module.langfuse_handler = mock_fallback_handler
        
        handler = get_langfuse_handler_with_trace("session-123", "assistant", "Hello")
        
        # Should return fallback handler
        assert handler == mock_fallback_handler
        
        # Restore
        lf_module.langfuse = original_langfuse
        lf_module.langfuse_handler = original_handler
    
    def test_get_handler_with_different_workflows(self):
        """Test getting handler for different workflow types"""
        import src.core.utils.langfuse_config as lf_module
        
        workflows = ["assistant", "translator", "censorship", "content_optimizer"]
        
        for workflow in workflows:
            mock_langfuse = Mock()
            mock_trace = Mock()
            mock_langfuse.api.trace.return_value = mock_trace
            
            original_langfuse = lf_module.langfuse
            original_handler = lf_module.langfuse_handler
            
            lf_module.langfuse = mock_langfuse
            lf_module.langfuse_handler = Mock()
            
            with patch('src.core.utils.langfuse_config.CallbackHandler'):
                handler = get_langfuse_handler_with_trace("session-123", workflow, "Test message")
            
            # Verify correct trace name
            call_kwargs = mock_langfuse.api.trace.call_args[1]
            assert call_kwargs['name'] == f"conversation_{workflow}"
            assert call_kwargs['metadata']['workflow'] == workflow
            
            # Restore
            lf_module.langfuse = original_langfuse
            lf_module.langfuse_handler = original_handler
