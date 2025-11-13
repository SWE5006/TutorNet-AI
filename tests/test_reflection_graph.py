"""
Tests for reflection graph and quality validation
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.core.utils.agents.reflection_graph import (
    extract_regeneration_instructions,
    create_reflection_graph,
    reflect_on_response_with_agent,
    ReflectionState
)
from src.core.utils.models import ConversationRequest


class TestExtractRegenerationInstructions:
    """Test cases for extract_regeneration_instructions function"""
    
    def test_extract_with_valid_instructions(self):
        """Test extracting valid regeneration instructions"""
        validation_result = """
        VALIDATION_RESULT: REJECT
        REGENERATION_INSTRUCTIONS: Please make the response more concise and focused.
        Remove unnecessary details.
        REQUIRED_CORRECTIONS: Reduce length by 50%
        """
        
        instructions = extract_regeneration_instructions(validation_result)
        
        assert "Please make the response more concise" in instructions
        assert "Remove unnecessary details" in instructions
        assert "REQUIRED_CORRECTIONS" not in instructions
    
    def test_extract_without_instructions_section(self):
        """Test extraction when no instructions section exists"""
        validation_result = "Simple validation result without sections"
        
        instructions = extract_regeneration_instructions(validation_result)
        
        assert instructions == validation_result
    
    def test_extract_with_empty_instructions(self):
        """Test extraction with empty instructions section"""
        validation_result = "REGENERATION_INSTRUCTIONS: \nREQUIRED_CORRECTIONS:"
        
        instructions = extract_regeneration_instructions(validation_result)
        
        assert isinstance(instructions, str)
    
    def test_extract_with_exception(self):
        """Test that exceptions are handled gracefully"""
        # Pass None to trigger exception
        validation_result = None
        
        instructions = extract_regeneration_instructions(validation_result)
        
        # Should return None (the input) after error handling
        assert instructions is None


class TestCreateReflectionGraph:
    """Test cases for create_reflection_graph function"""
    
    def test_create_graph_basic(self):
        """Test creating a basic reflection graph"""
        mock_llm = Mock()
        
        graph = create_reflection_graph(mock_llm, "test-session", "reflection")
        
        # Graph should be created successfully
        assert graph is not None
    
    def test_create_graph_with_session_id(self):
        """Test graph creation with session ID"""
        mock_llm = Mock()
        mock_llm.callbacks = []
        
        with patch('src.core.utils.agents.reflection_graph.get_langfuse_handler_with_trace') as mock_langfuse:
            mock_handler = Mock()
            mock_langfuse.return_value = mock_handler
            
            graph = create_reflection_graph(mock_llm, "session-123", "test-workflow")
            
            # Should have called langfuse with correct params
            mock_langfuse.assert_called_once_with("session-123", "test-workflow", "reflection_validation")
            assert mock_llm.callbacks == [mock_handler]
    
    def test_create_graph_without_session_id(self):
        """Test graph creation without session ID"""
        mock_llm = Mock()
        mock_llm.callbacks = []
        
        with patch('src.core.utils.agents.reflection_graph.get_langfuse_handler_with_trace') as mock_langfuse:
            mock_langfuse.return_value = None
            
            graph = create_reflection_graph(mock_llm)
            
            # Should use "unknown" as default session
            mock_langfuse.assert_called_once()
            call_args = mock_langfuse.call_args[0]
            assert call_args[0] == "unknown"


class TestValidationNode:
    """Test cases for validation node logic"""
    
    @pytest.mark.asyncio
    async def test_validation_node_approves_response(self):
        """Test validation node approving a good response"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "VALIDATION_RESULT: APPROVED\n\nASSESSMENT: Response is excellent."
        mock_llm.invoke.return_value = mock_response
        
        graph = create_reflection_graph(mock_llm, "test-session", "reflection")
        
        initial_state = {
            "user_message": "What is Python?",
            "original_response": "Python is a programming language.",
            "tool_outputs": None,
            "current_response": "Python is a programming language.",
            "validation_result": "",
            "is_approved": False,
            "retry_count": 0,
            "max_retries": 2,
            "final_response": "",
            "workflow": "general"
        }
        
        result = await graph.ainvoke(initial_state)
        
        assert result['is_approved'] is True
        assert "APPROVED" in result['validation_result']
    
    @pytest.mark.asyncio
    async def test_validation_node_rejects_response(self):
        """Test validation node rejecting a poor response"""
        mock_llm = Mock()
        
        # First call: reject
        reject_response = Mock()
        reject_response.content = "VALIDATION_RESULT: REJECT\n\nREGENERATION_INSTRUCTIONS: Be more specific."
        
        # Second call (after regeneration): approve
        approve_response = Mock()
        approve_response.content = "VALIDATION_RESULT: APPROVED\n\nASSESSMENT: Much better."
        
        # Third call for regeneration
        regen_response = Mock()
        regen_response.content = "Python is a high-level programming language."
        
        mock_llm.invoke.side_effect = [reject_response, regen_response, approve_response]
        
        graph = create_reflection_graph(mock_llm, "test-session", "reflection")
        
        initial_state = {
            "user_message": "What is Python?",
            "original_response": "Python is a language.",
            "tool_outputs": None,
            "current_response": "Python is a language.",
            "validation_result": "",
            "is_approved": False,
            "retry_count": 0,
            "max_retries": 2,
            "final_response": "",
            "workflow": "general"
        }
        
        result = await graph.ainvoke(initial_state)
        
        # Should eventually approve after regeneration
        assert result['retry_count'] == 1
        assert "Python is a high-level" in result['current_response']
    
    @pytest.mark.asyncio
    async def test_validation_node_detects_error_response(self):
        """Test validation node auto-approves error responses"""
        mock_llm = Mock()
        
        graph = create_reflection_graph(mock_llm, "test-session", "reflection")
        
        initial_state = {
            "user_message": "Search for courses",
            "original_response": "I'm experiencing technical difficulties. Please try again later.",
            "tool_outputs": None,
            "current_response": "I'm experiencing technical difficulties. Please try again later.",
            "validation_result": "",
            "is_approved": False,
            "retry_count": 0,
            "max_retries": 2,
            "final_response": "",
            "workflow": "general"
        }
        
        result = await graph.ainvoke(initial_state)
        
        # Should auto-approve error response without calling LLM
        assert result['is_approved'] is True
        assert "Error response detected" in result['validation_result']
        # LLM should not have been called
        mock_llm.invoke.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_validation_node_various_error_indicators(self):
        """Test different error message indicators"""
        error_messages = [
            "An error occurred",
            "Failed to process request",
            "Exception encountered",
            "Unable to complete task",
            "Could not find information",
            "Cannot access the service",
            "Service unavailable"
        ]
        
        for error_msg in error_messages:
            mock_llm = Mock()
            graph = create_reflection_graph(mock_llm, "test-session", "reflection")
            
            initial_state = {
                "user_message": "Test query",
                "original_response": error_msg,
                "tool_outputs": None,
                "current_response": error_msg,
                "validation_result": "",
                "is_approved": False,
                "retry_count": 0,
                "max_retries": 2,
                "final_response": "",
                "workflow": "general"
            }
            
            result = await graph.ainvoke(initial_state)
            
            assert result['is_approved'] is True, f"Failed to auto-approve: {error_msg}"
    
    @pytest.mark.asyncio
    async def test_validation_node_handles_exception(self):
        """Test validation node handles LLM exceptions"""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("LLM error")
        
        graph = create_reflection_graph(mock_llm, "test-session", "reflection")
        
        initial_state = {
            "user_message": "What is Python?",
            "original_response": "Python is a language.",
            "tool_outputs": None,
            "current_response": "Python is a language.",
            "validation_result": "",
            "is_approved": False,
            "retry_count": 0,
            "max_retries": 2,
            "final_response": "",
            "workflow": "general"
        }
        
        result = await graph.ainvoke(initial_state)
        
        # Should not crash, but won't be approved
        assert result['is_approved'] is False
        assert "error" in result['validation_result'].lower()


