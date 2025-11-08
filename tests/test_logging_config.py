"""
Comprehensive tests for the logging_config module.
"""
import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from src.core.logging_config import (
    LoggerMixin,
    log_security_event,
    get_request_context,
    ProductionLogger,
    request_id_context,
    user_id_context
)


class TestLoggerMixin:
    """Test LoggerMixin class"""
    
    def test_logger_mixin_returns_logger(self):
        """Test that LoggerMixin provides a logger"""
        class TestClass(LoggerMixin):
            pass
        
        obj = TestClass()
        assert hasattr(obj, 'logger')
        assert isinstance(obj.logger, logging.Logger)
    
    def test_logger_name_matches_class_name(self):
        """Test that logger name matches class name"""
        class MyTestClass(LoggerMixin):
            pass
        
        obj = MyTestClass()
        assert obj.logger.name == "MyTestClass"
    
    def test_multiple_instances_share_logger(self):
        """Test that multiple instances of same class share logger"""
        class SharedLoggerClass(LoggerMixin):
            pass
        
        obj1 = SharedLoggerClass()
        obj2 = SharedLoggerClass()
        
        assert obj1.logger.name == obj2.logger.name
        assert obj1.logger is obj2.logger
    
    def test_different_classes_have_different_loggers(self):
        """Test that different classes have different loggers"""
        class ClassA(LoggerMixin):
            pass
        
        class ClassB(LoggerMixin):
            pass
        
        obj_a = ClassA()
        obj_b = ClassB()
        
        assert obj_a.logger.name != obj_b.logger.name
        assert obj_a.logger.name == "ClassA"
        assert obj_b.logger.name == "ClassB"


class TestLogSecurityEvent:
    """Test log_security_event function"""
    
    @patch('src.core.logging_config.logging.getLogger')
    def test_log_security_event_basic(self, mock_get_logger):
        """Test basic security event logging"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        log_security_event("login_attempt", "User login failed")
        
        mock_get_logger.assert_called_once_with("security")
        mock_logger.log.assert_called_once()
    
    @patch('src.core.logging_config.logging.getLogger')
    def test_log_security_event_with_severity(self, mock_get_logger):
        """Test security event with custom severity"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        log_security_event("unauthorized_access", "Forbidden", severity="ERROR")
        
        # Check that ERROR level was used
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.ERROR
    
    @patch('src.core.logging_config.logging.getLogger')
    def test_log_security_event_with_kwargs(self, mock_get_logger):
        """Test security event with additional context"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        log_security_event(
            "suspicious_activity",
            "Multiple failed attempts",
            severity="WARNING",
            user_ip="192.168.1.1",
            attempt_count=5
        )
        
        # Check that extra data includes kwargs
        call_args = mock_logger.log.call_args
        extra_data = call_args[1]['extra']
        assert extra_data['user_ip'] == "192.168.1.1"
        assert extra_data['attempt_count'] == 5
    
    @patch('src.core.logging_config.logging.getLogger')
    def test_log_security_event_includes_context(self, mock_get_logger):
        """Test that security event includes request context"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Set context
        request_id_context.set("req-123")
        user_id_context.set("user-456")
        
        log_security_event("test_event", "Test message")
        
        # Check extra data includes context
        call_args = mock_logger.log.call_args
        extra_data = call_args[1]['extra']
        assert extra_data['request_id'] == "req-123"
        assert extra_data['user_id'] == "user-456"
        
        # Clean up
        request_id_context.set(None)
        user_id_context.set(None)
    
    @patch('src.core.logging_config.logging.getLogger')
    def test_log_security_event_default_severity(self, mock_get_logger):
        """Test that default severity is WARNING"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        log_security_event("test", "message")
        
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.WARNING
    
    @patch('src.core.logging_config.logging.getLogger')
    def test_log_security_event_critical_severity(self, mock_get_logger):
        """Test CRITICAL severity level"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        log_security_event("breach", "Security breach detected", severity="CRITICAL")
        
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.CRITICAL
    
    @patch('src.core.logging_config.logging.getLogger')
    def test_log_security_event_info_severity(self, mock_get_logger):
        """Test INFO severity level"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        log_security_event("login", "Successful login", severity="INFO")
        
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.INFO
    
    @patch('src.core.logging_config.logging.getLogger')
    def test_log_security_event_debug_severity(self, mock_get_logger):
        """Test DEBUG severity level"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        log_security_event("debug_event", "Debug info", severity="DEBUG")
        
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == logging.DEBUG


class TestGetRequestContext:
    """Test get_request_context function"""
    
    def test_get_request_context_empty(self):
        """Test getting context when nothing is set"""
        # Clear context
        request_id_context.set(None)
        user_id_context.set(None)
        
        context = get_request_context()
        
        assert 'request_id' in context
        assert 'user_id' in context
        assert context['request_id'] is None
        assert context['user_id'] is None
    
    def test_get_request_context_with_request_id(self):
        """Test getting context with request ID"""
        request_id_context.set("test-request-123")
        
        context = get_request_context()
        
        assert context['request_id'] == "test-request-123"
        
        # Clean up
        request_id_context.set(None)
    
    def test_get_request_context_with_user_id(self):
        """Test getting context with user ID"""
        user_id_context.set("test-user-456")
        
        context = get_request_context()
        
        assert context['user_id'] == "test-user-456"
        
        # Clean up
        user_id_context.set(None)
    
    def test_get_request_context_with_both(self):
        """Test getting context with both IDs set"""
        request_id_context.set("req-789")
        user_id_context.set("user-012")
        
        context = get_request_context()
        
        assert context['request_id'] == "req-789"
        assert context['user_id'] == "user-012"
        
        # Clean up
        request_id_context.set(None)
        user_id_context.set(None)
    
    def test_get_request_context_returns_dict(self):
        """Test that context is returned as dictionary"""
        context = get_request_context()
        
        assert isinstance(context, dict)
        assert len(context) == 2


