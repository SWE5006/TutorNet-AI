
from fastapi import APIRouter
from src.api import conversation

def setup_router() -> APIRouter:
    """Setup router for API endpoints"""
    api_router = APIRouter()
    
    # Include conversation router - handles /api/conversation/*
    api_router.include_router(conversation.router, tags=["conversation"])
    
    return api_router