"""Tests for ascor-api endpoints.

This module contains automated tests to validate the functionality of our API endpoints
defined in v1/app.py. It uses FastAPI's TestClient for making HTTP requests and pytest
as the testing framework.

Current tests:
- Country data endpoint (/v1/country-data/{country_code}/{year})

Author: @jonjoncardoso
"""
from fastapi.testclient import TestClient


def test_get_country_data(client):
    """Test endpoint /v1/country-data/{country_code}/{year}.
    This test verifies if the endpoint returns correct response for country data retrieval.
    The test uses Great Britain (GBR) as country code and 2023 as the year.
    Expected behavior:
    - Returns HTTP 200 status code for successful request
    """

    response = client.get("/v1/country-data/Italy/2023")
    assert response.status_code == 200