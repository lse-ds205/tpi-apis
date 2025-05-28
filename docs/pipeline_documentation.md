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

1. **Initialization**
   - Database connection setup
   - Logger configuration
   - Data validator initialization

2. **Table Management**
   - Drop existing tables (except audit_log)
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

### Validation Types

1. **Structural Validation**
   - Required fields presence
   - Data type correctness
   - Field length constraints
   - Primary key uniqueness

2. **Relational Validation**
   - Foreign key integrity
   - One-to-many relationship consistency
   - Many-to-many relationship validation

3. **Business Logic Validation**
   - Date range validity
   - Numeric value ranges
   - Categorical value validation
   - Cross-field validation rules

### Validation Process

1. **Pre-insertion Validation**
   - Validates all data before any database operations
   - Generates comprehensive error and warning reports
   - Blocks insertion if critical errors exist

2. **Error Handling**
   - Critical errors: Block data insertion
   - Warnings: Allow insertion with notification
   - Detailed error messages for troubleshooting

3. **Validation Integration**
   - Modular validation per table
   - Custom validation rules for specific data types
   - Extensible validation framework

## SQLAlchemy Models

### ASCOR Models

#### Country
- **Purpose**: Stores country-level information
- **Key Fields**:
  - `country_name` (String, PK): Unique identifier
  - `iso` (String): ISO country code
  - `region` (String): Geographic region
  - `bank_lending_group` (String): World Bank classification
  - `imf_category` (String): IMF classification
  - `un_party_type` (String): UNFCCC party type
- **Relationships**:
  - One-to-many with `Benchmark`
  - One-to-many with `AssessmentResult`
  - One-to-many with `AssessmentTrend`

#### AssessmentElement
- **Purpose**: Defines assessment questions and criteria
- **Key Fields**:
  - `code` (String, PK): Unique element code
  - `text` (String): Question text
  - `response_type` (String): Expected response format
  - `type` (String): Element classification
- **Relationships**:
  - One-to-many with `AssessmentResult`

#### AssessmentResult
- **Purpose**: Stores country assessment responses
- **Key Fields**:
  - `assessment_id` (Integer, PK): Unique assessment identifier
  - `code` (String, FK): References AssessmentElement
  - `response` (String): Assessment response
  - `assessment_date` (Date): When assessment was conducted
  - `publication_date` (Date): When results were published
  - `country_name` (String, FK): References Country
- **Relationships**:
  - Many-to-one with `Country`
  - Many-to-one with `AssessmentElement`

### TPI Models

#### Company
- **Purpose**: Stores company information
- **Key Fields**:
  - `company_name` (String, PK): Company identifier
  - `version` (String, PK): Data version
  - `geography` (String): Company location
  - `isin` (String): ISIN identifier
  - `sector_name` (String): Industry sector
- **Relationships**:
  - One-to-many with `CompanyAnswer`
  - One-to-many with `MQAssessment`
  - One-to-many with `CPAssessment`

#### MQAssessment
- **Purpose**: Stores Management Quality assessments
- **Key Fields**:
  - `assessment_date` (Date, PK): Assessment date
  - `company_name` (String, PK): References Company
  - `version` (String, PK): Data version
  - `tpi_cycle` (Integer, PK): Assessment cycle
  - `level` (String): Assessment level
  - `performance_change` (String): Change indicator
- **Relationships**:
  - Many-to-one with `Company`

#### CPAssessment
- **Purpose**: Stores Carbon Performance assessments
- **Key Fields**:
  - `assessment_date` (Date, PK): Assessment date
  - `company_name` (String, PK): References Company
  - `version` (String, PK): Data version
  - `is_regional` (String, PK): Regional scope indicator
  - `cp_unit` (String): Performance unit
  - `benchmark_id` (String): Reference benchmark
- **Relationships**:
  - Many-to-one with `Company`
  - One-to-many with `CPProjection`
  - One-to-many with `CPAlignment`

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

## Running the Pipeline

1. **Prerequisites**
   - Python 3.8+
   - Required packages (see requirements.txt)
   - Database credentials
   - Data files in correct format

2. **Data Directory Structure**
   ```
   data/
   ├── TPI_sector_data_All_sectors_08032025/
   └── TPI_ASCOR_data_13012025/
   ```

3. **Execution**
   ```bash
   python run_pipeline.py
   ```

4. **Monitoring**
   - Check logs for progress
   - Monitor validation results
   - Review audit trail
   - Verify data integrity




