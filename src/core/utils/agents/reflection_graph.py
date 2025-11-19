"""
Reflection agent graph for response quality validation and improvement.
"""

from typing import Optional, Tuple
from typing_extensions import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from src.core.utils.models import ConversationRequest
from src.core.utils.langfuse_config import get_langfuse_handler_with_trace
from src.core.utils.system_prompts import get_system_prompt_for_workflow
import logging

logger = logging.getLogger(__name__)


class ReflectionState(TypedDict):
    """State for the reflection agent graph."""
    user_message: str
    original_response: str
    tool_outputs: Optional[str]
    current_response: str
    validation_result: str
    is_approved: bool
    retry_count: int
    max_retries: int
    final_response: str
    workflow: str


def extract_regeneration_instructions(validation_result: str) -> str:
    """
    Extract regeneration instructions from validation result.
    
    Args:
        validation_result: The validation result from reflection agent
        
    Returns:
        Extracted instructions or full result as fallback
    """
    try:
        # Look for REGENERATION_INSTRUCTIONS section
        if "REGENERATION_INSTRUCTIONS:" in validation_result:
            parts = validation_result.split("REGENERATION_INSTRUCTIONS:")
            if len(parts) > 1:
                instructions = parts[1].split("REQUIRED_CORRECTIONS:")[0].strip()
                return instructions
        
        # Fallback: return the whole validation result
        return validation_result
    except Exception as e:
        logger.error(f"Error extracting regeneration instructions: {e}")
        return validation_result


