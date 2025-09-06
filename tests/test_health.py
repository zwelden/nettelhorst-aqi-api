import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint returns correct status"""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FastAPI Backend"
    assert data["version"] == "1.0.0"


def test_health_check_response_format(client):
    """Test the health check endpoint returns correct response format"""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert len(data) == 3  # Should only have these three fields