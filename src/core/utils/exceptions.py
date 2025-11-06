"""
Enhanced error handling and custom exceptions for the application.
"""
from typing import Any, Optional, Dict


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
