import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.aqi_location import AqiLocation

logger = logging.getLogger(__name__)

NETTELHORST_LOCATION_DATA = {
    "location_id": 80146,
    "location_name": "Nettelhorst Elementary School (NE Corner)",
    "location_description": "3252 N Broadway, Chicago IL 60657",
    "serial_no": "744dbdc08034",
    "model": "O-1PS",
    "firmware_version": "3.3.9"
}


def seed_aqi_locations(db: Session) -> bool:
    """
    Seed the aqi_location table with initial data.
    
    Args:
        db: Database session
        
    Returns:
        True if data was seeded, False if already existed
    """
    try:
        # Check if location already exists
        existing_location = get_location_exists(NETTELHORST_LOCATION_DATA["location_id"])

        if existing_location:
            logger.info(f"Location {NETTELHORST_LOCATION_DATA['location_id']} already exists, skipping seed")
            return False
        
        # Create new location with timestamps
        now = datetime.now(timezone.utc)
        location_data = {
            **NETTELHORST_LOCATION_DATA,
            "created_at": now,
            "updated_at": now
        }
        location = AqiLocation(**location_data)
        db.add(location)
        db.commit()
        db.refresh(location)
        
        logger.info(f"Successfully seeded location: {location.location_name} (ID: {location.id})")
        return True
        
    except Exception as e:
        logger.error(f"Error seeding aqi_locations: {str(e)}")
        db.rollback()
        raise


def seed_database() -> None:
    """
    Seed the entire database with initial data.
    """
    logger.info("Starting database seeding...")
    
    with SessionLocal() as db:
        seeded = seed_aqi_locations(db)
        
        if seeded:
            logger.info("Database seeding completed successfully")
        else:
            logger.info("Database already contains seed data, no changes made")


def get_location_exists(location_id: int) -> bool:
    """
    Check if a location exists in the database.
    
    Args:
        location_id: The location ID to check
        
    Returns:
        True if location exists, False otherwise
    """
    with SessionLocal() as db:
        location = db.query(AqiLocation).filter(
            AqiLocation.location_id == location_id
        ).first()
        return location is not None