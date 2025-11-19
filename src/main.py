from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from contextlib import asynccontextmanager

from src.core.utils.secure_secrets import load_secret_into_env
from src.core.utils.settings import get_settings, setup_logging
from src.core.utils.exceptions import BaseApplicationError
from src.core.utils.error_handling import ErrorHandler
from src.core.router import setup_router


print("[src.main] imported, creating app")

# Initialize settings and logging
settings = get_settings()
logger = setup_logging(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for application start and shutdown events.
    """
    logger.info("Application start: Initializing services.")

    logger.info("Application started.")
    yield
    
    logger.info("Application shutdown: Cleaning up resources.")
    
    # Stop the trace log consumer
    if hasattr(app.state, 'consumer_task') and app.state.consumer_task:
        app.state.consumer_task.cancel()
        await app.state.consumer_task

# Initialize FastAPI app
app = FastAPI(
    title="TutorNet Agentic AI",
    description="AI agent platform for TutorNet",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)



#Add health check
@app.get("/foundation/healthz")
def health_check():
    key = load_secret_into_env()
    return {"status": "Live. This is for cicd-demo video recording","key_tail": len(key) if key else 0}

# Add error handling middleware
@app.exception_handler(BaseApplicationError)
async def application_error_handler(request: Request, exc: BaseApplicationError):
    """Handle application-specific errors."""
    return await ErrorHandler.handle_http_exception(request, exc)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return await ErrorHandler.handle_http_exception(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    return await ErrorHandler.handle_general_exception(request, exc)

# Enhanced CORS configuration with security
if settings.cors_origins_list:
    # Validate CORS origins for security
    secure_origins = []
    for origin in settings.cors_origins_list:
        # Only allow HTTPS in production (except localhost for development)
        if origin.startswith('https://') or origin.startswith('http://localhost') or origin.startswith('http://127.0.0.1'):
            secure_origins.append(origin)
        else:
            logger.warning(f"Skipping insecure CORS origin: {origin}")
    
    if secure_origins:
        app.add_middleware( 
            CORSMiddleware,
            allow_origins=secure_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods only
            allow_headers=["*"],  # Specific headers only
            # expose_headers=["X-Request-ID", "X-Process-Time"],  # Headers exposed to client
            max_age=3600,  # Cache preflight requests for 1 hour
        )
        logger.info(f"CORS middleware added with secure origins: {secure_origins}")
    else:
        logger.error("No secure CORS origins configured. CORS middleware not added.")
else:
    logger.warning(
        "CORS_ORIGINS not set in environment. CORS middleware will not be added."
    )


# Initialize Langfuse for tracing and observability
langfuse = None
langfuse_handler = None

if settings.langfuse_enable:
    langfuse = Langfuse()
    langfuse_handler = CallbackHandler()


# Include API routers
api_router = setup_router()

app.include_router(api_router, prefix="/foundation")