class TestRegenerationNode:
    """Test cases for regeneration node logic"""
    
    @pytest.mark.asyncio
    async def test_regeneration_node_creates_new_response(self):
        """Test regeneration node creates improved response"""
        mock_llm = Mock()
        
        # Validation rejects
        reject_response = Mock()
        reject_response.content = "VALIDATION_RESULT: REJECT\n\nREGENERATION_INSTRUCTIONS: Add more details."
        
        # Regeneration creates new response
        regen_response = Mock()
        regen_response.content = "Python is a high-level, interpreted programming language."
        
        # Second validation approves
        approve_response = Mock()
        approve_response.content = "VALIDATION_RESULT: APPROVED"
        
        mock_llm.invoke.side_effect = [reject_response, regen_response, approve_response]
        
        graph = create_reflection_graph(mock_llm, "test-session", "reflection")
        
        initial_state = {
            "user_message": "What is Python?",
            "original_response": "Python.",
            "tool_outputs": "Python is a programming language",
            "current_response": "Python.",
            "validation_result": "",
            "is_approved": False,
            "retry_count": 0,
            "max_retries": 2,
            "final_response": "",
            "workflow": "assistant"
        }
        
        result = await graph.ainvoke(initial_state)
        
        # Should have regenerated
        assert result['current_response'] == "Python is a high-level, interpreted programming language."
        assert result['retry_count'] == 1
    
    @pytest.mark.asyncio
    async def test_regeneration_node_handles_exception(self):
        """Test regeneration node handles exceptions gracefully"""
        mock_llm = Mock()
        
        # Validation rejects
        reject_response = Mock()
        reject_response.content = "VALIDATION_RESULT: REJECT\n\nREGENERATION_INSTRUCTIONS: Improve."
        
        # Regeneration fails
        mock_llm.invoke.side_effect = [
            reject_response,
            Exception("Regeneration error"),
            reject_response  # Will hit max retries
        ]
        
        graph = create_reflection_graph(mock_llm, "test-session", "reflection")
        
        initial_state = {
            "user_message": "What is Python?",
            "original_response": "Python.",
            "tool_outputs": None,
            "current_response": "Python.",
            "validation_result": "",
            "is_approved": False,
            "retry_count": 0,
            "max_retries": 1,
            "final_response": "",
            "workflow": "general"
        }
        
        result = await graph.ainvoke(initial_state)
        
        # Should increment retry count even on error
        assert result['retry_count'] >= 1


