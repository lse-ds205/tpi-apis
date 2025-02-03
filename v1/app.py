import pandas as pd
from fastapi import FastAPI, HTTPException
from .models import Metric, Indicator, Area, Pillar, CountryDataResponse #Need to specify .models because . represents where I'm at
from typing import List, Dict, Union
from pydantic import BaseModel, Field

app = FastAPI()
filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx"
df_assessments = pd.read_excel(filepath, engine='openpyxl')

@app.get("/")
async def read_root():
    return {"Hello": "World"} 

# Specifying the classes to reflect the models.py file
class Metric(BaseModel):
    name: str
    value: str

class Indicator(BaseModel):
    name: str
    assessment: str
    metrics: List[Union[Metric, str]] = Field(default_factory=list)

class Area(BaseModel):
    name: str
    assessment: str
    indicators: List[Indicator]

class Pillar(BaseModel):
    name: str = Field(..., pattern="^(EP|CP|CF)$")
    areas: List[Area]

class CountryDataResponse(BaseModel):
    country: str
    assessment_year: int
    pillars: List[Pillar]

class CountryDataProcessor:
    def __init__(self, df: pd.DataFrame, country: str, assessment_year: int):
        self.df = df
        self.country = country.lower()
        self.assessment_year = assessment_year
        self.filtered_df = self.filter_data()
        
    def filter_data(self) -> pd.DataFrame:
        self.df['Assessment date'] = pd.to_datetime(self.df['Assessment date'], errors='coerce')
        mask = (
            (self.df['Country'].str.lower() == self.country) & 
            (self.df['Assessment date'].dt.year == self.assessment_year)
        )
        filtered_df = self.df[mask]
        
        if filtered_df.empty:
            raise HTTPException(status_code=404, detail="Data not found")
        
        return filtered_df.iloc[0]  # Return the first matching row
    
    def process_pillar(self, pillar: str) -> Pillar:
        areas = []
        area_dict: Dict[str, Dict] = {}
        pillar_cols = [col for col in self.filtered_df.index if f" {pillar}." in col]
        
        for col in pillar_cols:
            self.process_column(col, pillar, area_dict)
        
        for area_name, area_data in area_dict.items():
            areas.append(self.create_area(area_name, area_data))
        
        return Pillar(name=pillar, areas=areas)
    
    def process_column(self, col: str, pillar: str, area_dict: Dict[str, Dict]):
        parts = col.split()
        if len(parts) < 2:
            return
        
        col_type, col_path = parts[0], parts[1]
        path_parts = col_path.split('.')
        if len(path_parts) < 2:
            return
        
        area_num = path_parts[1]
        area_key = f"{pillar}.{area_num}"
        
        if area_key not in area_dict:
            area_dict[area_key] = {
                'assessment': str(self.filtered_df.get(f"area {pillar}.{area_num}", "")),
                'indicators': {}
            }
        
        if len(path_parts) >= 3 and col_type == 'indicator':
            indicator_num = path_parts[2]
            indicator_key = f"{area_key}.{indicator_num}"
            area_dict[area_key]['indicators'][indicator_key] = {
                'assessment': str(self.filtered_df[col]),
                'metrics': []
            }
        
        elif len(path_parts) >= 4 and col_type == 'metric':
            indicator_num = path_parts[2]
            metric_num = path_parts[3]
            indicator_key = f"{area_key}.{indicator_num}"
            if indicator_key in area_dict[area_key]['indicators']:
                metric = Metric(name=f"{indicator_key}.{metric_num}", value=str(self.filtered_df[col]))
                area_dict[area_key]['indicators'][indicator_key]['metrics'].append(metric)
    
    def create_area(self, area_name: str, area_data: Dict) -> Area:
        indicators = []
        for ind_name, ind_data in area_data['indicators'].items():
            metrics = ind_data['metrics'] if ind_data['metrics'] else []
            indicators.append(Indicator(name=ind_name, assessment=ind_data['assessment'], metrics=metrics))
        
        return Area(name=area_name, assessment=area_data['assessment'], indicators=indicators)
    
    def process_country_data(self) -> CountryDataResponse:
        pillars = [self.process_pillar(pillar) for pillar in ['EP', 'CP', 'CF']]
        return CountryDataResponse(country=self.country, assessment_year=self.assessment_year, pillars=pillars)

@app.get("/v1/country-data/{country}/{assessment_year}", response_model=CountryDataResponse)
async def get_country_data(country: str, assessment_year: int) -> CountryDataResponse:
    try:
        processor = CountryDataProcessor(df_assessments, country, assessment_year)
        return processor.process_country_data()
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
