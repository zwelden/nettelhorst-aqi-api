from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Dict, Any, Optional
from app.core.database import SessionLocal
from app.models.task_log import TaskLog
from app.models.aqi_5_minute_history import Aqi5MinuteHistory
from app.models.aqi_30_minute_history import Aqi30MinuteHistory
from app.models.aqi_location import AqiLocation
from app.services.aqi_data_service import aqi_data_service
from app.tasks.utils import update_task_log
import logging

logger = logging.getLogger(__name__)


def round_down_to_half_hour(dt: datetime) -> datetime:
    """
    Round datetime down to the nearest half hour
    """
    if dt.minute >= 30:
        return dt.replace(minute=30, second=0, microsecond=0)
    else:
        return dt.replace(minute=0, second=0, microsecond=0)


def get_30_minute_windows(start_time: datetime, end_time: datetime) -> List[tuple]:
    """
    Generate 30-minute time windows between start and end time
    Returns list of (window_start, window_end) tuples
    Windows are exclusive of start, inclusive of end: >start_time <= end_time
    """
    windows = []
    current = round_down_to_half_hour(start_time)
    
    while current < end_time:
        window_start = current
        if current.minute == 0:
            window_end = current.replace(minute=30)
        elif current.hour == 23:
            window_end_temp = current + timedelta(days=1)
            window_end = window_end_temp.replace(hour=0, minute=0)
        else:
            window_end = current.replace(hour=current.hour + 1, minute=0)
        
        if window_end <= end_time:
            windows.append((window_start, window_end))
        
        current = window_end
    
    return windows


def average_measure_data(records: List[Aqi5MinuteHistory]) -> Dict[str, float]:
    """
    Average the specified measure_data fields across records
    Only averages: rco2_corrected, atmp, tvoc, tvocIndex, rhum_corrected, pm02_corrected
    """
    fields_to_average = ['rco2_corrected', 'atmp', 'tvoc', 'tvocIndex', 'rhum_corrected', 'pm02_corrected']
    averages = {}
    
    for field in fields_to_average:
        values = []
        for record in records:
            if isinstance(record.measure_data, dict) and field in record.measure_data:
                value = record.measure_data[field]
                if value is not None and isinstance(value, (int, float)):
                    values.append(float(value))
        
        if values:
            averages[field] = round(sum(values) / len(values), 2)
    
    return averages


async def aggregate_30_minute_data():
    """
    Scheduled task to aggregate 5-minute AQI data into 30-minute averages
    Runs every 30 minutes to process new data
    """
    task_name = "aggregate_30_minute_data"
    task_log_id = None
    
    try:
        # Create task log entry
        with SessionLocal() as db:
            task_log = TaskLog(
                task_name=task_name,
                status="started",
                started_at=datetime.now()
            )
            db.add(task_log)
            db.commit()
            db.refresh(task_log)
            task_log_id = task_log.id
        
        logger.info(f"Starting {task_name} (Task Log ID: {task_log_id})")
        
        # Get current time rounded down to nearest half hour
        current_time = datetime.now(timezone.utc)
        # Add 30-minute buffer in case 5-minute table is not fully caught up
        buffered_time = current_time - timedelta(minutes=30)
        max_end_time = round_down_to_half_hour(buffered_time)
        
        # Get all AQI locations
        locations = aqi_data_service.get_all_locations()
        if not locations:
            logger.warning("No AQI locations found in database")
            await update_task_log(task_log_id, "completed", "No locations found", True)
            return
        
        total_aggregated = 0
        location_results = {}
        
        # Process each location
        for location in locations:
            logger.info(f"Processing location {location.location_id} ({location.location_name})")
            
            with SessionLocal() as db:
                # Find the most recent 30-minute record for this location
                latest_30min = db.query(Aqi30MinuteHistory).filter(
                    Aqi30MinuteHistory.aqi_location_id == location.id
                ).order_by(desc(Aqi30MinuteHistory.measure_time)).first()
                
                # Determine start time for processing
                if latest_30min:
                    start_time = latest_30min.measure_time
                else:
                    # If no 30-minute records exist, start from 30 days ago
                    start_time = current_time - timedelta(days=30)
                
                # Get all 5-minute records newer than the last 30-minute record
                five_min_records = db.query(Aqi5MinuteHistory).filter(
                    and_(
                        Aqi5MinuteHistory.aqi_location_id == location.id,
                        Aqi5MinuteHistory.measure_time > start_time,
                        Aqi5MinuteHistory.measure_time <= max_end_time
                    )
                ).order_by(Aqi5MinuteHistory.measure_time).all()
                
                if not five_min_records:
                    logger.info(f"No new 5-minute records found for location {location.location_id}")
                    location_results[location.location_id] = 0
                    continue
                
                # Generate 30-minute windows
                windows = get_30_minute_windows(start_time, max_end_time)
                
                aggregated_count = 0
                
                # Process each 30-minute window
                for window_start, window_end in windows:
                    # Filter records for this window (exclusive start, inclusive end)
                    window_records = [
                        record for record in five_min_records
                        if window_start < record.measure_time <= window_end
                    ]
                    
                    if not window_records:
                        logger.debug(f"No data for window {window_start} to {window_end}")
                        continue
                    
                    # Average the specified measure_data fields
                    averaged_data = average_measure_data(window_records)
                    
                    if not averaged_data:
                        logger.warning(f"No valid data to average for window {window_start} to {window_end}")
                        continue
                    
                    # Check if 30-minute record already exists
                    existing_record = db.query(Aqi30MinuteHistory).filter(
                        and_(
                            Aqi30MinuteHistory.aqi_location_id == location.id,
                            Aqi30MinuteHistory.measure_time == window_end
                        )
                    ).first()
                    
                    if existing_record:
                        logger.debug(f"30-minute record already exists for {window_end}")
                        continue
                    
                    # Create new 30-minute record
                    new_record = Aqi30MinuteHistory(
                        measure_time=window_end,
                        aqi_location_id=location.id,
                        measure_data=averaged_data
                    )
                    
                    db.add(new_record)
                    aggregated_count += 1
                    
                    logger.debug(f"Created 30-minute record for {window_end} with {len(window_records)} source records")
                
                db.commit()
                location_results[location.location_id] = aggregated_count
                total_aggregated += aggregated_count
                
                logger.info(f"Completed location {location.location_id}: {aggregated_count} records aggregated")
        
        # Prepare result summary
        result_summary = {
            "locations_processed": len(locations),
            "total_records_aggregated": total_aggregated,
            "aggregation_results_by_location": location_results,
            "max_end_time": max_end_time.isoformat()
        }
        
        logger.info(f"Task completed successfully: {result_summary}")
        
        # Update task log with success
        await update_task_log(
            task_log_id, 
            "completed", 
            f"Processed {len(locations)} locations, aggregated {total_aggregated} records",
            True
        )
        
    except Exception as e:
        error_message = f"Error in {task_name}: {str(e)}"
        logger.error(error_message, exc_info=True)
        
        # Update task log with failure
        if task_log_id:
            await update_task_log(task_log_id, "failed", error_message, False)