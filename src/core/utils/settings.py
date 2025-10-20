"""
Configuration management for the application.
Centralized configuration loading and validation.
"""
import os
import logging
from typing import Optional
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    
    # API
    api_key: str
    api_prefix: str = ""
    
    # CORS
    cors_origins: str = ""
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "auto"  # auto, json, or text (auto detects environment)
    enable_request_logging: bool = True
    enable_security_logging: bool = True
    enable_performance_logging: bool = True
    enable_callback_logging: bool = False  # Flag to control custom callback handler logs
    
    # Cache
    graph_cache_max_size: int = 10
    agent_cache_max_size: int = 50
    cache_ttl: int = 3600  # Increased to 1 hour for better performance
    
    # Guardrails
    guardrails_config_path: str = "./config/guardrails"

    # MCP
    mcp_url: str

    # Langfuse
    langfuse_enable: bool = False
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: Optional[str] = None

    # Qwen
    qwen_openai_enabled: bool = False
    qwen_openai_url: str = None

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model_name: str = None

    # Debug mode
    debug_mode: bool = False
    
    # Security Configuration
    security_enabled: bool = True
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    enable_brute_force_protection: bool = True
    max_failed_attempts: int = 5
    blacklist_duration_minutes: int = 60
    min_api_key_length: int = 32
    require_https_in_production: bool = True
    
    # Input Validation Settings
    max_request_size_mb: int = 10
    max_query_params: int = 50
    enable_sql_injection_detection: bool = True
    enable_xss_detection: bool = True
    enable_input_sanitization: bool = True
    
    # Message Validation Settings
    message_validation_enabled: bool = True
    bomb_threat_detection_enabled: bool = True
    pii_detection_enabled: bool = True
    validation_log_level: str = "INFO"  # CRITICAL, HIGH, MEDIUM, LOW
    
    # Security threat keywords (can be overridden via environment)
    threat_keywords_critical: str = "bomb,explod,explosi,terrori,burn,kill,murder,time-bomb,explosiv,blow,shoot"
    threat_keywords_high: str = "kill,murder,assassinate,execute,slaughter,mass shooting,school shooting,gun down,open fire,rampage,massacre,bloodbath,hostage"
    threat_keywords_medium: str = "threat,harm,hurt,damage,destroy,violence,attack,assault,revenge,payback,vengeance,retaliate"
    threat_keywords_low: str = "angry,mad,furious,hate,despise,eliminate,remove,take out,deal with"
    
    # Monitoring and alerting thresholds
    security_alert_threshold: int = 1  # Alert after this many security events per hour
    pii_alert_threshold: int = 10  # Alert after this many PII detections per hour


    @field_validator('mcp_url')
    @classmethod
    def validate_mcp_url(cls, v):
        if not v:
            raise ValueError("MCP_URL is required")
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    
    return settings


def setup_logging(settings: Optional[Settings] = None) -> logging.Logger:
    """Setup centralized logging configuration with enhanced JSON support for Kubernetes."""
    if settings is None:
        settings = get_settings()
    
    # Import here to avoid circular imports
    from src.core.logging_config import ProductionLogger
    
    # Setup production logging for console only (K8s will collect)
    ProductionLogger.setup_logging(
        level=settings.log_level,
        format_type=settings.log_format
    )
    
    return logging.getLogger(__name__)
