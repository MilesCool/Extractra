"""Main FastAPI application."""

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.v1.tasks import router as tasks_router
from api.v1.extraction import router as extraction_router
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Extractra backend service")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Extractra backend service")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Intelligent multi-agent system for web data extraction",
        lifespan=lifespan,
        debug=settings.DEBUG,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    # app.include_router(
    #     tasks_router,
    #     prefix=settings.API_V1_STR,
    #     tags=["tasks"]
    # )
        
    app.include_router(
        extraction_router,
        prefix=settings.API_V1_STR,
        tags=["extraction"]
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": "/health",
        }
    
    return app


# Create app instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    ) 