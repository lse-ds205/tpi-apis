# tests/test_cp_routes.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ------------------------------------------------------------------------------
# General Endpoint Tests
# ------------------------------------------------------------------------------
def test_get_latest_cp_assessments():
    """Test that the /cp/latest endpoint returns a paginated list of CP assessment details."""
    response = client.get("/v1/cp/latest?page=1&page_size=10")
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    if data:
        keys = data[0].keys()
        assert "company_id" in keys
        assert "latest_assessment_year" in keys


def test_get_company_cp_history_not_found():
    """Test that a non-existent company returns 404 from the CP history endpoint."""
    response = client.get("/v1/cp/company/nonexistent_company")
    assert response.status_code == 404


def test_get_company_cp_alignment_not_found():
    """Test that the CP alignment endpoint returns 404 for a non-existent company."""
    response = client.get("/v1/cp/company/nonexistent_company/alignment")
    assert response.status_code == 404


def test_compare_company_cp_insufficient_data():
    """
    Test that when there is insufficient data for a CP comparison,
    the endpoint returns the insufficient data response.
    """
    response = client.get(
        "/v1/cp/company/insufficient_data_company/comparison"
    )
    assert response.status_code == 200

    data = response.json()

    assert "message" in data
    assert "available_assessment_years" in data


# --------------------------------------------------------------------------
# Company-Specific Tests: Vectren
# --------------------------------------------------------------------------
def test_get_company_cp_history_vectren():
    """
    Test that an existing company 'vectren' returns exactly one CP assessment record
    with the fields shown in the screenshot (e.g., latest_assessment_year=2019, etc.).
    """
    response = client.get("/v1/cp/company/vectren")
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    record = data[0]
    assert record["company_id"].lower() == "vectren"
    assert record["name"] == "Vectren"
    assert record["sector"] == "Electricity Utilities"
    assert record["geography"] == "United States of America"
    assert record["latest_assessment_year"] == 2019

    assert record["carbon_performance_2025"] == "N/A"
    assert record["carbon_performance_2027"] == "N/A"
    assert record["carbon_performance_2035"] == "N/A"
    assert record["carbon_performance_2050"] == "N/A"


def test_get_company_cp_alignment_vectren():
    """
    Test that the alignment endpoint for 'vectren' returns a dictionary
    with target years (2025, 2027, 2035, 2050) all set to 'N/A'.
    """
    response = client.get("/v1/cp/company/vectren/alignment")
    assert response.status_code == 200

    data = response.json()

    for year in ["2025", "2027", "2035", "2050"]:
        assert year in data
        assert data[year] == "N/A"


def test_compare_company_cp_vectren_insufficient_data():
    """
    Test that when 'vectren' has only one CP record, the comparison endpoint
    returns the 'insufficient data' response with the year [2019].
    """
    response = client.get("/v1/cp/company/vectren/comparison")
    assert response.status_code == 200

    data = response.json()

    assert data["company_id"].lower() == "vectren"
    assert "message" in data
    assert data["message"] == "Insufficient data for comparison"
    assert data["available_assessment_years"] == [2019]
