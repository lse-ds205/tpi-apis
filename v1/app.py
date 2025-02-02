import os
import pandas as pd
from fastapi import FastAPI, HTTPException
import numpy as np

app = FastAPI()
filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx"
df_assessments = pd.read_excel(filepath, engine='openpyxl')

@app.get("/")
async def read_root():
    return {"Hello": "No"} 

@app.get("/v1/country-data/{country}/{assessment_year}")
async def get_country_data(country: str, assessment_year: int):
    try:
        # Convert dates
        df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
        df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'])
        
        # Case-insensitive country match
        mask = (
            (df_assessments['Country'].str.lower() == country.lower()) & 
            (df_assessments['Assessment date'].dt.year == assessment_year)
        )
        filtered_df = df_assessments[mask]
        
        # Check if any data exists
        if filtered_df.empty:
            raise HTTPException(status_code=404, detail="Data not found")
        
        # Column selection and cleaning
        filtered_df = filtered_df.iloc[:, 1:10].drop(
            columns=["Id", "Assessment date", "Publication date", "Country Id", "Country"],
            errors='ignore'  # Ignore if columns don't exist
        )
        
        # Convert to dict
        df_dict = filtered_df.iloc[0].to_dict()
        
        return {
            "message": f"You requested data for {country} in {assessment_year}",
            "data": df_dict
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))