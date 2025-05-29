# Dynamic File Discovery for TPI and ASCOR Pipelines

## Overview

The TPI and ASCOR pipelines have been enhanced with dynamic file discovery capabilities, making them more flexible and robust when dealing with different data directory structures and file naming conventions.

## Key Improvements

### 1. Automatic Directory Discovery

**Before:**
- Hardcoded directory paths: `'TPI_sector_data_All_sectors_08032025'`
- Required exact directory names to match

**After:**
- Dynamic discovery based on patterns: directories containing `'sector_data'` or `'ascor'`
- Automatic date extraction and selection of the latest directory
- Support for multiple date formats: `DDMMYYYY`, `MMDDYYYY`, `YYYYMMDD`

### 2. Flexible File Discovery

**Before:**
- Hardcoded file names: `'Company_Latest_Assessments_5.0.csv'`
- Required exact file names to match

**After:**
- Pattern-based file discovery using glob patterns
- Automatic categorization of files by type (e.g., version 4.0 vs 5.0)
- Latest file selection when multiple files match a pattern

### 3. Centralized Utility Functions

Created `utils/file_discovery.py` with reusable functions:

- `find_latest_directory()`: Find latest directory by date pattern
- `find_latest_file()`: Find latest file by date pattern
- `find_files_by_pattern()`: Find multiple files using pattern dictionary
- `find_methodology_files()`: Specialized function for MQ methodology files
- `categorize_files()`: Categorize files based on keywords
- `extract_date_from_name()`: Extract dates from filenames/directory names

## Usage Examples

### TPI Pipeline

```python
# Automatically finds latest TPI directory
pipeline = TPIPipeline('data', logger)

# Discovers files dynamically:
# - Company_Latest_Assessments*.csv files (categorized by version)
# - MQ_Assessments*.csv files (sorted by methodology number)
# - CP_Assessments*.csv files (categorized as regional/standard)
# - Sector_Benchmarks*.csv files (latest by date)
```

### ASCOR Pipeline

```python
# Automatically finds latest ASCOR directory
pipeline = ASCORPipeline('data', logger)

# Discovers files dynamically:
# - ASCOR_countries.*
# - ASCOR_benchmarks.*
# - ASCOR_indicators.*
# - ASCOR_assessments_results.*
# - ASCOR_assessments_results_trends_pathways.*
```

## Supported Patterns

### Directory Patterns
- TPI: Any directory containing `'sector_data'` (case insensitive)
- ASCOR: Any directory containing `'ascor'` (case insensitive)

### Date Formats
- `DDMMYYYY` (e.g., 08032025 = March 8, 2025)
- `MMDDYYYY` (e.g., 03082025 = March 8, 2025)
- `YYYYMMDD` (e.g., 20250308 = March 8, 2025)

### File Categorization
- **Company Assessments**: Categorized by version (4.0, 5.0) based on filename
- **MQ Assessments**: Sorted by methodology number extracted from filename
- **CP Assessments**: Categorized as 'regional' or 'standard' based on keywords

## Benefits

1. **Flexibility**: Works with different data directory structures and dates
2. **Robustness**: Graceful fallback to lexicographic sorting if date parsing fails
3. **Maintainability**: Centralized file discovery logic reduces code duplication
4. **Logging**: Comprehensive logging of file discovery decisions
5. **Future-proof**: Easy to add new file patterns and discovery rules

## Migration

The changes are backward compatible. Existing data directories and file structures will continue to work, but the pipelines will now also work with:

- New data directories with different dates
- Files with different naming conventions (as long as they match the patterns)
- Multiple versions of the same file type

## Error Handling

The system provides clear error messages when:
- No matching directories are found
- Required files are missing
- Date parsing fails (with fallback to name-based sorting)

All errors include context about what was being searched for and where. 