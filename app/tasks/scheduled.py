from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.task_log import TaskLog
import logging
import asyncio

logger = logging.getLogger(__name__)


def register_scheduled_tasks(scheduler):
    """
    Register all scheduled tasks with the scheduler
    """
    # Add your scheduled tasks here
    # Example:
    # scheduler.add_job(
    #     your_task_function,
    #     'interval',
    #     hours=1,
    #     id='your_task_id',
    #     replace_existing=True
    # )
    
    logger.info("Scheduled tasks registered successfully")