class TestProductionLogger:
    """Test ProductionLogger class"""
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    @patch('src.core.logging_config.sys.stdout')
    def test_setup_logging_default(self, mock_stdout, mock_dictConfig):
        """Test setup logging with defaults"""
        mock_stdout.isatty.return_value = False
        
        ProductionLogger.setup_logging()
        
        mock_dictConfig.assert_called_once()
        config = mock_dictConfig.call_args[0][0]
        assert config['version'] == 1
        assert 'formatters' in config
        assert 'handlers' in config
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    @patch('src.core.logging_config.sys.stdout')
    def test_setup_logging_json_format(self, mock_stdout, mock_dictConfig):
        """Test setup logging with JSON format"""
        mock_stdout.isatty.return_value = True
        
        ProductionLogger.setup_logging(format_type="json")
        
        config = mock_dictConfig.call_args[0][0]
        formatter = config['formatters']['default']
        assert 'pythonjsonlogger' in formatter['class']
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    def test_setup_logging_text_format(self, mock_dictConfig):
        """Test setup logging with text format"""
        ProductionLogger.setup_logging(format_type="text")
        
        config = mock_dictConfig.call_args[0][0]
        formatter = config['formatters']['default']
        assert formatter['class'] == 'logging.Formatter'
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    @patch('src.core.logging_config.sys.stdout')
    def test_setup_logging_auto_format_tty(self, mock_stdout, mock_dictConfig):
        """Test auto format detection with TTY"""
        mock_stdout.isatty.return_value = True
        
        ProductionLogger.setup_logging(format_type="auto")
        
        config = mock_dictConfig.call_args[0][0]
        formatter = config['formatters']['default']
        # Should use JSON when TTY
        assert 'pythonjsonlogger' in formatter['class']
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    @patch('src.core.logging_config.sys.stdout')
    def test_setup_logging_auto_format_no_tty(self, mock_stdout, mock_dictConfig):
        """Test auto format detection without TTY"""
        mock_stdout.isatty.return_value = False
        
        ProductionLogger.setup_logging(format_type="auto")
        
        config = mock_dictConfig.call_args[0][0]
        formatter = config['formatters']['default']
        # Should use text when not TTY
        assert formatter['class'] == 'logging.Formatter'
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    @patch('src.core.logging_config.logging.getLogger')
    def test_setup_logging_sets_external_loggers(self, mock_get_logger, mock_dictConfig):
        """Test that external logger levels are set"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        ProductionLogger.setup_logging()
        
        # Should be called for httpx, opentelemetry, grpc
        assert mock_get_logger.call_count >= 3
        assert mock_logger.setLevel.call_count >= 3
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    def test_setup_logging_debug_level(self, mock_dictConfig):
        """Test setup with DEBUG level"""
        ProductionLogger.setup_logging(level="DEBUG")
        
        config = mock_dictConfig.call_args[0][0]
        assert config['root']['level'] == "DEBUG"
        assert config['handlers']['console']['level'] == "DEBUG"
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    def test_setup_logging_error_level(self, mock_dictConfig):
        """Test setup with ERROR level"""
        ProductionLogger.setup_logging(level="ERROR")
        
        config = mock_dictConfig.call_args[0][0]
        assert config['root']['level'] == "ERROR"
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    def test_setup_logging_has_uvicorn_loggers(self, mock_dictConfig):
        """Test that uvicorn loggers are configured"""
        ProductionLogger.setup_logging()
        
        config = mock_dictConfig.call_args[0][0]
        assert 'uvicorn' in config['loggers']
        assert 'uvicorn.error' in config['loggers']
        assert 'uvicorn.access' in config['loggers']
    
    @patch('src.core.logging_config.logging.config.dictConfig')
    def test_setup_logging_disable_existing_loggers_false(self, mock_dictConfig):
        """Test that existing loggers are not disabled"""
        ProductionLogger.setup_logging()
        
        config = mock_dictConfig.call_args[0][0]
        assert config['disable_existing_loggers'] is False


class TestContextVars:
    """Test context variables"""
    
    def test_request_id_context_isolation(self):
        """Test that request_id_context is isolated"""
        request_id_context.set("test-123")
        assert request_id_context.get() == "test-123"
        
        request_id_context.set("test-456")
        assert request_id_context.get() == "test-456"
        
        # Clean up
        request_id_context.set(None)
    
    def test_user_id_context_isolation(self):
        """Test that user_id_context is isolated"""
        user_id_context.set("user-abc")
        assert user_id_context.get() == "user-abc"
        
        user_id_context.set("user-xyz")
        assert user_id_context.get() == "user-xyz"
        
        # Clean up
        user_id_context.set(None)
    
    def test_context_vars_default_none(self):
        """Test that context vars default to None"""
        request_id_context.set(None)
        user_id_context.set(None)
        
        assert request_id_context.get() is None
        assert user_id_context.get() is None
