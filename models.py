from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Boolean, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import logging
from utils.database_creation_utils import get_engine
from sqlalchemy import text

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

AscorBase = declarative_base()
TpiBase = declarative_base()

# ASCOR Models
class Country(AscorBase):
    """Country model for ASCOR database"""
    __tablename__ = 'country'
    
    country_name = Column(String, primary_key=True)
    iso = Column(String, nullable=True)
    region = Column(String, nullable=True)
    bank_lending_group = Column(String, nullable=True)
    imf_category = Column(String, nullable=True)
    un_party_type = Column(String, nullable=True)
    
    # Relationships
    benchmarks = relationship("Benchmark", back_populates="country")
    assessment_results = relationship("AssessmentResult", back_populates="country")
    assessment_trends = relationship("AssessmentTrend", back_populates="country")
    trend_values = relationship("TrendValue", back_populates="country")
    value_per_years = relationship("ValuePerYear", back_populates="country")

class AssessmentElement(AscorBase):
    """Assessment element model for ASCOR database"""
    __tablename__ = 'assessment_elements'
    
    code = Column(String, primary_key=True)
    text = Column(String, nullable=False)
    response_type = Column(String, nullable=False)
    type = Column(String, nullable=False)
    
    # Relationships
    results = relationship("AssessmentResult", back_populates="element")

class AssessmentResult(AscorBase):
    """Assessment result model for ASCOR database"""
    __tablename__ = 'assessment_results'
    
    assessment_id = Column(Integer, primary_key=True)
    code = Column(String, ForeignKey('assessment_elements.code'), primary_key=True)
    response = Column(String, nullable=True)
    assessment_date = Column(Date, nullable=False)
    publication_date = Column(Date, nullable=True)
    source = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    country_name = Column(String, ForeignKey('country.country_name'), nullable=False)
    
    # Relationships
    country = relationship("Country", back_populates="assessment_results")
    element = relationship("AssessmentElement", back_populates="results")

class AssessmentTrend(AscorBase):
    """Assessment trend model for ASCOR database"""
    __tablename__ = 'assessment_trends'
    
    trend_id = Column(Integer)
    country_name = Column(String, ForeignKey('country.country_name'))
    emissions_metric = Column(String, nullable=True)
    emissions_boundary = Column(String, nullable=True)
    units = Column(String, nullable=True)
    assessment_date = Column(Date, nullable=True)
    publication_date = Column(Date, nullable=True)
    last_historical_year = Column(Integer, nullable=True)
    
    __table_args__ = (
        PrimaryKeyConstraint('trend_id', 'country_name'),
    )
    
    # Relationships
    country = relationship("Country", back_populates="assessment_trends")
    trend_values = relationship("TrendValue", back_populates="trend")
    value_per_years = relationship("ValuePerYear", back_populates="trend")

class TrendValue(AscorBase):
    """Trend value model for ASCOR database"""
    __tablename__ = 'trend_values'
    
    trend_id = Column(Integer)
    country_name = Column(String, ForeignKey('country.country_name'))
    year = Column(Integer)
    value = Column(Float, nullable=False)
    
    __table_args__ = (
        PrimaryKeyConstraint('trend_id', 'country_name', 'year'),
        ForeignKeyConstraint(
            ['trend_id', 'country_name'],
            ['assessment_trends.trend_id', 'assessment_trends.country_name']
        ),
    )
    
    # Relationships
    trend = relationship("AssessmentTrend", back_populates="trend_values")
    country = relationship("Country", back_populates="trend_values")

class ValuePerYear(AscorBase):
    """Value per year model for ASCOR database"""
    __tablename__ = 'value_per_year'
    
    year = Column(Integer)
    value = Column(Float, nullable=False)
    trend_id = Column(Integer)
    country_name = Column(String, ForeignKey('country.country_name'))
    
    __table_args__ = (
        PrimaryKeyConstraint('year', 'trend_id', 'country_name'),
        ForeignKeyConstraint(
            ['trend_id', 'country_name'],
            ['assessment_trends.trend_id', 'assessment_trends.country_name']
        ),
    )
    
    # Relationships
    trend = relationship("AssessmentTrend", back_populates="value_per_years")
    country = relationship("Country", back_populates="value_per_years")

