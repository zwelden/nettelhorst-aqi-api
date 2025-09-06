import logging
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.aqi_location import AqiLocation
from app.services.historical_data_service import historical_data_service

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


async def seed_historical_aqi_data(
    days_back: int = 130,
    batch_size_days: int = 7,
    delay_between_requests: float = 0.5,
    delay_between_locations: float = 1.0,
    validate_api_first: bool = True
) -> dict:
    """
    Seed the database with historical AQI data from AirGradient API
    
    Args:
        days_back: Number of days back to fetch data (default: 130)
        batch_size_days: Number of days to fetch per batch (default: 7)
        delay_between_requests: Delay between API requests in seconds (default: 1.0)
        delay_between_locations: Delay between processing locations in seconds (default: 2.0)
        validate_api_first: Whether to validate API connectivity before starting (default: True)
        
    Returns:
        Dictionary with seeding results and statistics
    """
    logger.info("=" * 60)
    logger.info("STARTING HISTORICAL AQI DATA SEEDING")
    logger.info("=" * 60)
    logger.info(f"Parameters: days_back={days_back}, batch_size_days={batch_size_days}")
    logger.info(f"Delays: requests={delay_between_requests}s, locations={delay_between_locations}s")
    
    try:
        # Validate API connectivity first if requested
        if validate_api_first:
            logger.info("Validating API connectivity...")
            if not await historical_data_service.validate_api_connectivity_async():
                error_msg = "API connectivity validation failed. Aborting seeding operation."
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "total_locations": 0,
                    "locations_processed": 0,
                    "total_fetched": 0,
                    "total_saved": 0
                }
            logger.info("API connectivity validation successful")
        
        # Configure the historical data service with provided parameters
        historical_data_service.batch_size_days = batch_size_days
        historical_data_service.delay_between_requests = delay_between_requests
        
        # Start the historical data fetch
        start_time = datetime.now()
        logger.info(f"Starting historical data fetch at {start_time}")
        
        result = await historical_data_service.fetch_historical_data_for_all_locations(
            days_back=days_back,
            delay_between_locations=delay_between_locations
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Enhance the result with timing information
        result.update({
            "success": True,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "duration_formatted": str(duration)
        })
        
        logger.info("=" * 60)
        logger.info("HISTORICAL AQI DATA SEEDING COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Duration: {result['duration_formatted']}")
        logger.info(f"Locations processed: {result['locations_processed']}/{result['total_locations']}")
        logger.info(f"Total data points fetched: {result['total_fetched']}")
        logger.info(f"Total records saved: {result['total_saved']}")
        logger.info(f"Overall success rate: {result['success_rate']:.2%}")
        
        if result['locations_failed'] > 0:
            logger.warning(f"Failed locations: {result['locations_failed']}")
        
        return result
        
    except Exception as e:
        error_msg = f"Historical data seeding failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": error_msg,
            "total_locations": 0,
            "locations_processed": 0,
            "total_fetched": 0,
            "total_saved": 0
        }


def seed_historical_data_sync(
    days_back: int = 130,
    batch_size_days: int = 7,
    delay_between_requests: float = 0.5,
    delay_between_locations: float = 1.0,
    validate_api_first: bool = True
) -> dict:
    """
    Synchronous wrapper for seed_historical_aqi_data
    
    This function creates and manages its own event loop to run the async seeding operation.
    Use this function when calling from a synchronous context.
    
    Args:
        days_back: Number of days back to fetch data (default: 130)
        batch_size_days: Number of days to fetch per batch (default: 7)
        delay_between_requests: Delay between API requests in seconds (default: 1.0)
        delay_between_locations: Delay between processing locations in seconds (default: 2.0)
        validate_api_first: Whether to validate API connectivity before starting (default: True)
        
    Returns:
        Dictionary with seeding results and statistics
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(seed_historical_aqi_data(
            days_back=days_back,
            batch_size_days=batch_size_days,
            delay_between_requests=delay_between_requests,
            delay_between_locations=delay_between_locations,
            validate_api_first=validate_api_first
        ))
    finally:
        loop.close()