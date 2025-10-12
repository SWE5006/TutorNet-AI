"""
Enhanced error handling and custom exceptions for the application.
"""
from typing import Any, Optional, Dict
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class BaseApplicationError(Exception):
    """Base exception for all application errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class WorkflowNotFoundError(BaseApplicationError):
    """Raised when a workflow is not found."""
    
    def __init__(self, workflow_id: str):
        super().__init__(
            message=f"Workflow with ID '{workflow_id}' not found",
            error_code="WORKFLOW_NOT_FOUND",
            details={"workflow_id": workflow_id}
        )


class AgentNotFoundError(BaseApplicationError):
    """Raised when an agent is not found."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent with ID '{agent_id}' not found",
            error_code="AGENT_NOT_FOUND",
            details={"agent_id": agent_id}
        )


class ConfigurationError(BaseApplicationError):
    """Raised when there's a configuration issue."""
    
    def __init__(self, message: str, config_type: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_type": config_type}
        )


class GraphBuildError(BaseApplicationError):
    """Raised when graph building fails."""
    
    def __init__(self, workflow_id: str, reason: str):
        super().__init__(
            message=f"Failed to build graph for workflow '{workflow_id}': {reason}",
            error_code="GRAPH_BUILD_ERROR",
            details={"workflow_id": workflow_id, "reason": reason}
        )


class ValidationError(BaseApplicationError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field}
        )


def handle_application_error(error: BaseApplicationError) -> HTTPException:
    """Convert application errors to HTTP exceptions."""
    
    status_map = {
        "WORKFLOW_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "AGENT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFIGURATION_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "GRAPH_BUILD_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    
    http_status = status_map.get(error.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=http_status,
        detail={
            "message": error.message,
            "error_code": error.error_code,
            "details": error.details
        }
    )


async def safe_execute(
    operation: callable,
    operation_name: str,
    *args,
    **kwargs
) -> Any:
    """Safely execute an operation with proper error handling."""
    
    try:
        logger.debug(f"Executing operation: {operation_name}")
        result = await operation(*args, **kwargs)
        logger.debug(f"Operation {operation_name} completed successfully")
        return result
        
    except BaseApplicationError:
        logger.warning(f"Application error in {operation_name}")
        raise
        
    except Exception as e:
        logger.exception(f"Unexpected error in {operation_name}: {e}")
        raise BaseApplicationError(
            message=f"Unexpected error in {operation_name}",
            error_code="INTERNAL_ERROR",
            details={"original_error": str(e)}
        )
