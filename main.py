"""
Main entry point for TutorNet Agentic AI.

This module serves as the entry point for the FastAPI application,
importing the app from the src package for use with uvicorn/gunicorn.
"""

# Import the FastAPI app from the src package
from src.main import app

# Expose the app for uvicorn/gunicorn
__all__ = ["app"]
