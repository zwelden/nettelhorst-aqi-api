# FastAPI Backend with PostgreSQL and APScheduler

A production-ready FastAPI backend with PostgreSQL database integration and scheduled task management using APScheduler.

## Features

- FastAPI web framework with async support
- PostgreSQL database with SQLAlchemy ORM
- Database migrations with Alembic
- Scheduled tasks with APScheduler
- Structured logging
- Environment-based configuration
- CORS middleware
- Error handling

## Project Structure

```
app/
├── api/            # API endpoints
├── core/           # Core configuration
├── models/         # Database models
├── schemas/        # Pydantic schemas
├── crud/           # Database operations
├── services/       # Business logic
└── tasks/          # Scheduled tasks
```

## Setup

1. **Create and activate virtual environment:**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Create database:**
   ```bash
   createdb nettelhorst_aqi
   ```

5. **Run database migrations:**
   ```bash
   # Generate initial migration
   alembic revision --autogenerate -m "Initial migration"
   
   # Apply migrations
   alembic upgrade head
   ```

6. **Run the application:**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

   Or directly:
   ```bash
   python app/main.py
   ```

## API Documentation

Once running, visit:
- API Documentation: http://localhost:8000/api/v1/docs
- Alternative docs: http://localhost:8000/api/v1/redoc
- OpenAPI schema: http://localhost:8000/api/v1/openapi.json

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Scheduled Tasks

Tasks are defined in `app/tasks/scheduled.py` and registered automatically on application startup. The scheduler uses PostgreSQL to persist job state.

To add a new scheduled task:

1. Define your task function in `app/tasks/scheduled.py`
2. Register it in the `register_scheduled_tasks()` function
3. Choose scheduling type:
   - Interval: `scheduler.add_job(func, 'interval', hours=1)`
   - Cron: `scheduler.add_job(func, 'cron', hour=0, minute=0)`
   - Date: `scheduler.add_job(func, 'date', run_date=datetime(...))`

## Testing

Run tests using pytest:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app
```

## Development

- The application uses structured logging with rotation
- Logs are stored in the `logs/` directory
- Debug mode can be enabled via the `DEBUG` environment variable
- The scheduler stores job state in the PostgreSQL database

## Environment Variables

See `.env.example` for all available configuration options:
- `DATABASE_URL`: PostgreSQL connection string
- `DEBUG`: Enable debug mode
- `SCHEDULER_TIMEZONE`: Timezone for scheduled tasks
- And more...