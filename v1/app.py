import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from .models import CountryData, Area, Indicator, Metric, MetricSource, IndicatorSource

file_path = './data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx'
df_assessments = pd.read_excel(file_path)
df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'], format='%d/%m/%Y')
df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'], format='%d/%m/%Y')
column_headings = df_assessments.columns.tolist()

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
        raise HTTPException(status_code=404, detail="Data not found for the specified country and year")

    # JSON does not allow for NaN or NULL. 
    # The equivalent is just to leave an empty string instead
    data = data.fillna('')

    # Create areas, indicators, and metrics
    def create_metrics(indicator_name):
        metrics = []
        for col in column_headings:
            if col.startswith(f"metric {indicator_name}."):
                metric_name = col
                metric_value = data.iloc[0][col]
                source_col = f"source {col}"
                metric_source = MetricSource(source_name=data.iloc[0][source_col]) if source_col in data else None
                if metric_value != '':
                    metrics.append(Metric(name=metric_name, value=metric_value, source=metric_source))
        return metrics

    def create_indicators(area_name):
        indicators = []
        for col in column_headings:
            if col.startswith(f"indicator {area_name}."):
                indicator_name = col
                metrics = create_metrics(col.split(" ")[1])
                source_col = f"source {col}"
                indicator_source = IndicatorSource(source_name=data.iloc[0][source_col]) if source_col in data else None
                if metrics:  # Only add indicators with non-empty metrics
                    indicators.append(Indicator(name=indicator_name, metrics=metrics, source=indicator_source))
        return indicators

    def create_areas():
        areas = []
        for col in column_headings:
            if col.startswith("area "):
                area_name = col.replace("area ", "")
                indicators = create_indicators(area_name)
                if indicators:  # Only add areas with non-empty indicators
                    areas.append(Area(name=area_name, indicators=indicators))
        return areas

    areas = create_areas()

    output_dict = CountryData(
        country=country,
        assessment_year=assessment_year,
        areas=areas
    )
    return output_dict