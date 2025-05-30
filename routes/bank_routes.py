from fastapi import APIRouter, HTTPException, Query, Path
import pandas as pd
from typing import Dict, Any, List, Optional
import re

# Load data files
PILOT_INDICATORS_FILE = "data/Banking Data May 18 2025/Framework of pilot indicators.xlsx"
BANK_ASSESSMENTS_FILE = "data/Banking Data May 18 2025/Bank assessments 18052025.xlsx"
BANK_CP_FILE = "data/Banking Data May 18 2025/Bank CP assessments 18052025.xlsx"

pilot_df = pd.read_excel(PILOT_INDICATORS_FILE)
bank_df = pd.read_excel(BANK_ASSESSMENTS_FILE)
bank_df.columns = bank_df.columns.str.strip().str.lower()
bank_cp_df = pd.read_excel(BANK_CP_FILE)
bank_cp_df.columns = bank_cp_df.columns.str.strip().str.lower()

router = APIRouter(prefix="/bank", tags=["Bank Endpoints"])

@router.get("/pilot-indicator/{indicator_number}")
def get_pilot_indicator(indicator_number: str = Path(..., description="Pilot indicator number (e.g., '1.1', '1.1.a')")) -> Dict[str, Any]:
    """
    Retrieve the type and text for a given pilot indicator number.
    """
    row = pilot_df[pilot_df['Number'].astype(str).str.lower() == indicator_number.strip().lower()]
    if row.empty:
        raise HTTPException(404, f"Pilot indicator '{indicator_number}' not found.")
    result = row.iloc[0]
    return {"type": result['Type'], "text": result['Text']}

@router.get("/bank-data/{bank_identifier}")
def get_bank_data(
    bank_identifier: str = Path(..., description="Bank name, ISIN, or SEDOL (case-insensitive; ISINs can be separated by ';' in the data)"),
    area: Optional[str] = Query(None, description="Filter by area number (e.g., '1')"),
    indicator: Optional[str] = Query(None, description="Filter by indicator number (e.g., '1.1')"),
    sub_indicator: Optional[str] = Query(None, description="Filter by sub-indicator number (e.g., '1.1.a')")
) -> Dict[str, Any]:
    """
    Retrieve all indicators and sub-indicators for a bank, identified by name, ISIN, or SEDOL.
    Optionally filter by area, indicator, or sub-indicator.
    The output structure is: areas -> indicators -> sub-indicators.
    """
    ident = bank_identifier.strip().lower()
    # Try ISIN match
    match = bank_df[bank_df['isins'].astype(str).str.lower().str.split(';').apply(lambda x: ident in [i.strip().lower() for i in x if i])]
    if match.empty:
        # Try SEDOL match
        match = bank_df[bank_df['sedol'].astype(str).str.strip().str.lower() == ident]
    if match.empty:
        # Try bank name match
        match = bank_df[bank_df['bank'].astype(str).str.strip().str.lower() == ident]
    if match.empty:
        raise HTTPException(404, f"Bank '{bank_identifier}' not found.")
    bank_row = match.iloc[0]
    # Group indicators and sub-indicators by Area and Indicator number
    area_data = {}
    # First, find all area numbers
    for col in bank_df.columns:
        if col.startswith('area'):
            m = re.match(r'area\s*(\d+)', col)
            if m:
                area_num = m.group(1)
                area_data[area_num] = {"area_value": bank_row[col], "indicators": {}}
    # Now group indicators and sub-indicators
    for col in bank_df.columns:
        if col.startswith('indicator') or col.startswith('sub indicator'):
            m = re.match(r'(sub indicator|indicator)\s*(\d+)(?:\.(\d+))?(?:\.(\w+))?', col)
            if not m:
                continue
            area_num = m.group(2)
            indicator_num = m.group(2)
            if m.group(3):
                indicator_num += f'.{m.group(3)}'
            if area_num not in area_data:
                area_data[area_num] = {"area_value": None, "indicators": {}}
            if indicator_num not in area_data[area_num]["indicators"]:
                area_data[area_num]["indicators"][indicator_num] = {"value": None, "sub_indicators": {}}
            if col.startswith('indicator') and m.group(3):
                area_data[area_num]["indicators"][indicator_num]["value"] = bank_row[col]
            elif col.startswith('sub indicator') and m.group(4):
                sub_indicator_num = f'{m.group(2)}.{m.group(3)}.{m.group(4)}'
                area_data[area_num]["indicators"][indicator_num]["sub_indicators"][sub_indicator_num] = bank_row[col]
    # Apply optional filters
    filtered_areas = area_data
    if area:
        filtered_areas = {k: v for k, v in filtered_areas.items() if k == area}
    if indicator:
        for a in list(filtered_areas.keys()):
            filtered_areas[a]["indicators"] = {k: v for k, v in filtered_areas[a]["indicators"].items() if k == indicator}
    if sub_indicator:
        for a in list(filtered_areas.keys()):
            for i in list(filtered_areas[a]["indicators"].keys()):
                filtered_areas[a]["indicators"][i]["sub_indicators"] = {k: v for k, v in filtered_areas[a]["indicators"][i]["sub_indicators"].items() if k == sub_indicator}
    return {
        "bank": bank_row['bank'],
        "geography": bank_row.get('geography', None),
        "isin": bank_row.get('isins', None),
        "sedol": bank_row.get('sedol', None),
        "areas": filtered_areas
    }

