"""
This module provides FastAPI endpoints for retrieving Management Quality (MQ) assessments.
It uses the database manager and SQL templates for efficient data retrieval.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Request, Depends, Path as PathParam
from typing import List, Dict, Optional
from middleware.rate_limiter import limiter
from schemas import (
    MQAssessmentDetail,
    MQDetail,
    MQListResponse,
    MQIndicatorsResponse,
    PaginatedMQResponse,
    MQTrendsResponse
)
from utils.filters import CompanyFilters, build_company_filter_conditions
from log_config import get_logger
from utils.database_manager import DatabaseManagerFactory

logger = get_logger(__name__)

# -------------------------------------------------------------------------
# Router Initialization
# -------------------------------------------------------------------------
mq_router = APIRouter(tags=["MQ Endpoints"])

# SQL file paths
SQL_DIR = Path(__file__).parent.parent / "sql" / "tpi" / "queries"

# ------------------------------------------------------------------------------
# Endpoint: GET /latest - Latest MQ Assessments
# ------------------------------------------------------------------------------
@mq_router.get("/latest", response_model=PaginatedMQResponse)
@limiter.limit("100/minute")
async def get_latest_mq_assessments(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of results per page (max 100)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """Retrieve the latest MQ assessment scores for all companies with pagination."""
    try:
        logger.info(f"Getting latest MQ assessments - page {page}, size {page_size}")
        db_manager = DatabaseManagerFactory.get_manager("tpi_api")
        
        # Build filter conditions
        where_clause, params = build_company_filter_conditions(filter)
        
        # Add pagination parameters
        params.update({
            "limit": page_size,
            "offset": (page - 1) * page_size
        })
        
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_latest_mq_assessments.sql",
            params=params,
            where_clause=where_clause
        )
        
        # Convert to response models
        companies = []
        for _, row in result.iterrows():
            assessment = MQAssessmentDetail(
                company_id=row["company_id"],
                name=row["name"],
                sector=row["sector"],
                geography=row["geography"],
                latest_assessment_year=row["latest_assessment_year"],
                management_quality_score=row["management_quality_score"]
            )
            companies.append(assessment)
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) as total FROM company c JOIN mq_assessment mq ON c.company_name = mq.company_name"
        if where_clause:
            count_query += f" WHERE 1=1 {where_clause}"
        else:
            count_query += " WHERE 1=1"
        
        count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
        count_result = db_manager.execute_query(count_query, count_params)
        total_records = count_result.iloc[0]['total'] if not count_result.empty else 0

        logger.info(f"Successfully retrieved {len(companies)} MQ assessments")
        return PaginatedMQResponse(
            total_records=total_records,
            page=page,
            page_size=page_size,
            results=companies
        )
        
    except Exception as e:
        logger.exception(f"Error getting latest MQ assessments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# Endpoint: GET /methodology/{methodology_id} - MQ Assessments by Methodology
# ------------------------------------------------------------------------------
@mq_router.get("/methodology/{methodology_id}", response_model=PaginatedMQResponse)
@limiter.limit("100/minute")
async def get_mq_by_methodology(
    request: Request,
    methodology_id: int = PathParam(..., ge=1, description="Methodology cycle ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Records per page (max 100)"),
    filter: CompanyFilters = Depends(CompanyFilters)
):
    """Returns MQ assessments based on a specific research methodology cycle with pagination."""
    try:
        logger.info(f"Getting MQ assessments for methodology {methodology_id} - page {page}, size {page_size}")
        db_manager = DatabaseManagerFactory.get_manager("tpi_api")
        
        # Build filter conditions
        where_clause, params = build_company_filter_conditions(filter)
        
        # Add methodology and pagination parameters
        params.update({
            "methodology_id": methodology_id,
            "limit": page_size,
            "offset": (page - 1) * page_size
        })
        
        # Add methodology filter to WHERE clause
        if where_clause and where_clause.strip():
            where_clause += " AND mq.tpi_cycle = :methodology_id"
        else:
            where_clause = " AND mq.tpi_cycle = :methodology_id"
        
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_latest_mq_assessments.sql",
            params=params,
            where_clause=where_clause
        )
        
        # Validate methodology exists
        if result.empty:
            # Check if methodology exists at all
            check_result = db_manager.execute_query(
                "SELECT DISTINCT tpi_cycle FROM mq_assessment WHERE tpi_cycle = :methodology_id",
                params={"methodology_id": methodology_id}
            )
            if check_result.empty:
                raise HTTPException(status_code=422, detail=f"Invalid methodology cycle: {methodology_id}")
        
        # Convert to response models
        companies = []
        for _, row in result.iterrows():
            assessment = MQAssessmentDetail(
                company_id=row["company_id"],
                name=row["name"],
                sector=row["sector"],
                geography=row["geography"],
                latest_assessment_year=row["latest_assessment_year"],
                management_quality_score=row["management_quality_score"]
            )
            companies.append(assessment)
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) as total FROM company c JOIN mq_assessment mq ON c.company_name = mq.company_name"
        if where_clause:
            count_query += f" WHERE 1=1 {where_clause}"
        else:
            count_query += " WHERE 1=1"
        
        count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
        count_result = db_manager.execute_query(count_query, count_params)
        total_records = count_result.iloc[0]['total'] if not count_result.empty else 0

        logger.info(f"Successfully retrieved {len(companies)} MQ assessments for methodology {methodology_id}")
        return PaginatedMQResponse(
            total_records=total_records,
            page=page,
            page_size=page_size,
            results=companies
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting MQ assessments for methodology {methodology_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# Endpoint: GET /trends/sector/{sector} - MQ Trends by Sector
# ------------------------------------------------------------------------------
@mq_router.get("/trends/sector/{sector}", response_model=PaginatedMQResponse)
@limiter.limit("100/minute")
async def get_mq_trends_sector(
    request: Request,
    sector: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Records per page (max 100)")
):
    """Fetches MQ trends for all companies in a given sector with pagination."""
    try:
        logger.info(f"Getting MQ trends for sector '{sector}' - page {page}, size {page_size}")
        db_manager = DatabaseManagerFactory.get_manager("tpi_api")
        
        # For sector trends, we don't use additional filters since sector is specified in path
        where_clause = " AND LOWER(c.sector_name) = :target_sector"
        params = {
            "target_sector": sector.lower(),
            "limit": page_size,
            "offset": (page - 1) * page_size
        }
        
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_mq_sector_trends.sql",
            params=params,
            where_clause=where_clause
        )
        
        # Check if sector exists
        if result.empty:
            raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found.")
        
        # Convert to response models
        companies = []
        for _, row in result.iterrows():
            assessment = MQAssessmentDetail(
                company_id=row["company_id"],
                name=row["name"],
                sector=sector.lower(),  # Use the requested sector format
                geography=row["geography"],
                latest_assessment_year=row["latest_assessment_year"],
                management_quality_score=row["management_quality_score"]
            )
            companies.append(assessment)
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) as total FROM company c JOIN mq_assessment mq ON c.company_name = mq.company_name"
        if where_clause:
            count_query += f" WHERE 1=1 {where_clause}"
        else:
            count_query += " WHERE 1=1"
        
        count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
        count_result = db_manager.execute_query(count_query, count_params)
        total_records = count_result.iloc[0]['total'] if not count_result.empty else 0

        logger.info(f"Successfully retrieved {len(companies)} MQ trends for sector '{sector}'")
        return PaginatedMQResponse(
            total_records=total_records,
            page=page,
            page_size=page_size,
            results=companies
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting MQ trends for sector '{sector}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id} - Company MQ History
# ------------------------------------------------------------------------------
@mq_router.get("/company/{company_id}", response_model=List[MQDetail])
@limiter.limit("100/minute")
async def get_company_mq_history(request: Request, company_id: str):
    """Retrieve all MQ assessments for a specific company across different assessment cycles."""
    try:
        logger.info(f"Getting MQ history for company {company_id}")
        db_manager = DatabaseManagerFactory.get_manager("tpi_api")
        
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_mq_company_history.sql",
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
            assessment = MQDetail(
                company_id=row["company_id"],
                name=row["name"],
                sector=row["sector"],
                geography=row["geography"],
                latest_assessment_year=row["latest_assessment_year"],
                management_quality_score=row["management_quality_score"],
                methodology_cycle=row["methodology_cycle"]
            )
            history.append(assessment)
        
        logger.info(f"Successfully retrieved MQ history for company {company_id}")
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting MQ history for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------------------------------------------------------------------
# Endpoint: GET /company/{company_id}/indicators/{assessment_year} - MQ Indicators
# ------------------------------------------------------------------------------
@mq_router.get("/company/{company_id}/indicators/{assessment_year}", response_model=MQIndicatorsResponse)
@limiter.limit("100/minute")
async def get_company_mq_indicators(
    request: Request, 
    company_id: str, 
    assessment_year: int
) -> MQIndicatorsResponse:
    """Get detailed MQ indicator scores for a specific company and assessment year."""
    try:
        logger.info(f"Getting MQ indicators for company {company_id}, year {assessment_year}")
        db_manager = DatabaseManagerFactory.get_manager("tpi_api")
        
        result = db_manager.execute_sql_template(
            SQL_DIR / "get_mq_indicators.sql",
            params={
                "company_id": company_id,
                "assessment_year": assessment_year
            }
        )
        
        if result.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No MQ data found for company '{company_id}' in year {assessment_year}"
            )
        
        # Convert to response model
        data = result.iloc[0]
        indicators = {}
        
        # Extract indicator scores (assuming columns like indicator_1_score, etc.)
        for col in result.columns:
            if col.startswith('indicator_') and col.endswith('_score'):
                indicator_name = col.replace('_score', '').replace('_', ' ').title()
                indicators[indicator_name] = data[col]
        
        response = MQIndicatorsResponse(
            company_id=company_id,
            assessment_year=assessment_year,
            methodology_cycle=data["methodology_cycle"],
            indicators=indicators
        )
        
        logger.info(f"Successfully retrieved MQ indicators for company {company_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting MQ indicators for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))