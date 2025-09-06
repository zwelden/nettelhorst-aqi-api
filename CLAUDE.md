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

# Seed database with initial data
python seed_database.py
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
pytest tests/test_locations.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app
```

#### Test Structure
- `tests/conftest.py`: SQLite test database configuration with JSONB compatibility
- `tests/test_health.py`: Health endpoint tests
- `tests/test_locations.py`: AQI locations endpoint tests (6 comprehensive test cases)
- Tests use temporary SQLite databases for isolation (no mocks required)

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

7. **Database Seeding** (`app/db/`)
   - `seed.py`: Database seeding functions and utilities
   - Contains initial data for AQI locations
   - Prevents duplicate entries during seeding operations

### Key Design Patterns

1. **Dependency Injection**: Database sessions injected via FastAPI's `Depends()`
2. **Async/Await**: Full async support with `asyncpg` for database operations
3. **Environment-based Config**: All settings loaded from `.env` via pydantic-settings
4. **Lifecycle Management**: Uses FastAPI's lifespan context manager for startup/shutdown

### Database Schema

The application includes the following main database tables:

#### AQI Location (`aqi_location`)
Stores information about AQI monitoring locations and devices:
- `id` (INTEGER, PRIMARY KEY): Auto-incrementing primary key
- `location_id` (INTEGER, NOT NULL): Unique location identifier
- `location_name` (TEXT, NOT NULL): Human-readable location name
- `location_description` (TEXT, NOT NULL): Detailed location description
- `serial_no` (VARCHAR(24), NOT NULL): Device serial number
- `model` (VARCHAR(120), NOT NULL): Device model information
- `firmware_version` (VARCHAR(10), NOT NULL): Device firmware version
- `created_at` (TIMESTAMP(3), NOT NULL, DEFAULT CURRENT_TIMESTAMP): Creation timestamp
- `updated_at` (TIMESTAMP(3), NOT NULL): Last update timestamp (auto-updated)

#### AQI 5-Minute History (`aqi_5_minute_history`)
Stores AQI measurement data at 5-minute intervals:
- `id` (INTEGER, PRIMARY KEY): Auto-incrementing primary key
- `measure_time` (TIMESTAMP(3), NOT NULL, INDEXED): Timestamp of measurement (indexed for performance)
- `aqi_location_id` (INTEGER, NOT NULL, FK): Foreign key to `aqi_location.id`
- `measure_data` (JSONB, NOT NULL): Flexible measurement data storage in JSON format
- `created_at` (TIMESTAMP(3), NOT NULL, DEFAULT CURRENT_TIMESTAMP): Creation timestamp
- `updated_at` (TIMESTAMP(3), NOT NULL): Last update timestamp (auto-updated)

#### Task Logs (`task_logs`)
Tracks scheduled task execution history:
- `id` (INTEGER, PRIMARY KEY): Auto-incrementing primary key
- `task_name` (STRING, NOT NULL, INDEXED): Name of the executed task
- `status` (STRING, NOT NULL): Execution status ('started', 'completed', 'failed')
- `started_at` (DATETIME): Task start timestamp
- `completed_at` (DATETIME, NULLABLE): Task completion timestamp
- `error_message` (TEXT, NULLABLE): Error details if task failed
- `result` (TEXT, NULLABLE): Task execution result
- `is_successful` (BOOLEAN, DEFAULT FALSE): Success flag

#### Key Relationships
- `aqi_5_minute_history.aqi_location_id` → `aqi_location.id` (Foreign Key)
- SQLAlchemy relationships configured for easy navigation between models

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
- `GET /api/v1/locations/`: Retrieve all AQI monitoring locations
  - Returns JSON array of location objects with complete metadata
  - Uses `AqiDataService` for database operations
  - Includes location details, device information, and timestamps

## Important Notes

- Always activate the virtual environment before running any commands
- Database name is `nettelhorst_aqi` 
- Scheduler stores job state in PostgreSQL, survives restarts
- Logs are written to `logs/` directory with rotation
- All models must be imported in `app/models/__init__.py` for Alembic to detect them