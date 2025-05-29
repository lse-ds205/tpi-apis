"""
Utility functions for data loading and normalization.

This module provides helper functions used across the TPI API project, including:
- Selecting the latest available data directory and CSV files based on naming conventions
- Extracting embedded dates from filenames and folder names
- Normalizing company names into consistent, URL-safe identifiers
"""

# -------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------
import io
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Union
import pandas as pd
import plotly.graph_objects as go
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

# -------------------------------------------------------------------------
# Utility Functions for Data Loading, File Selection, and Normalization
# -------------------------------------------------------------------------
def get_latest_data_dir(base_path: Path, prefix: str = "TPI_sector_data_All_sectors_") -> Path:
    """
    Finds and returns the latest data directory whose name starts with the given prefix
    and ends with an 8-digit date in MMDDYYYY format.

    Folder naming pattern:
        TPI sector data - All sectors - MMDDYYYY

    Parameters:
        base_data_dir (Path): The base directory containing possible data folders.
        prefix (str): The prefix that data folder names should start with.

    Returns:
        Path: The Path object for the latest data folder.

    Raises:
        FileNotFoundError: If no matching data directory is found.
    """
    matching_dirs = [
        d
        for d in base_path.iterdir()
        if d.is_dir() and d.name.startswith(prefix)
    ]

    if not matching_dirs:
        raise FileNotFoundError(
            "No data directories found with the specified prefix in the base path."
        )

    # Match directories with valid MMDDYYYY suffixes
    date_pattern = re.compile(rf"^{re.escape(prefix)}(\d{{8}})$")
    dirs_with_dates = []

    for d in matching_dirs:
        match = date_pattern.match(d.name)
        if match:
            date_str = match.group(1)
            try:
                d_date = datetime.strptime(date_str, "%m%d%Y")
                dirs_with_dates.append((d, d_date))
            except ValueError:
                continue

    if not dirs_with_dates:
        # Fall back to lexicographic sort if no valid dates found
        matching_dirs.sort()
        return matching_dirs[-1]

    # Return the directory with the latest valid date
    dirs_with_dates.sort(key=lambda x: x[1])
    return dirs_with_dates[-1][0]


def get_latest_assessment_file(pattern: str, data_dir: Path) -> Path:
    """
    Finds and returns the latest company assessments file based on the date embedded in the filename.

    The filenames are expected to follow the pattern:
        Company_Latest_Assessments*.csv
    with a date in MMDDYYYY format before the .csv extension.

    Parameters:
        pattern (str): Glob pattern to match the files.
        data_dir (Path): The directory containing the CSV files.

    Returns:
        Path: The Path object corresponding to the latest file.

    Raises:
        FileNotFoundError: If no files matching the pattern are found.
    """
    files = list(data_dir.glob(pattern))

    if not files:
        raise FileNotFoundError("No company assessments files found.")

    date_pattern = re.compile(r"_(\d{8})\.csv$")

    def extract_date(file_path: Path):
        match = date_pattern.search(file_path.name)
        if match:
            date_str = match.group(1)
            try:
                return datetime.strptime(date_str, "%m%d%Y")
            except ValueError:
                return None
        return None

    files_with_dates = [(f, extract_date(f)) for f in files]

    files_with_dates = [(f, d) for f, d in files_with_dates if d is not None]

    if not files_with_dates:
        # Fall back to alphabetic order if no valid dates
        files.sort()
        return files[-1]
    files_with_dates.sort(key=lambda x: x[1])

    # Return the file with the latest valid date
    return files_with_dates[-1][0]


