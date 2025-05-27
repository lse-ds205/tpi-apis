"""
This module provides FastAPI endpoints for retrieving Carbon Performance (CP) assessments.
It uses the database manager and SQL templates for efficient data retrieval.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import List, Optional, Dict, Union
from middleware.rate_limiter import limiter
from schemas import (
    CPAssessmentDetail,
    CPComparisonResponse,
    PerformanceComparisonInsufficientDataResponse,
)
from utils.filters import CompanyFilters, build_company_filter_conditions
from log_config import get_logger
from utils.database_manager import DatabaseManagerFactory

logger = get_logger(__name__)

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
cp_router = APIRouter(tags=["CP Endpoints"])

# SQL file paths
SQL_DIR = Path(__file__).parent.parent / "sql" / "tpi" / "queries"

# ------------------------------------------------------------------------------
# Endpoint: GET /latest - Latest CP Assessments with Pagination
# ------------------------------------------------------------------------------
@cp_router.get("/latest", response_model=List[CPAssessmentDetail])
@limiter.limit("2/minute")
async def get_latest_cp_assessments(
    request: Request, 
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(10, ge=1, le=100, description="Results per page (max 100)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """Retrieve the latest CP assessment levels for all companies with pagination."""
    try:
        logger.info(f"Getting latest CP assessments - page {page}, size {page_size}")
        db_manager = DatabaseManagerFactory.get_manager("tpi_api")
        
        # Build filter conditions
        where_clause, params = build_company_filter_conditions(filter)
        
        # Add pagination parameters
        params.update({
            "limit": page_size,
            "offset": (page - 1) * page_size
        })
        
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_latest_cp_assessments.sql",
            params=params,
            where_clause=where_clause
        )
        
        # Convert to response models
        assessments = []
        for _, row in result.iterrows():
            assessment = CPAssessmentDetail(
                company_id=row["company_id"],
                name=row["name"],
                sector=row["sector"],
                geography=row["geography"],
                latest_assessment_year=row["latest_assessment_year"],
                carbon_performance_2025=row["carbon_performance_2025"],
                carbon_performance_2027=row["carbon_performance_2027"],
                carbon_performance_2035=row["carbon_performance_2035"],
                carbon_performance_2050=row["carbon_performance_2050"]
            )
            assessments.append(assessment)
        
        logger.info(f"Successfully retrieved {len(assessments)} CP assessments")
        return assessments
        
    except Exception as e:
        logger.exception(f"Error getting latest CP assessments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id} - Company CP History
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_id}", response_model=List[CPAssessmentDetail])
@limiter.limit("100/minute")
async def get_company_cp_history(request: Request, company_id: str):
    """Retrieve all CP assessments for a specific company across different assessment cycles."""
    try:
        logger.info(f"Getting CP history for company {company_id}")
        db_manager = DatabaseManagerFactory.get_manager("tpi_api")
        
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_cp_company_history.sql",
            params={"company_id": company_id}
        )
        
        if result.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"Company '{company_id}' not found."
            )
        
        # Convert to response models
        history = []
        for _, row in result.iterrows():
            assessment = CPAssessmentDetail(
                company_id=row["company_id"],
                name=row["name"],
                sector=row["sector"],
                geography=row["geography"],
                latest_assessment_year=row["latest_assessment_year"],
                carbon_performance_2025=row["carbon_performance_2025"],
                carbon_performance_2027=row["carbon_performance_2027"],
                carbon_performance_2035=row["carbon_performance_2035"],
                carbon_performance_2050=row["carbon_performance_2050"]
            )
            history.append(assessment)
        
        logger.info(f"Successfully retrieved CP history for company {company_id}")
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting CP history for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/alignment - Alignment Status
# ------------------------------------------------------------------------------
@cp_router.get("/company/{company_id}/alignment", response_model=Dict[str, str])
@limiter.limit("100/minute")
async def get_company_cp_alignment(request: Request, company_id: str):
    """Get the latest Carbon Performance alignment for a specific company."""
    try:
        logger.info(f"Getting CP alignment for company {company_id}")
        db_manager = DatabaseManagerFactory.get_manager("tpi_api")
        
        # Get latest CP assessment for the company
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_cp_company_history.sql",
            params={"company_id": company_id}
        )
        
        if result.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ID {company_id} not found"
            )
        
        # Get the latest record
        latest_data = result.iloc[0]
        
        response = {
            "2025": latest_data.get("carbon_performance_2025") or "N/A",
            "2027": latest_data.get("carbon_performance_2027") or "N/A",
            "2035": latest_data.get("carbon_performance_2035") or "N/A",
            "2050": latest_data.get("carbon_performance_2050") or "N/A"
        }
        
        logger.info(f"Successfully retrieved CP alignment for company {company_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting CP alignment for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/comparison - Compare CP over Time
# ------------------------------------------------------------------------------
@cp_router.get(
    "/company/{company_id}/comparison",
    response_model=Union[CPComparisonResponse, PerformanceComparisonInsufficientDataResponse],
)
@limiter.limit("100/minute")
async def compare_company_cp(request: Request, company_id: str):
    """Compare Carbon Performance alignment between the most recent and previous assessment."""
    try:
        logger.info(f"Comparing CP for company {company_id}")
        db_manager = DatabaseManagerFactory.get_manager("tpi_api")
        
        # Get company history to find available years
        history_result = db_manager.execute_sql_template(
            SQL_DIR / "get_cp_company_history.sql",
            params={"company_id": company_id}
        )
        
        if history_result.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ID {company_id} not found"
            )
        
        # Check if we have at least 2 assessments
        if len(history_result) < 2:
            available_years = history_result['latest_assessment_year'].tolist()
            return PerformanceComparisonInsufficientDataResponse(
                company_id=company_id,
                message="Insufficient data for comparison",
                available_assessment_years=available_years
            )
        
        # Get the two most recent assessments
        latest = history_result.iloc[0]
        previous = history_result.iloc[1]
        
        response = CPComparisonResponse(
            company_id=company_id,
            current_year=int(latest['latest_assessment_year']),
            previous_year=int(previous['latest_assessment_year']),
            latest_cp_2025=latest.get('carbon_performance_2025') or "N/A",
            previous_cp_2025=previous.get('carbon_performance_2025') or "N/A",
            latest_cp_2035=latest.get('carbon_performance_2035') or "N/A",
            previous_cp_2035=previous.get('carbon_performance_2035') or "N/A"
        )
        
        logger.info(f"Successfully compared CP for company {company_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error comparing CP for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))