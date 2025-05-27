# TPI Assessment API — Overview

Welcome to the official documentation site for the **TPI Assessment API** — a FastAPI-based application that enables programmatic access to sovereign and corporate climate assessments developed by the [Transition Pathway Initiative Centre](https://www.transitionpathwayinitiative.org/). This landing page will help you get oriented quickly and direct you to the resources you need.

---

## What This API Does

The TPI Assessment API allows developers, researchers, and data analysts to retrieve, compare, and analyze data from major TPI assessment frameworks:

- **ASCOR**: Assessing Sovereign Climate-related Opportunities and Risks
- **Carbon Performance (CP)**
- **Management Quality (MQ)**
- **Corporate Assessments**

Whether you're building dashboards, conducting climate-financial research, or integrating ESG data into applications, this API helps you fetch structured climate data for sovereigns and companies alike.

---

## Use Cases

You can use the API to:
- Retrieve ASCOR scores for a country
- Compare a company’s performance across assessment cycles
- Query MQ or CP data by sector or region
- Build automated pipelines for ESG data updates
- Integrate with dashboards (e.g., Power BI, Tableau)

---

## How It Works (High-Level Flow)

1. **Choose your request type** (e.g. ASCOR, MQ, CP, Company)  
2. **Send a GET request** to the appropriate endpoint  
3. **Receive a structured JSON response** with normalized, up-to-date assessment data  

---

## Key Features

- RESTful API built with FastAPI  
- Sovereign & corporate climate assessments (ASCOR, CP, MQ)  
- Sector & company filtering  
- Cycle-by-cycle comparisons  
- Built-in pagination and efficient querying  
- Interactive API docs in [Documentation](Overview_Documentation.md)  
- Robust error handling and validation with Pydantic  

---

See [Tutorial](Tutorial.md) to understand how to use the api
