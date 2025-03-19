# tests/test_mq_routes.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_latest_mq_assessments():
    """Test that the /mq/latest endpoint returns paginated MQ assessments."""
    response = client.get("/mq/latest?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    # Validate response structure
    assert "total_records" in data
    assert "page" in data
    assert "page_size" in data
    assert "results" in data
    if data["results"]:
        assert "company_id" in data["results"][0]

def test_get_mq_by_methodology_invalid():
    """Test that providing an invalid methodology cycle id returns a validation error (422)."""
    # Pass a methodology id that is out of the allowed range.
    response = client.get("/mq/methodology/999?page=1&page_size=10")
    assert response.status_code == 422

def test_get_mq_trends_sector_not_found():
    """Test that an invalid sector id returns a 404 error."""
    response = client.get("/mq/trends/sector/nonexistent_sector?page=1&page_size=10")
    assert response.status_code == 404
