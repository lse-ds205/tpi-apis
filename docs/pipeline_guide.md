# Quick Start Guide

## 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Database Setup
```bash
# Create PostgreSQL databases
createdb tpi_api
createdb ascor_api

# Create .env file
touch .env  # On Windows: type nul > .env
```

Add the following to your `.env` file:
```env
DB_USER=your_postgres_username
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tpi_api  # This will be overridden by the specific db_name parameter
```

## 3. Run Pipeline
```bash
# Run the pipeline
python run_pipeline.py
```

The pipeline will:
- Drop existing tables (if any)
- Create new tables
- Process and validate data
- Populate both TPI and ASCOR databases

Check the logs for any warnings or errors during execution. 