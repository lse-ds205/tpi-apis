# Database Pipeline System

This system provides a structured way to process and load data into TPI and ASCOR databases using an object-oriented approach.

## Structure

The pipeline system is organized into a package structure:

```
pipelines/
├── __init__.py
├── base_pipeline.py
├── tpi_pipeline.py
└── ascor_pipeline.py
```

### Base Pipeline

`BasePipeline` is an abstract base class that defines the common interface and functionality for all database pipelines:

- `drop_tables()`: Drops all tables in the database
- `create_tables()`: Creates all required tables
- `populate_tables()`: Processes and loads data into tables
- Abstract methods that must be implemented by child classes:
  - `_get_table_creation_sql()`: Returns SQL statements for table creation
  - `_process_data()`: Processes data from files into dataframes
  - `_validate_data()`: Validates the processed data
  - `_get_primary_tables()`: Returns list of primary tables to be inserted first

### TPI Pipeline

`TPIPipeline` handles the TPI database operations:
- Processes company data, assessments, and benchmarks
- Creates and manages TPI-specific tables
- Validates TPI data structure and relationships

### ASCOR Pipeline

`ASCORPipeline` handles the ASCOR database operations:
- Processes country data, assessments, and trends
- Creates and manages ASCOR-specific tables
- Validates ASCOR data structure and relationships

## Running the Pipeline

The pipeline can be run using the `run_pipeline.py` script:


To run the pipeline:

1. Ensure your data files are in the correct location (NEED TO UPDATE FOR FUTURE DATES ALSO):
   ```
   data/
   ├── TPI_sector_data_All_sectors_08032025/
   └── TPI_ASCOR_data_13012025/
   ```

2. Run the script:
   ```bash
   python run_pipeline.py
   ```

The script will:
1. Set up logging to track progress and errors
2. Initialize both TPI and ASCOR pipelines
3. Drop existing tables (if any)
4. Create new tables with proper schemas
5. Process and validate data
6. Populate the tables with data

## Data Validation





