import os
import pandas as pd


from fastapi import FastAPI
from .models import CountryData 

app = FastAPI()

# from .models import CountryData 

filepath = './data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx'
df_assessments = pd.read_excel(filepath)

df_assessments['Assessment date'] = pd.to_datetime(df_assessments['Assessment date'])
df_assessments['Publication date'] = pd.to_datetime(df_assessments['Publication date'])

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/v1/country-data/{country}/{assessment_year}")
async def get_country_data(country: str, assessment_year: int):

    #only include country, year row
    mask = (df_assessments['Assessment date'].dt.year == assessment_year) & (df_assessments['Country'] == country)
    filtered_df = df_assessments[mask]
    filtered_df = filtered_df.iloc[: , 1:10] #####test here to see if missing values cause errors

    #remove irrelevant columns
    filtered_df = filtered_df.drop(["Id", "Assessment date", "Publication date", "Country Id", "Country"], axis=1)

    #return results as a dictionary
    df_dict = filtered_df.iloc[0].to_dict()

    return {
        "message": f"You requested data for {country} in {assessment_year}",
        "data": df_dict
    }