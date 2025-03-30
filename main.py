"""
This module initializes the FastAPI application and registers the route modules for the TPI API.

It integrates endpoints for:
- Company assessments
- Management Quality (MQ) assessments
- Carbon Performance (CP) assessments

It also defines a basic root endpoint for a welcome message.
"""

from fastapi import FastAPI
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

# -------------------------------------------------------------------------
# Root Registration
# -------------------------------------------------------------------------
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
