# app/api/middleware/cors.py
"""
CORS middleware configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings


def setup_cors(app: FastAPI, settings: Settings):
    """Setup CORS middleware with proper configuration"""

    # Parse CORS origins from settings
    cors_origins = settings.cors_origins
    if isinstance(cors_origins, str):
        # Handle string representation of list
        import ast

        try:
            cors_origins = ast.literal_eval(cors_origins)
        except (ValueError, SyntaxError):
            # Fallback to single origin
            cors_origins = [cors_origins]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )
