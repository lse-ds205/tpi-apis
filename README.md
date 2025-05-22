## TPI Assessment API 

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.7-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A FastAPI-based application to retrieve, process, and compare data from the [Transition Pathway Initiative Centre](https://www.transitionpathwayinitiative.org/) (TPI). It provides a fully functional API for serving data from the following assessment frameworks developed by the TPI Centre: 

* [ASCOR](https://www.transitionpathwayinitiative.org/ascor)[^1]
* [Carbon Performance and Management Quality](https://www.transitionpathwayinitiative.org/corporates)

**A partnership:**

<div style="display: flex; justify-content: top; vertical-align: middle; align-items: center; gap: 2em; margin: 2em 0;">
<a href="https://lse.ac.uk/dsi"><img src="./icons/LSE_DSI.png" alt="LSE Data Science Institute" role="presentation" style="object-fit: contain;height:3em;margin-right:2em"/></a>

<a href="https://www.transitionpathwayinitiative.org/"><img src="./icons/TPI.png" alt="Transition Pathway Initiative" role="presentation" style="object-fit: contain;height:3em;"/></a>

<a href="https://lse-dsi.github.io/DS205" style="align-items:middle"><img src="./icons/DS205_2024_25_icon_200px.png" alt="DS205 Students" role="presentation" style="object-fit: contain;height:3em;"><span style="display:block;float:right">DS205 students <br>(Winter Term 2024/25)</span></a>
</div>

[^1]: **ASCOR** stands for "**A**ssessing **S**overeign **C**limate-related **O**pportunities and **R**isks". You can read more about their methodology [here](https://www.transitionpathwayinitiative.org/publications/2024-ascor-framework-methodology-note-version-1-1).

This project is led by Dr [Jon Cardoso-Silva](https://jonjoncardoso.github.io), developed together with students enrolled in the LSE Data Science Institute's <img src="./icons/DS205_2024_25_icon_200px.png" alt="Image Created with AI Designer" role="presentation" style="object-fit: cover;width:1em;height:1em;vertical-align: middle;padding-bottom: 0.2em;"/> [DS205 course](https://lse-dsi.github.io/DS205) (Winter Term 2024/2025) and is a collaboration with Sylvan Lutz from the [Transition Pathway Initiative Centre](https://www.transitionpathwayinitiative.org/) (TPI Centre). 

The application is structured to meet good standards for data validation, error handling, and robust documentation, ensuring it can be easily reviewed and extended.

## Table of Contents
1. [Guiding Architectural Design Principles](#features)
2. [Directory Structure](#directory-structure)
3. [Prerequisites and Installation](#prerequisites-and-installation)
4. [Running the Application](#running-the-application)
5. [Usage and API Endpoints](#usage-and-api-endpoints)
6. 📟 [Contact Us](#-contact-us)

## Guiding Architectural Design Principles

We aim to develop a system that can efficiently process and serve assessments of sovereign entities and publicly listed companies, ensuring ease of use, scalability, and accuracy. The key functionalities and capabilities of the API include:

- **Automated Data Loading**: The application dynamically selects the latest available dataset without requiring manual updates.
- **FastAPI-based RESTful API**: Provides structured endpoints for retrieving ASCOR, Management Quality (MQ) and Carbon Performance (CP) assessments.
- **Pagination Support**: Efficiently handles large datasets with built-in pagination for retrieving assessment records.
- **Company Performance Comparison**: Enables comparisons between different assessment cycles for a given company.
- **Sector-Based Filtering**: Fetches assessment trends for companies within a specific sector.
- **Data Normalisation**: Standardizes column names, handles missing values, and ensures consistent processing of company data.
- **Error Handling & Validation**: Implements structured validation using [Pydantic models](https://docs.pydantic.dev/latest/) and raises appropriate HTTP exceptions.
- **Efficient Querying**: Optimized pandas operations for sorting, grouping, and filtering large datasets.
- **Modular Codebase**: Clean, well-structured code organised into distinct modules for easy maintenance and scalability.

## Directory Structure

The project follows a structured directory layout to ensure modularity, maintainability, and ease of expansion. The separation of concerns allows for clear organisation of API routes, data management, and application logic.

```bash
tpi_api/
tpi_api/
├── venv/                 # Virtual environment
├── data/                 # CSV datasets used for assessments
├── routes/               # FastAPI route handlers
│   ├── __init__.py       # Makes 'routes' a Python package for imports
│   ├── company_routes.py # Company assessments endpoints
│   ├── mq_routes.py      # Management Quality endpoints
│   └── cp_routes.py      # Carbon Performance endpoints
├── tests/*               # Unit tests for route handlers and utilities
├── schemas.py            # Pydantic models for data validation
├── main.py               # Application entry point
├── requirements.txt      # Project dependencies
└── README.md             # Documentation
```

## Prerequisites and Installation

Before installing and running the application, ensure your system meets the following requirements:

- **Python 3.10 or higher**

  Check version with `python --version` or `python3 --version`.

- **pip (Python package manager)**

  Ensure it is installed with `pip --version`

To install the dependencies for this project, run the code below in the terminal:

**Setting up a Virtual Environment**

It is always a good idea to have a separate environment for each Python project. We recommend using the following commands to set up a virtual environment for this project:

  ```bash
  python -m venv tpi-env
  ```

  You only need to run this command once to create the virtual environment.

Then, activate the virtual environment:

  ```bash
  # If on Mac or Linux (e.g. Nuvolos)
  source tpi-env/bin/activate

  # If on Windows
  tpi-env\Scripts\activate
  ```

  ⚠️ **IMPORTANT:** You need to (re-)activate the virtual environment every time you work on this project.

Finally, install the dependencies:

  ```bash
  pip install -r requirements.txt
  ```

  You only need to run this once, or whenever the `requirements.txt` file is updated.

## Set Up Environment Variables

Create a `.env` file in the root directory of the project. This file will store your environment variables. For now, the `.env` should only contain a single line:

```bash
SECRET_KEY=somerandomstringherefornow
```

This secret key is used in the few POST endpoints we have on the API. It is a placeholder for now, the whole POST endpoints are experimental, so any string will do.

## Running the Application

After installing dependencies and activating your virtual environment, navigate to your project's root directory (the place where your `main.py` file is located) and execute the following command in your terminal:

  ```bash
  uvicorn main:app --reload
  ```

  The `uvicorn` command launches the FastAPI application, while the `--reload` parameter here enables automatic reload, ensuring that the server reflects any changes in real-time, significantly speeding up the development cycle. 

The terminal will indicate that the server is running and the API can be accessed via the following endpoints: 

- **Base URL**: http://127.0.0.1:8000/
- **Interactive API documentation (Swagger UI)**: http://127.0.0.1:8000/docs

You can stop the Uvicorn server at anytime by pressing `CTRL + C` in the terminal.

## Usage and API Endpoints

(WIP)

## 📟 Contact Us

If you have any questions about a particular functionality or need assistance with the codebase, post a message to the [Discussions](https://github.com/lse-ds205/tpi-apis/discussions) section of this repository.