
from src.api import conversation
from fastapi import APIRouter

def setup_router() -> APIRouter:
    """Setup router"""
   # Include API routers
    api_router = APIRouter()
    
    
    # Include conversation router - handles /api/conversation/*
    api_router.include_router(conversation.router, tags=["conversation"])
    
    return api_router