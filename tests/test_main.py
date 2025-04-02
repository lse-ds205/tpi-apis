# tests/test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ------------------------------------------------------------------------------
# Root & Documentation Endpoints
# ------------------------------------------------------------------------------
def test_home_endpoint():
    """Test the home endpoint returns the welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the TPI API!"}


def test_swagger_ui():
    """Test that the Swagger UI documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_ui():
    """Test that the ReDoc documentation is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
