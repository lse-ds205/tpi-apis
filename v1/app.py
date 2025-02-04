import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException

from .models import CountryData, Metric, Pillar, Area, Indicator, CountryDataResponse

df_assessments = pd.read_excel("./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx")
df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'])

def __is_running_on_nuvolos():
    """
    If we are running this script from Nuvolos Cloud, 
    there will be an environment variable called HOSTNAME
    which starts with 'nv-'
    """

    hostname = os.getenv("HOSTNAME")
    return hostname is not None and hostname.startswith('nv-')

if __is_running_on_nuvolos():
    # Nuvolos alters the URL of the API (likely for security reasons)
    # Instead of https://A-BIG-IP-ADDRESS:8000/
    # The API is actually served at https://A-BIG-IP-ADDRESS/proxy/8000/
    app = FastAPI(root_path="/proxy/8000/")
else:
    # No need to set up anything else if running this on local machine
    app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/v1/country-data/{country}/{assessment_year}", response_model=CountryData)
async def get_country_data(country: str, assessment_year: int):

    selected_row = (
        (df_assessments["Country"] == country) &
        (df_assessments['Assessment date'].dt.year == assessment_year)
    )

    # Filter the data
    data = df_assessments[selected_row]

    if data.empty:
        raise HTTPException(status_code=404, 
                            detail=f"There is no data for country: {country} and year: {assessment_year}")

    # Selected and filter columns
    area_columns = [col for col in df_assessments.columns if col.startswith("area")]
    data = data[area_columns]

    # JSON does not allow for NaN or NULL. 
    # The equivalent is just to leave an empty string instead
    data = data.fillna('')

    #Rename columns
    data['country'] = country
    data['assessment_year'] = assessment_year

    remap_area_column_names = {
        col: col.replace('area ', '').replace('.', '_')
        for col in area_columns
    }

    data = data.rename(columns=remap_area_column_names)
    output_dict = data.iloc[0].to_dict()

    output = CountryData(**output_dict)

    # Grab just the first element (there should only be one anyway)
    # and return it as a dictionary
    return output

@app.get("/v1/country-metrics/{country}/{assessment_year}", response_model=List[Metric])
async def get_country_metrics(country: str, assessment_year: int):

    selected_row = (
        (df_assessments["Country"] == country) &
        (df_assessments['Assessment date'].dt.year == assessment_year)
    )

    # Filter the data
    data = df_assessments[selected_row]

    if data.empty:
        raise HTTPException(status_code=404, 
                            detail=f"There is no data for country: {country} and year: {assessment_year}")

    # Select just the metrics
    metric_columns = [col for col in df_assessments.columns 
                      if col.startswith('metric')]
    data = data[metric_columns]

    # JSON does not allow for NaN or NULL. 
    # The equivalent is just to leave an empty string instead
    data = data.fillna('')

    remap_area_column_names = {
        col: col.replace('metric ', '')
        for col in metric_columns
    }

    data = data.rename(columns=remap_area_column_names)

    data_as_dict = data.iloc[0].to_dict()

    list_metrics = []
    for name, value in data_as_dict.items():
        individual_metric = Metric(name=name, value=value)
        list_metrics.append(individual_metric)
    # Grab just the first element (there should only be one anyway)
    # and return it as a dictionary
    return list_metrics

#######
# Work in progress. Pure ChatGPT code; edit next time

