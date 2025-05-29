# Database Pipeline System Documentation

## Overview

This system provides a structured way to process and load data into TPI and ASCOR databases using an object-oriented approach. The pipeline handles data ingestion, validation, and database population while maintaining a comprehensive audit trail.

## System Architecture

### Directory Structure

```
pipelines/
├── __init__.py
├── base_pipeline.py      # Abstract base class defining common pipeline functionality
├── tpi_pipeline.py       # TPI-specific pipeline implementation
└── ascor_pipeline.py     # ASCOR-specific pipeline implementation
```

### Pipeline Flow

1. **Initialisation**
   - Database connection setup
   - Logger configuration
   - Data validator initialization

2. **Table Management**
   - Drop existing tables (except audit_logs)
   - Create new tables with proper schemas
   - Log pipeline start

3. **Data Processing**
   - Read source files
   - Transform data into appropriate formats
   - Store processed data in memory

4. **Data Validation**
   - Validate data structure and content
   - Check for required fields
   - Verify data types and relationships
   - Generate validation report

5. **Database Population**
   - Insert validated data into tables
   - Maintain referential integrity
   - Log successful insertions

6. **Audit Trail**
   - Log pipeline execution details
   - Record validation results
   - Track source files and row counts

## Data Validation

The pipeline validates data at multiple levels:

### Validation Process
1. **Pre-insertion Checks**
   - Validates all data before database operations
   - Blocks insertion if critical errors exist
   - Allows warnings to proceed with notification

2. **Validation Types**
   - Schema validation (required fields, data types)
   - Format validation (version numbers, ISO codes, dates)
   - Data integrity (duplicates, null values)
   - Basic business rules:
     - TPI cycle values (1-5)
     - Year ranges (2000-2100)
     - Version format (x.x)
     - ISO code format (2-3 letters)

3. **Validation Results**
   All validation results are logged to the audit_log table with:
   - Status: PASSED/WARNINGS/FAILED
   - Error/warning messages
   - Affected rows
   - Validation rules checked

## SQLAlchemy Models

The pipeline uses SQLAlchemy models to define the database schema and relationships. Each model represents a table in either the TPI or ASCOR database.

### ASCOR Models

#### Country
- **Purpose**: Stores country-level information and metadata
- **Key Fields**:
  - `country_name` (String, PK): Unique identifier for the country
  - `iso` (String): ISO country code (2-3 letters)
  - `region` (String): Geographic region classification
  - `bank_lending_group` (String): World Bank classification
  - `imf_category` (String): IMF classification
  - `un_party_type` (String): UNFCCC party type
- **Relationships**:
  - One-to-many with `Benchmark`
  - One-to-many with `AssessmentResult`
  - One-to-many with `AssessmentTrend`
- **Validation Rules**:
  - ISO code must be 2-3 letters
  - Country name is required and unique

#### AssessmentElement
- **Purpose**: Defines assessment questions, criteria, and response types
- **Key Fields**:
  - `code` (String, PK): Unique element code (alphanumeric with dots)
  - `text` (String): Question or assessment text
  - `response_type` (String): Expected response format
  - `type` (String): Element classification
- **Relationships**:
  - One-to-many with `AssessmentResult`
- **Validation Rules**:
  - Code must be alphanumeric with dots
  - All fields are required

#### AssessmentResult
- **Purpose**: Stores country assessment responses and metadata
- **Key Fields**:
  - `assessment_id` (Integer, PK): Unique assessment identifier
  - `code` (String, FK): References AssessmentElement
  - `response` (String): Assessment response
  - `assessment_date` (Date): When assessment was conducted
  - `publication_date` (Date): When results were published
  - `source` (String): Data source
  - `year` (Integer): Assessment year
  - `country_name` (String, FK): References Country
- **Relationships**:
  - Many-to-one with `Country`
  - Many-to-one with `AssessmentElement`
- **Validation Rules**:
  - Assessment date must be valid
  - Country must exist
  - Element code must exist

#### AssessmentTrend
- **Purpose**: Tracks emissions trends and metrics for countries
- **Key Fields**:
  - `trend_id` (Integer, PK): Unique trend identifier
  - `country_name` (String, PK): References Country
  - `emissions_metric` (String): Type of emissions measurement
  - `emissions_boundary` (String): Scope of emissions
  - `units` (String): Measurement units
  - `assessment_date` (Date): When trend was assessed
  - `publication_date` (Date): When trend was published
  - `last_historical_year` (Integer): Last year of historical data
- **Relationships**:
  - Many-to-one with `Country`
  - One-to-many with `TrendValue`
  - One-to-many with `ValuePerYear`
- **Validation Rules**:
  - Country must exist
  - Years must be between 2000-2100

#### TrendValue
- **Purpose**: Stores annual values for assessment trends
- **Key Fields**:
  - `trend_id` (Integer, PK): References AssessmentTrend
  - `country_name` (String, PK): References Country
  - `year` (Integer, PK): Year of the value
  - `value` (Float): Trend value
