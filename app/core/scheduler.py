from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from pytz import timezone
from app.core.config import settings
import logging

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

jobstores = {
    'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
}

executors = {
    'default': AsyncIOExecutor(),
}

job_defaults = {
    'coalesce': settings.SCHEDULER_JOB_DEFAULTS_COALESCE,
    'max_instances': settings.SCHEDULER_JOB_DEFAULTS_MAX_INSTANCES,
    'misfire_grace_time': 30
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=timezone(settings.SCHEDULER_TIMEZONE)
)


def init_scheduler():
    """
    Initialize the scheduler and add jobs
    """
    from app.tasks.scheduled import register_scheduled_tasks
    
    if not scheduler.running:
        scheduler.start()
        register_scheduled_tasks(scheduler)
        logging.info("Scheduler started and tasks registered")


def shutdown_scheduler():
    """
    Shutdown the scheduler
    """
    if scheduler.running:
        scheduler.shutdown()
        logging.info("Scheduler shutdown")