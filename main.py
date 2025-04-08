"""
This module initializes the FastAPI application and registers the route modules for the TPI API.

It integrates endpoints for:
- Company assessments
- Management Quality (MQ) assessments
- Carbon Performance (CP) assessments

It also defines a basic root endpoint for a welcome message.
"""

from fastapi import FastAPI, HTTPException, Request, Response
from slowapi.errors import RateLimitExceeded
from middleware.rate_limiter import limiter, rate_limit_exceeded_handler

from routes.ascor_routes import router as ascor_router
from routes.company_routes import (
    router as company_router,
)
from routes.mq_routes import mq_router
from routes.cp_routes import cp_router

# -------------------------------------------------------------------------
# App Initialization
# -------------------------------------------------------------------------
app = FastAPI(
    title="Transition Pathway Initiative API",
    version="1.0",
    description="Provides company, MQ, and CP assessments via REST endpoints.",
)

# Add limiter to app state
app.state.limiter = limiter

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# -------------------------------------------------------------------------
# Root Registration
# -------------------------------------------------------------------------
app.include_router(ascor_router, prefix="/v1")
app.include_router(company_router, prefix="/v1")
app.include_router(mq_router, prefix="/v1")
app.include_router(cp_router, prefix="/v1")


# -------------------------------------------------------------------------
# Root Endpoint
# -------------------------------------------------------------------------
@app.get("/")
def home():
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to the TPI API!"}
