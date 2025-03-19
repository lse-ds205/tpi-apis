# tests/test_cp_routes.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_latest_cp_assessments():
    """Test that the /cp/latest endpoint returns a paginated list of CP assessment details."""
    response = client.get("/cp/latest?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    # Check that the response is a list of assessments
    assert isinstance(data, list)
    if data:
        # Ensure the expected keys exist in at least one item
        keys = data[0].keys()
        assert "company_id" in keys
        assert "latest_assessment_year" in keys

def test_get_company_cp_history_not_found():
    """Test that a non-existent company returns 404 from the CP history endpoint."""
    response = client.get("/cp/company/nonexistent_company")
    assert response.status_code == 404

def test_get_company_cp_alignment_not_found():
    """Test that the CP alignment endpoint returns 404 for a non-existent company."""
    response = client.get("/cp/company/nonexistent_company/alignment")
    assert response.status_code == 404

def test_compare_company_cp_insufficient_data():
    """
    Test that when there is insufficient data for a CP comparison,
    the endpoint returns the insufficient data response.
    """
    # Adjust the company id to one that is known to have less than 2 records in your test dataset.
    response = client.get("/cp/company/insufficient_data_company/comparison")
    # Here, we expect the endpoint to return a 200 with a message indicating insufficient data.
    assert response.status_code == 200
    data = response.json()
    # Check for the message and available_assessment_years keys.
    assert "message" in data
    assert "available_assessment_years" in data