- **Relationships**:
  - Many-to-one with `AssessmentTrend`
- **Validation Rules**:
  - Year must be between 2000-2100
  - Value must be numeric

#### ValuePerYear
- **Purpose**: Stores detailed yearly values for trends
- **Key Fields**:
  - `year` (Integer, PK): Year of the value
  - `value` (Float): Yearly value
  - `trend_id` (Integer, PK): References AssessmentTrend
  - `country_name` (String, PK): References Country
- **Relationships**:
  - Many-to-one with `AssessmentTrend`
- **Validation Rules**:
  - Year must be between 2000-2100
  - Value must be numeric

#### Benchmark
- **Purpose**: Defines emissions benchmarks and metrics
- **Key Fields**:
  - `benchmark_id` (Integer, PK): Unique benchmark identifier
  - `publication_date` (Date): When benchmark was published
  - `emissions_metric` (String): Type of emissions measurement
  - `emissions_boundary` (String): Scope of emissions
  - `units` (String): Measurement units
  - `benchmark_type` (String): Classification of benchmark
  - `country_name` (String, FK): References Country
- **Relationships**:
  - Many-to-one with `Country`
  - One-to-many with `BenchmarkValue`
- **Validation Rules**:
  - Publication date must be valid
  - Country must exist if specified

#### BenchmarkValue
- **Purpose**: Stores annual values for benchmarks
- **Key Fields**:
  - `year` (Integer, PK): Year of the value
  - `benchmark_id` (Integer, PK): References Benchmark
  - `value` (Float): Benchmark value
- **Relationships**:
  - Many-to-one with `Benchmark`
- **Validation Rules**:
  - Year must be between 2000-2100
  - Value must be numeric

### TPI Models

#### Company
- **Purpose**: Stores company information and metadata
- **Key Fields**:
  - `company_name` (String, PK): Company identifier
  - `version` (String, PK): Data version (x.x format)
  - `geography` (String): Company location
  - `isin` (String): ISIN identifier
  - `ca100_focus` (String): Climate Action 100+ focus
  - `size_classification` (String): Company size category
  - `geography_code` (String): Geographic code
  - `sedol` (String): SEDOL identifier
  - `sector_name` (String): Industry sector
- **Relationships**:
  - One-to-many with `CompanyAnswer`
  - One-to-many with `MQAssessment`
  - One-to-many with `CPAssessment`
- **Validation Rules**:
  - Version must be in x.x format
  - Company name and version combination must be unique

#### CompanyAnswer
- **Purpose**: Stores company questionnaire responses
- **Key Fields**:
  - `question_code` (String, PK): References question
  - `company_name` (String, PK): References Company
  - `version` (String, PK): Data version
  - `question_text` (String): Question text
  - `response` (String): Company's response
- **Relationships**:
  - Many-to-one with `Company`
- **Validation Rules**:
  - Question code must be alphanumeric
  - Company must exist
  - Version must match company version

#### MQAssessment
- **Purpose**: Stores Management Quality assessments
- **Key Fields**:
  - `assessment_date` (Date, PK): Assessment date
  - `company_name` (String, PK): References Company
  - `version` (String, PK): Data version
  - `tpi_cycle` (Integer, PK): Assessment cycle (1-5)
  - `level` (String): Assessment level
  - `performance_change` (String): Change indicator
  - `publication_date` (Date): When assessment was published
- **Relationships**:
  - Many-to-one with `Company`
- **Validation Rules**:
  - TPI cycle must be between 1-5
  - Assessment date must be valid
  - Company must exist

#### CPAssessment
- **Purpose**: Stores Carbon Performance assessments
- **Key Fields**:
  - `assessment_date` (Date, PK): Assessment date
  - `company_name` (String, PK): References Company
  - `version` (String, PK): Data version
  - `is_regional` (String, PK): Regional scope indicator
  - `publication_date` (Date): When assessment was published
  - `assumptions` (String): Assessment assumptions
  - `cp_unit` (String): Performance unit
  - `projection_cutoff` (Date): History to projection cutoff
  - `benchmark_id` (String): Reference benchmark
- **Relationships**:
  - Many-to-one with `Company`
  - One-to-many with `CPProjection`
  - One-to-many with `CPAlignment`
- **Validation Rules**:
  - Assessment date must be valid
  - Company must exist
  - Regional indicator must be valid

#### CPAlignment
- **Purpose**: Stores carbon performance alignment data
- **Key Fields**:
  - `cp_alignment_year` (Integer, PK): Alignment year
  - `cp_alignment_value` (String): Alignment value
  - `assessment_date` (Date, PK): References CPAssessment
  - `company_name` (String, PK): References Company
  - `version` (String, PK): Data version
  - `is_regional` (String, PK): Regional scope indicator
- **Relationships**:
  - Many-to-one with `CPAssessment`
- **Validation Rules**:
  - Year must be between 2000-2100
  - Assessment must exist

