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

This entity stores data from the **ASCOR_assessments_results.xlsx** file. Each row in this file represents one response to one element (e.g EP.1.a or r EP.2.d) by one country, and is uniquely identified by a composite primary key of (assessment_id, code). Here the code refers the the response element and further information on each code can be found by joining this entity with assessment_elements based on the code. The assessment_id is a unique identifier for each full country assessment. However, because one assessment includes multiple element responses (each tagged by a code), a composite key is necessary. 

How **Source** and **Year** are extracted:
- In the original Excel file, each column contains year and response in the following structure *year indicator EP.1.a* and *source indicator EP.1.a*
- The year is extracted from the respective year XXX column (e.g., year indicator EP.1.a) only if present and not null.
- The source is taken from the matching source XXX column (e.g., source indicator EP.1.a) if available.

This structure allows the model to support:

- Multiple assessments per country (over time).
- Multiple responses per assessment.
- Linkage to both the indicator and country context via foreign keys.
- The year and source fields are optional but included when available, to give further metadata about the timing and provenance of the response.

Once again, null values are permitted in non-key attributes to allow for incomplete submissions or ongoing data collection.

**Data Types:**
```
assessment_id        INT NOT NULL (PK part)  
code                 VARCHAR NOT NULL (PK part, FK to assessment_elements.code)  
country_name         VARCHAR NOT NULL (FK to country.country_name)  
response             VARCHAR  
assessment_date      DATE  
publication_date     DATE  
source               VARCHAR  
year                 INT  
```

**Entry Example:**
```
assessment_id        235  
code                 EP.1.a  
country_name         Angola  
response             Yes  
assessment_date      2024-10-15  
publication_date     2024-12-01  
source               https://1p5ndc-pathways.climateanalytics.org/
year                 2023  
```
#### assessment_elements

This entity stores metadata from the **ASCOR_indicators.xlsx file**, defining each individual indicator, area, or metric used in ASCOR assessments. Each entry corresponds to a unique assessment element and is identified by a code, such as EP.1.a, which acts as the primary key. This table serves as a reference for interpreting codes in the assessment_results entity and enables consistent definitions for each element used across assessments. This also means future codes can be easily added in the future. 

**Data Types:**
```
code                 VARCHAR NOT NULL (PK)  
text                 VARCHAR 
response_type        VARCHAR 
type                 VARCHAR 
```

**Example assessment_elements entity:**
```
code                 EP.1.a  
text                 Has the country improved its emissions profile over the past 5 years?
response_type        Yes/No  
type                 indicator  
```

### Assessment Trends 

The Excel file **ASCOR_assessments_results_trends_pathways.xlsx** contains a mix of structurally different data types:  trend metadata, single-value metrics, and yearly time series projections. These are all stored into a single flat file. Following the best practices in relational database design (especially normalization and separation of concerns), the data was split into three distinct but related entities described below.

#### assessment_trends 

This entity stores data from the **ASCOR_assessments_results_trends_pathways.xlsx** file. This table stores general metadata about each emissions trend and each record corresponds to one emissions trend assessment (row in the file). A composite primary key on (trend_id, country_name) is used because the id column alone is reused across countries and their are multiple rows for each country. 

**Data Type:**
```
trend_id             INT NOT NULL (PK part)  
country_name         VARCHAR NOT NULL (PK part, FK to country.country_name)  
emissions_metric     VARCHAR  
emissions_boundary   VARCHAR  
units                VARCHAR  
assessment_date      DATE  
publication_date     DATE  
last_historical_year INT  
```
**Example Entry:**
```
trend_id             291  
country_name         Australia  
emissions_metric     Intensity per GDP-PPP  
emissions_boundary   Production - excluding LULUCF  
units                tCO₂e/Million US$  
assessment_date      2023-10-31  
publication_date     2023-12-01  
last_historical_year 2022  
```

##### trend_values 

This entity stores specific metrics and performance change summaries of the assessment trends.

To organize this data:

- Metric values such as metric_ep1.a.i are cleaned (e.g., converting "No data" to NULL).
- Change values (e.g., metric_ep1.a.ii_1-year) originally included percent signs or the string "Not applicable" and are cleaned into a consistent format (as strings or nulls).

The same composite key (trend_id, country_name) is used, and a foreign key constraint links it to assessment_trends.

**Data Types:**
```
trend_id                 INT NOT NULL (PK part, FK to assessment_trends.trend_id)  
country_name             VARCHAR NOT NULL (PK part, FK to assessment_trends.country_name)  
metric_ep1_a_i           FLOAT  
source_metric_ep1_a_i    VARCHAR  
year_metric_ep1_a_i      INT  
metric_ep1_a_ii_1_year   VARCHAR  
metric_ep1_a_ii_3_year   VARCHAR  
metric_ep1_a_ii_5_year   VARCHAR  
```

**Example Entry:**
```
trend_id                 291  
country_name             Australia  
metric_ep1_a_i           328.04  
source_metric_ep1_a_i    NULL  
year_metric_ep1_a_i      NULL  
metric_ep1_a_ii_1_year   -11.20  
metric_ep1_a_ii_3_year   -8.20  
metric_ep1_a_ii_5_year   -7.00  
```


##### values_per_year

This entity stores the projected emissions values for each year for each country and trend. In the raw Excel data, these values were stored as separate columns for each year, in a wide format, but to improve flexibility and reduce redundancy, these columns are normalized into a long format. This normalization allows easy updates as future years are added and cleaner handling of missing data as missing data not stored.

The foreign key (trend_id, country_name) references the trend_values table to maintain relational consistency.

**Data Types:**
```
year                    INT NOT NULL  
value                   FLOAT NOT NULL  
trend_id                INT NOT NULL (FK to trend_values.trend_id)  
country_name            VARCHAR NOT NULL (FK to trend_values.country_name)  
```

**Example Entry:**
```
year        2005  
value       805.91  
trend_id    291  
country_name Australia  
```


