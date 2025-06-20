"""
Dynamic file discovery utilities for TPI and ASCOR pipelines.

This module provides functions to automatically discover data directories and files
based on naming patterns and dates, making the pipelines more flexible and robust.
"""

import re
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging


def extract_date_from_name(name: str, date_formats: List[str] = None) -> Optional[datetime]:
    """
    Extract date from a filename or directory name.
    
    Args:
        name (str): The filename or directory name
        date_formats (List[str]): List of date formats to try. Defaults to common formats.
        
    Returns:
        Optional[datetime]: Parsed date if found, None otherwise
    """
    if date_formats is None:
        date_formats = ['%d%m%Y', '%m%d%Y', '%Y%m%d']
    
    # Look for 8-digit date patterns
    date_pattern = re.compile(r'(\d{8})')
    match = date_pattern.search(name)
    
    if match:
        date_str = match.group(1)
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
    
    return None


def find_latest_directory(base_path: Path, pattern: str, logger: logging.Logger = None) -> Path:
    """
    Find the latest directory matching a pattern based on embedded dates.
    
    Args:
        base_path (Path): Base directory to search in
        pattern (str): Pattern to match directory names (case insensitive)
        logger (logging.Logger): Optional logger for info messages
        
    Returns:
        Path: Path to the latest matching directory
        
    Raises:
        FileNotFoundError: If no matching directories are found
    """
    matching_dirs = [
        d for d in base_path.iterdir() 
        if d.is_dir() and pattern.lower() in d.name.lower()
    ]
    
    if not matching_dirs:
        raise FileNotFoundError(f"No directories found matching pattern: {pattern}")
    
    # Try to extract dates and sort by them
    dirs_with_dates = []
    for d in matching_dirs:
        date = extract_date_from_name(d.name)
        if date:
            dirs_with_dates.append((d, date))
    
    if dirs_with_dates:
        # Sort by date and return the latest
        dirs_with_dates.sort(key=lambda x: x[1])
        selected_dir = dirs_with_dates[-1][0]
    else:
        # Fall back to lexicographic sort if no valid dates found
        matching_dirs.sort(key=lambda x: x.name)
        selected_dir = matching_dirs[-1]
    
    if logger:
        logger.info(f"Selected directory: {selected_dir}")
    
    return selected_dir


def find_latest_file(directory: Path, pattern: str, logger: logging.Logger = None) -> Path:
    """
    Find the latest file matching a pattern based on embedded dates.
    
    Args:
        directory (Path): Directory to search in
        pattern (str): Glob pattern to match files
        logger (logging.Logger): Optional logger for info messages
        
    Returns:
        Path: Path to the latest matching file
        
    Raises:
        FileNotFoundError: If no matching files are found
    """
    matching_files = list(directory.glob(pattern))
    
    if not matching_files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    # Try to extract dates and sort by them
    files_with_dates = []
    for f in matching_files:
        date = extract_date_from_name(f.name)
        if date:
            files_with_dates.append((f, date))
    
    if files_with_dates:
        # Sort by date and return the latest
        files_with_dates.sort(key=lambda x: x[1])
        selected_file = files_with_dates[-1][0]
    else:
        # Fall back to lexicographic sort if no valid dates found
        matching_files.sort(key=lambda x: x.name)
        selected_file = matching_files[-1]
    
    if logger:
        logger.info(f"Selected file: {selected_file.name}")
    
    return selected_file


def find_files_by_pattern(directory: Path, patterns: Dict[str, str], logger: logging.Logger = None) -> Dict[str, Path]:
    """
    Find files matching multiple patterns and return the latest for each.
    
    Args:
        directory (Path): Directory to search in
        patterns (Dict[str, str]): Dictionary mapping file types to glob patterns
        logger (logging.Logger): Optional logger for info messages
        
    Returns:
        Dict[str, Path]: Dictionary mapping file types to their latest file paths
        
    Raises:
        FileNotFoundError: If any required files are not found
    """
    files = {}
    
    for file_type, pattern in patterns.items():
        try:
            files[file_type] = find_latest_file(directory, pattern, logger)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Required {file_type} file not found: {e}")
    
    return files


def find_methodology_files(directory: Path, base_pattern: str = "MQ_Assessments*", 
                          logger: logging.Logger = None) -> List[Path]:
    """
    Find and sort methodology files by their methodology number.
    
    Args:
        directory (Path): Directory to search in
        base_pattern (str): Base pattern to match methodology files
        logger (logging.Logger): Optional logger for info messages
        
    Returns:
        List[Path]: List of methodology files sorted by methodology number
        
    Raises:
        FileNotFoundError: If no methodology files are found
    """
    methodology_files = list(directory.glob(base_pattern))
    
    if not methodology_files:
        raise FileNotFoundError(f"No methodology files found matching pattern: {base_pattern}")
    
    # Sort by methodology number if present
    def extract_methodology_number(filename):
        match = re.search(r'Methodology_(\d+)', filename.name)
        return int(match.group(1)) if match else 0
    
    methodology_files.sort(key=extract_methodology_number)
    
    if logger:
        logger.info(f"Found {len(methodology_files)} methodology files")
    
    return methodology_files


def categorize_files(files: List[Path], categories: Dict[str, List[str]], 
                    logger: logging.Logger = None) -> Dict[str, Path]:
    """
    Categorize files based on keywords in their names.
    
    Args:
        files (List[Path]): List of files to categorize
        categories (Dict[str, List[str]]): Dictionary mapping categories to keyword lists
        logger (logging.Logger): Optional logger for info messages
        
    Returns:
        Dict[str, Path]: Dictionary mapping categories to file paths
    """
    categorized = {}
    
    for file in files:
        for category, keywords in categories.items():
            if any(keyword.lower() in file.name.lower() for keyword in keywords):
                categorized[category] = file
                if logger:
                    logger.info(f"Categorized {file.name} as {category}")
                break
    
    return categorized 