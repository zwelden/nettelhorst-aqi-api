# Nettelhorst AQI Backend

A FastAPI backend application for monitoring Air Quality Index (AQI) data at Nettelhorst, with PostgreSQL database integration and scheduled task management using APScheduler.

## Features

- FastAPI web framework with async support
- PostgreSQL database with SQLAlchemy ORM
- Database migrations with Alembic
- Scheduled tasks with APScheduler
- **Automated AirGradient API data collection** - pulls air quality data every 15 minutes
- AQI location and history tracking
- JSONB support for flexible measurement data storage
- Structured logging with task execution tracking
- Environment-based configuration
- CORS middleware
- Error handling and resilience

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
   # Edit .env with your database credentials and AirGradient API token
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

### Active Scheduled Tasks

- **AirGradient Data Pull** (`pull_airgradient_data`):
  - Runs every 15 minutes
  - Fetches the last hour's air quality data from AirGradient API
  - Processes all locations in the `aqi_location` table
  - Saves measurement data to `aqi_5_minute_history` table
  - Prevents duplicate data insertion
  - Logs all activity to `task_logs` table

### Adding New Scheduled Tasks

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

## Database Schema

The application includes the following main database tables:

### AQI Location (`aqi_location`)
Stores information about AQI monitoring locations:
- `id`: Primary key
- `location_id`: Unique location identifier
- `location_name`: Human-readable location name
- `location_description`: Detailed location description
- `serial_no`: Device serial number (24 chars max)
- `model`: Device model (120 chars max)
- `firmware_version`: Device firmware version (10 chars max)
- `created_at`, `updated_at`: Automatic timestamps

### AQI 5-Minute History (`aqi_5_minute_history`)
Stores AQI measurement data at 5-minute intervals:
- `id`: Primary key
- `measure_time`: Timestamp of measurement (indexed for performance)
- `aqi_location_id`: Foreign key to `aqi_location.id`
- `measure_data`: JSONB field for flexible measurement data storage
- `created_at`, `updated_at`: Automatic timestamps

### Task Logs (`task_logs`)
Tracks scheduled task execution:
- Task execution status, timestamps, and error handling

## Development

- The application uses structured logging with rotation
- Logs are stored in the `logs/` directory
- Debug mode can be enabled via the `DEBUG` environment variable
- The scheduler stores job state in the PostgreSQL database
- All models must be imported in `app/models/__init__.py` for Alembic to detect them

## Environment Variables

See `.env.example` for all available configuration options:

### Database
- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_URL_ASYNC`: Async PostgreSQL connection string (auto-generated if not provided)

### Application
- `DEBUG`: Enable debug mode
- `API_V1_PREFIX`: API route prefix (default: `/api/v1`)

### Scheduler
- `SCHEDULER_TIMEZONE`: Timezone for scheduled tasks (default: `UTC`)
- `SCHEDULER_JOB_DEFAULTS_COALESCE`: Job coalescing setting
- `SCHEDULER_JOB_DEFAULTS_MAX_INSTANCES`: Maximum job instances

### AirGradient API
- `AIRGRADIENT_API_TOKEN`: **Required** - API token for AirGradient API access
- `AIRGRADIENT_API_BASE_URL`: AirGradient API base URL (default: `https://api.airgradient.com/public/api/v1`)

## Monitoring and Troubleshooting

### Task Execution Monitoring
- Check `task_logs` table for scheduled task execution history
- View application logs in `logs/` directory
- Monitor task status: `started`, `completed`, `failed`

### Data Collection Status
- Verify data collection in `aqi_5_minute_history` table
- Check for recent timestamps in `measure_time` column
- Review `measure_data` JSONB field for complete API response data

### Common Issues
- **No data being collected**: Verify `AIRGRADIENT_API_TOKEN` is valid
- **Task failures**: Check `task_logs.error_message` for details
- **Missing locations**: Ensure locations exist in `aqi_location` table