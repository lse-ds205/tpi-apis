"""
This module initializes the FastAPI application and registers the route modules for the TPI API.

It integrates endpoints for:
- Company assessments
- Management Quality (MQ) assessments
- Carbon Performance (CP) assessments

It also defines a basic root endpoint for a welcome message.
"""

import os
import time
import pandas as pd 
from pathlib import Path
from log_config import get_logger
from fastapi import FastAPI, APIRouter, Request, HTTPException 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from routes.ascor_routes import router as ascor_router
from routes.company_routes import router as company_router
from routes.cp_routes import cp_router
from routes.mq_routes import mq_router
from routes.bank_routes import router as bank_router
from authentication.auth_router import router as auth_router
from authentication.post_router import router as post_router

from dotenv import load_dotenv
load_dotenv()

logger = get_logger(__name__) # Get logger for main module

# -------------------------------------------------------------------------
# App Initialization

# Using default docs_url and redoc_url (Swagger UI at /docs, ReDoc at /redoc)
app = FastAPI(
    title="Transition Pathway Initiative API",
    version="1.0",
    description="Provides company, MQ, and CP assessments via REST endpoints.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.middleware("http")
async def allow_iframe(request: Request, call_next):
    response = await call_next(request)
    if "x-frame-options" in response.headers:
        del response.headers["x-frame-options"]
    return response

raw = os.getenv("CORS_ORIGINS", "")
origins = [o for o in raw.split(",") if o] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,    # now ["*"] if CORS_ORIGINS is empty
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --- Logging Middleware ---
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"START Request: {request.method} {request.url.path}")

        response = None # Initialize response variable
        try:
            response = await call_next(request)
        except Exception as e:
            # Log unhandled exceptions originating from downstream
            process_time = time.time() - start_time
            logger.error(
                f"ERROR Request: {request.method} {request.url.path} - "
                f"Error: {e} - Time: {process_time:.4f}s"
            )
            # Reraise the exception to be handled by FastAPI's exception handlers
            raise e # Or return a generic error response
        finally:
            process_time = time.time() - start_time
            status_code = response.status_code if response else 500 # Get status code if response exists
            logger.info(
                f"END Request: {request.method} {request.url.path} - "
                f"Status: {status_code} - Time: {process_time:.4f}s"
            )
        return response

app.add_middleware(LoggingMiddleware)


# --- Root Registration ---
app.include_router(ascor_router, prefix="/v1/ascor")
app.include_router(company_router, prefix="/v1/company")
app.include_router(cp_router, prefix="/v1/cp")
app.include_router(mq_router, prefix="/v1/mq")
app.include_router(bank_router, prefix="/v1/bank")
app.include_router(auth_router, prefix="/v1")
app.include_router(post_router, prefix="/v1")

# Add sector data routes for demonstrating logging with real data files
sector_router = APIRouter(prefix="/sectors", tags=["Sector Endpoints"])

@sector_router.get("/company-assessments")
@limiter.limit("100/minute")
async def get_sector_company_assessments(
    request: Request
):
    try:
        sector_file = "data/TPI_sector_data_All_sectors_08032025/Company_Latest_Assessments.csv"
        logger.info(f"Loading sector company assessments from {sector_file}")
        
        df = pd.read_csv(sector_file)
        
        # Get the first 5 records for a sample
        sample_data = df.head(5).to_json(orient="records")
        logger.info(f"Successfully loaded {len(df)} company assessments, returning sample of 5")
        
        return {
            "total_records": len(df),
            "sample_data": sample_data
        }
    except Exception as e:
        logger.exception(f"Error loading sector data: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading sector data: {str(e)}")

app.include_router(sector_router, prefix="/v1")

# --- Root Endpoint ---
@app.get("/")
@limiter.limit("100/minute")
async def home(request: Request):
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to the TPI API!"}

# Global exception handler for any *unexpected* errors in your business logic
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Let FastAPI/Starlette handle its own HTTPExceptions & validation errors
    if isinstance(exc, (StarletteHTTPException, RequestValidationError)):
        raise exc

    # Otherwise log and return a 500
    logger.error(f"Unhandled Exception for {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )