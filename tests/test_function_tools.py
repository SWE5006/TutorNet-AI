"""
Unit tests for function_tools module
Tests the tool wrapper functions for course and tutor search
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.function_tools import (
    wrap_search_tutor_service,
    wrap_search_course_service,
    wrap_get_course_by_userid_service,
    wrap_get_course_details_service,
    wrap_place_order_service
)


class TestSearchTutorService:
    """Test cases for search_tutor service wrapper"""
    
    def test_wrap_search_tutor_service_success(self, mock_wrapper_config):
        """Test successful tutor search"""
        with patch('src.core.function_tools.requests.get') as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = [
                {"id": "tutor-1", "name": "John Doe", "expertise": "Python"},
                {"id": "tutor-2", "name": "Jane Smith", "expertise": "JavaScript"}
            ]
            mock_get.return_value = mock_response
            
            # Get the tool function
            search_tutor = wrap_search_tutor_service(mock_wrapper_config)
            
            # Execute the tool
            result = search_tutor.invoke({"keyword": "python"})
            
            # Assertions
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["id"] == "tutor-1"
            assert result[0]["name"] == "John Doe"
            
            # Verify the API was called correctly
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "authorization" in call_args[1]["headers"]
            
    def test_wrap_search_tutor_service_error(self, mock_wrapper_config):
        """Test tutor search with network error"""
        with patch('src.core.function_tools.requests.get') as mock_get:
            # Mock exception
            mock_get.side_effect = Exception("Network error")
            
            # Get the tool function
            search_tutor = wrap_search_tutor_service(mock_wrapper_config)
            
            # Execute the tool
            result = search_tutor.invoke({"keyword": "python"})
            
            # Assertions
            assert isinstance(result, str)
            assert "Error:" in result
            assert "Network error" in result


class TestSearchCourseService:
    """Test cases for search_course service wrapper"""
    
    def test_wrap_search_course_service_success(self, mock_wrapper_config, mock_tool_response):
        """Test successful course search"""
        with patch('src.core.function_tools.requests.get') as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = mock_tool_response
            mock_get.return_value = mock_response
            
            # Get the tool function
            search_course = wrap_search_course_service(mock_wrapper_config)
            
            # Execute the tool
            result = search_course.invoke({"keyword": "python"})
            
            # Assertions
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["title"] == "Python Basics"
            assert result[1]["rating"] == 4.8
            
            # Verify the API was called
            mock_get.assert_called_once()
            
    def test_wrap_search_course_service_empty_result(self, mock_wrapper_config):
        """Test course search with empty results"""
        with patch('src.core.function_tools.requests.get') as mock_get:
            # Mock empty response
            mock_response = Mock()
            mock_response.json.return_value = []
            mock_get.return_value = mock_response
            
            # Get the tool function
            search_course = wrap_search_course_service(mock_wrapper_config)
            
            # Execute the tool
            result = search_course.invoke({"keyword": "nonexistent"})
            
            # Assertions
            assert isinstance(result, list)
            assert len(result) == 0
            
    def test_wrap_search_course_service_error(self, mock_wrapper_config):
        """Test course search with API error"""
        with patch('src.core.function_tools.requests.get') as mock_get:
            # Mock exception
            mock_get.side_effect = Exception("API timeout")
            
            # Get the tool function
            search_course = wrap_search_course_service(mock_wrapper_config)
            
            # Execute the tool
            result = search_course.invoke({"keyword": "python"})
            
            # Assertions
            assert isinstance(result, str)
            assert "Error:" in result
            assert "API timeout" in result


class TestGetCourseByUserIdService:
    """Test cases for wrap_get_course_by_userid_service"""
    
    def test_wrap_get_course_by_userid_success(self, mock_wrapper_config):
        """Test successful get course by user ID"""
        with patch('src.core.function_tools.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "success": True, 
                "courses": [
                    {"id": "course-1", "title": "My Course"}
                ]
            }
            mock_get.return_value = mock_response
            
            get_course_by_userid = wrap_get_course_by_userid_service(mock_wrapper_config)
            result = get_course_by_userid.invoke({"user_id": "test-user-123"})
            
            assert isinstance(result, dict)
            assert "success" in result
            assert "courses" in result
            assert len(result["courses"]) == 1
            
            # Verify API call
            mock_get.assert_called_once()
            
    def test_wrap_get_course_by_userid_error(self, mock_wrapper_config):
        """Test get course by user ID with error"""
        with patch('src.core.function_tools.requests.get') as mock_get:
            mock_get.side_effect = Exception("User not found")
            
            get_course_by_userid = wrap_get_course_by_userid_service(mock_wrapper_config)
            result = get_course_by_userid.invoke({"user_id": "invalid-user"})
            
            assert isinstance(result, str)
            assert "Error:" in result
            assert "User not found" in result


class TestGetCourseDetailsService:
    """Test cases for get_course_details service wrapper"""
    
    def test_wrap_get_course_details_success(self, mock_wrapper_config):
        """Test successful retrieval of course details"""
        with patch('src.core.function_tools.requests.get') as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = {
                "course_id": "course-123",
                "title": "Advanced Python",
                "description": "Learn advanced Python concepts",
                "tutor": "John Doe",
                "variants": [
                    {"id": "variant-1", "price": 99.99, "availability": True}
                ]
            }
            mock_get.return_value = mock_response
            
            # Get the tool function
            get_course_details = wrap_get_course_details_service(mock_wrapper_config)
            
            # Execute the tool
            result = get_course_details.invoke({"course_id": "course-123"})
            
            # Assertions
            assert isinstance(result, dict)
            assert result["course_id"] == "course-123"
            assert result["title"] == "Advanced Python"
            assert len(result["variants"]) == 1
            
            # Verify API call
            mock_get.assert_called_once()
            
    def test_wrap_get_course_details_not_found(self, mock_wrapper_config):
        """Test retrieval of non-existent course"""
        with patch('src.core.function_tools.requests.get') as mock_get:
            # Mock exception
            mock_get.side_effect = Exception("Course not found")
            
            # Get the tool function
            get_course_details = wrap_get_course_details_service(mock_wrapper_config)
            
            # Execute the tool
            result = get_course_details.invoke({"course_id": "invalid-id"})
            
            # Assertions
            assert isinstance(result, str)
            assert "Error:" in result
            assert "Course not found" in result


class TestPlaceOrderService:
    """Test cases for place_order service wrapper"""
    
    def test_wrap_place_order_success(self, mock_wrapper_config):
        """Test successful order placement"""
        with patch('src.core.function_tools.requests.post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = {
                "order_id": "order-123",
                "status": "success",
                "message": "Order placed successfully"
            }
            mock_post.return_value = mock_response
            
            # Get the tool function
            place_order = wrap_place_order_service(mock_wrapper_config)
            
            # Execute the tool
            result = place_order.invoke({"variation_id": "variant-123"})
            
            # Assertions
            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert "order_id" in result
            
            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "authorization" in call_args[1]["headers"]
            
    def test_wrap_place_order_failure(self, mock_wrapper_config):
        """Test order placement failure"""
        with patch('src.core.function_tools.requests.post') as mock_post:
            # Mock exception
            mock_post.side_effect = Exception("Payment failed")
            
            # Get the tool function
            place_order = wrap_place_order_service(mock_wrapper_config)
            
            # Execute the tool
            result = place_order.invoke({"variation_id": "variant-123"})
            
            # Assertions
            assert isinstance(result, str)
            assert "Error:" in result
            assert "Payment failed" in result
