"""Tests for ascor-api endpoints.

This module contains automated tests to validate the functionality of our API endpoints
defined in v1/app.py. It uses FastAPI's TestClient for making HTTP requests and pytest
as the testing framework.

This module relies on the following fixtures defined in conftest.py:

- client: A FastAPI TestClient instance that allows us to emulate sending HTTP requests to
    our FastAPI application.

Current tests:
- Country data endpoint (/v1/country-data/{country_code}/{year})

Author: @jonjoncardoso
"""

import pycountry
import pytest 
import warnings

INSTRUCTIONS_URL = "https://moodle.lse.ac.uk/mod/page/view.php?id=1563098#here-comes-a-challenge-1-hour--"

"""
TESTS IF THE API RETURNS THE EXPECTED STATUS CODES
"""

def test_get_valid_country_data(client, df_assessments):
    """Test GET endpoint /v1/country-data/{country}/{year}.

    Tests if the endpoint returns HTTP 200 status code for ALL valid country-year combinations.
    Using assessment data from a DataFrame fixture, iterates through valid country and year
    combinations and verifies each request returns successful response.

    The two fixtures (client, df_assessments) are defined in conftest.py and are 
    automatically injected into this test function by pytest.

    Args:
        client: TestClient fixture for making HTTP requests to the FastAPI application
        df_assessments: DataFrame fixture containing the ASCOR assessment data
    Returns:
        None
    """

    valid_requests = (
        df_assessments[['Country', 'Assessment date']]
        .assign(Year=lambda x: x['Assessment date'].dt.year)
        .drop(columns='Assessment date')
    )

    print(valid_requests)

    for country, year in zip(valid_requests["Country"], valid_requests["Year"]):
        response = client.get(f"/v1/country-data/{country}/{year}")
        msg = (
            f"Failed for {country} and {year}. "
            f"Expected 200 status code for a valid country-year combination."
        )
        assert response.status_code == 200, msg

def test_get_country_data_not_assessed(client, df_assessments):
    """Test GET endpoint /v1/country-data/{country}/{year} for a country that has not been assessed.

    Tests if the endpoint returns HTTP 404 status code for a country that has not been assessed by ASCOR.
    Using assessment data from a DataFrame fixture, verifies that the API returns 404 status code
    for a country that has not been assessed.

    The two fixtures (client, df_assessments) are defined in conftest.py and are 
    automatically injected into this test function by pytest.

    Args:
        client: TestClient fixture for making HTTP requests to the FastAPI application
        df_assessments: DataFrame fixture containing the ASCOR assessment data
    Returns:
        None
    """

    # Get a list of all countries that have been assessed
    assessed_countries = df_assessments["Country"].unique()

    # Get a list of all countries
    all_countries = [country.name for country in pycountry.countries]

    # Find a country that has not been assessed
    not_assessed = [country for country in all_countries if country not in assessed_countries]

    for country in not_assessed:
        response = client.get(f"/v1/country-data/{country}/2024")
        msg = (
            f"Failed for {country}. "
            f"Expected 404 status code for a country that has not been assessed."
        )
        assert response.status_code == 404, msg

"""
TESTS IF THE API RETURNS THE EXPECTED JSON RESPONSES
"""

def test_get_a_json(client, df_assessments):
    """Test GET endpoint /v1/country-data/{country}/{year} for valid country-year combinations.

    Tests if the endpoint returns a valid JSON response for ALL valid country-year combinations.
    Using assessment data from a DataFrame fixture, iterates through valid country and year
    combinations and verifies each request returns a JSON response.

    The two fixtures (client, df_assessments) are defined in conftest.py and are 
    automatically injected into this test function by pytest.

    Args:
        client: TestClient fixture for making HTTP requests to the FastAPI application
        df_assessments: DataFrame fixture containing the ASCOR assessment data
    Returns:
        None
    """

    valid_requests = (
        df_assessments[['Country', 'Assessment date']]
        .assign(Year=lambda x: x['Assessment date'].dt.year)
        .drop(columns='Assessment date')
    )

    for country, year in zip(valid_requests["Country"], valid_requests["Year"]):
        response = client.get(f"/v1/country-data/{country}/{year}")
        msg = (
            f"Failed for {country} and {year}. "
            f"Expected a JSON response for a valid country-year combination."
        )
        assert response.headers["content-type"] == "application/json", msg

