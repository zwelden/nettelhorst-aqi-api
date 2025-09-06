import pytest
from datetime import datetime


def test_get_all_locations_empty(client):
    """Test GET /locations with empty database"""
    response = client.get("/api/v1/locations/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_all_locations_success(client, seed_single_location):
    """Test successful retrieval of locations from database"""
    response = client.get("/api/v1/locations/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    
    # Verify the location data
    location = data[0]
    assert location["location_id"] == 80146
    assert location["location_name"] == "Nettelhorst Elementary School (NE Corner)"


def test_get_all_locations_data_integrity(client, seed_single_location):
    """Test that all location fields are returned correctly"""
    response = client.get("/api/v1/locations/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    location = data[0]
    
    # Verify all fields
    assert location["location_id"] == 80146
    assert location["location_name"] == "Nettelhorst Elementary School (NE Corner)"
    assert location["location_description"] == "3252 N Broadway, Chicago IL 60657"
    assert location["serial_no"] == "744dbdc08034"
    assert location["model"] == "O-1PS"
    assert location["firmware_version"] == "3.3.9"
    
    # Verify metadata fields exist
    assert "id" in location
    assert "created_at" in location
    assert "updated_at" in location
    
    # Verify datetime fields are strings (ISO format)
    assert isinstance(location["created_at"], str)
    assert isinstance(location["updated_at"], str)
    
    # Verify datetime fields can be parsed
    datetime.fromisoformat(location["created_at"].replace("Z", "+00:00"))
    datetime.fromisoformat(location["updated_at"].replace("Z", "+00:00"))


def test_get_all_locations_multiple_records(client, seed_multiple_locations):
    """Test retrieval of multiple location records"""
    response = client.get("/api/v1/locations/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    
    # Verify we have all three locations
    location_ids = [loc["location_id"] for loc in data]
    assert 80146 in location_ids
    assert 80147 in location_ids
    assert 80148 in location_ids
    
    # Verify each location has unique data
    location_names = [loc["location_name"] for loc in data]
    assert "Nettelhorst Elementary School (NE Corner)" in location_names
    assert "Test School South" in location_names
    assert "Test School North" in location_names


def test_get_all_locations_response_schema(client, seed_single_location):
    """Test that response matches expected schema"""
    response = client.get("/api/v1/locations/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    location = data[0]
    
    # Define expected fields and their types
    expected_fields = {
        "id": int,
        "location_id": int,
        "location_name": str,
        "location_description": str,
        "serial_no": str,
        "model": str,
        "firmware_version": str,
        "created_at": str,
        "updated_at": str
    }
    
    # Verify all expected fields are present
    for field_name in expected_fields:
        assert field_name in location, f"Missing field: {field_name}"
    
    # Verify field types
    for field_name, expected_type in expected_fields.items():
        assert isinstance(location[field_name], expected_type), \
            f"Field {field_name} should be {expected_type}, got {type(location[field_name])}"
    
    # Verify no extra fields
    assert set(location.keys()) == set(expected_fields.keys())


def test_get_all_locations_json_content_type(client, seed_single_location):
    """Test that response has correct content type"""
    response = client.get("/api/v1/locations/")
    
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]