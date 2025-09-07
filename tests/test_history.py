import pytest
from datetime import datetime, timezone, timedelta


# Tests for /api/v1/history/{location_id}/hours endpoint


def test_get_history_by_hours_empty(client):
    """Test GET /history/{location_id}/hours with empty database"""
    response = client.get("/api/v1/history/80146/hours")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_history_by_hours_invalid_location(client, seed_history_data):
    """Test GET /history/{location_id}/hours with non-existent location"""
    response = client.get("/api/v1/history/99999/hours")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_history_by_hours_default_24(client, seed_history_data):
    """Test GET /history/{location_id}/hours with default 24 hours"""
    summary = seed_history_data
    
    response = client.get("/api/v1/history/80146/hours")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == summary["records_last_24h"]
    
    # Verify response schema
    if len(data) > 0:
        record = data[0]
        assert "id" in record
        assert "measure_time" in record
        assert "aqi_location_id" in record
        assert "measure_data" in record
        assert "created_at" in record
        assert "updated_at" in record


def test_get_history_by_hours_custom_hours(client, seed_history_data):
    """Test GET /history/{location_id}/hours with custom hours parameter"""
    summary = seed_history_data
    
    # Test 3 hours - should get records within 3 hours
    response = client.get("/api/v1/history/80146/hours?hours=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == summary["records_last_3h"]
    
    # Test 12 hours - should get records within 12 hours
    response = client.get("/api/v1/history/80146/hours?hours=12")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == summary["records_last_12h"]
    
    # Test 72 hours - should get all records
    response = client.get("/api/v1/history/80146/hours?hours=72")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == summary["records_last_72h"]


def test_get_history_by_hours_data_filtering(client, seed_history_data):
    """Test that hours filtering works correctly"""
    # Test 2 hours - should get records within last 2 hours
    response = client.get("/api/v1/history/80146/hours?hours=2")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == seed_history_data["records_last_2h"]
    
    # Verify all records are within the time range
    for record in data:
        measure_time = datetime.fromisoformat(record["measure_time"].replace("Z", "+00:00"))
        assert measure_time is not None


def test_get_history_by_hours_sorting(client, seed_history_data):
    """Test that results are sorted by measure_time ascending (oldest first)"""
    response = client.get("/api/v1/history/80146/hours?hours=72")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 1
    
    # Check that results are sorted by measure_time ascending
    for i in range(len(data) - 1):
        current_time = datetime.fromisoformat(data[i]["measure_time"].replace("Z", "+00:00"))
        next_time = datetime.fromisoformat(data[i + 1]["measure_time"].replace("Z", "+00:00"))
        assert current_time <= next_time, "Records should be sorted by measure_time ascending"


def test_get_history_by_hours_boundary_values(client, seed_history_data):
    """Test boundary values for hours parameter"""
    # Test minimum value (1 hour)
    response = client.get("/api/v1/history/80146/hours?hours=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == seed_history_data["records_last_1h"]
    
    # Test maximum value (168 hours = 1 week)
    response = client.get("/api/v1/history/80146/hours?hours=168")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == seed_history_data["total_records"]  # All records


def test_get_history_by_hours_invalid_params(client, seed_history_data):
    """Test invalid hour parameter values"""
    # Test hours = 0 (below minimum)
    response = client.get("/api/v1/history/80146/hours?hours=0")
    assert response.status_code == 422  # Validation error
    
    # Test hours = 169 (above maximum)
    response = client.get("/api/v1/history/80146/hours?hours=169")
    assert response.status_code == 422  # Validation error
    
    # Test negative hours
    response = client.get("/api/v1/history/80146/hours?hours=-5")
    assert response.status_code == 422  # Validation error
    
    # Test invalid string
    response = client.get("/api/v1/history/80146/hours?hours=invalid")
    assert response.status_code == 422  # Validation error


def test_get_history_by_hours_response_schema(client, seed_history_data):
    """Test that response matches expected schema"""
    response = client.get("/api/v1/history/80146/hours?hours=24")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    record = data[0]
    
    # Define expected fields and their types
    expected_fields = {
        "id": int,
        "measure_time": str,
        "aqi_location_id": int,
        "measure_data": dict,
        "created_at": str,
        "updated_at": str
    }
    
    # Verify all expected fields are present
    for field_name in expected_fields:
        assert field_name in record, f"Missing field: {field_name}"
    
    # Verify field types
    for field_name, expected_type in expected_fields.items():
        assert isinstance(record[field_name], expected_type), \
            f"Field {field_name} should be {expected_type}, got {type(record[field_name])}"
    
    # Verify measure_data contains expected AQI fields
    measure_data = record["measure_data"]
    assert "atmp" in measure_data
    assert "rco2" in measure_data
    assert "locationId" in measure_data
    assert measure_data["locationId"] == 80146


def test_get_history_by_hours_json_content_type(client, seed_history_data):
    """Test that response has correct content type"""
    response = client.get("/api/v1/history/80146/hours")
    
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# Tests for /api/v1/history/{location_id}/days endpoint


def test_get_history_by_days_empty(client):
    """Test GET /history/{location_id}/days with empty database"""
    response = client.get("/api/v1/history/80146/days?days=1")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_history_by_days_invalid_location(client, seed_history_data):
    """Test GET /history/{location_id}/days with non-existent location"""
    response = client.get("/api/v1/history/99999/days?days=1")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_history_by_days_single_day(client, seed_history_data):
    """Test GET /history/{location_id}/days with 1 day parameter"""
    response = client.get("/api/v1/history/80146/days?days=1")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should include records from past 24 hours
    assert len(data) == seed_history_data["records_last_24h"]


def test_get_history_by_days_multiple_days(client, seed_history_data):
    """Test GET /history/{location_id}/days with various day values"""
    # Test 2 days - should get records from past 48 hours
    response = client.get("/api/v1/history/80146/days?days=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == seed_history_data["records_last_48h"]
    
    # Test 3 days - should get all records
    response = client.get("/api/v1/history/80146/days?days=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == seed_history_data["records_last_72h"]


def test_get_history_by_days_data_filtering(client, seed_history_data):
    """Test that day filtering works correctly"""
    # Test 1 day - should only get records from last 24 hours
    response = client.get("/api/v1/history/80146/days?days=1")
    
    assert response.status_code == 200
    data = response.json()
    expected_count = seed_history_data["records_last_24h"]
    assert len(data) == expected_count
    
    # Verify all records are within the time range
    for record in data:
        measure_time = datetime.fromisoformat(record["measure_time"].replace("Z", "+00:00"))
        assert measure_time is not None


def test_get_history_by_days_sorting(client, seed_history_data):
    """Test that results are sorted by measure_time ascending (oldest first)"""
    response = client.get("/api/v1/history/80146/days?days=3")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 1
    
    # Check that results are sorted by measure_time ascending
    for i in range(len(data) - 1):
        current_time = datetime.fromisoformat(data[i]["measure_time"].replace("Z", "+00:00"))
        next_time = datetime.fromisoformat(data[i + 1]["measure_time"].replace("Z", "+00:00"))
        assert current_time <= next_time, "Records should be sorted by measure_time ascending"


def test_get_history_by_days_boundary_values(client, seed_history_data):
    """Test boundary values for days parameter"""
    # Test minimum value (1 day)
    response = client.get("/api/v1/history/80146/days?days=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == seed_history_data["records_last_24h"]
    
    # Test maximum value (365 days)
    response = client.get("/api/v1/history/80146/days?days=365")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == seed_history_data["total_records"]  # All records


def test_get_history_by_days_invalid_params(client, seed_history_data):
    """Test invalid day parameter values"""
    # Test missing days parameter (required)
    response = client.get("/api/v1/history/80146/days")
    assert response.status_code == 422  # Validation error
    
    # Test days = 0 (below minimum)
    response = client.get("/api/v1/history/80146/days?days=0")
    assert response.status_code == 422  # Validation error
    
    # Test days = 366 (above maximum)
    response = client.get("/api/v1/history/80146/days?days=366")
    assert response.status_code == 422  # Validation error
    
    # Test negative days
    response = client.get("/api/v1/history/80146/days?days=-5")
    assert response.status_code == 422  # Validation error
    
    # Test invalid string
    response = client.get("/api/v1/history/80146/days?days=invalid")
    assert response.status_code == 422  # Validation error


def test_get_history_by_days_response_schema(client, seed_history_data):
    """Test that response matches expected schema"""
    response = client.get("/api/v1/history/80146/days?days=1")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    record = data[0]
    
    # Define expected fields and their types
    expected_fields = {
        "id": int,
        "measure_time": str,
        "aqi_location_id": int,
        "measure_data": dict,
        "created_at": str,
        "updated_at": str
    }
    
    # Verify all expected fields are present
    for field_name in expected_fields:
        assert field_name in record, f"Missing field: {field_name}"
    
    # Verify field types
    for field_name, expected_type in expected_fields.items():
        assert isinstance(record[field_name], expected_type), \
            f"Field {field_name} should be {expected_type}, got {type(record[field_name])}"
    
    # Verify measure_data contains expected AQI fields
    measure_data = record["measure_data"]
    assert "atmp" in measure_data
    assert "rco2" in measure_data
    assert "locationId" in measure_data
    assert measure_data["locationId"] == 80146


def test_get_history_by_days_json_content_type(client, seed_history_data):
    """Test that response has correct content type"""
    response = client.get("/api/v1/history/80146/days?days=1")
    
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_history_endpoints_consistency(client, seed_history_data):
    """Test that hours and days endpoints return consistent data"""
    # Get data for 24 hours using hours endpoint
    hours_response = client.get("/api/v1/history/80146/hours?hours=24")
    assert hours_response.status_code == 200
    hours_data = hours_response.json()
    
    # Get data for 1 day using days endpoint
    days_response = client.get("/api/v1/history/80146/days?days=1")
    assert days_response.status_code == 200
    days_data = days_response.json()
    
    # Both should return the same number of records
    assert len(hours_data) == len(days_data)
    
    # Verify the records are the same (compare IDs)
    hours_ids = sorted([record["id"] for record in hours_data])
    days_ids = sorted([record["id"] for record in days_data])
    assert hours_ids == days_ids


# Tests for /api/v1/history/{location_id}/week endpoint


def test_get_history_week_empty(client):
    """Test GET /history/{location_id}/week with empty database"""
    response = client.get("/api/v1/history/80146/week")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_history_week_invalid_location(client, seed_30_minute_history_data):
    """Test GET /history/{location_id}/week with non-existent location"""
    response = client.get("/api/v1/history/99999/week")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_history_week_returns_7_days(client, seed_30_minute_history_data):
    """Test GET /history/{location_id}/week returns exactly 7 days of data"""
    summary = seed_30_minute_history_data
    
    response = client.get("/api/v1/history/80146/week")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == summary["records_last_7_days"]
    
    # Verify response schema for 30-minute history
    if len(data) > 0:
        record = data[0]
        assert "id" in record
        assert "measure_time" in record
        assert "aqi_location_id" in record
        assert "measure_data" in record
        assert "created_at" in record
        assert "updated_at" in record


def test_get_history_week_ascending_order(client, seed_30_minute_history_data):
    """Test that results are sorted by measure_time ascending (oldest first)"""
    response = client.get("/api/v1/history/80146/week")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 1
    
    # Check that results are sorted by measure_time ascending
    for i in range(len(data) - 1):
        current_time = datetime.fromisoformat(data[i]["measure_time"].replace("Z", "+00:00"))
        next_time = datetime.fromisoformat(data[i + 1]["measure_time"].replace("Z", "+00:00"))
        assert current_time <= next_time, "Records should be sorted by measure_time ascending (oldest first)"


def test_get_history_week_data_filtering(client, seed_30_minute_history_data):
    """Test that only last 7 days of data are included"""
    response = client.get("/api/v1/history/80146/week")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only include records from last 7 days
    assert len(data) == seed_30_minute_history_data["records_last_7_days"]
    
    # Verify all records are within 7 days
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)
    
    for record in data:
        measure_time_str = record["measure_time"].replace("Z", "").replace("T", " ")
        measure_time = datetime.fromisoformat(measure_time_str)
        assert measure_time >= seven_days_ago, f"Record {record['id']} is older than 7 days"


def test_get_history_week_response_schema(client, seed_30_minute_history_data):
    """Test that response matches Aqi30MinuteHistoryResponse schema"""
    response = client.get("/api/v1/history/80146/week")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    record = data[0]
    
    # Define expected fields and their types for 30-minute history
    expected_fields = {
        "id": int,
        "measure_time": str,
        "aqi_location_id": int,
        "measure_data": dict,
        "created_at": str,
        "updated_at": str
    }
    
    # Verify all expected fields are present
    for field_name in expected_fields:
        assert field_name in record, f"Missing field: {field_name}"
    
    # Verify field types
    for field_name, expected_type in expected_fields.items():
        assert isinstance(record[field_name], expected_type), \
            f"Field {field_name} should be {expected_type}, got {type(record[field_name])}"
    
    # Verify measure_data contains expected AQI fields
    measure_data = record["measure_data"]
    assert "atmp" in measure_data
    assert "rco2" in measure_data
    assert "locationId" in measure_data
    assert measure_data["locationId"] == 80146
    
    # Verify this is 30-minute aggregated data (should have datapoints = 6)
    assert "datapoints" in measure_data
    assert measure_data["datapoints"] == 6


def test_get_history_week_30_minute_intervals(client, seed_30_minute_history_data):
    """Test that data comes from 30-minute history table with proper intervals"""
    response = client.get("/api/v1/history/80146/week")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 10  # Should have many records with 30-minute intervals
    
    # Check that timestamps are at 30-minute intervals (when sorted)
    timestamps = [datetime.fromisoformat(record["measure_time"].replace("Z", "+00:00")) for record in data]
    
    # Verify we have expected number of records for 7 days at 30-minute intervals
    # 7 days * 24 hours * 2 (30-minute intervals per hour) = 336 records
    expected_count = seed_30_minute_history_data["records_last_7_days"]
    assert len(data) == expected_count
    
    # Check intervals between consecutive records (should be 30 minutes)
    for i in range(min(10, len(timestamps) - 1)):  # Check first 10 intervals
        time_diff = timestamps[i + 1] - timestamps[i]
        # Should be 30 minutes (1800 seconds)
        assert time_diff.total_seconds() == 1800, f"Expected 30-minute interval, got {time_diff.total_seconds()} seconds"


def test_get_history_week_json_content_type(client, seed_30_minute_history_data):
    """Test that response has correct content type"""
    response = client.get("/api/v1/history/80146/week")
    
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_get_history_week_excludes_older_data(client, seed_30_minute_history_data):
    """Test that data older than 7 days is excluded"""
    summary = seed_30_minute_history_data
    
    response = client.get("/api/v1/history/80146/week")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only return records from last 7 days, not older records
    assert len(data) == summary["records_last_7_days"]
    
    # Verify no records are older than 7 days
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)
    
    for record in data:
        measure_time_str = record["measure_time"].replace("Z", "").replace("T", " ")
        measure_time = datetime.fromisoformat(measure_time_str)
        assert measure_time >= seven_days_ago, f"Found record older than 7 days: {measure_time}"