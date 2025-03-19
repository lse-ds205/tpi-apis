# tests/test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home_endpoint():
    """Test the home endpoint returns the welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the TPI API!"}