class TestReflectOnResponseWithAgent:
    """Test cases for reflect_on_response_with_agent function"""
    
    @pytest.mark.asyncio
    async def test_reflect_returns_improved_response(self):
        """Test reflection returns improved response"""
        mock_llm = Mock()
        
        # Reject then regenerate then approve
        reject_response = Mock()
        reject_response.content = "VALIDATION_RESULT: REJECT\n\nREGENERATION_INSTRUCTIONS: Be more specific."
        
        regen_response = Mock()
        regen_response.content = "Python is a high-level programming language used for web development."
        
        approve_response = Mock()
        approve_response.content = "VALIDATION_RESULT: APPROVED"
        
        mock_llm.invoke.side_effect = [reject_response, regen_response, approve_response]
        
        request = ConversationRequest(
            message="What is Python?",
            session_id="test-123",
            workflow="assistant"
        )
        
        final_response, feedback = await reflect_on_response_with_agent(
            content="Python is a language.",
            request=request,
            llm_instance=mock_llm,
            tool_outputs=None,
            max_retries=2
        )
        
        assert "Python is a high-level programming language" in final_response
        assert "APPROVED" in feedback
    
    @pytest.mark.asyncio
    async def test_reflect_with_tool_outputs(self):
        """Test reflection with tool outputs context"""
        mock_llm = Mock()
        
        approve_response = Mock()
        approve_response.content = "VALIDATION_RESULT: APPROVED\n\nASSESSMENT: Good use of tool outputs."
        mock_llm.invoke.return_value = approve_response
        
        request = ConversationRequest(
            message="Find Python courses",
            session_id="test-123",
            workflow="assistant"
        )
        
        tool_outputs = "TOOL: search_course\nOUTPUT: Found 5 Python courses"
        
        final_response, feedback = await reflect_on_response_with_agent(
            content="I found 5 Python courses for you.",
            request=request,
            llm_instance=mock_llm,
            tool_outputs=tool_outputs,
            max_retries=2
        )
        
        assert final_response == "I found 5 Python courses for you."
        assert "APPROVED" in feedback
    
    @pytest.mark.asyncio
    async def test_reflect_hits_max_retries(self):
        """Test reflection stops after max retries"""
        mock_llm = Mock()
        
        # Always reject
        reject_response = Mock()
        reject_response.content = "VALIDATION_RESULT: REJECT\n\nREGENERATION_INSTRUCTIONS: Try again."
        
        regen_response = Mock()
        regen_response.content = "Attempt 1"
        
        mock_llm.invoke.side_effect = [
            reject_response, regen_response,  # First attempt
            reject_response, regen_response,  # Second attempt
            reject_response  # Third validation (hits max)
        ]
        
        request = ConversationRequest(
            message="Test",
            session_id="test-123",
            workflow="general"
        )
        
        final_response, feedback = await reflect_on_response_with_agent(
            content="Original response",
            request=request,
            llm_instance=mock_llm,
            tool_outputs=None,
            max_retries=2
        )
        
        # Should have tried regeneration up to max_retries
        assert "Attempt 1" in final_response or "Original response" in final_response
    
    @pytest.mark.asyncio
    async def test_reflect_handles_exception(self):
        """Test reflection handles exceptions gracefully"""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("Reflection system error")
        
        request = ConversationRequest(
            message="Test",
            session_id="test-123",
            workflow="general"
        )
        
        original_content = "Original response"
        final_response, feedback = await reflect_on_response_with_agent(
            content=original_content,
            request=request,
            llm_instance=mock_llm,
            tool_outputs=None,
            max_retries=2
        )
        
        # Should return original content on error
        assert final_response == original_content
        assert "error" in feedback.lower()
    
    @pytest.mark.asyncio
    async def test_reflect_with_different_workflows(self):
        """Test reflection works with different workflow types"""
        workflows = ["assistant", "translator", "censorship", "content_optimizer"]
        
        for workflow in workflows:
            mock_llm = Mock()
            approve_response = Mock()
            approve_response.content = "VALIDATION_RESULT: APPROVED"
            mock_llm.invoke.return_value = approve_response
            
            request = ConversationRequest(
                message="Test message",
                session_id=f"test-{workflow}",
                workflow=workflow
            )
            
            final_response, feedback = await reflect_on_response_with_agent(
                content="Test response",
                request=request,
                llm_instance=mock_llm,
                tool_outputs=None,
                max_retries=1
            )
            
            assert final_response == "Test response"
            assert "APPROVED" in feedback
    
    @pytest.mark.asyncio
    async def test_reflect_preserves_original_on_approval(self):
        """Test that approved responses are not changed"""
        mock_llm = Mock()
        
        approve_response = Mock()
        approve_response.content = "VALIDATION_RESULT: APPROVED\n\nASSESSMENT: Perfect response."
        mock_llm.invoke.return_value = approve_response
        
        request = ConversationRequest(
            message="What is 2+2?",
            session_id="test-123",
            workflow="assistant"
        )
        
        original = "2+2 equals 4."
        final_response, feedback = await reflect_on_response_with_agent(
            content=original,
            request=request,
            llm_instance=mock_llm,
            tool_outputs=None,
            max_retries=2
        )
        
        # Original response should be preserved
        assert final_response == original
        assert "APPROVED" in feedback
    
    @pytest.mark.asyncio
    async def test_reflect_with_zero_max_retries(self):
        """Test reflection with no retries allowed"""
        mock_llm = Mock()
        
        reject_response = Mock()
        reject_response.content = "VALIDATION_RESULT: REJECT"
        mock_llm.invoke.return_value = reject_response
        
        request = ConversationRequest(
            message="Test",
            session_id="test-123",
            workflow="general"
        )
        
        original = "Original response"
        final_response, feedback = await reflect_on_response_with_agent(
            content=original,
            request=request,
            llm_instance=mock_llm,
            tool_outputs=None,
            max_retries=0
        )
        
        # Should stop immediately after first rejection
        assert final_response == original
        assert "REJECT" in feedback


class TestReflectionState:
    """Test cases for ReflectionState TypedDict"""
    
    def test_reflection_state_structure(self):
        """Test that ReflectionState has correct structure"""
        state: ReflectionState = {
            "user_message": "Test message",
            "original_response": "Original",
            "tool_outputs": "Tool output",
            "current_response": "Current",
            "validation_result": "Result",
            "is_approved": False,
            "retry_count": 0,
            "max_retries": 2,
            "final_response": "Final",
            "workflow": "general"
        }
        
        # Should be able to access all keys
        assert state['user_message'] == "Test message"
        assert state['retry_count'] == 0
        assert state['is_approved'] is False