@router.get("/cp-data/{bank_identifier}")
def get_bank_cp_data(
    bank_identifier: str = Path(..., description="Bank name, ISIN, or SEDOL (case-insensitive; ISINs can be separated by ';' in the data)"),
    sector: Optional[str] = Query(None, description="Filter by sector name (case-insensitive)"),
    year: Optional[str] = Query(None, description="Filter by year (e.g., '2025')")
) -> Dict[str, Any]:
    """
    Retrieve CP assessments for a bank, nested by sector name and then by year.
    Optionally filter by sector and/or year.
    """
    ident = bank_identifier.strip().lower()
    # Try ISIN match
    match = bank_df[bank_df['isins'].astype(str).str.lower().str.split(';').apply(lambda x: ident in [i.strip().lower() for i in x if i])]
    if match.empty:
        # Try SEDOL match
        match = bank_df[bank_df['sedol'].astype(str).str.strip().str.lower() == ident]
    if match.empty:
        # Try bank name match
        match = bank_df[bank_df['bank'].astype(str).str.strip().str.lower() == ident]
    if match.empty:
        raise HTTPException(404, f"Bank '{bank_identifier}' not found.")
    bank_row = match.iloc[0]
    bank_name = bank_row['bank']
    # Find all CP rows for this bank in the CP file
    cp_matches = bank_cp_df[bank_cp_df['bank name'].astype(str).str.strip().str.lower() == bank_name.strip().lower()]
    if cp_matches.empty:
        return {"bank": bank_name, "cp_assessments": None}
    # Group by sector, then by year
    cp_by_sector = {}
    for _, row in cp_matches.iterrows():
        sector_name = row.get('sector', 'Unknown')
        if sector_name not in cp_by_sector:
            cp_by_sector[sector_name] = {}
        for y in range(2018, 2051):
            y_str = str(y)
            if y_str in row:
                cp_by_sector[sector_name][y_str] = row[y_str]
    # Apply optional filters
    filtered_cp = cp_by_sector
    if sector:
        filtered_cp = {k: v for k, v in filtered_cp.items() if k.lower() == sector.lower()}
    if year:
        for s in list(filtered_cp.keys()):
            filtered_cp[s] = {k: v for k, v in filtered_cp[s].items() if k == year}
    return {"bank": bank_name, "cp_assessments": filtered_cp}
