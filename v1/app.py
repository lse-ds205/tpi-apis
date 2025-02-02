import os
import pandas as pd
from fastapi import FastAPI, HTTPException
import numpy as np
from .models import CountryData 

app = FastAPI()
filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx"
df_assessments = pd.read_excel(filepath, engine='openpyxl')

@app.get("/")
async def read_root():
    return {"Hello": "Yes"} 

@app.get("/v1/country-data/{country}/{assessment_year}", response_model=CountryData)
async def get_country_data(country: str, assessment_year: int) -> CountryData:
    try:        
        # Convert dates
        df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
        # Filter data
        mask = (
            (df_assessments['Country'].str.lower() == country.lower()) & 
            (df_assessments['Assessment date'].dt.year == assessment_year)
        )
        filtered_df = df_assessments[mask]
        
        if filtered_df.empty:
            raise HTTPException(status_code=404, detail="Data not found")
        # Selected and filter columns
        area_columns = [col for col in df_assessments.columns if col.startswith("area")]
        filtered_df = filtered_df[area_columns]
        filtered_df = filtered_df.fillna('')
        # Clean and transform data
        #Rename columns
        filtered_df['country'] = country
        filtered_df['assessment_year'] = assessment_year
        
        remap_area_column_names = {
            col: col.replace('area ', '').replace('.', '_')
            for col in area_columns
        }

        filtered_df = filtered_df.rename(columns=remap_area_column_names)
        data = filtered_df.iloc[0]
        EP = {col: data[col] for col in data.index if col.startswith("EP")}
        CP = {col: data[col] for col in data.index if col.startswith("CP")}
        CF = {col: data[col] for col in data.index if col.startswith("CF")}
        output_dict = {
            "country": country,
            "assessment_year": assessment_year,
            "EP": {"indicators": EP},
            "CP": {"indicators": CP},
            "CF": {"indicators": CF}
        } 

        output = CountryData(**output_dict)
        return output
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    