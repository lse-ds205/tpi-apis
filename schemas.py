"""
This module defines the Pydantic models used for data validation and serialization
across the API. It includes models for Company, Management Quality (MQ) assessments,
and Carbon Performance (CP) assessments, along with various response models such as
paginated lists and performance comparison responses.
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
from pydantic import BaseModel, Field
from typing import Optional, List, Union, Dict


# ------------------------------------------------------------------------------
# Company Models
# ------------------------------------------------------------------------------
class CompanyBase(BaseModel):
    """
    Base model for a company.
    Contains key identifiers and basic information.
    """

    company_id: str = Field(
        ..., description="Unique identifier for the company"
    )
    name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Sector of operation")
    geography: Optional[str] = Field(None, description="Geographical region")
    latest_assessment_year: Optional[int] = Field(
        None, description="Year of latest assessment"
    )


class CompanyDetail(CompanyBase):
    """
    Extended company model including assessment details.
    Inherits from CompanyBase and adds fields for MQ and CP data.
    """

    management_quality_score: Optional[float] = Field(
        None, description="Management Quality Score"
    )
    carbon_performance_alignment_2035: Optional[str] = Field(
        None, description="Alignment with 2035 carbon targets"
    )
    emissions_trend: Optional[str] = Field(
        None, description="Emissions trend classification"
    )


class CompanyListResponse(BaseModel):
    """
    Response model for listing companies with pagination.
    Contains total count, current page, items per page, and a list of CompanyBase.
    """

    total: int
    page: int
    per_page: int
    companies: List[CompanyBase]


class CompanyHistoryResponse(BaseModel):
    """
    Response model for retrieving a company's historical assessments.
    Contains the company_id and a history of CompanyDetail records.
    """

    company_id: str
    history: List[CompanyDetail]


# ------------------------------------------------------------------------------
# Performance Comparison Models
# ------------------------------------------------------------------------------
class PerformanceComparisonResponse(BaseModel):
    """
    Response model for comparing company performance over two assessment cycles.
    Contains the company id, years of the two assessments, and the CP/MQ scores.
    """

    company_id: str
    current_year: int
    previous_year: int
    latest_mq_score: Optional[float]
    previous_mq_score: Optional[float]
    latest_cp_alignment: Optional[str]
    previous_cp_alignment: Optional[str]


class PerformanceComparisonInsufficientDataResponse(BaseModel):
    """
    Response model for cases where a performance comparison cannot be made.
    Provides a message and lists the available assessment years.
    """

    company_id: str
    message: str
    available_assessment_years: List[str]


# ------------------------------------------------------------------------------
# Management Quality (MQ) Models
# ------------------------------------------------------------------------------
class MQAssessmentDetail(BaseModel):
    """
    Model for a single MQ assessment record.
    Includes company details and the latest assessment year.
    """

    company_id: str = Field(
        ..., description="Unique identifier for the company"
    )
    name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Sector of operation")
    geography: Optional[str] = Field(None, description="Geographical region")
    latest_assessment_year: Optional[int] = Field(
        None, description="Year of latest MQ assessment"
    )
    management_quality_score: Optional[float] = Field(
        None, description="Management Quality Score"
    )


class MQDetail(MQAssessmentDetail):
    """
    Extended MQ model including methodology cycle information.
    Useful for detailed views where the research cycle is relevant.
    """

    methodology_cycle: Optional[int] = Field(
        None, description="Assessment methodology cycle"
    )


class MQListResponse(BaseModel):
    """
    Response model for listing all latest MQ scores.
    Contains a list of MQAssessmentDetail objects.
    """

    companies: List[MQAssessmentDetail]


class MQIndicatorsResponse(BaseModel):
    """
    Model for MQ assessment indicators.
    Provides detailed indicator scores for a specific company and assessment.
    """

    company_id: str = Field(
        ..., description="Unique identifier for the company"
    )
    assessment_year: int = Field(..., description="Year of the assessment")
    methodology_cycle: int = Field(..., description="Methodology cycle")
    indicators: Dict[str, Optional[float]] = Field(
        ..., description="Scores for individual MQ indicators"
    )


class PaginatedMQResponse(BaseModel):
    """
    Response model for paginated MQ assessments.
    Contains pagination details and a list of MQ assessment records.
    """

    total_records: int = Field(
        ..., description="Total number of records available"
    )
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    results: List[MQAssessmentDetail] = Field(
        ..., description="List of MQ assessments for the given page"
    )


class MQTrendsResponse(BaseModel):
    """
    Response model for MQ trends within a sector.
    Provides trend scores for a sector over time.
    """

    sector: str = Field(..., description="Sector name")
    trends: Dict[str, float] = Field(
        ..., description="MQ trend scores over time"
    )


# ------------------------------------------------------------------------------
# Carbon Performance (CP) Models
# ------------------------------------------------------------------------------
class CPAssessmentDetail(BaseModel):
    """
    Model for a single CP assessment record.
    Contains company details and carbon performance scores for various target years.
    """

    company_id: str = Field(
        ..., description="Unique identifier for the company"
    )
    name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Sector of operation")
    geography: Optional[str] = Field(None, description="Geographical region")
    latest_assessment_year: Optional[int] = Field(
        None, description="Year of latest CP assessment"
    )
    carbon_performance_2025: Optional[str] = Field(
        None, description="Alignment with 2025 target"
    )
    carbon_performance_2027: Optional[str] = Field(
        None, description="Alignment with 2027 target"
    )
    carbon_performance_2035: Optional[str] = Field(
        None, description="Alignment with 2035 target"
    )
    carbon_performance_2050: Optional[str] = Field(
        None, description="Alignment with 2050 target"
    )


class CPComparisonResponse(BaseModel):
    """
    Model for comparing CP performance between two assessment cycles.
    Provides CP alignment details for the latest and previous assessments.
    """

    company_id: str
    current_year: int
    previous_year: int
    latest_cp_2025: Optional[str]
    previous_cp_2025: Optional[str]
    latest_cp_2035: Optional[str]
    previous_cp_2035: Optional[str]


class PerformanceComparisonInsufficientDataResponse(BaseModel):
    """
    Model for scenarios where there is insufficient CP data for a comparison.
    Contains a message and the years for which data is available.
    """

    company_id: str
    message: str
    available_assessment_years: List[int]
