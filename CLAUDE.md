# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI backend application with PostgreSQL database integration and scheduled task management using APScheduler. The project is designed for air quality index (AQI) monitoring for Nettelhorst.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment (required before all commands)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install/update dependencies
pip install -r requirements.txt
```

### Database Operations
```bash
# Create database (first time only)
createdb nettelhorst_aqi

# Generate migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Running the Application
```bash
# Development server with auto-reload
python -m uvicorn app.main:app --reload

# Alternative method
python app/main.py
```

### Testing
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

## Architecture Overview

### Core Application Structure

The application follows a layered architecture with clear separation of concerns:

1. **Entry Point** (`app/main.py`)
   - FastAPI application initialization
   - Lifecycle management (startup/shutdown events)
   - APScheduler initialization on startup
   - CORS middleware configuration
   - Global exception handlers
   - Root API router inclusion

2. **Configuration Layer** (`app/core/`)
   - `config.py`: Pydantic settings management reading from `.env`
   - `database.py`: SQLAlchemy engine and session management (sync/async)
   - `scheduler.py`: APScheduler configuration with PostgreSQL job persistence
   - `logging.py`: Structured logging with file rotation

3. **Data Layer**
   - `app/models/`: SQLAlchemy ORM models (Base class from `database.py`)
   - `app/schemas/`: Pydantic models for request/response validation
   - Database uses PostgreSQL with both sync and async connection support

4. **API Layer** (`app/api/v1/`)
   - `api.py`: Main API router aggregator
   - `endpoints/`: Individual endpoint modules
   - All routes prefixed with `/api/v1`

5. **Business Logic**
   - `app/services/`: Business logic layer (currently empty, ready for implementation)
   - `app/crud/`: Database operations layer (currently empty, ready for implementation)

6. **Scheduled Tasks** (`app/tasks/`)
   - `scheduled.py`: Task definitions and registration
   - Tasks persist in PostgreSQL via APScheduler's SQLAlchemyJobStore
   - Registered during application startup

### Key Design Patterns

1. **Dependency Injection**: Database sessions injected via FastAPI's `Depends()`
2. **Async/Await**: Full async support with `asyncpg` for database operations
3. **Environment-based Config**: All settings loaded from `.env` via pydantic-settings
4. **Lifecycle Management**: Uses FastAPI's lifespan context manager for startup/shutdown

### Database Schema

Currently includes:
- `TaskLog` model: Tracks scheduled task execution history

### Important Configuration

The application expects these environment variables (see `.env.example`):
- `DATABASE_URL`: PostgreSQL connection string (sync)
- `DATABASE_URL_ASYNC`: Automatically derived if not provided
- `DEBUG`: Enables debug logging and auto-reload
- `SCHEDULER_TIMEZONE`: Timezone for scheduled tasks (default: UTC)

### API Documentation

When running, interactive documentation available at:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

### Current Endpoints

- `GET /api/v1/health`: Basic health check endpoint

## Important Notes

- Always activate the virtual environment before running any commands
- Database name is `nettelhorst_aqi` (not a generic name)
- Scheduler stores job state in PostgreSQL, survives restarts
- Logs are written to `logs/` directory with rotation
- All models must be imported in `app/models/__init__.py` for Alembic to detect them