class Benchmark(AscorBase):
    """Benchmark model for ASCOR database"""
    __tablename__ = 'benchmarks'
    
    benchmark_id = Column(Integer, primary_key=True)
    publication_date = Column(Date, nullable=True)
    emissions_metric = Column(String, nullable=True)
    emissions_boundary = Column(String, nullable=True)
    units = Column(String, nullable=True)
    benchmark_type = Column(String, nullable=True)
    country_name = Column(String, ForeignKey('country.country_name'), nullable=True)
    
    # Relationships
    country = relationship("Country", back_populates="benchmarks")
    values = relationship("BenchmarkValue", back_populates="benchmark")

class BenchmarkValue(AscorBase):
    """Benchmark values model for ASCOR database"""
    __tablename__ = 'benchmark_values'
    
    year = Column(Integer, primary_key=True)
    benchmark_id = Column(Integer, ForeignKey('benchmarks.benchmark_id'), primary_key=True)
    value = Column(Float, nullable=False)
    
    # Relationships
    benchmark = relationship("Benchmark", back_populates="values")

# TPI Models
class Company(TpiBase):
    """Company model for TPI database"""
    __tablename__ = 'company'
    
    company_name = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    geography = Column(String, nullable=True)
    isin = Column(String, nullable=True)
    ca100_focus = Column(String, nullable=True)
    size_classification = Column(String, nullable=True)
    geography_code = Column(String, nullable=True)
    sedol = Column(String, nullable=True)
    sector_name = Column(String, nullable=True)
    
    # Relationships
    answers = relationship("CompanyAnswer", back_populates="company")
    mq_assessments = relationship("MQAssessment", back_populates="company")
    cp_assessments = relationship("CPAssessment", back_populates="company")

class CompanyAnswer(TpiBase):
    """Company answer model for TPI database"""
    __tablename__ = 'company_answer'
    
    question_code = Column(String, primary_key=True)
    company_name = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    question_text = Column(String, nullable=True)
    response = Column(String, nullable=True)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['company_name', 'version'],
            ['company.company_name', 'company.version']
        ),
    )
    
    # Relationships
    company = relationship("Company", back_populates="answers")

class MQAssessment(TpiBase):
    """Management Quality Assessment model for TPI database"""
    __tablename__ = 'mq_assessment'
    
    assessment_date = Column(Date, primary_key=True)
    company_name = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    tpi_cycle = Column(Integer, primary_key=True)
    publication_date = Column(Date, nullable=True)
    level = Column(String, nullable=True)
    performance_change = Column(String, nullable=True)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['company_name', 'version'],
            ['company.company_name', 'company.version']
        ),
    )
    
    # Relationships
    company = relationship("Company", back_populates="mq_assessments")

class CPAssessment(TpiBase):
    """Carbon Performance Assessment model for TPI database"""
    __tablename__ = 'cp_assessment'
    
    assessment_date = Column(Date, primary_key=True)
    company_name = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    is_regional = Column(String, primary_key=True)
    publication_date = Column(Date, nullable=True)
    assumptions = Column(String, nullable=True)
    cp_unit = Column(String, nullable=True)
    projection_cutoff = Column(Date, nullable=True)
    benchmark_id = Column(String, nullable=True)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['company_name', 'version'],
            ['company.company_name', 'company.version']
        ),
    )
    
    # Relationships
    company = relationship("Company", back_populates="cp_assessments")
    projections = relationship("CPProjection", back_populates="assessment")
    alignments = relationship("CPAlignment", back_populates="assessment")

class CPProjection(TpiBase):
    """Carbon Performance Projection model for TPI database"""
    __tablename__ = 'cp_projection'
    
    cp_projection_year = Column(Integer, primary_key=True)
    cp_projection_value = Column(Integer, nullable=True)
    assessment_date = Column(Date, primary_key=True)
    company_name = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    is_regional = Column(String, primary_key=True)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['assessment_date', 'company_name', 'version', 'is_regional'],
            ['cp_assessment.assessment_date', 'cp_assessment.company_name', 'cp_assessment.version', 'cp_assessment.is_regional']
        ),
    )
    
    # Relationships
    assessment = relationship("CPAssessment", back_populates="projections")

