from app.tasks.airgradient_task import pull_airgradient_data
from app.tasks.aggregation_task import aggregate_30_minute_data
import logging

logger = logging.getLogger(__name__)


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
    
    # Add 30-minute aggregation task - runs every 30 minutes
    scheduler.add_job(
        aggregate_30_minute_data,
        'interval',
        minutes=30,
        id='aggregate_30_minute_data',
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    
    logger.info("Scheduled tasks registered successfully")
    logger.info("AirGradient data pull task scheduled to run every 15 minutes")
    logger.info("30-minute data aggregation task scheduled to run every 30 minutes")