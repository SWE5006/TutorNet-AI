"""
Production logging configuration for the application.
"""
import logging
import logging.config
import sys
import uuid
from typing import Dict, Any, Optional
from contextvars import ContextVar

# Context variables for request tracking
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class LoggerMixin:
    """Mixin class to provide logger functionality to other classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(self.__class__.__name__)


def log_security_event(event_type: str, message: str, severity: str = "WARNING", **kwargs) -> None:
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        message: Event message
        severity: Log severity level
        **kwargs: Additional context data
    """
    logger = logging.getLogger("security")
    log_level = getattr(logging, severity.upper(), logging.WARNING)
    
    extra_data = {
        "event_type": event_type,
        "request_id": request_id_context.get(),
        "user_id": user_id_context.get(),
        **kwargs
    }
    
    logger.log(log_level, message, extra=extra_data)


def get_request_context() -> Dict[str, Any]:
    """
    Get current request context information.
    
    Returns:
        Dictionary containing request context
    """
    return {
        "request_id": request_id_context.get(),
        "user_id": user_id_context.get()
    }


class ProductionLogger:
    """Production logger configuration handler."""
    
    @staticmethod
    def setup_logging(level: str = "INFO", format_type: str = "auto") -> None:
        """
        Setup production logging configuration.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_type: Format type (auto, json, text)
        """
        # Determine format based on format_type
        if format_type == "auto":
            # Auto-detect based on environment
            format_type = "json" if sys.stdout.isatty() else "text"
        
        if format_type == "json":
            formatter_config = {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            }
        else:
            formatter_config = {
                "class": "logging.Formatter",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        
        # Logging configuration
        config: Dict[str, Any] = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": formatter_config
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": level,
                    "formatter": "default",
                    "stream": "ext://sys.stdout"
                }
            },
            "root": {
                "level": level,
                "handlers": ["console"]
            },
            "loggers": {
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False
                },
                "uvicorn.error": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False
                }
            }
        }
        
        # Apply configuration
        logging.config.dictConfig(config)
        
        # Set specific logger levels
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("opentelemetry").setLevel(logging.WARNING)
        logging.getLogger("grpc").setLevel(logging.WARNING)
