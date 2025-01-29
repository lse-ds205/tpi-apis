import os
import pandas as pd
from fastapi import FastAPI, HTTPException


# No need to set up anything else if running this on local machine
app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Load the data
filepath = "./data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx"
df_assessments = pd.read_excel(filepath)

# Convert the date columns to datetime type so we can filter by year later
df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'])

@app.get("/v1/country-data/{country}/{assessment_year}")
async def get_country_data(country: str, assessment_year: int):
   
    country_assessment = df_assessments[df_assessments['Country']==country]
    if len(country_assessment) == 0:
        return HTTPException(status_code=404, detail="Country not Found")
    

    country_year_assessment = country_assessment[country_assessment['Assessment date'].dt.year==assessment_year]
    if len(country_year_assessment) == 0:
        return HTTPException(status_code=404, detail=f"Year not Found")


    if len(country_year_assessment)>0:
        country_year_assessment = country_year_assessment.head(1)
    else:
        return HTTPException(status_code=404, detail=f"Country and Year combination not found")


    column_renames = {'area EP.1': 'EP.1',
                'area EP.2': 'EP.2',
                'area EP.3': 'EP.3',
                'area CP.1': 'CP.1',
                'area CP.2': 'CP.2',
                'area CP.3': 'CP.3',
                'area CP.4': 'CP.4',
                'area CP.5': 'CP.5',
                'area CP.6': 'CP.6',
                'area CF.1': 'CF.1',
                'area CF.2': 'CF.2',
                'area CF.3': 'CF.3',
                'area CF.4': 'CF.4',
                'Country': 'country',
                'Assessment date': 'assessment_year'}
    country_year_assessment = country_year_assessment[column_renames.keys()].rename(columns=column_renames).fillna("")
    country_year_assessment['assessment_year'] = country_year_assessment['assessment_year'].dt.year  
    return country_year_assessment.to_dict(orient='records')[0]
