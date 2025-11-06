"""
Enhanced error handling with structured logging for production.
"""
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.logging_config import (
    log_security_event,
    get_request_context,
    LoggerMixin
)

logger = logging.getLogger(__name__)


class ErrorHandler(LoggerMixin):
    """Error handler with logging."""
    
    @staticmethod
    def create_error_response(
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Create standardized error response."""
        error_data = {
            "error": {
                "message": message,
                "status_code": status_code,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "request_id": request_id or get_request_context().get('request_id'),
                "error_code": error_code or f"ERR_{status_code}"
            }
        }
        
        if details:
            error_data["error"]["details"] = details
        
        return JSONResponse(
            status_code=status_code,
            content=error_data
        )
    
    @classmethod
    async def handle_http_exception(cls, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with structured logging."""
        request_context = get_request_context()
        request_id = request_context.get('request_id', 'unknown')
        
        error_data = {
            'event': 'http_exception',
            'status_code': exc.status_code,
            'detail': exc.detail,
            'http_method': request.method,
            'http_path': request.url.path,
            'query_params': dict(request.query_params) if request.query_params else None,
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', ''),
            **request_context
        }
        
        # Log based on severity
        if exc.status_code >= 500:
            logger.error(f"Server error: {exc.detail}", extra=error_data)
        elif exc.status_code == 429:
            log_security_event(
                'rate_limit_exceeded',
                f"Rate limit exceeded: {exc.detail}",
                severity='medium',
                endpoint=request.url.path,
                client_ip=request.client.host if request.client else 'unknown'
            )
        elif exc.status_code == 401:
            log_security_event(
                'unauthorized_access',
                f"Unauthorized access attempt: {exc.detail}",
                severity='high',
                endpoint=request.url.path,
                client_ip=request.client.host if request.client else 'unknown'
            )
        elif exc.status_code == 403:
            log_security_event(
                'forbidden_access',
                f"Forbidden access attempt: {exc.detail}",
                severity='high',
                endpoint=request.url.path,
                client_ip=request.client.host if request.client else 'unknown'
            )
        else:
            logger.warning(f"Client error: {exc.detail}", extra=error_data)
        
        return cls.create_error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
            request_id=request_id
        )
    
    @classmethod
    async def handle_starlette_http_exception(cls, request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        request_context = get_request_context()
        request_id = request_context.get('request_id', 'unknown')
        
        error_data = {
            'event': 'starlette_http_exception',
            'status_code': exc.status_code,
            'detail': exc.detail,
            'http_method': request.method,
            'http_path': request.url.path,
            **request_context
        }
        
        logger.warning(f"Starlette HTTP exception: {exc.detail}", extra=error_data)
        
        return cls.create_error_response(
            status_code=exc.status_code,
            message=str(exc.detail),
            request_id=request_id
        )
    
    @classmethod
    async def handle_general_exception(cls, request: Request, exc: Exception) -> JSONResponse:
        """Handle general exceptions."""
        request_context = get_request_context()
        request_id = request_context.get('request_id', 'unknown')
        
        # Get traceback for detailed logging
        tb_str = traceback.format_exc()
        
        error_data = {
            'event': 'unhandled_exception',
            'error_type': type(exc).__name__,
            'error_message': str(exc),
            'traceback': tb_str,
            'http_method': request.method,
            'http_path': request.url.path,
            'query_params': dict(request.query_params) if request.query_params else None,
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', ''),
            **request_context
        }
        
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True, extra=error_data)
        
        # Log as security event if it might be an attack
        if any(pattern in str(exc).lower() for pattern in ['sql', 'injection', 'script', 'xss']):
            log_security_event(
                'potential_attack',
                f"Potential security threat detected: {str(exc)}",
                severity='high',
                error_type=type(exc).__name__,
                endpoint=request.url.path,
                client_ip=request.client.host if request.client else 'unknown'
            )
        
        return cls.create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
            error_code="INTERNAL_ERROR",
            request_id=request_id
        )