#### CPProjection
- **Purpose**: Stores carbon performance projections
- **Key Fields**:
  - `cp_projection_year` (Integer, PK): Projection year
  - `cp_projection_value` (Integer): Projection value
  - `assessment_date` (Date, PK): References CPAssessment
  - `company_name` (String, PK): References Company
  - `version` (String, PK): Data version
  - `is_regional` (String, PK): Regional scope indicator
- **Relationships**:
  - Many-to-one with `CPAssessment`
- **Validation Rules**:
  - Year must be between 2000-2100
  - Assessment must exist

#### SectorBenchmark
- **Purpose**: Defines sector-specific benchmarks
- **Key Fields**:
  - `benchmark_id` (String, PK): Unique benchmark identifier
  - `sector_name` (String, PK): Industry sector
  - `scenario_name` (String, PK): Scenario identifier
  - `region` (String): Geographic region
  - `release_date` (Date): When benchmark was released
  - `unit` (String): Measurement unit
- **Relationships**:
  - One-to-many with `BenchmarkProjection`
- **Validation Rules**:
  - Release date must be valid
  - Sector name must be valid

#### BenchmarkProjection
- **Purpose**: Stores sector benchmark projections
- **Key Fields**:
  - `benchmark_projection_year` (Integer, PK): Projection year
  - `benchmark_projection_attribute` (Float): Projection value
  - `benchmark_id` (String, PK): References SectorBenchmark
  - `sector_name` (String, PK): References SectorBenchmark
  - `scenario_name` (String, PK): References SectorBenchmark
- **Relationships**:
  - Many-to-one with `SectorBenchmark`
- **Validation Rules**:
  - Year must be between 2000-2100
  - Benchmark must exist

## Audit Trail

### Logging System

1. **Pipeline Execution Logs**
   - Process name and status
   - Start and end timestamps
   - Error messages and stack traces
   - Validation results

2. **Data Operation Logs**
   - Table modifications
   - Row counts
   - Source file information
   - Operation timestamps

3. **Validation Logs**
   - Validation rule results
   - Error and warning details
   - Data quality metrics

### Log Storage

- **Database Table**: `audit_log`
- **Fields**:
  - `execution_id`: Unique log identifier
  - `process`: Process name
  - `status`: Execution status
  - `notes`: Additional information
  - `table_name`: Affected table
  - `source_file`: Data source
  - `rows_inserted`: Operation size
  - `timestamp`: Operation time

## Audit Logging System
Both TPI and ASCOR databases maintain an identical `audit_log` table that tracks all pipeline operations and validation results:

```sql
CREATE TABLE audit_log (
    execution_id SERIAL PRIMARY KEY,
    execution_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_user VARCHAR(255) DEFAULT CURRENT_USER,
    process VARCHAR(255) NOT NULL,
    execution_status VARCHAR(50) NOT NULL,
    execution_notes TEXT,
    table_name VARCHAR(255),
    source_file VARCHAR(1024),
    rows_inserted INTEGER
);
```

The audit log table serves multiple purposes:
1. **Pipeline Execution Tracking**
   - Records start and end of pipeline runs
   - Tracks data loading operations noting the table and files accessed
   - Logs any errors or failures

2. **Validation Results**
   - Records validation start and completion
   - Tracks validation status (PASSED/WARNINGS/FAILED)
   - Stores detailed validation messages and affected rows

### Validation Status Codes
The following status codes are used in the audit log:
- `VALIDATION_START`: Validation process begins
- `VALIDATION_PASSED`: All validation checks passed successfully
- `VALIDATION_WARNINGS`: Validation passed with warnings
- `VALIDATION_FAILED`: Validation failed with errors

## Base Pipeline Class
The `BasePipeline` class defines common methods for database operations:

### Key Methods
- `drop_tables()`: Drops all tables except audit_log
- `create_tables()`: Creates all necessary tables
- `populate_tables()`: Processes and loads data into tables
- `_process_data()`: Abstract method for data processing
- `_validate_data()`: Abstract method for data validation

### Error Handling
The pipeline includes comprehensive error handling:
- Database connection errors
- Permission issues
- Data validation failures
- File access problems

All errors are logged to the audit_log table with detailed error messages.

## Database Models
The pipeline uses SQLAlchemy models for database operations. Key models include:

### TPI Models
- `Company`: Company information
- `CompanyAnswer`: Company questionnaire responses
- `MQAssessment`: Management Quality assessments
- `CPAssessment`: Carbon Performance assessments

### ASCOR Models
- `Country`: Country information
- `AssessmentElement`: Assessment questions
- `AssessmentResult`: Assessment responses
- `AssessmentTrend`: Trend data


## Logging
The pipeline uses a comprehensive logging system:

### Log Types
1. **Pipeline Logs**
   - Execution status
   - Processing steps
   - Performance metrics

2. **Validation Logs**
   - Validation rules
   - Error messages
   - Warning details

3. **Data Quality Logs**
   - Row counts
   - Data statistics
   - Quality metrics

### Log Storage
All logs are stored in the audit_log table with:
- Timestamps
- User information
- Detailed messages
- Related data metrics

