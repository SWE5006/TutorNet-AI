"""
Pytest configuration and fixtures for TutorNet-AI tests
"""
import pytest
import os
from unittest.mock import Mock, MagicMock
from typing import Dict, Any


@pytest.fixture
def mock_settings():
    """Fixture for mocked settings"""
    settings = Mock()
    settings.service_api_url = "http://test-api.com"
    settings.openai_api_key = "test-key"
    settings.llm_model_name = "gpt-4"
    settings.llm_visual_model_name = "gpt-4-vision"
    settings.qwen_openai_enabled = False
    settings.qwen_openai_url = "http://test-qwen.com"
    settings.langfuse_enable = False
    settings.api_key = "test-api-key"
    settings.cors_origins = "http://localhost:3000"
    return settings


@pytest.fixture
def mock_wrapper_config():
    """Fixture for wrapper config with authorization"""
    return {"authorization": "Bearer test-token"}


@pytest.fixture
def sample_conversation_request():
    """Fixture for sample conversation request data"""
    return {
        "message": "Tell me about Python courses",
        "session_id": "test-session-123",
        "workflow": "course",
        "temperature": 0.7,
        "tool_names": ["search_course"]
    }


@pytest.fixture
def mock_llm_response():
    """Fixture for mocked LLM response"""
    response = Mock()
    response.content = "Here are some Python courses..."
    return response


@pytest.fixture
def mock_tool_response():
    """Fixture for mocked tool response"""
    return [
        {
            "id": "course-1",
            "title": "Python Basics",
            "description": "Learn Python from scratch",
            "rating": 4.5,
            "price": 29.99
        },
        {
            "id": "course-2",
            "title": "Advanced Python",
            "description": "Master advanced Python concepts",
            "rating": 4.8,
            "price": 49.99
        }
    ]


@pytest.fixture
def mock_session_memory():
    """Fixture for mocked session memory"""
    from langchain.memory import ConversationBufferMemory
    memory = ConversationBufferMemory(return_messages=True)
    return memory


# Set test environment variables
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["SERVICE_API_URL"] = "http://test-api.com"
    os.environ["API_KEY"] = "test-api-key"
    os.environ["LLM_MODEL_NAME"] = "gpt-4"
    os.environ["MCP_URL"] = "http://test-mcp.com"
    yield
    # Cleanup if needed
