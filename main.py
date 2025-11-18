"""
Main entry point for TutorNet Agentic AI.

This module serves as the entry point for the FastAPI application,
importing the app from the src package for use with uvicorn/gunicorn.
"""
from dotenv import load_dotenv
load_dotenv()

# Import the FastAPI app from the src package
from src.main import app as fastapi_app
from src.main import load_secret_into_env


# Expose the app for uvicorn/gunicorn
app = fastapi_app

