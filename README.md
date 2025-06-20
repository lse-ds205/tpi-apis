## TPI Assessment API 
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-15-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
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
## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/ColemanCochran"><img src="https://avatars.githubusercontent.com/u/123137609?v=4?s=100" width="100px;" alt="Coleman Cochran"/><br /><sub><b>Coleman Cochran</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=ColemanCochran" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/GAURVI27"><img src="https://avatars.githubusercontent.com/u/147526356?v=4?s=100" width="100px;" alt="Urvi Gaur"/><br /><sub><b>Urvi Gaur</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=GAURVI27" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/deyavuz"><img src="https://avatars.githubusercontent.com/u/185213861?v=4?s=100" width="100px;" alt="Defne"/><br /><sub><b>Defne</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=deyavuz" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/billyblue1"><img src="https://avatars.githubusercontent.com/u/114443347?v=4?s=100" width="100px;" alt="billyblue1"/><br /><sub><b>billyblue1</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=billyblue1" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/krishyb123"><img src="https://avatars.githubusercontent.com/u/123502998?v=4?s=100" width="100px;" alt="Krish Bhatia"/><br /><sub><b>Krish Bhatia</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=krishyb123" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Yiwen-x"><img src="https://avatars.githubusercontent.com/u/147771778?v=4?s=100" width="100px;" alt="Yiwen-x"/><br /><sub><b>Yiwen-x</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=Yiwen-x" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/DylanButcher"><img src="https://avatars.githubusercontent.com/u/43067126?v=4?s=100" width="100px;" alt="DylanButcher"/><br /><sub><b>DylanButcher</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=DylanButcher" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/alexgabriellafaith"><img src="https://avatars.githubusercontent.com/u/146425549?v=4?s=100" width="100px;" alt="alexgabriellafaith"/><br /><sub><b>alexgabriellafaith</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=alexgabriellafaith" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/MaddoxLeigh"><img src="https://avatars.githubusercontent.com/u/147736410?v=4?s=100" width="100px;" alt="MaddoxLeigh"/><br /><sub><b>MaddoxLeigh</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=MaddoxLeigh" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/BilalNHashim"><img src="https://avatars.githubusercontent.com/u/153951896?v=4?s=100" width="100px;" alt="BilalNHashim"/><br /><sub><b>BilalNHashim</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=BilalNHashim" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Jessie-Fung"><img src="https://avatars.githubusercontent.com/u/147734161?v=4?s=100" width="100px;" alt="Jessie Fung"/><br /><sub><b>Jessie Fung</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=Jessie-Fung" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/datascraper758"><img src="https://avatars.githubusercontent.com/u/183512656?v=4?s=100" width="100px;" alt="datascraper758"/><br /><sub><b>datascraper758</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=datascraper758" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Nayrbnat"><img src="https://avatars.githubusercontent.com/u/97864681?v=4?s=100" width="100px;" alt="Nayrbnat"/><br /><sub><b>Nayrbnat</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=Nayrbnat" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/felix-brown"><img src="https://avatars.githubusercontent.com/u/107852540?v=4?s=100" width="100px;" alt="Felix Brown"/><br /><sub><b>Felix Brown</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/commits?author=felix-brown" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/tz1211"><img src="https://avatars.githubusercontent.com/u/114442618?v=4?s=100" width="100px;" alt="Terry Zhou"/><br /><sub><b>Terry Zhou</b></sub></a><br /><a href="https://github.com/ds205/tpi-apis/pulls?q=is%3Apr+reviewed-by%3Atz1211" title="Reviewed Pull Requests">👀</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!