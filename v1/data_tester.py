import os 
import pandas as pd 
from fastapi import FastAPI
from models import CountryData 

filepath =  '../data/TPI ASCOR data - 13012025/ASCOR_assessments_results.xlsx'

data = pd.read_excel(filepath)

country = 'Australia'
year_end = 2024
return_data_mask = (data['Country'] == country) & (data['Assessment date'].str[-4:] == str(year_end))
return_data_mask = (data['Country'] == country) & (data['Assessment date'].str[-4:] == str(year_end))
return_data = data[return_data_mask]

if return_data.empty:
    return f'Sorry the data you queried does not exist for {country} in {year_end}'

column_names = list(return_data.columns.values)

relevant_areas = list(filter(lambda x: x.startswith('area'), column_names))

return_dict = {}
for column in column_names:
    if column in relevant_areas:
        if pd.isna(return_data[column].iloc[0]):
            return_dict[column] = ''

        else:
            return_dict[column] = return_data[column].iloc[0]
return_dict['Country'] = 
print(return_dict)