def get_latest_cp_file(pattern: str, data_dir: Path) -> List[Path]:
    """
    Finds and returns a sorted list of CP assessment files matching the pattern
    (e.g., CP_Assessments_*.csv) in the latest data directory.

    Parameters:
        pattern (str): Glob pattern to match the files (e.g., "CP_Assessments_*.csv").
        data_dir (Path): The directory containing the CSV files.

    Returns:
        List[Path]: A sorted list of file paths matching the pattern.

    Raises:
        FileNotFoundError: If no files matching the pattern are found.
    """
    files = sorted(data_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No CP datasets found in {data_dir}")
    return files


def normalize_company_id(company_name: str) -> str:
    """
    Normalizes a company name into a lowercase, underscore-separated identifier.

    Steps:
        1. Strip leading/trailing whitespace
        2. Replace internal spaces with underscores
        3. Convert to lowercase

    Parameters:
        company_name (str): Raw company name.

    Returns:
        str: Normalized company identifier.
    """
    return company_name.strip().replace(" ", "_").lower()

def get_company_carbon_intensity(
    company_id: str,
    include_sector_benchmarks: bool = False,
    cp_df: pd.DataFrame = None,
    sector_bench_df: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Extracts carbon intensity data for a company including historical values,
    sector means, and benchmarks.
    
    Parameters:
        company_id (str): Company identifier to extract data for
        include_sector_benchmarks (bool): Whether to include sector benchmark data
        cp_df (pd.DataFrame): Optional dataframe with CP data (if None, must be loaded by caller)
        sector_bench_df (pd.DataFrame): Optional dataframe with sector benchmarks (if None, must be loaded by caller)
        
    Returns:
        Dict[str, Any]: Structured carbon intensity data with years and values
        
    Raises:
        HTTPException: If company is not found or data processing fails
    """
    if cp_df is None:
        raise ValueError("cp_df must be provided")
        
    sub = cp_df[cp_df["company name"].str.lower() == company_id.lower()]
    if sub.empty:
        raise HTTPException(404, f"Company '{company_id}' not found")

    year_map = {
        int(m.group(1)): col
        for col in sub.columns
        for m in [re.search(r"(\d{4})$", col)]
        if m and 1900 <= int(m.group(1)) <= 2100
    }

    # pick the row with the latest assessment date
    sub = sub.copy()
    sub["_ad"] = pd.to_datetime(sub["assessment date"], dayfirst=True, errors="coerce")
    if sub["_ad"].isna().all():
        raise HTTPException(500, "No valid assessment dates found in CP data")
    row = sub.sort_values("_ad", ascending=True).iloc[-1]

    # reported history (filter out NaNs)
    pts = []
    for yr, col in sorted(year_map.items()):
        val = pd.to_numeric(row[col], errors="coerce")
        if pd.notnull(val):
            pts.append((yr, float(val)))
    if pts:
        ys, vs = zip(*pts)
        data = {"years": list(ys), "values": list(vs)}
    else:
        data = {}

    # sector mean
    sector = row.get("sector", "").strip().lower()
    if sector:
        # Get latest assessment for each company in the sector
        sector_peers = cp_df[cp_df["sector"].str.lower() == sector]
        latest_assessments = sector_peers.sort_values("assessment date").groupby("company name").tail(1)
        sm = []
        for yr, col in sorted(year_map.items()):
            vals = pd.to_numeric(latest_assessments[col], errors="coerce").dropna()
            if not vals.empty:
                sm.append((yr, float(vals.mean())))
        if sm:
            y2, v2 = zip(*sm)
            data.update({"sector_mean_years": list(y2), "sector_mean_values": list(v2)})

    # benchmarks
    if include_sector_benchmarks and sector_bench_df is not None:
        sb = sector_bench_df[sector_bench_df["sector name"].str.lower() == sector]
        bench = {}
        for scenario in ["International Pledges", "Below 2 Degrees", "1.5 Degrees"]:
            sc = sb[sb["scenario name"].str.lower() == scenario.lower()]
            if sc.empty:
                continue
            latest = sc.sort_values(["release date"], key=lambda c: pd.to_datetime(c, dayfirst=True)).iloc[-1]
            recs = [(yr, float(latest.get(str(yr)))) for yr in range(2013, 2051) if pd.notna(latest.get(str(yr)))]
            if recs:
                ys, vs = zip(*recs)
                bench[scenario] = {"years": list(ys), "values": list(vs)}
        if bench:
            data.update({"benchmarks": bench, "unit": latest.get("unit", "Carbon Intensity")})

    return data


# ----------------------------------------------------------------------------
# Carbon Performance Visualization
# ----------------------------------------------------------------------------
class CarbonPerformanceVisualizer:
    """
    Utility class for generating visualizations of carbon performance data.
    """
    
    @staticmethod
    def generate_carbon_intensity_graph(
        data: Dict[str, Any],
        title: str,
        width: int,
        height: int,
        as_image: bool,
        image_format: str
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """
        Generates a carbon intensity graph from the provided data.
        
        Parameters:
            data (Dict[str, Any]): The carbon intensity data to visualize
            title (str): The title of the graph
            width (int): The width of the graph in pixels
            height (int): The height of the graph in pixels
            as_image (bool): Whether to return the graph as an image
            image_format (str): The format of the image (png/jpeg)
            
        Returns:
            Union[StreamingResponse, Dict[str, Any]]: Either a streaming response with the image
                or a dictionary representation of the figure
        """
        fig = go.Figure()
        # benchmark bands (stacked: bottom → top)
        if data.get("benchmarks"):
            colors = {
                "1.5 Degrees":           "rgba(153,194,255,0.35)",    # light blue (bottom)
                "Below 2 Degrees":       "rgba(100,144,233,0.25)",    # more blue (middle) - more transparent
                "International Pledges": "rgba(100,149,237,0.35)"     # darker blue (top)
            }
            scenarios = ["1.5 Degrees", "Below 2 Degrees", "International Pledges"]
            for i, scenario in enumerate(scenarios):
                band = data["benchmarks"].get(scenario)
                if not band:
                    continue
                fig.add_trace(go.Scatter(
                    x=band["years"],
                    y=band["values"],
                    mode="none",
                    fill="tozeroy" if i == 0 else "tonexty",
                    fillcolor=colors[scenario],
                    name=f"{scenario} Pathway",
                    hoverinfo="skip"
                ))
        # sector mean
        if data.get("sector_mean_years"):
            # Filter years up to 2022
            years = data["sector_mean_years"]
            values = data["sector_mean_values"]
            filtered_data = [(y, v) for y, v in zip(years, values) if y <= 2022]
            if filtered_data:
                y2, v2 = zip(*filtered_data)
                fig.add_trace(go.Scatter(
                    x=list(y2),
                    y=list(v2),
                    mode="lines",
                    name="Sector Mean",
                    line=dict(color="red", width=2)
                ))
        # reported history: solid up to 2022, dashed thereafter
        if data.get("years"):
            yrs = data["years"]
            vals = data["values"]
            
            # Find the transition point (data at 2022 or closest year)
            transition_year = 2022
            transition_idx = None
            
            # First find if there's an exact 2022 point
            for i, year in enumerate(yrs):
                if year == transition_year:
                    transition_idx = i
                    break
            
            # If no exact match, find closest year before 2022 as transition
            if transition_idx is None:
                before_transition = [i for i, y in enumerate(yrs) if y < transition_year]
                if before_transition:
                    transition_idx = max(before_transition)
            
            # Split at transition point, ensuring overlap
            solid_pts = [(y, v) for y, v in zip(yrs, vals) if y <= transition_year]
            dash_pts = [(y, v) for y, v in zip(yrs, vals) if y >= transition_year]
            
            # Add the historical data (solid line)
            if solid_pts:
                x_s, y_s = zip(*solid_pts)
                fig.add_trace(go.Scatter(
                    x=list(x_s), y=list(y_s),
                    mode="lines",
                    name="Reported",
                    line=dict(color="black", width=2),
                    showlegend=len(dash_pts) == 0  
                ))
            
            # Add the projected data (dashed line)
            if dash_pts:
                x_d, y_d = zip(*dash_pts)
                fig.add_trace(go.Scatter(
                    x=list(x_d), y=list(y_d),
                    mode="lines",
                    name="Reported (projected)",
                    line=dict(color="black", width=2, dash="dash")
                ))

            # Add green dot at 2030 if we have data for that year
            for i, year in enumerate(yrs):
                if year == 2030:
                    fig.add_trace(go.Scatter(
                        x=[year],
                        y=[vals[i]],
                        mode="markers",
                        name="2030 Target",
                        marker=dict(color="green", size=8),
                        showlegend=False
                    ))
                    break

        # target series (dotted)
        if data.get("target_years") and data.get("target_values"):
            fig.add_trace(go.Scatter(
                x=data["target_years"],
                y=data["target_values"],
                mode="lines+markers",
                name="Target",
                line=dict(dash="dot", color="green"),
                marker=dict(symbol="circle", size=6, color="green"),
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Year",
            yaxis_title=data.get("unit", "Carbon Intensity"),
            width=width,
            height=height,
            hovermode="x unified",
            legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="black", borderwidth=1)
        )

        if as_image:
            img = fig.to_image(format=image_format)
            return StreamingResponse(io.BytesIO(img), media_type=f"image/{image_format}")
        return fig.to_dict()
