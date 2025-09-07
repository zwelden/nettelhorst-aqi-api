from datetime import datetime
from app.core.database import SessionLocal
from app.models.task_log import TaskLog
import logging

logger = logging.getLogger(__name__)


async def update_task_log(task_log_id: int, status: str, result: str, is_successful: bool):
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