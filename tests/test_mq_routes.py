# tests/test_mq_routes.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ------------------------------------------------------------------------------
# General Endpoint Tests
# ------------------------------------------------------------------------------
def test_get_latest_mq_assessments():
    """Test that the /mq/latest endpoint returns paginated MQ assessments."""
    response = client.get("/v1/mq/latest?page=1&page_size=10")
    assert response.status_code == 200

    data = response.json()

    assert "total_records" in data
    assert "page" in data
    assert "page_size" in data
    assert "results" in data

    if data["results"]:
        assert "company_id" in data["results"][0]


def test_get_latest_mq_assessments_pagination():
    """
    Test that /v1/mq/latest handles pagination edge cases properly,
    e.g., page_size=1 and page=999.
    """
    # page_size = 1
    response = client.get("/v1/mq/latest?page=1&page_size=1")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert len(data["results"]) <= 1

    # page = 999
    large_page_response = client.get("/v1/mq/latest?page=999&page_size=1")
    assert large_page_response.status_code == 200
    large_page_data = large_page_response.json()
    assert len(large_page_data["results"]) in [0, 1]


# ------------------------------------------------------------------------------
# Methodology Cycle Tests
# ------------------------------------------------------------------------------
def test_get_mq_by_methodology_invalid():
    """Test that providing an invalid methodology cycle id returns a validation error (422)."""
    response = client.get("/v1/mq/methodology/999?page=1&page_size=10")
    assert response.status_code == 422


def test_get_mq_by_methodology_success():
    """
    Test that providing a valid methodology cycle id returns a 200 response
    with a paginated list of MQ assessments.
    """
    # Replace 1 with a methodology ID you know exists in your data
    response = client.get("/v1/mq/methodology/1?page=1&page_size=5")
    assert response.status_code == 200

    data = response.json()

    # Check basic structure
    assert "total_records" in data
    assert "page" in data
    assert "page_size" in data
    assert "results" in data

    if data["results"]:
        first_record = data["results"][0]
        assert "company_id" in first_record
        assert "management_quality_score" in first_record


# ------------------------------------------------------------------------------
# Sector Trends Tests
# ------------------------------------------------------------------------------
def test_get_mq_trends_sector_not_found():
    """Test that an invalid sector id returns a 404 error."""
    response = client.get(
        "/v1/mq/trends/sector/nonexistent_sector?page=1&page_size=10"
    )
    assert response.status_code == 404


def test_get_mq_trends_sector_success():
    """
    Test that a valid sector (e.g., 'Coal Mining') returns a 200 response
    with a paginated list of MQ assessments for that sector.
    """
    response = client.get(
        "/v1/mq/trends/sector/coal%20mining?page=1&page_size=5"
    )
    assert response.status_code == 200

    data = response.json()

    assert "total_records" in data
    assert "page" in data
    assert "page_size" in data
    assert "results" in data

    if data["results"]:
        first_record = data["results"][0]
        assert "company_id" in first_record
        assert "name" in first_record
        assert "sector" in first_record
        assert first_record["sector"].lower() == "coal mining"
