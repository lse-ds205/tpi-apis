# TPI and ASCOR Database Pipeline

## Overview
This pipeline populates two PostgreSQL databases (TPI and ASCOR) with data from various CSV and Excel files. It handles data validation, transformation, and ensures referential integrity.

## Pipeline Steps

### 1. Database Setup
- Drops existing tables (if any)
- Creates new tables with proper schemas
- Sets up foreign key relationships

### 2. Data Processing

#### TPI Database
- Processes company data from multiple sources
- Handles MQ assessments and company answers
- Processes CP assessments (regional and non-regional)
- Manages sector benchmarks and projections

#### ASCOR Database
- Processes country data
- Handles assessment elements and results
- Manages benchmarks and trends
- Processes yearly values and metrics

### 3. Data Validation
- Validates required fields and data types
- Checks foreign key relationships
- Ensures data consistency
- Logs warnings and errors

## Key Features
- Centralized data validation
- Automatic foreign key handling
- Detailed logging
- Error handling and reporting

## Usage
Run the pipeline using:
```bash
python run_pipeline.py
```

The pipeline will process all data and populate both databases. Check the logs for any warnings or errors 