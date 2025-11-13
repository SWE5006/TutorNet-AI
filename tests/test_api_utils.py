"""
Tests for API utility functions
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from src.core.utils.api_utils import (
    validate_and_get_tools,
    get_error_fallback_message,
    extract_regeneration_instructions
)


class TestValidateAndGetTools:
    """Test cases for validate_and_get_tools function"""
    
    def test_validate_tools_success(self):
        """Test successful tool validation"""
        with patch('src.core.utils.api_utils.wrap_search_course_service') as mock_course:
            with patch('src.core.utils.api_utils.wrap_search_tutor_service') as mock_tutor:
                mock_course.return_value = Mock(name="search_course")
                mock_tutor.return_value = Mock(name="search_tutor")
                
                tools = validate_and_get_tools(["search_course", "search_tutor"], "Bearer token")
                
                assert len(tools) == 2
                mock_course.assert_called_once()
                mock_tutor.assert_called_once()
    
    def test_validate_tools_missing_tool(self):
        """Test validation with missing tool"""
        with pytest.raises(HTTPException) as exc_info:
            validate_and_get_tools(["nonexistent_tool"], "Bearer token")
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()
    
    def test_validate_tools_multiple_missing(self):
        """Test validation with multiple missing tools"""
        with pytest.raises(HTTPException) as exc_info:
            validate_and_get_tools(["missing_1", "missing_2"], "Bearer token")
        
        assert exc_info.value.status_code == 404
        assert "missing_1" in str(exc_info.value.detail)
        assert "missing_2" in str(exc_info.value.detail)
    
    def test_validate_tools_with_authorization(self):
        """Test tool validation with authorization header"""
        with patch('src.core.utils.api_utils.wrap_search_course_service') as mock_course:
            mock_course.return_value = Mock(name="search_course")
            
            tools = validate_and_get_tools(["search_course"], "Bearer test-token")
            
            assert len(tools) == 1
            # Verify authorization was passed in config
            call_args = mock_course.call_args[0][0]
            assert call_args["authorization"] == "Bearer test-token"
    
    def test_validate_tools_without_authorization(self):
        """Test tool validation without authorization"""
        with patch('src.core.utils.api_utils.wrap_search_course_service') as mock_course:
            mock_course.return_value = Mock(name="search_course")
            
            tools = validate_and_get_tools(["search_course"], None)
            
            assert len(tools) == 1
            # Verify empty authorization was passed
            call_args = mock_course.call_args[0][0]
            assert call_args["authorization"] == ""
    
    def test_validate_tools_exception_handling(self):
        """Test exception handling during tool validation"""
        with patch('src.core.utils.api_utils.wrap_search_course_service') as mock_course:
            mock_course.side_effect = Exception("Tool loading error")
            
            with pytest.raises(HTTPException) as exc_info:
                validate_and_get_tools(["search_course"], None)
            
            assert exc_info.value.status_code == 500
            assert "Failed to load function tools" in str(exc_info.value.detail)
    
    def test_validate_all_available_tools(self):
        """Test validation with all available tools"""
        with patch('src.core.utils.api_utils.wrap_search_course_service') as mock_course:
            with patch('src.core.utils.api_utils.wrap_search_tutor_service') as mock_tutor:
                with patch('src.core.utils.api_utils.wrap_get_course_by_userid_service') as mock_userid:
                    with patch('src.core.utils.api_utils.wrap_get_course_details_service') as mock_details:
                        with patch('src.core.utils.api_utils.wrap_place_order_service') as mock_order:
                            # Setup all mocks
                            mock_course.return_value = Mock(name="search_course")
                            mock_tutor.return_value = Mock(name="search_tutor")
                            mock_userid.return_value = Mock(name="get_course_by_userid")
                            mock_details.return_value = Mock(name="get_course_details")
                            mock_order.return_value = Mock(name="place_order")
                            
                            tools = validate_and_get_tools([
                                "search_course",
                                "search_tutor",
                                "get_course_by_userid",
                                "get_course_details",
                                "place_order"
                            ], None)
                            
                            assert len(tools) == 5


class TestErrorFallbackMessage:
    """Test cases for get_error_fallback_message function"""
    
    def test_connection_error_message(self):
        """Test connection error fallback message"""
        message = get_error_fallback_message("Connection refused error")
        assert "connection" in message.lower()
        assert "try again" in message.lower()
    
    def test_timeout_error_message(self):
        """Test timeout error fallback message"""
        message = get_error_fallback_message("Request timeout occurred")
        assert "timeout" in message.lower() or "longer than expected" in message.lower()
    
    def test_generic_error_message(self):
        """Test generic error fallback message"""
        message = get_error_fallback_message("Some unknown error")
        assert "technical difficulties" in message.lower()
        assert "try again" in message.lower()
    
    def test_case_insensitive_matching(self):
        """Test that error matching is case-insensitive"""
        message1 = get_error_fallback_message("CONNECTION ERROR")
        message2 = get_error_fallback_message("connection error")
        assert message1 == message2
    
    def test_timeout_uppercase(self):
        """Test timeout detection with uppercase"""
        message = get_error_fallback_message("TIMEOUT ERROR")
        assert "timeout" in message.lower() or "longer than expected" in message.lower()


class TestExtractRegenerationInstructions:
    """Test cases for extract_regeneration_instructions function"""
    
    def test_extract_with_instructions(self):
        """Test extracting regeneration instructions"""
        validation_result = """
        VALIDATION_RESULT: REJECT
        REGENERATION_INSTRUCTIONS: Please revise the response to be more concise.
        REQUIRED_CORRECTIONS: Remove unnecessary details.
        """
        
        instructions = extract_regeneration_instructions(validation_result)
        
        assert "Please revise" in instructions
        assert "REQUIRED_CORRECTIONS" not in instructions
    
    def test_extract_without_instructions(self):
        """Test extraction when no instructions section exists"""
        validation_result = "This is a simple validation result"
        
        instructions = extract_regeneration_instructions(validation_result)
        
        assert instructions == validation_result
    
    def test_extract_with_malformed_result(self):
        """Test extraction with malformed validation result"""
        validation_result = "REGENERATION_INSTRUCTIONS:"
        
        instructions = extract_regeneration_instructions(validation_result)
        
        # Should handle gracefully without crashing
        assert isinstance(instructions, str)
    
    def test_extract_with_multiple_sections(self):
        """Test extraction with complete validation structure"""
        validation_result = """
        VALIDATION_RESULT: REJECT
        REASON: Response is too vague
        REGENERATION_INSTRUCTIONS: Provide specific examples and details.
        Include concrete information.
        REQUIRED_CORRECTIONS: Add examples, add statistics
        """
        
        instructions = extract_regeneration_instructions(validation_result)
        
        assert "Provide specific examples" in instructions
        assert "Include concrete information" in instructions
        assert "REQUIRED_CORRECTIONS" not in instructions
    
    def test_extract_exception_handling(self):
        """Test that exceptions are handled gracefully"""
        # Passing None will cause an exception that should be handled
        validation_result = None
        
        instructions = extract_regeneration_instructions(validation_result)
        
        # When error occurs, should return None or the original input
        assert instructions is None or instructions == validation_result
    
    def test_extract_empty_string(self):
        """Test extraction with empty string"""
        instructions = extract_regeneration_instructions("")
        assert instructions == ""
    
    def test_extract_only_instructions_marker(self):
        """Test with only the instruction marker"""
        validation_result = "REGENERATION_INSTRUCTIONS: Make it better"
        
        instructions = extract_regeneration_instructions(validation_result)
        
        assert "Make it better" in instructions
