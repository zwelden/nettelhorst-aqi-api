import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from app.tasks.aggregation_task import round_down_to_half_hour, get_30_minute_windows, average_measure_data
from app.models.aqi_5_minute_history import Aqi5MinuteHistory


def test_round_down_to_half_hour():
    """Test rounding datetime down to nearest half hour"""
    # Test times at exact half hour boundaries
    dt1 = datetime(2023, 1, 1, 12, 0, 0)
    assert round_down_to_half_hour(dt1) == datetime(2023, 1, 1, 12, 0, 0)
    
    dt2 = datetime(2023, 1, 1, 12, 30, 0)
    assert round_down_to_half_hour(dt2) == datetime(2023, 1, 1, 12, 30, 0)
    
    # Test times that need rounding down
    dt3 = datetime(2023, 1, 1, 12, 15, 30)
    assert round_down_to_half_hour(dt3) == datetime(2023, 1, 1, 12, 0, 0)
    
    dt4 = datetime(2023, 1, 1, 12, 45, 45)
    assert round_down_to_half_hour(dt4) == datetime(2023, 1, 1, 12, 30, 0)
    
    dt5 = datetime(2023, 1, 1, 12, 59, 59, 999999)
    assert round_down_to_half_hour(dt5) == datetime(2023, 1, 1, 12, 30, 0)


def test_get_30_minute_windows():
    """Test generation of 30-minute time windows"""
    start_time = datetime(2023, 1, 1, 10, 15, 0)
    end_time = datetime(2023, 1, 1, 12, 0, 0)
    
    windows = get_30_minute_windows(start_time, end_time)
    
    expected_windows = [
        (datetime(2023, 1, 1, 10, 0, 0), datetime(2023, 1, 1, 10, 30, 0)),
        (datetime(2023, 1, 1, 10, 30, 0), datetime(2023, 1, 1, 11, 0, 0)),
        (datetime(2023, 1, 1, 11, 0, 0), datetime(2023, 1, 1, 11, 30, 0)),
        (datetime(2023, 1, 1, 11, 30, 0), datetime(2023, 1, 1, 12, 0, 0)),
    ]
    
    assert windows == expected_windows


def test_get_30_minute_windows_edge_cases():
    """Test edge cases for 30-minute window generation"""
    # Start and end at exact half hour boundaries
    start_time = datetime(2023, 1, 1, 10, 30, 0)
    end_time = datetime(2023, 1, 1, 11, 0, 0)
    
    windows = get_30_minute_windows(start_time, end_time)
    expected_windows = [
        (datetime(2023, 1, 1, 10, 30, 0), datetime(2023, 1, 1, 11, 0, 0)),
    ]
    
    assert windows == expected_windows
    
    # Test with very short time span
    start_time = datetime(2023, 1, 1, 10, 45, 0)
    end_time = datetime(2023, 1, 1, 10, 50, 0)
    
    windows = get_30_minute_windows(start_time, end_time)
    assert windows == []  # No complete 30-minute windows in this span


def test_average_measure_data():
    """Test averaging of measure_data fields"""
    # Create mock records with test data
    records = []
    
    # Record 1
    record1 = Aqi5MinuteHistory(
        id=1,
        measure_time=datetime.now(timezone.utc),
        aqi_location_id=1,
        measure_data={
            'rco2_corrected': 450.0,
            'atmp': 22.5,
            'tvoc': 100,
            'tvocIndex': 50,
            'rhum_corrected': 45.0,
            'pm02_corrected': 12.0,
            'other_field': 999  # This should be ignored
        }
    )
    records.append(record1)
    
    # Record 2
    record2 = Aqi5MinuteHistory(
        id=2,
        measure_time=datetime.now(timezone.utc),
        aqi_location_id=1,
        measure_data={
            'rco2_corrected': 500.0,
            'atmp': 23.0,
            'tvoc': 120,
            'tvocIndex': 55,
            'rhum_corrected': 40.0,
            'pm02_corrected': 15.0
        }
    )
    records.append(record2)
    
    # Record 3 with some missing fields
    record3 = Aqi5MinuteHistory(
        id=3,
        measure_time=datetime.now(timezone.utc),
        aqi_location_id=1,
        measure_data={
            'rco2_corrected': 480.0,
            'atmp': 22.0,
            'tvoc': None,  # Null value should be ignored
            'tvocIndex': 60,
            'rhum_corrected': 50.0
            # pm02_corrected missing entirely
        }
    )
    records.append(record3)
    
    averages = average_measure_data(records)
    
    # Expected averages
    expected = {
        'rco2_corrected': (450.0 + 500.0 + 480.0) / 3,  # 476.67
        'atmp': (22.5 + 23.0 + 22.0) / 3,  # 22.5
        'tvoc': (100 + 120) / 2,  # 110.0 (record3 has null, so excluded)
        'tvocIndex': (50 + 55 + 60) / 3,  # 55.0
        'rhum_corrected': (45.0 + 40.0 + 50.0) / 3,  # 45.0
        'pm02_corrected': (12.0 + 15.0) / 2  # 13.5 (record3 missing, so excluded)
    }
    
    assert len(averages) == 6
    for key, expected_value in expected.items():
        assert abs(averages[key] - expected_value) < 0.01  # Allow small floating point errors


def test_average_measure_data_empty_records():
    """Test averaging with empty record list"""
    averages = average_measure_data([])
    assert averages == {}


def test_average_measure_data_no_valid_data():
    """Test averaging when no records have the required fields"""
    record = Aqi5MinuteHistory(
        id=1,
        measure_time=datetime.now(timezone.utc),
        aqi_location_id=1,
        measure_data={
            'other_field': 123,
            'another_field': 456
        }
    )
    
    averages = average_measure_data([record])
    assert averages == {}


def test_average_measure_data_invalid_data_types():
    """Test averaging with invalid data types"""
    record = Aqi5MinuteHistory(
        id=1,
        measure_time=datetime.now(timezone.utc),
        aqi_location_id=1,
        measure_data={
            'rco2_corrected': 'invalid_string',
            'atmp': [1, 2, 3],  # Invalid type
            'tvoc': 100.0,  # Valid
            'tvocIndex': True,  # This is actually valid (True -> 1.0)
            'rhum_corrected': None,  # Null value
            'pm02_corrected': 15.5  # Valid
        }
    )
    
    averages = average_measure_data([record])
    
    # Should only average the valid numeric fields (True is converted to 1.0)
    expected = {
        'tvoc': 100.0,
        'tvocIndex': 1.0,
        'pm02_corrected': 15.5
    }
    
    assert averages == expected