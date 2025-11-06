"""
Comprehensive tests for the exceptions module.
"""
import pytest
from src.core.utils.exceptions import BaseApplicationError


class TestBaseApplicationError:
    """Test BaseApplicationError class"""
    
    def test_base_error_with_message_only(self):
        """Test creating error with message only"""
        error = BaseApplicationError("Test error message")
        
        assert error.message == "Test error message"
        assert error.error_code is None
        assert error.details == {}
        assert str(error) == "Test error message"
    
    def test_base_error_with_error_code(self):
        """Test creating error with error code"""
        error = BaseApplicationError(
            message="Test error",
            error_code="TEST_ERROR"
        )
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {}
    
    def test_base_error_with_details(self):
        """Test creating error with details"""
        details = {"key1": "value1", "key2": 123}
        error = BaseApplicationError(
            message="Test error",
            details=details
        )
        
        assert error.message == "Test error"
        assert error.details == details
        assert error.details["key1"] == "value1"
        assert error.details["key2"] == 123
    
    def test_base_error_with_all_params(self):
        """Test creating error with all parameters"""
        details = {"user_id": "123", "action": "delete"}
        error = BaseApplicationError(
            message="Operation failed",
            error_code="OPERATION_FAILED",
            details=details
        )
        
        assert error.message == "Operation failed"
        assert error.error_code == "OPERATION_FAILED"
        assert error.details == details
        assert str(error) == "Operation failed"
    
    def test_base_error_with_none_details(self):
        """Test that None details defaults to empty dict"""
        error = BaseApplicationError(
            message="Test error",
            error_code="TEST",
            details=None
        )
        
        assert error.details == {}
        assert isinstance(error.details, dict)
    
    def test_base_error_can_be_raised(self):
        """Test that error can be raised and caught"""
        with pytest.raises(BaseApplicationError) as exc_info:
            raise BaseApplicationError("Test exception")
        
        assert exc_info.value.message == "Test exception"
        assert str(exc_info.value) == "Test exception"
    
    def test_base_error_inherits_from_exception(self):
        """Test that BaseApplicationError is an Exception"""
        error = BaseApplicationError("Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, BaseApplicationError)
    
    def test_base_error_with_empty_message(self):
        """Test creating error with empty message"""
        error = BaseApplicationError("")
        
        assert error.message == ""
        assert str(error) == ""
    
    def test_base_error_with_complex_details(self):
        """Test creating error with nested details"""
        details = {
            "user": {"id": 1, "name": "John"},
            "errors": ["error1", "error2"],
            "metadata": {"timestamp": "2025-11-05"}
        }
        error = BaseApplicationError(
            message="Complex error",
            error_code="COMPLEX",
            details=details
        )
        
        assert error.details["user"]["id"] == 1
        assert error.details["errors"] == ["error1", "error2"]
        assert error.details["metadata"]["timestamp"] == "2025-11-05"
    
    def test_base_error_details_are_mutable(self):
        """Test that details dict can be modified after creation"""
        error = BaseApplicationError("Test")
        
        error.details["new_key"] = "new_value"
        assert error.details["new_key"] == "new_value"
    
    def test_base_error_attributes_are_accessible(self):
        """Test that all attributes are accessible"""
        error = BaseApplicationError(
            message="Test message",
            error_code="TEST_CODE",
            details={"key": "value"}
        )
        
        # Test attribute access
        assert hasattr(error, 'message')
        assert hasattr(error, 'error_code')
        assert hasattr(error, 'details')
        
        # Test values
        assert error.message == "Test message"
        assert error.error_code == "TEST_CODE"
        assert error.details["key"] == "value"
    
    def test_base_error_with_special_characters(self):
        """Test error with special characters in message"""
        error = BaseApplicationError(
            message="Error: Invalid input 'test@123' with symbols !@#$%",
            error_code="INVALID_INPUT"
        )
        
        assert "test@123" in error.message
        assert "!@#$%" in error.message
    
    def test_base_error_with_unicode(self):
        """Test error with unicode characters"""
        error = BaseApplicationError(
            message="错误消息 - Error message with 日本語",
            error_code="UNICODE_ERROR"
        )
        
        assert "错误消息" in error.message
        assert "日本語" in error.message
    
    def test_base_error_equality(self):
        """Test error equality comparison"""
        error1 = BaseApplicationError("Test", "CODE", {"key": "value"})
        error2 = BaseApplicationError("Test", "CODE", {"key": "value"})
        
        # Errors are different objects even with same values
        assert error1 is not error2
        assert error1.message == error2.message
        assert error1.error_code == error2.error_code
    
    def test_base_error_can_be_caught_as_exception(self):
        """Test that BaseApplicationError can be caught as generic Exception"""
        try:
            raise BaseApplicationError("Test error", "TEST")
        except Exception as e:
            assert isinstance(e, BaseApplicationError)
            assert e.message == "Test error"
    
    def test_base_error_repr(self):
        """Test string representation includes message"""
        error = BaseApplicationError("Test error message")
        
        # The __str__ method should return the message
        assert str(error) == "Test error message"
    
    def test_multiple_errors_with_different_codes(self):
        """Test creating multiple errors with different error codes"""
        error1 = BaseApplicationError("Error 1", "CODE_1")
        error2 = BaseApplicationError("Error 2", "CODE_2")
        error3 = BaseApplicationError("Error 3", "CODE_3")
        
        assert error1.error_code == "CODE_1"
        assert error2.error_code == "CODE_2"
        assert error3.error_code == "CODE_3"
        
        assert error1.message != error2.message
        assert error2.message != error3.message
