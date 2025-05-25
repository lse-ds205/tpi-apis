# SQL Database Justification 

This section is the justification and explanation of the ASCOR and TPI databases. ChatGBT was used to enhance writing in this report, it did not come up with ideas but helped me improve my writing. I wrote detailed bullet points of ideas for each sections/simple paragraphs and had chatgbt fix grammer and flow of ideas.

## ASCOR_API Database 

The **ascor_api** database is used to store the files from the *data/TPI_ASCOR_data_13012025* folder in the *TPI_API* repository. 

### ERD Diagram

![AScor Logo](icons/ascor_ERD.png)

#### Relationships Constraints

Here in the modelling stage, I chose to use optional relationships in cases where the presence of related data could not be guaranteed. For example, not every country in the ASCOR dataset currently has benchmark or trend. By allowing these relationships to be optional, the schema remains flexible which is important for future data expansion, allowing countries to be incrementally updated as more information becomes available.

***HAS_BENCHMARK:*** Each country can optionally have benchmark and each country cna have many benchmarks. Each benchmark must be connect to one country maximum. 

***HAS_VALUE:*** Each benchmark value (this is a pair of value and year) is linked to exactly one benchmark. Each benchmark can optionally have a benchmark value (this accounts for missing data) and can also have many benchmark values, most countries have years 2023-2030.

***HAS_ASSESSMENT:*** Each assessment is linked to exactly one country and each country can optionally have an assessment (avoiding rigid schema assumptions here) and can have maximum one assessment according to the file.

***RESULT_HAS_ELEMENT:*** Each assessment result (e.g metric) has exactly one assessment element (e.g. EP.1.a.i). Each assessment element can have multiple assessment results, for example the assessment element EP.1.a.i is used many times for each country.

***HAS_TRENDS:*** Each country can optionally have trends recorded and can also have multiple trends recorded, such as for different emmissions metrics. Each trend recorded is linked to exactly one country.

***TREND_HAS_VALUE:*** Each trend often has multiple values and each trend value must be linked to exactly one assessment trend.

***VALUES_PER_YEAR:*** Each trend value has multiple values per year, recorded from 2005 to 2030 for most countries. Each trend value pair (such as 29.88 for 2007) musyt be linked to exactly one trend value.

### Relational Schema 

![AScor Logo](icons/ascor_RS.png)

### Overview of Structure and Design Choices

The following is an overview of the design choices made in response the the ASCOR data structure to ensure completeness, normalization, extensibility and a future proofed design.

First, **all non primary and foriegn key attributes were made nullable** as the ASCOR data files contains frequent missing entries (e.g., countries with partial trend data, missing source URLs). Allowing null values for all attributes was important as it meant partial values for some country assessments would not prevent this row being added to the database. This is especially important for a strong future-proof foundation to ensure all new data gets added to the database despite missingness.

Second, the **'No data' values in rows were turned into NULL values** so that the columns could be normalised into the correct data type. For example, the column *metric_ep1_a_i* in the ASCOR trends file held integer values, however the 'No data' entries prevented this being treated as the correct data type. 

Third, **primary and foreign keys were chosen based on identifiers that were consistently present** across files and are unlikely to change in future data releases, making them ideal anchors for long-term consistency. Such as benchmark_id, assessment_id, and country_name.

Fourth, in consideration of future data, the **schema avoids rigid design choices**. For example, assessment_elements allows for the addition of new assessment codes; value_per_year supports emissions trajectories through 2030 and beyond; trend_values can be expanded with new metrics as ASCOR's methodology evolves.

### Future-Proofing Considerations 

XXXXX


### Entities and Attributes 

#### Benchmarks

This entity stores data from the **ASCOR_benchmarks.xlsx** file. This file uses the id column in the excel file as the PK as this is unique for every country and country could not be used as there was multiple benchmarks for each country. All attributes are nullable to ensure that missing data does not prevent data being added. The logic for the initial benchmark entity is straightforward, as the attributes directly link to the names of the columns in the files and each country can have multiple benchmarks, uniquely defined by a combination of benchmark_id and country_name.

**Data types:**
```
benchmark_id         INT NOT NULL (PK)  
publication_date     DATE 
emissions_metric     VARCHAR 
emissions_boundary   VARCHAR 
units                VARCHAR
benchmark_type       VARCHAR 
country_name         VARCHAR NOT NULL (FK to country.country_name)  
```

**Example benchmark entity:**
```
benchmark_id         96  
country_name         Angola  
publication_date     2024-11-01  
emissions_metric     Absolute  
emissions_boundary   Production - excluding LULUCF  
units                MtCO₂e  
benchmark_type       National 1.5C benchmark  
```

##### benchmark_values

This entity holds the year/value pairs for each country benchmark. Instead of using a wide format, where the benchmarks table would include separate columns for each year (e.g., 2023, 2024, ..., 2030), a separate normalized table (benchmark_values) is used. This is advantageous because: 
- It supports flexibility as future years can be added without altering the table schema.
- It also avoids sparse data as  years with no values aren't stored as empty columns.
- It maintains relational integrity and reduces redundancy by linking to the benchmarks table.

Moreover, to accurately model this one-to-many relationship, where each benchmark can have one value per year, the benchmark_values table uses a composite primary key on (benchmark_id, year).

The year attribute is derived from the column name in the original Excel file and must not be null, as it's logically impossible for a benchmark value to lack a corresponding year. Moreover, the value must also not be null — null values are excluded during data transformation to avoid storing meaningless or incomplete records.
**Data Types:**
```
benchmark_id         INT NOT NULL (PK part, FK to benchmarks.benchmark_id)  
year                 INT NOT NULL (PK part)  
value                FLOAT NOT NULL  
```

**Example Entry:**
```
benchmark_id         96
year                 2025
value                20.09  
```
#### country 

The country entities are used to store data in the **ASCOR_countries.xlsx** file. Here, each country has one entry, therefore country was used as the PK. An alternative approach would have been to create a composite primary key between the country name and the id (first column), however, after further inspection of the data I realised these ids were not consistent across file. Therefore, introducing id as a composite primary key would have been inefficient for joining tables together, given the ids across files for countries do not match up. 

Once again, all attributes can be null, apart from the PK, to ensure missing data does not result in country not being added to the dataset.

**Data Types:**
```
country_name         VARCHAR NOT NULL (PK)  
iso                  VARCHAR  
region               VARCHAR
bank_lending_group   VARCHAR 
IMF_category         VARCHAR 
UN_party_type        VARCHAR 
```
**Example county entity:**
```
country_name         Angola  
iso                  AGO  
region               Sub-Saharan Africa  
bank_lending_group   Lower-middle-income  
IMF_category         Emerging market economies  
UN_party_type        Non-Annex I and Non-Annex II  
```

#### assessment_results 

This entity stores 
#### assessment_elements


#### assessment_trends 

##### trend_values 

##### values_per_year