def create_reflection_graph(
    llm_instance,
    session_id: Optional[str] = None,
    workflow: str = "reflection"
):
    """
    Create a LangGraph for the reflection agent with proper logging.
    
    The graph includes:
    - validation_node: Validates response quality and checks for hallucinations
    - regeneration_node: Regenerates response based on feedback if rejected
    - decision_node: Decides whether to approve, regenerate, or fail
    
    Args:
        llm_instance: The LLM instance for reflection
        session_id: Session ID for tracing
        workflow: Workflow type for tracing
        
    Returns:
        Compiled reflection graph
    """
    
    # Get reflection system prompt
    reflection_prompt = get_system_prompt_for_workflow("reflection")
    
    # Add Langfuse tracing if available
    trace_handler = get_langfuse_handler_with_trace(
        session_id or "unknown",
        workflow,
        "reflection_validation"
    )
    if trace_handler:
        llm_instance.callbacks = [trace_handler]
    
    def validation_node(state: ReflectionState) -> ReflectionState:
        """Node that validates the response using reflection agent."""
        logger.info(
            f"[Reflection Graph] Validation node - Attempt "
            f"{state['retry_count'] + 1}/{state['max_retries'] + 1}"
        )
        
        current_response = state['current_response']
        
        # Check if the response is an error message - if so, auto-approve it
        error_indicators = [
            "error", "failed", "exception", "unable to",
            "could not", "cannot", "experiencing issues",
            "technical difficulties", "try again", "unavailable"
        ]
        
        is_error_response = any(
            indicator in current_response.lower()
            for indicator in error_indicators
        )
        
        if is_error_response:
            logger.info(
                "[Reflection Graph] Detected error response - auto-approving without validation"
            )
            return {
                **state,
                "validation_result": (
                    "VALIDATION_RESULT: APPROVED\n\n"
                    "ASSESSMENT: Error response detected and allowed to pass. "
                    "Error messages are exempt from quality validation as they "
                    "communicate system issues to users."
                ),
                "is_approved": True
            }
        
        validation_message = f"""
Please validate the following response for quality and hallucination detection:

ORIGINAL USER QUERY: 
{state['user_message']}

TOOL OUTPUTS/CONTEXT PROVIDED:
{state['tool_outputs'] if state['tool_outputs'] else "No tool outputs available"}

AGENT RESPONSE TO VALIDATE:
{current_response}

{"[REGENERATION ATTEMPT " + str(state['retry_count']) + "/" + str(state['max_retries']) + "]" if state['retry_count'] > 0 else ""}

Provide your validation assessment following the specified format.
"""
        
        messages = [
            SystemMessage(content=reflection_prompt),
            HumanMessage(content=validation_message)
        ]
        
        try:
            # Invoke reflection agent
            reflection_response = llm_instance.invoke(messages)
            validation_result = reflection_response.content
            
            # Check if approved
            is_approved = "VALIDATION_RESULT: APPROVED" in validation_result
            
            logger.info(
                f"[Reflection Graph] Validation result: "
                f"{'APPROVED' if is_approved else 'REJECTED'}"
            )
            
            return {
                **state,
                "validation_result": validation_result,
                "is_approved": is_approved
            }
        except Exception as e:
            logger.error(f"[Reflection Graph] Validation error: {e}")
            return {
                **state,
                "validation_result": f"Validation error: {str(e)}",
                "is_approved": False
            }
    
    def regeneration_node(state: ReflectionState) -> ReflectionState:
        """Node that regenerates response based on feedback."""
        logger.info(
            f"[Reflection Graph] Regeneration node - Attempt {state['retry_count'] + 1}"
        )
        
        # Extract regeneration instructions
        regeneration_instructions = extract_regeneration_instructions(
            state['validation_result']
        )
        
        # Create regeneration prompt
        original_workflow = state.get('workflow', 'general')
        system_prompt = get_system_prompt_for_workflow(original_workflow)
        
        regeneration_message = f"""
Your previous response was reviewed and needs improvement.

ORIGINAL USER QUERY:
{state['user_message']}

TOOL OUTPUTS/CONTEXT:
{state['tool_outputs'] if state['tool_outputs'] else "No tool outputs available"}

PREVIOUS RESPONSE (REJECTED):
{state['current_response']}

FEEDBACK FROM REFLECTION AGENT:
{regeneration_instructions}

Please regenerate the response addressing all the feedback points. Ensure:
1. The response is well-structured and coherent
2. All information is grounded in the provided context/tool outputs
3. No hallucinated information is included
4. All feedback points are addressed
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=regeneration_message)
        ]
        
        try:
            regenerated = llm_instance.invoke(messages)
            new_response = regenerated.content
            
            logger.info("[Reflection Graph] Response regenerated successfully")
            
            return {
                **state,
                "current_response": new_response,
                "retry_count": state['retry_count'] + 1
            }
        except Exception as e:
            logger.error(f"[Reflection Graph] Regeneration error: {e}")
            # Keep the current response on error
            return {
                **state,
                "retry_count": state['retry_count'] + 1
            }
    
    def decision_node(state: ReflectionState) -> str:
        """Decide next action based on validation result."""
        if state['is_approved']:
            logger.info("[Reflection Graph] Decision: APPROVED - Moving to END")
            return "approved"
        elif state['retry_count'] >= state['max_retries']:
            logger.warning("[Reflection Graph] Decision: MAX_RETRIES - Moving to END")
            return "max_retries"
        else:
            logger.info("[Reflection Graph] Decision: REGENERATE")
            return "regenerate"
    
    # Build the graph
    workflow_graph = StateGraph(ReflectionState)
    
    # Add nodes
    workflow_graph.add_node("validate", validation_node)
    workflow_graph.add_node("regenerate", regeneration_node)
    
    # Set entry point
    workflow_graph.set_entry_point("validate")
    
    # Add conditional edges from validate
    workflow_graph.add_conditional_edges(
        "validate",
        decision_node,
        {
            "approved": END,
            "max_retries": END,
            "regenerate": "regenerate"
        }
    )
    
    # After regeneration, go back to validation
    workflow_graph.add_edge("regenerate", "validate")
    
    # Compile the graph
    return workflow_graph.compile()


async def reflect_on_response_with_agent(
    content: str,
    request: ConversationRequest,
    llm_instance,
    tool_outputs: Optional[str] = None,
    max_retries: int = 2
) -> Tuple[str, str]:
    """
    Validate and improve response using reflection agent graph.
    This version uses LangGraph for proper logging and traceability.
    
    Args:
        content: The AI response to validate
        request: The conversation request with context
        llm_instance: LLM instance for reflection
        tool_outputs: Optional tool outputs/context used to generate the response
        max_retries: Maximum number of regeneration attempts
        
    Returns:
        Tuple of (final_response: str, validation_feedback: str)
    """
    try:
        logger.info(
            f"[Reflection] Starting reflection workflow for session {request.session_id}"
        )
        
        # Create reflection graph
        reflection_graph = create_reflection_graph(
            llm_instance=llm_instance,
            session_id=request.session_id,
            workflow="reflection"
        )
        
        # Initialize state
        initial_state: ReflectionState = {
            "user_message": request.message,
            "original_response": content,
            "tool_outputs": tool_outputs,
            "current_response": content,
            "validation_result": "",
            "is_approved": False,
            "retry_count": 0,
            "max_retries": max_retries,
            "final_response": content,
            "workflow": request.workflow or "general"
        }
        
        # Execute the graph
        logger.info("[Reflection] Executing reflection graph...")
        final_state = await reflection_graph.ainvoke(initial_state)
        
        logger.info(
            f"[Reflection] Completed with approval: {final_state['is_approved']}"
        )
        
        # Use current_response as the final response
        final_response = final_state['current_response']
        validation_feedback = final_state['validation_result']
        
        return final_response, validation_feedback
        
    except Exception as e:
        logger.error(f"[Reflection] Error in reflection workflow: {e}")
        return content, f"Reflection error: {str(e)}"