class CPAlignment(TpiBase):
    """Carbon Performance Alignment model for TPI database"""
    __tablename__ = 'cp_alignment'
    
    cp_alignment_year = Column(Integer, primary_key=True)
    cp_alignment_value = Column(String, nullable=True)
    assessment_date = Column(Date, primary_key=True)
    company_name = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    is_regional = Column(String, primary_key=True)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['assessment_date', 'company_name', 'version', 'is_regional'],
            ['cp_assessment.assessment_date', 'cp_assessment.company_name', 'cp_assessment.version', 'cp_assessment.is_regional']
        ),
    )
    
    # Relationships
    assessment = relationship("CPAssessment", back_populates="alignments")

class SectorBenchmark(TpiBase):
    """Sector benchmark model for TPI database"""
    __tablename__ = 'sector_benchmark'
    
    benchmark_id = Column(String, primary_key=True)
    sector_name = Column(String, primary_key=True)
    scenario_name = Column(String, primary_key=True)
    region = Column(String, nullable=True)
    release_date = Column(Date, nullable=True)
    unit = Column(String, nullable=True)
    
    # Relationships
    projections = relationship("BenchmarkProjection", back_populates="benchmark")

class BenchmarkProjection(TpiBase):
    """Benchmark projection model for TPI database"""
    __tablename__ = 'benchmark_projection'
    
    benchmark_projection_year = Column(Integer, primary_key=True)
    benchmark_projection_attribute = Column(Float, nullable=True)
    benchmark_id = Column(String, primary_key=True)
    sector_name = Column(String, primary_key=True)
    scenario_name = Column(String, primary_key=True)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['benchmark_id', 'sector_name', 'scenario_name'],
            ['sector_benchmark.benchmark_id', 'sector_benchmark.sector_name', 'sector_benchmark.scenario_name']
        ),
    )
    
    # Relationships
    benchmark = relationship("SectorBenchmark", back_populates="projections")

def create_tables(db_name: str) -> None:
    """
    Create all tables in the specified database, dropping existing ones first
    
    Args:
        db_name: Name of the database to create tables in
    """
    try:
        engine = get_engine(db_name)
        
        # Drop tables in correct order to handle dependencies
        with engine.connect() as conn:
            # Drop ASCOR tables
            conn.execute(text("""
                DROP TABLE IF EXISTS value_per_year CASCADE;
                DROP TABLE IF EXISTS trend_values CASCADE;
                DROP TABLE IF EXISTS assessment_trends CASCADE;
                DROP TABLE IF EXISTS assessment_results CASCADE;
                DROP TABLE IF EXISTS assessment_elements CASCADE;
                DROP TABLE IF EXISTS benchmark_values CASCADE;
                DROP TABLE IF EXISTS benchmarks CASCADE;
                DROP TABLE IF EXISTS country CASCADE;
            """))
            
            # Drop TPI tables
            conn.execute(text("""
                DROP TABLE IF EXISTS cp_projection CASCADE;
                DROP TABLE IF EXISTS cp_alignment CASCADE;
                DROP TABLE IF EXISTS cp_assessment CASCADE;
                DROP TABLE IF EXISTS mq_assessment CASCADE;
                DROP TABLE IF EXISTS company_answer CASCADE;
                DROP TABLE IF EXISTS company CASCADE;
                DROP TABLE IF EXISTS benchmark_projection CASCADE;
                DROP TABLE IF EXISTS sector_benchmark CASCADE;
            """))
            conn.commit()
        
        # Create all tables
        AscorBase.metadata.create_all(engine)
        TpiBase.metadata.create_all(engine)
        logger.info(f"Created tables in database: {db_name}")
    except Exception as e:
        logger.error(f"Failed to create tables in {db_name}: {str(e)}")
        raise

if __name__ == "__main__":
    # Create tables in both databases
    create_tables("ascor_api")
    create_tables("tpi_api") 