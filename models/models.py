from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# ASCOR Models
class ASCORTrendsPathways(Base):
    __tablename__ = "ASCOR_assessments_results_trends_pathways"
    
    id = Column(Integer, primary_key=True)
    country = Column(String)
    emissions_metric = Column(String)
    emissions_boundary = Column(String)
    units = Column(String)
    assessment_date = Column(DateTime)
    publication_date = Column(DateTime)
    last_historical_year = Column(Float)
    trends_data = Column(JSON)
    pathways_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ASCORAssessments(Base):
    __tablename__ = "ASCOR_assessments_results"
    
    id = Column(Integer, primary_key=True)
    country_id = Column(Integer)
    country = Column(String)
    assessment_date = Column(DateTime)
    publication_date = Column(DateTime)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ASCORBenchmarks(Base):
    __tablename__ = "ASCOR_benchmarks"
    
    id = Column(Integer, primary_key=True)
    country = Column(String)
    publication_date = Column(DateTime)
    emissions_metric = Column(String)
    emissions_boundary = Column(String)
    units = Column(String)
    benchmark_type = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ASCORCountries(Base):
    __tablename__ = "ASCOR_countries"
    
    id = Column(Integer, primary_key=True)
    country_id = Column(Integer)
    country = Column(String)
    region = Column(String)
    income_group = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ASCORIndicators(Base):
    __tablename__ = "ASCOR_indicators"
    
    id = Column(Integer, primary_key=True)
    indicator_id = Column(String)
    indicator_name = Column(String)
    indicator_description = Column(String)
    indicator_category = Column(String)
    indicator_type = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# Sector Models
class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(String, unique=True)
    name = Column(String)
    sector = Column(String)
    geography = Column(String)
    latest_assessment_year = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ManagementQualityAssessment(Base):
    __tablename__ = "mq_assessments"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(String, ForeignKey('companies.company_id'))
    assessment_year = Column(Integer)
    methodology_cycle = Column(Integer)
    management_quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    company = relationship("Company", backref="mq_assessments")

class CarbonPerformanceAssessment(Base):
    __tablename__ = "cp_assessments"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(String, ForeignKey('companies.company_id'))
    assessment_year = Column(Integer)
    carbon_performance_2025 = Column(String)
    carbon_performance_2027 = Column(String)
    carbon_performance_2035 = Column(String)
    carbon_performance_2050 = Column(String)
    emissions_trend = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    company = relationship("Company", backref="cp_assessments")

class SectorBenchmarks(Base):
    __tablename__ = "sector_benchmarks"

    id = Column(Integer, primary_key=True)
    sector_name = Column(String)
    scenario_name = Column(String)
    region = Column(String)
    release_date = Column(DateTime)
    unit = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now) 