# Now let's check if the JSON response has the expected structure
def test_get_country_data_structure(client, df_assessments):
    """Test GET endpoint /v1/country-data/{country}/{year} for valid country-year combinations.

    Tests if the endpoint returns a JSON response with the expected structure for ALL valid country-year combinations.
    Using assessment data from a DataFrame fixture, iterates through valid country and year
    combinations and verifies each request returns a JSON response with the expected structure.

    The two fixtures (client, df_assessments) are defined in conftest.py and are 
    automatically injected into this test function by pytest.

    Args:
        client: TestClient fixture for making HTTP requests to the FastAPI application
        df_assessments: DataFrame fixture containing the ASCOR assessment data
    Returns:
        None
    """

    valid_requests = (
        df_assessments[['Country', 'Assessment date']]
        .assign(Year=lambda x: x['Assessment date'].dt.year)
        .drop(columns='Assessment date')
    )

    # As a tester, I have to pretend I don't know anything about pydantic models
    for country, year in zip(valid_requests["Country"], valid_requests["Year"]):
        response = client.get(f"/v1/country-data/{country}/{year}")
        data = response.json()

        base_error_msg = f"FAILED TEST:  {country} and {year} | "

        nice_to_have_keys = ["country", "assessment_year"]
        for key in nice_to_have_keys:
            base_msg = (
                f"TEST:  {country} and {year} | "
                f"We forgot to specify this in the instructions (see {INSTRUCTIONS_URL}) " 
            )

            if key in data.keys():
                print(base_msg + f"but it was great that you specified a `{key}` key at the top of the JSON")
            else:
                warnings.warn(base_msg + f"but it would be great to have a `{key}` key at the top of the JSON")

        msg = base_error_msg + "There should be a 'pillars' key at the top of the JSON response."
        keys = list(data.keys())
        assert "pillars" in keys, msg

        msg = base_error_msg + "The 'pillars' key should be a list and there should be exactly 3 pillars in the response."
        assert isinstance(data['pillars'], list) and len(data['pillars']) == 3, msg

        for pillar in data["pillars"]:

            expected_pillar_keys = ["name", "areas"]

            for key in expected_pillar_keys:
                msg = base_error_msg + f"Expected a '{key}' key under each pillar."
                assert key in list(pillar.keys()), msg

            msg = base_error_msg + "'areas' should be a list and there should be at least one area under each pillar."
            assert isinstance(pillar["areas"], list) and len(pillar["areas"]) > 0, msg

            for area in pillar["areas"]:
                
                expected_area_keys = ["name", "assessment", "indicators"]
                for key in expected_area_keys:
                    msg = base_error_msg + f"Expected a '{key}' key under each area."
                    assert key in list(area.keys()), msg

                # CF.4 does not have indicators
                if area['name'] != 'CF.4':
                    msg = (
                        base_error_msg,
                        "'indicators' should be a list and there should be at least one indicator under each area. "
                        f"Area object: {area}"
                    )
                    assert isinstance(area["indicators"], list) and len(area["indicators"]) > 0, msg

                    for indicator in area["indicators"]:
                        
                        expected_indicator_keys = ["name", "assessment", "metrics", "source"]
                        for key in expected_indicator_keys:
                            msg = base_error_msg + f"Expected a '{key}' key under each indicator."
                            assert key in list(indicator.keys()), msg

                        metrics = indicator["metrics"]
                        assert type(metrics) == list, base_error_msg + "Metrics should be a dict (even if an empty one)"
                        if len(metrics) != 0:
                            for metric in metrics:
                                assert type(metric) == dict, base_error_msg + "Each metric should be a dict"
                                assert len(metric) == 3, base_error_msg + "Each metric should have exactly 2 keys"
                                assert metric['name'] is not None, base_error_msg + "Each metric should have a 'name' key"
                                assert metric['value'] is not None, base_error_msg + "Each metric should have a 'value' key"
                                assert metric['source'] is not None, base_error_msg + "Each metric should have a 'source' key"

# Now lets test if the JSON response matches the expected fixture response for canada, 2023
def test_ascor_response_matches_fixture(client, expected_ascor_response):
    """Test that country data endpoint matches expected fixture response"""
    response = client.get("/v1/country-data/canada/2023")
    assert response.status_code == 200
    
    assert response.json() == expected_ascor_response