@app.get("/v1/country-nested/{country}/{assessment_year}", response_model=CountryDataResponse)
async def get_country_data(country: str, assessment_year: int):
    # Filter the global DataFrame (df_assessments) by country (case-insensitive) and assessment year.
    selected_row = (
        (df_assessments["Country"].str.lower() == country.lower()) &
        (df_assessments["Assessment date"].dt.year == assessment_year)
    )
    data = df_assessments[selected_row]
    if data.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data for country: {country} and year: {assessment_year}"
        )
    # Replace any NaN/NULL values with an empty string.
    data = data.fillna('')
    row_dict = data.iloc[0].to_dict()

    def transform_flat_to_nested(flat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms a flat dictionary (e.g. one Excel row) into the nested JSON structure.
        Expected keys:
          - "Country" and "Assessment date" (dd/mm/YYYY)
          - "area <pillar>.<number>" e.g. "area EP.1"
          - "indicator <area>.<letter>" e.g. "indicator EP.1.a"
          - "metric <indicator>.<suffix>" e.g. "metric EP.2.a.i"
        """
        country_val = flat_data.get("Country", "").strip().lower()
        assessment_date = flat_data.get("Assessment date", "")
        try:
            dt = datetime.strptime(assessment_date, "%d/%m/%Y")
            year_val = dt.year
        except Exception:
            year_val = None

        result: Dict[str, Any] = {
            "country": country_val,
            "assessment_year": year_val,
            "pillars": []
        }
        # Define the pillar codes to process.
        for pillar in ["EP", "CP", "CF"]:
            pillar_obj = {"name": pillar, "areas": []}
            # Process areas for the pillar.
            for key, area_assessment in flat_data.items():
                if key.startswith("area "):
                    area_code = key[5:].strip()  # e.g. "EP.1"
                    if area_code.startswith(f"{pillar}."):
                        area_obj = {
                            "name": area_code,
                            "assessment": area_assessment,
                            "indicators": []
                        }
                        # Process indicators within this area.
                        for ikey, indicator_assessment in flat_data.items():
                            if ikey.startswith("indicator "):
                                indicator_code = ikey[len("indicator "):].strip()  # e.g. "EP.1.a"
                                if indicator_code.startswith(f"{area_code}."):
                                    indicator_obj = {
                                        "name": indicator_code,
                                        "assessment": indicator_assessment,
                                        "metrics": []
                                    }
                                    # Process metrics for this indicator.
                                    for mkey, metric_value in flat_data.items():
                                        if mkey.startswith("metric "):
                                            metric_code = mkey[len("metric "):].strip()  # e.g. "EP.1.a.i"
                                            if metric_code.startswith(indicator_code):
                                                if metric_value not in (None, "", "No data"):
                                                    indicator_obj["metrics"].append({
                                                        "name": metric_code,
                                                        "value": metric_value
                                                    })
                                    area_obj["indicators"].append(indicator_obj)
                        pillar_obj["areas"].append(area_obj)
            result["pillars"].append(pillar_obj)
        return result

    nested_data = transform_flat_to_nested(row_dict)
    return nested_data

# async def transform_flat_to_nested(flat_data: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Transforms a flat dictionary (e.g. a row from the Excel file)
#     into the nested JSON structure.
    
#     Expected keys include:
#       - "Country" (the country name)
#       - "Assessment date" (a date string, e.g. "15/03/2024")
#       - For each pillar area: a key "area {pillar}.{number}" (e.g. "area EP.1")
#       - For each indicator: a key "indicator {area_code}.{letter}" (e.g. "indicator EP.1.a")
#       - For each metric: a key "metric {indicator_code}.{suffix}" (e.g. "metric EP.2.a.i")
    
#     Returns a nested dictionary that follows the structure:
    
#     {
#       "country": <str>,
#       "assessment_year": <int>,
#       "pillars": [
#          {
#            "name": "EP",
#            "areas": [
#               {
#                 "name": "EP.1",
#                 "assessment": <str>,
#                 "indicators": [
#                    {
#                      "name": "EP.1.a",
#                      "assessment": <str>,
#                      "metrics": [
#                         { "name": "EP.1.a.i", "value": <str> },
#                         ...
#                      ]
#                    },
#                    ...
#                 ]
#               },
#               ...
#            ]
#          },
#          { "name": "CP", "areas": [ ... ] },
#          { "name": "CF", "areas": [ ... ] }
#       ]
#     }
#     """
#     # Extract top-level fields.
#     country = flat_data.get("Country", "").strip().lower()
#     assessment_date = flat_data.get("Assessment date", "").strip()
#     try:
#         # Expecting a date in the format "dd/mm/YYYY"
#         dt = datetime.strptime(assessment_date, "%d/%m/%Y")
#         assessment_year = dt.year
#     except Exception:
#         assessment_year = None

#     # Initialize the output structure.
#     result: Dict[str, Any] = {
#         "country": country,
#         "assessment_year": assessment_year,
#         "pillars": []
#     }

#     # Define the pillars we expect.
#     pillar_names = ["EP", "CP", "CF"]

#     # For each pillar, find the corresponding areas.
#     for pillar in pillar_names:
#         pillar_obj = {"name": pillar, "areas": []}
        
#         # Look for keys that start with "area " for this pillar.
#         for key, area_assessment in flat_data.items():
#             if key.startswith("area "):
#                 # Remove the "area " prefix to get the area code (e.g. "EP.1").
#                 area_code = key[5:].strip()
#                 if area_code.startswith(f"{pillar}."):
#                     area_obj = {
#                         "name": area_code,
#                         "assessment": area_assessment,
#                         "indicators": []
#                     }
#                     # Find all indicators that belong to this area.
#                     for ikey, indicator_assessment in flat_data.items():
#                         if ikey.startswith("indicator "):
#                             # Extract the indicator code (e.g. "EP.1.a").
#                             indicator_code = ikey[len("indicator "):].strip()
#                             if indicator_code.startswith(f"{area_code}."):
#                                 indicator_obj = {
#                                     "name": indicator_code,
#                                     "assessment": indicator_assessment,
#                                     "metrics": []
#                                 }
#                                 # Find all metrics for this indicator.
#                                 for mkey, metric_value in flat_data.items():
#                                     if mkey.startswith("metric "):
#                                         metric_code = mkey[len("metric "):].strip()
#                                         if metric_code.startswith(indicator_code):
#                                             # Optionally filter out empty or "No data" values.
#                                             if metric_value not in (None, "", "No data"):
#                                                 indicator_obj["metrics"].append({
#                                                     "name": metric_code,
#                                                     "value": metric_value
#                                                 })
#                                 area_obj["indicators"].append(indicator_obj)
#                     pillar_obj["areas"].append(area_obj)
#         result["pillars"].append(pillar_obj)

#     return result