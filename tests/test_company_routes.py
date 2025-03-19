# tests/test_company_routes.py
from fastapi.testclient import TestClient
from main import app  

client = TestClient(app)

def test_get_all_companies():
    """Test that the /company/companies endpoint returns a paginated list of companies."""
    response = client.get("/company/companies?page=1&per_page=10")
    assert response.status_code == 200
    data = response.json()
    # Check that the response contains the expected keys.
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert "companies" in data

def test_get_company_details_not_found():
    """Test the company details endpoint returns 404 for a non-existent company."""
    response = client.get("/company/nonexistent_company")
    assert response.status_code == 404
