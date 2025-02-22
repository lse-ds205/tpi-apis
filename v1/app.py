import os
import pandas as pd
from typing import List
from fastapi import FastAPI, HTTPException
from .models import CountryData
app = FastAPI()


df_assessments = pd.read_excel("./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx")
df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'])

@app.get("/v1/country-data/{country}/{assessment_year}", response_model=CountryData)
async def get_country_data(country: str, assessment_year: int) -> CountryData:

    selected_row = (
        (df_assessments["Country"] == country) &
        (df_assessments['Assessment date'].dt.year == assessment_year)
    )

    # Filter the data
    data = df_assessments[selected_row]

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

    # Grab just the first element (there should only be one anyway)
    # and return it as a dictionary
    output_dict = data.iloc[0].to_dict()

    output = CountryData(**output_dict)

    return output