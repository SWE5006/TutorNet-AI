"""
Unit tests for settings module
Tests the settings configuration and validation
"""
import pytest
from unittest.mock import patch, MagicMock
import os


class TestSettings:
    """Test cases for Settings configuration"""
    
    def test_settings_loads_from_env(self):
        """Test that settings loads from environment variables"""
        from src.core.utils.settings import get_settings
        
        # Settings should be loaded
        settings = get_settings()
        assert settings is not None
        
    def test_settings_has_required_attributes(self):
        """Test that settings has all required attributes"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        # Check for essential attributes
        assert hasattr(settings, 'openai_api_key')
        assert hasattr(settings, 'llm_model_name')
        assert hasattr(settings, 'qwen_openai_enabled')
        assert hasattr(settings, 'api_key')
        
    def test_settings_qwen_openai_enabled_default(self):
        """Test Qwen OpenAI enabled default value"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        # Should have a boolean value
        assert isinstance(settings.qwen_openai_enabled, bool)
        
    def test_settings_temperature_constants(self):
        """Test that temperature constants are within valid range"""
        from src.core.utils.models import DEFAULT_TEMPERATURE
        
        assert DEFAULT_TEMPERATURE >= 0.0
        assert DEFAULT_TEMPERATURE <= 1.0
        
    def test_settings_timeout_values(self):
        """Test timeout configuration values"""
        from src.core.utils.models import REQUEST_TIMEOUT, MAX_RETRIES
        
        assert REQUEST_TIMEOUT > 0
        assert MAX_RETRIES >= 0
        
    def test_settings_langfuse_config(self):
        """Test Langfuse configuration"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        # Check Langfuse settings exist
        assert hasattr(settings, 'langfuse_enable')
        assert isinstance(settings.langfuse_enable, bool)
        
    def test_settings_has_request_domain(self):
        """Test that settings has service API URL configured"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        assert hasattr(settings, 'service_api_url')
        # Should be a string (URL)
        if settings.service_api_url:
            assert isinstance(settings.service_api_url, str)
            
    def test_settings_visual_model_config(self):
        """Test visual model configuration"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        assert hasattr(settings, 'llm_visual_model_name')
        # Can be None or string
        if settings.llm_visual_model_name:
            assert isinstance(settings.llm_visual_model_name, str)
            
    def test_settings_security_config(self):
        """Test security configuration"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        assert hasattr(settings, 'security_enabled')
        assert isinstance(settings.security_enabled, bool)
        assert hasattr(settings, 'rate_limiting_enabled')
        assert isinstance(settings.rate_limiting_enabled, bool)
        
    def test_settings_logging_config(self):
        """Test logging configuration"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        assert hasattr(settings, 'log_level')
        assert hasattr(settings, 'log_format')
        assert settings.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class TestSettingsValidation:
    """Test cases for settings validation logic"""
    
    def test_qwen_settings_validation(self):
        """Test Qwen OpenAI settings validation"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        # If Qwen is enabled, should have required config
        if settings.qwen_openai_enabled:
            assert settings.qwen_openai_url is not None or settings.qwen_openai_enabled == False
            
    def test_model_name_attribute_exists(self):
        """Test that model name attribute exists"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        # Should have a model name attribute
        assert hasattr(settings, 'llm_model_name')
        
    def test_settings_cache_config(self):
        """Test cache configuration"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        assert hasattr(settings, 'graph_cache_max_size')
        assert hasattr(settings, 'agent_cache_max_size')
        assert settings.graph_cache_max_size > 0
        assert settings.agent_cache_max_size > 0
        
    def test_settings_cors_config(self):
        """Test CORS configuration"""
        from src.core.utils.settings import get_settings
        
        settings = get_settings()
        assert hasattr(settings, 'cors_origins')
        assert isinstance(settings.cors_origins, str)


class TestSettingsCaching:
    """Test cases for settings caching"""
    
    def test_get_settings_returns_same_instance(self):
        """Test that get_settings returns cached instance"""
        from src.core.utils.settings import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should return the same cached instance
        assert settings1 is settings2
