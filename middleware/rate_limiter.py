"""
This module provides the rate limiter for the FastAPI. It also creates the limit exceeded error handler.
"""

from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"])

# Create error handler for rate limit exceeded
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Too many requests.",
            "retry_after": "Try again after 1 minute, when your requests will reset.",
        },
    )