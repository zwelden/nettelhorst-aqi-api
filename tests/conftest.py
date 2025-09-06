import pytest
import tempfile
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, JSON
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Monkey-patch JSONB to JSON for SQLite compatibility before importing models
from sqlalchemy.dialects import postgresql
postgresql.JSONB = JSON

from app.core.database import Base
from app.models.aqi_location import AqiLocation
from app.models.aqi_5_minute_history import Aqi5MinuteHistory
from app.main import app


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary SQLite database for testing"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    
    # Create engine and tables
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override the app's SessionLocal
    import app.core.database
    original_session = app.core.database.SessionLocal
    app.core.database.SessionLocal = TestSessionLocal
    
    # Also override in the service module
    import app.services.aqi_data_service
    app.services.aqi_data_service.SessionLocal = TestSessionLocal
    
    yield TestSessionLocal
    
    # Cleanup
    app.core.database.SessionLocal = original_session
    app.services.aqi_data_service.SessionLocal = original_session
    
    # Close and remove database
    engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(test_db):
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def seed_single_location(test_db):
    """Seed database with a single test location"""
    db = test_db()
    try:
        location = AqiLocation(
            location_id=80146,
            location_name="Nettelhorst Elementary School (NE Corner)",
            location_description="3252 N Broadway, Chicago IL 60657",
            serial_no="744dbdc08034",
            model="O-1PS",
            firmware_version="3.3.9",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        return location
    finally:
        db.close()


@pytest.fixture
def seed_multiple_locations(test_db):
    """Seed database with multiple test locations"""
    db = test_db()
    try:
        locations = [
            AqiLocation(
                location_id=80146,
                location_name="Nettelhorst Elementary School (NE Corner)",
                location_description="3252 N Broadway, Chicago IL 60657",
                serial_no="744dbdc08034",
                model="O-1PS",
                firmware_version="3.3.9",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ),
            AqiLocation(
                location_id=80147,
                location_name="Test School South",
                location_description="123 Test St, Chicago IL 60601",
                serial_no="123abc456def",
                model="O-2PS",
                firmware_version="3.4.0",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            ),
            AqiLocation(
                location_id=80148,
                location_name="Test School North",
                location_description="456 Example Ave, Chicago IL 60602",
                serial_no="789ghi012jkl",
                model="O-1PS",
                firmware_version="3.3.9",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        ]
        
        for location in locations:
            db.add(location)
        
        db.commit()
        return locations
    finally:
        db.close()