# tests/test_company_routes.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ------------------------------------------------------------------------------
# General Endpoint Tests
# ------------------------------------------------------------------------------
def test_get_all_companies():
    """Test that the /company/companies endpoint returns a paginated list of companies."""
    response = client.get("/v1/company/companies?page=1&per_page=10")
    assert response.status_code == 200
    data = response.json()
    # Check that the response contains the expected keys.
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "companies" in data


def test_get_company_details_not_found():
    """Test the company details endpoint returns 404 for a non-existent company."""
    response = client.get("/v1/company/nonexistent_company")
    assert response.status_code == 404


# --------------------------------------------------------------------------
# Company specific tests: 3M
# --------------------------------------------------------------------------
def test_get_company_details_3m():
    """
    Test that an existing company '3m' returns correct fields and data
    for the /v1/company/{company_id} endpoint.
    """
    response = client.get("/v1/company/company/3m")
    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "3m"
    assert data["name"] == "3m"
    assert data["sector"] == "Industrials"
    assert data["geography"] == "United States of America"

    assert data["latest_assessment_year"] is None
    assert data["management_quality_score"] == 3
    assert data["carbon_performance_alignment_2035"] == "N/A"
    assert data["emissions_trend"] == "down"


def test_get_company_history_3m():
    """Test the /v1/company/{company_id}/history endpoint for company '3m'."""
    response = client.get("/v1/company/company/3m/history")
    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "3m"
    assert "history" in data
    assert isinstance(data["history"], list)
    assert len(data["history"]) == 1

    history_record = data["history"][0]

    assert history_record["company_id"] == "3m"
    assert history_record["name"] == "3m"
    assert history_record["sector"] == "Industrials"
    assert history_record["geography"] == "United States of America"
    assert history_record["latest_assessment_year"] == 2024
    assert history_record["management_quality_score"] == 3
    assert history_record["carbon_performance_alignment_2035"] in [
        "nan",
        "NaN",
    ]
    assert history_record["emissions_trend"] == "down"


def test_compare_company_performance_3m_insufficient_data():
    """Test the performance comparison endpoint returns insufficient data for '3m'."""
    response = client.get("/v1/company/company/3m/performance-comparison")
    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "3m"
    assert "message" in data
    assert (
        data["message"]
        == "Only one record exists for '3m', so performance comparison is not possible."
    )
    assert data["available_assessment_years"] == [2024]
