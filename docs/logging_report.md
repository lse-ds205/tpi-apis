**Title**: [ALL] Add comprehensive logging system across API

**Reviewer**: @jonjoncardoso


## Major changes
- I have added a logging system for the API. 
- I did this by creating a file called log_config.py. The "application log can include your own messages integrated with messages from third-party modules" according to the official python documentation. 
- I used Logging Middleware, a tool that is a custom middleware for FastAPI
- It helps log all requests and responses including status codes, content, methods, paths, etc: **source** : https://medium.com/@dhavalsavalia/fastapi-logging-middleware-logging-requests-and-responses-with-ease-and-style-201b9aa4001a
- [TIME][LEVEL] MODULE_NAME: MESSAGE
- it also los messages that include the the original module for an easy source identification
- I also implemented a tpi_api.log file that stores the logs and is stored longterm. 
-   Here it is ![Logging System](../tpi_apis/images/logging.png)
- - Here it is:
    ![Logging System](/Users/rishisiddharth/Desktop/LSE_2024_2045/classes/DS205W/Summative1_logging/tpi_apis/images/logging.png) (I did it twice bcos neither of them are showing up jsut in case I will include a copy and pasate of the output)

-     [2025-04-10 19:47:52][INFO] routes.ascor_routes: Successfully loaded data from /Users/rishisiddharth/Desktop/LSE_2024_2045/classes/DS205W/Summative1_logging/tpi_apis/data/TPI_ASCOR_data_13012025/ASCOR_assessments_results.xlsx
[2025-04-10 19:47:57][INFO] main: START Request: GET /v1/companies
[2025-04-10 19:47:57][INFO] main: END Request: GET /v1/companies - Status: 404 - Time: 0.0010s
[2025-04-10 19:48:01][INFO] routes.ascor_routes: Attempting to load data from /Users/rishisiddharth/Desktop/LSE_2024_2045/classes/DS205W/Summative1_logging/tpi_apis/data/TPI_ASCOR_data_13012025/ASCOR_assessments_results.xlsx
[2025-04-10 19:48:01][INFO] routes.ascor_routes: Successfully loaded data from /Users/rishisiddharth/Desktop/LSE_2024_2045/classes/DS205W/Summative1_logging/tpi_apis/data/TPI_ASCOR_data_13012025/ASCOR_assessments_results.xlsx
[2025-04-10 19:48:21][INFO] routes.ascor_routes: Attempting to load data from /Users/rishisiddharth/Desktop/LSE_2024_2045/classes/DS205W/Summative1_logging/tpi_apis/data/TPI_ASCOR_data_13012025/ASCOR_assessments_results.xlsx
[2025-04-10 19:48:21][INFO] routes.ascor_routes: Successfully loaded data from /Users/rishisiddharth/Desktop/LSE_2024_2045/classes/DS205W/Summative1_logging/tpi_apis/data/TPI_ASCOR_data_13012025/ASCOR_assessments_results.xlsx
[2025-04-10 19:48:25][INFO] main: START Request: GET /v1/companies
[2025-04-10 19:48:25][INFO] main: END Request: GET /v1/companies - Status: 307 - Time: 0.0033s
[2025-04-10 19:48:25][INFO] main: START Request: GET /v1/companies/
[2025-04-10 19:48:25][INFO] main: Fetching list of sample companies
[2025-04-10 19:48:25][INFO] main: Successfully retrieved 5 sample companies
[2025-04-10 19:48:25][INFO] main: END Request: GET /v1/companies/ - Status: 200 - Time: 0.0023s
[2025-04-10 19:48:59][INFO] main: START Request: GET /v1/ascor/countries
[2025-04-10 19:48:59][INFO] routes.ascor_routes: Getting list of all countries
[2025-04-10 19:48:59][INFO] routes.ascor_routes: Found 70 countries in the dataset
[2025-04-10 19:48:59][INFO] main: END Request: GET /v1/ascor/countries - Status: 200 - Time: 0.0122s
[2025-04-10 19:49:09][INFO] main: START Request: GET /v1/ascor/countries
[2025-04-10 19:49:09][INFO] routes.ascor_routes: Getting list of all countries
[2025-04-10 19:49:09][INFO] routes.ascor_routes: Found 70 countries in the dataset
[2025-04-10 19:49:09][INFO] main: END Request: GET /v1/ascor/countries - Status: 200 - Time: 0.0030s




## How to validate

To confirm that this P›R works as expected:

1. Clone this branch
2. <instructions on how to test the changes>
