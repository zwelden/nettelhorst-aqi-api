import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.airgradient_service import airgradient_service
from app.services.aqi_data_service import aqi_data_service

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """Service for fetching and seeding historical AirGradient data"""
    
    def __init__(
        self, 
        batch_size_days: Optional[int] = None, 
        delay_between_requests: Optional[float] = None
    ):
        """
        Initialize the historical data service
        
        Args:
            batch_size_days: Number of days to fetch in each batch (defaults from config)
            delay_between_requests: Delay in seconds between API requests (defaults from config)
        """
        self.batch_size_days = batch_size_days or settings.HISTORICAL_SEED_BATCH_SIZE_DAYS
        self.delay_between_requests = delay_between_requests or settings.HISTORICAL_SEED_DELAY_BETWEEN_REQUESTS
    
    def _get_date_chunks(self, days_back: int) -> List[tuple[datetime, datetime]]:
        """
        Split a date range into smaller chunks for batch processing
        
        Args:
            days_back: Number of days back from now to fetch data
            
        Returns:
            List of (start_date, end_date) tuples for each chunk
        """
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days_back)
        
        chunks = []
        current_start = start_date
        
        while current_start < now:
            current_end = min(current_start + timedelta(days=self.batch_size_days), now)
            chunks.append((current_start, current_end))
            current_start = current_end
        
        return chunks
    
    async def fetch_historical_data_for_location(
        self, 
        location_id: int, 
        days_back: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch historical data for a single location
        
        Args:
            location_id: The location ID to fetch data for
            days_back: Number of days back to fetch data (defaults from config)
            
        Returns:
            Dictionary with fetch statistics and results
        """
        days_back = days_back or settings.HISTORICAL_SEED_DAYS_BACK
        logger.info(f"Starting historical data fetch for location {location_id} ({days_back} days)")
        
        chunks = self._get_date_chunks(days_back)
        total_fetched = 0
        total_saved = 0
        failed_chunks = 0
        
        logger.info(f"Processing {len(chunks)} date chunks for location {location_id}")
        
        for i, (start_date, end_date) in enumerate(chunks, 1):
            try:
                logger.info(f"Processing chunk {i}/{len(chunks)} for location {location_id}: {start_date.date()} to {end_date.date()}")
                
                # Fetch data for this chunk
                chunk_data = await airgradient_service.fetch_location_data_range(
                    location_id, start_date, end_date
                )
                
                total_fetched += len(chunk_data)
                
                if chunk_data:
                    # Save data to database
                    saved_count = aqi_data_service.save_measurement_data(chunk_data)
                    total_saved += saved_count
                    
                    logger.info(f"Chunk {i}/{len(chunks)}: Fetched {len(chunk_data)}, Saved {saved_count}")
                else:
                    logger.info(f"Chunk {i}/{len(chunks)}: No data found")
                
                # Add delay between requests to be nice to the API
                if i < len(chunks):  # Don't delay after the last chunk
                    await asyncio.sleep(self.delay_between_requests)
                    
            except Exception as e:
                logger.error(f"Failed to process chunk {i}/{len(chunks)} for location {location_id}: {str(e)}")
                failed_chunks += 1
                continue
        
        result = {
            "location_id": location_id,
            "chunks_processed": len(chunks),
            "chunks_failed": failed_chunks,
            "total_fetched": total_fetched,
            "total_saved": total_saved,
            "success_rate": (len(chunks) - failed_chunks) / len(chunks) if chunks else 0
        }
        
        logger.info(f"Completed historical data fetch for location {location_id}: {result}")
        return result
    
    async def fetch_historical_data_for_all_locations(
        self, 
        days_back: Optional[int] = None,
        delay_between_locations: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Fetch historical data for all locations in the database
        
        Args:
            days_back: Number of days back to fetch data (defaults from config)
            delay_between_locations: Additional delay between processing different locations (defaults from config)
            
        Returns:
            Dictionary with overall fetch statistics and results
        """
        days_back = days_back or settings.HISTORICAL_SEED_DAYS_BACK
        delay_between_locations = delay_between_locations or settings.HISTORICAL_SEED_DELAY_BETWEEN_LOCATIONS
        logger.info(f"Starting historical data fetch for all locations ({days_back} days)")
        
        # Get all locations
        locations = aqi_data_service.get_all_locations()
        if not locations:
            logger.warning("No AQI locations found in database")
            return {
                "total_locations": 0,
                "locations_processed": 0,
                "locations_failed": 0,
                "total_fetched": 0,
                "total_saved": 0,
                "location_results": []
            }
        
        logger.info(f"Found {len(locations)} locations to process")
        
        location_results = []
        total_fetched = 0
        total_saved = 0
        failed_locations = 0
        
        for i, location in enumerate(locations, 1):
            try:
                logger.info(f"Processing location {i}/{len(locations)}: {location.location_name} (ID: {location.location_id})")
                
                result = await self.fetch_historical_data_for_location(
                    location.location_id, days_back
                )
                
                location_results.append(result)
                total_fetched += result["total_fetched"]
                total_saved += result["total_saved"]
                
                if result["chunks_failed"] > 0:
                    logger.warning(f"Location {location.location_id} had {result['chunks_failed']} failed chunks")
                
                # Add delay between locations
                if i < len(locations):  # Don't delay after the last location
                    logger.info(f"Waiting {delay_between_locations}s before processing next location...")
                    await asyncio.sleep(delay_between_locations)
                    
            except Exception as e:
                logger.error(f"Failed to process location {location.location_id}: {str(e)}")
                failed_locations += 1
                location_results.append({
                    "location_id": location.location_id,
                    "error": str(e),
                    "chunks_processed": 0,
                    "chunks_failed": 0,
                    "total_fetched": 0,
                    "total_saved": 0,
                    "success_rate": 0
                })
                continue
        
        overall_result = {
            "total_locations": len(locations),
            "locations_processed": len(locations) - failed_locations,
            "locations_failed": failed_locations,
            "total_fetched": total_fetched,
            "total_saved": total_saved,
            "success_rate": (len(locations) - failed_locations) / len(locations) if locations else 0,
            "location_results": location_results
        }
        
        logger.info(f"Completed historical data fetch for all locations: {overall_result}")
        return overall_result
    
    async def validate_api_connectivity_async(self) -> bool:
        """
        Validate that we can connect to the AirGradient API (async version)
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Get a location to test with
            locations = aqi_data_service.get_all_locations()
            if not locations:
                logger.error("No locations available for API connectivity test")
                return False
            
            test_location_id = locations[0].location_id
            logger.info(f"Testing API connectivity with location {test_location_id}")
            
            # Test with a small date range (just last hour)
            now = datetime.now(timezone.utc)
            one_hour_ago = now - timedelta(hours=1)
            
            test_data = await airgradient_service.fetch_location_data_range(
                test_location_id, one_hour_ago, now
            )
            logger.info(f"API connectivity test successful. Received {len(test_data)} data points")
            return True
                
        except Exception as e:
            logger.error(f"API connectivity test failed: {str(e)}")
            return False
    
    def validate_api_connectivity(self) -> bool:
        """
        Validate that we can connect to the AirGradient API (sync wrapper)
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            import asyncio
            # Check if there's already an event loop running
            try:
                loop = asyncio.get_running_loop()
                # If we're here, there's already a loop running
                # This shouldn't happen in normal usage, but we handle it
                logger.warning("Event loop already running, using sync validation")
                return False
            except RuntimeError:
                # No loop running, we can create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.validate_api_connectivity_async())
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"API connectivity validation failed: {str(e)}")
            return False


historical_data_service = HistoricalDataService()