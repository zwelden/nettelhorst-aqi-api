import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.aqi_location import AqiLocation
from app.models.aqi_5_minute_history import Aqi5MinuteHistory

logger = logging.getLogger(__name__)


class AqiDataService:
    """Service for AQI data database operations"""
    
    def get_all_locations(self) -> List[AqiLocation]:
        """
        Get all AQI locations from the database
        
        Returns:
            List of AqiLocation objects
        """
        try:
            with SessionLocal() as db:
                locations = db.query(AqiLocation).all()
                logger.info(f"Retrieved {len(locations)} locations from database")
                return locations
        except Exception as e:
            logger.error(f"Error retrieving locations from database: {str(e)}")
            raise
    
    def get_location_by_location_id(self, location_id: int) -> Optional[AqiLocation]:
        """
        Get AQI location by location_id
        
        Args:
            location_id: The external location ID
            
        Returns:
            AqiLocation object or None if not found
        """
        try:
            with SessionLocal() as db:
                location = db.query(AqiLocation).filter(
                    AqiLocation.location_id == location_id
                ).first()
                return location
        except Exception as e:
            logger.error(f"Error retrieving location {location_id} from database: {str(e)}")
            raise
    
    def save_measurement_data(self, measurements: List[Dict[str, Any]]) -> int:
        """
        Save measurement data to the database
        
        Args:
            measurements: List of measurement data dictionaries
            
        Returns:
            Number of records successfully saved
        """
        if not measurements:
            logger.info("No measurements to save")
            return 0
        
        saved_count = 0
        try:
            with SessionLocal() as db:
                for measurement in measurements:
                    try:
                        # Extract timestamp and convert to datetime
                        timestamp_str = measurement.get('timestamp')
                        if not timestamp_str:
                            logger.warning("Measurement missing timestamp, skipping")
                            continue
                        
                        # Parse ISO 8601 timestamp
                        measure_time = datetime.fromisoformat(
                            timestamp_str.replace('Z', '+00:00')
                        )
                        
                        # Get location_id from the measurement data
                        location_id = measurement.get('locationId')
                        if not location_id:
                            logger.warning("Measurement missing locationId, skipping")
                            continue
                        
                        # Find the corresponding AQI location
                        aqi_location = self.get_location_by_location_id(location_id)
                        if not aqi_location:
                            logger.warning(f"No AQI location found for location_id {location_id}, skipping")
                            continue
                        
                        # Check if this measurement already exists
                        existing = db.query(Aqi5MinuteHistory).filter(
                            Aqi5MinuteHistory.aqi_location_id == aqi_location.id,
                            Aqi5MinuteHistory.measure_time == measure_time
                        ).first()
                        
                        if existing:
                            logger.debug(f"Measurement already exists for location {location_id} at {measure_time}")
                            continue
                        
                        # Create new measurement record
                        # Handle JSONB vs Text difference between PostgreSQL and SQLite for testing
                        measure_data_value = measurement
                        try:
                            # Check if this is a Text column (likely SQLite test environment)
                            column_type = str(Aqi5MinuteHistory.measure_data.property.columns[0].type)
                            if 'TEXT' in column_type.upper():
                                measure_data_value = json.dumps(measurement)
                        except Exception:
                            # Default to original value if we can't determine the type
                            pass
                        
                        history_record = Aqi5MinuteHistory(
                            measure_time=measure_time,
                            aqi_location_id=aqi_location.id,
                            measure_data=measure_data_value
                        )
                        
                        db.add(history_record)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing individual measurement: {str(e)}")
                        continue
                
                if saved_count > 0:
                    db.commit()
                    logger.info(f"Successfully saved {saved_count} measurement records")
                else:
                    logger.info("No new measurement records to save")
                
        except Exception as e:
            logger.error(f"Error saving measurement data: {str(e)}")
            raise
        
        return saved_count
    
    def bulk_save_location_measurements(
        self, 
        location_data_map: Dict[int, List[Dict[str, Any]]]
    ) -> Dict[int, int]:
        """
        Save measurement data for multiple locations
        
        Args:
            location_data_map: Dictionary mapping location_id to list of measurements
            
        Returns:
            Dictionary mapping location_id to number of records saved
        """
        results = {}
        
        for location_id, measurements in location_data_map.items():
            try:
                saved_count = self.save_measurement_data(measurements)
                results[location_id] = saved_count
                logger.info(f"Saved {saved_count} measurements for location {location_id}")
            except Exception as e:
                logger.error(f"Failed to save measurements for location {location_id}: {str(e)}")
                results[location_id] = 0
        
        return results


aqi_data_service = AqiDataService()