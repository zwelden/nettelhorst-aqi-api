from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.task_log import TaskLog
from app.services.airgradient_service import airgradient_service
from app.services.aqi_data_service import aqi_data_service
import logging
import asyncio

logger = logging.getLogger(__name__)


async def pull_airgradient_data():
    """
    Scheduled task to pull air quality data from AirGradient API
    Runs every 15 minutes to fetch the last hour's worth of data
    """
    task_name = "pull_airgradient_data"
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
        
        # Get all AQI locations
        locations = aqi_data_service.get_all_locations()
        if not locations:
            logger.warning("No AQI locations found in database")
            await _update_task_log(task_log_id, "completed", "No locations found", True)
            return
        
        location_ids = [location.location_id for location in locations]
        logger.info(f"Found {len(locations)} locations to process: {location_ids}")
        
        # Fetch data from AirGradient API for all locations
        location_data_map = await airgradient_service.fetch_multiple_locations_data(location_ids)
        
        # Count total data points fetched
        total_fetched = sum(len(data) for data in location_data_map.values())
        logger.info(f"Fetched {total_fetched} total data points from API")
        
        # Save data to database
        save_results = aqi_data_service.bulk_save_location_measurements(location_data_map)
        
        # Count total records saved
        total_saved = sum(save_results.values())
        
        # Prepare result summary
        result_summary = {
            "locations_processed": len(locations),
            "total_data_points_fetched": total_fetched,
            "total_records_saved": total_saved,
            "save_results_by_location": save_results
        }
        
        logger.info(f"Task completed successfully: {result_summary}")
        
        # Update task log with success
        await _update_task_log(
            task_log_id, 
            "completed", 
            f"Processed {len(locations)} locations, saved {total_saved} records",
            True
        )
        
    except Exception as e:
        error_message = f"Error in {task_name}: {str(e)}"
        logger.error(error_message, exc_info=True)
        
        # Update task log with failure
        if task_log_id:
            await _update_task_log(task_log_id, "failed", error_message, False)


async def _update_task_log(task_log_id: int, status: str, result: str, is_successful: bool):
    """
    Update task log with completion status
    """
    try:
        with SessionLocal() as db:
            task_log = db.query(TaskLog).filter(TaskLog.id == task_log_id).first()
            if task_log:
                task_log.status = status
                task_log.completed_at = datetime.now()
                task_log.result = result
                task_log.is_successful = is_successful
                if not is_successful:
                    task_log.error_message = result
                db.commit()
    except Exception as e:
        logger.error(f"Error updating task log {task_log_id}: {str(e)}")


def register_scheduled_tasks(scheduler):
    """
    Register all scheduled tasks with the scheduler
    """
    # Add AirGradient data pull task - runs every 15 minutes
    scheduler.add_job(
        pull_airgradient_data,
        'interval',
        minutes=15,
        id='pull_airgradient_data',
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    
    logger.info("Scheduled tasks registered successfully")
    logger.info("AirGradient data pull task scheduled to run every 15 minutes")