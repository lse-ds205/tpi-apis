# tpi-apis/main.py
import time
from fastapi import FastAPI, Request, APIRouter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response # Import Response for type hint
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

# Import your routes...
from .routes.ascor_routes import router as ascor_router
from .log_config import get_logger
from .services import fetch_company_data, CompanyNotFoundError, CompanyDataError
from .schemas import Metric, MetricSource, Indicator, IndicatorSource, Area, Pillar, CountryDataResponse

logger = get_logger(__name__) # Get logger for main module

# App Initialization
app = FastAPI(
    title="Transition Pathway Initiative API",
    version="1.0",
    description="Provides company, MQ, and CP assessments via REST endpoints.",
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
app.include_router(ascor_router, prefix="/v1")

# Add company routes for testing the fetch_company_data function
company_router = APIRouter(prefix="/companies", tags=["Company Endpoints"])

@company_router.get("/{company_id}")
async def get_company(company_id: int):
    try:
        logger.info(f"Processing request for company ID: {company_id}")
        result = fetch_company_data(company_id)
        return result
    except CompanyNotFoundError as e:
        logger.error(f"Company not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except CompanyDataError as e:
        logger.error(f"Error processing company data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

app.include_router(company_router, prefix="/v1")

# Add sector data routes for demonstrating logging with real data files
sector_router = APIRouter(prefix="/sectors", tags=["Sector Endpoints"])

@sector_router.get("/company-assessments")
async def get_sector_company_assessments():
    try:
        sector_file = "/Users/rishisiddharth/Desktop/LSE_2024_2045/classes/DS205W/Summative1_logging/tpi_apis/data/TPI_sector_data_All_sectors_08032025/Company_Latest_Assessments.csv"
        logger.info(f"Loading sector company assessments from {sector_file}")
        
        # Use pandas to read the CSV file
        import pandas as pd
        df = pd.read_csv(sector_file)
        
        # Get the first 5 records for a sample
        sample_data = df.head(5).to_dict(orient="records")
        logger.info(f"Successfully loaded {len(df)} company assessments, returning sample of 5")
        
        return {
            "total_records": len(df),
            "sample_data": sample_data
        }
    except Exception as e:
        logger.exception(f"Error loading sector data: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading sector data: {str(e)}")

app.include_router(sector_router, prefix="/v1")
# ... other routers go here

# --- Root Endpoint ---
@app.get("/")
def home():
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to the TPI API!"}

# Global exception handler for more structured error logging
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the exception details here before returning the response
    logger.error(f"Unhandled Exception for {request.method} {request.url.path}: {exc}", exc_info=True) # exc_info=True adds traceback
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )
