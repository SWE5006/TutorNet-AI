"""
Comprehensive tests for the error_handling module.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.core.utils.error_handling import ErrorHandler


class TestErrorHandler:
    """Test ErrorHandler class"""
    
    def test_create_error_response_basic(self):
        """Test creating basic error response"""
        response = ErrorHandler.create_error_response(
            status_code=400,
            message="Bad request"
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        
        # Check response content
        content = response.body.decode()
        assert "Bad request" in content
        assert "ERR_400" in content
    
    def test_create_error_response_with_details(self):
        """Test creating error response with details"""
        details = {"field": "email", "error": "invalid format"}
        response = ErrorHandler.create_error_response(
            status_code=422,
            message="Validation error",
            details=details
        )
        
        assert response.status_code == 422
        content = response.body.decode()
        assert "Validation error" in content
        assert "email" in content
    
    def test_create_error_response_with_error_code(self):
        """Test creating error response with custom error code"""
        response = ErrorHandler.create_error_response(
            status_code=500,
            message="Database error",
            error_code="DB_CONNECTION_ERROR"
        )
        
        assert response.status_code == 500
        content = response.body.decode()
        assert "DB_CONNECTION_ERROR" in content
    
    def test_create_error_response_with_request_id(self):
        """Test creating error response with request ID"""
        response = ErrorHandler.create_error_response(
            status_code=404,
            message="Not found",
            request_id="req-123-456"
        )
        
        assert response.status_code == 404
        content = response.body.decode()
        assert "req-123-456" in content
    
    def test_create_error_response_with_all_params(self):
        """Test creating error response with all parameters"""
        response = ErrorHandler.create_error_response(
            status_code=403,
            message="Access denied",
            details={"resource": "admin_panel"},
            error_code="ACCESS_DENIED",
            request_id="req-789"
        )
        
        assert response.status_code == 403
        content = response.body.decode()
        assert "Access denied" in content
        assert "ACCESS_DENIED" in content
        assert "req-789" in content
        assert "admin_panel" in content
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_http_exception_server_error(self, mock_logger, mock_get_context):
        """Test handling HTTP exception with 500 status"""
        mock_get_context.return_value = {'request_id': 'test-req-id'}
        
        # Create mock request
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.query_params = {}
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = "test-agent"
        
        # Create HTTP exception
        exc = HTTPException(status_code=500, detail="Internal server error")
        
        response = await ErrorHandler.handle_http_exception(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.log_security_event')
    async def test_handle_http_exception_rate_limit(self, mock_security_log, mock_get_context):
        """Test handling HTTP exception with 429 rate limit status"""
        mock_get_context.return_value = {'request_id': 'test-req-id'}
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/submit"
        request.query_params = {}
        request.client.host = "192.168.1.1"
        request.headers.get.return_value = "bot-agent"
        
        exc = HTTPException(status_code=429, detail="Too many requests")
        
        response = await ErrorHandler.handle_http_exception(request, exc)
        
        assert response.status_code == 429
        mock_security_log.assert_called_once()
        call_args = mock_security_log.call_args
        assert call_args[0][0] == 'rate_limit_exceeded'
        assert call_args[1]['severity'] == 'medium'
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.log_security_event')
    async def test_handle_http_exception_unauthorized(self, mock_security_log, mock_get_context):
        """Test handling HTTP exception with 401 unauthorized status"""
        mock_get_context.return_value = {'request_id': 'test-req-id'}
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/protected"
        request.query_params = {}
        request.client.host = "10.0.0.1"
        request.headers.get.return_value = "curl/7.68"
        
        exc = HTTPException(status_code=401, detail="Unauthorized")
        
        response = await ErrorHandler.handle_http_exception(request, exc)
        
        assert response.status_code == 401
        mock_security_log.assert_called_once()
        call_args = mock_security_log.call_args
        assert call_args[0][0] == 'unauthorized_access'
        assert call_args[1]['severity'] == 'high'
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.log_security_event')
    async def test_handle_http_exception_forbidden(self, mock_security_log, mock_get_context):
        """Test handling HTTP exception with 403 forbidden status"""
        mock_get_context.return_value = {'request_id': 'test-req-id'}
        
        request = Mock(spec=Request)
        request.method = "DELETE"
        request.url.path = "/api/admin/delete"
        request.query_params = {}
        request.client.host = "172.16.0.1"
        request.headers.get.return_value = "Mozilla/5.0"
        
        exc = HTTPException(status_code=403, detail="Forbidden")
        
        response = await ErrorHandler.handle_http_exception(request, exc)
        
        assert response.status_code == 403
        mock_security_log.assert_called_once()
        call_args = mock_security_log.call_args
        assert call_args[0][0] == 'forbidden_access'
        assert call_args[1]['severity'] == 'high'
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_http_exception_client_error(self, mock_logger, mock_get_context):
        """Test handling HTTP exception with 400 client error"""
        mock_get_context.return_value = {'request_id': 'test-req-id'}
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/validate"
        request.query_params = {'param': 'value'}
        request.client.host = "192.168.0.1"
        request.headers.get.return_value = "test-client"
        
        exc = HTTPException(status_code=400, detail="Bad request")
        
        response = await ErrorHandler.handle_http_exception(request, exc)
        
        assert response.status_code == 400
        mock_logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_http_exception_with_query_params(self, mock_logger, mock_get_context):
        """Test handling HTTP exception with query parameters"""
        mock_get_context.return_value = {'request_id': 'test-req-id'}
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/search"
        request.query_params = {'q': 'test', 'page': '1'}
        request.client.host = "10.1.1.1"
        request.headers.get.return_value = "browser"
        
        exc = HTTPException(status_code=404, detail="Not found")
        
        response = await ErrorHandler.handle_http_exception(request, exc)
        
        assert response.status_code == 404
        # Verify query params were logged
        call_args = mock_logger.warning.call_args
        assert 'query_params' in str(call_args)
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_http_exception_no_client(self, mock_logger, mock_get_context):
        """Test handling HTTP exception when request has no client"""
        mock_get_context.return_value = {'request_id': 'test-req-id'}
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.query_params = {}
        request.client = None
        request.headers.get.return_value = ""
        
        exc = HTTPException(status_code=500, detail="Server error")
        
        response = await ErrorHandler.handle_http_exception(request, exc)
        
        assert response.status_code == 500
        # Verify it handled missing client gracefully
        call_args = mock_logger.error.call_args
        assert 'unknown' in str(call_args)
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_starlette_http_exception(self, mock_logger, mock_get_context):
        """Test handling Starlette HTTP exception"""
        mock_get_context.return_value = {'request_id': 'starlette-req-id'}
        
        request = Mock(spec=Request)
        request.method = "PUT"
        request.url.path = "/api/update"
        request.query_params = {}
        
        exc = StarletteHTTPException(status_code=404, detail="Resource not found")
        
        response = await ErrorHandler.handle_starlette_http_exception(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        mock_logger.warning.assert_called_once()
        content = response.body.decode()
        assert "Resource not found" in content
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_general_exception(self, mock_logger, mock_get_context):
        """Test handling general exception"""
        mock_get_context.return_value = {'request_id': 'general-req-id'}
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/process"
        request.query_params = {'id': '123'}
        request.client.host = "192.168.1.100"
        request.headers.get.return_value = "python-requests"
        
        exc = ValueError("Invalid value provided")
        
        response = await ErrorHandler.handle_general_exception(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        mock_logger.error.assert_called_once()
        content = response.body.decode()
        assert "Internal server error" in content
        assert "INTERNAL_ERROR" in content
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.log_security_event')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_general_exception_sql_injection(self, mock_logger, mock_security_log, mock_get_context):
        """Test handling exception that looks like SQL injection"""
        mock_get_context.return_value = {'request_id': 'security-req-id'}
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/data"
        request.query_params = {}
        request.client.host = "suspicious-ip"
        request.headers.get.return_value = "malicious-agent"
        
        exc = Exception("SQL injection attempt detected")
        
        response = await ErrorHandler.handle_general_exception(request, exc)
        
        assert response.status_code == 500
        mock_security_log.assert_called_once()
        call_args = mock_security_log.call_args
        assert call_args[0][0] == 'potential_attack'
        assert call_args[1]['severity'] == 'high'
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.log_security_event')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_general_exception_xss(self, mock_logger, mock_security_log, mock_get_context):
        """Test handling exception that looks like XSS attack"""
        mock_get_context.return_value = {'request_id': 'xss-req-id'}
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/comment"
        request.query_params = {}
        request.client.host = "attacker-ip"
        request.headers.get.return_value = "bot"
        
        exc = Exception("XSS script tag detected")
        
        response = await ErrorHandler.handle_general_exception(request, exc)
        
        assert response.status_code == 500
        mock_security_log.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.log_security_event')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_general_exception_script_injection(self, mock_logger, mock_security_log, mock_get_context):
        """Test handling exception with 'script' in message"""
        mock_get_context.return_value = {'request_id': 'script-req-id'}
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/input"
        request.query_params = {}
        request.client.host = "10.0.0.99"
        request.headers.get.return_value = "unknown"
        
        exc = Exception("Script injection detected in input")
        
        response = await ErrorHandler.handle_general_exception(request, exc)
        
        assert response.status_code == 500
        mock_security_log.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_general_exception_no_client(self, mock_logger, mock_get_context):
        """Test handling general exception when request has no client"""
        mock_get_context.return_value = {'request_id': 'no-client-req-id'}
        
        request = Mock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.query_params = None
        request.client = None
        request.headers.get.return_value = ""
        
        exc = RuntimeError("Runtime error occurred")
        
        response = await ErrorHandler.handle_general_exception(request, exc)
        
        assert response.status_code == 500
        # Verify it handled missing client gracefully
        call_args = mock_logger.error.call_args
        assert 'unknown' in str(call_args)
    
    @pytest.mark.asyncio
    @patch('src.core.utils.error_handling.get_request_context')
    @patch('src.core.utils.error_handling.logger')
    async def test_handle_general_exception_with_traceback(self, mock_logger, mock_get_context):
        """Test that traceback is included in error logging"""
        mock_get_context.return_value = {'request_id': 'tb-req-id'}
        
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/action"
        request.query_params = {}
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = "test"
        
        exc = Exception("Test exception")
        
        response = await ErrorHandler.handle_general_exception(request, exc)
        
        assert response.status_code == 500
        # Verify traceback was logged
        call_args = mock_logger.error.call_args
        assert 'traceback' in str(call_args) or call_args[1].get('exc_info') is True
    
    def test_error_handler_is_logger_mixin(self):
        """Test that ErrorHandler inherits from LoggerMixin"""
        from src.core.logging_config import LoggerMixin
        assert issubclass(ErrorHandler, LoggerMixin)
    
    def test_create_error_response_includes_timestamp(self):
        """Test that error response includes timestamp"""
        response = ErrorHandler.create_error_response(
            status_code=500,
            message="Test error"
        )
        
        content = response.body.decode()
        assert "timestamp" in content
        # ISO format ends with 'Z'
        assert 'Z' in content
