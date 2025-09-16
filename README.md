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

### Available Endpoints

#### Health Check
- `GET /api/v1/health` - Application health status

#### AQI Locations
- `GET /api/v1/locations/` - Retrieve all AQI monitoring locations
  - Returns JSON array of location objects with metadata
  - Includes location details, device information, and timestamps

#### AQI History Data
- `GET /api/v1/history/{location_id}/hours?hours=N` - Retrieve AQI history for past N hours
  - `location_id`: External location identifier
  - `hours`: Number of hours to retrieve (1-168, default: 24)
  - Returns measurement records sorted by time (most recent first)
- `GET /api/v1/history/{location_id}/days?days=N` - Retrieve AQI history for past N days  
  - `location_id`: External location identifier
  - `days`: Number of days to retrieve (1-365, required)
  - Returns measurement records sorted by time (most recent first)
- `GET /api/v1/history/{location_id}/week` - Retrieve 30-minute aggregated AQI history for past 7 days
  - `location_id`: External location identifier
  - Returns 30-minute averaged measurement records for the past week
  - Data sorted by time (oldest first) for chronological visualization

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

Tasks are organized into separate modules under `app/tasks/` and registered automatically on application startup. The scheduler uses PostgreSQL to persist job state.

### Task Organization

- `app/tasks/airgradient_task.py`: AirGradient API data collection tasks
- `app/tasks/aggregation_task.py`: Data aggregation and processing tasks
- `app/tasks/utils.py`: Shared task utilities and logging functions
- `app/tasks/scheduled.py`: Task registration and scheduling configuration

### Active Scheduled Tasks

- **AirGradient Data Pull** (`pull_airgradient_data`):
  - Runs every 15 minutes
  - Fetches the last hour's air quality data from AirGradient API
  - Processes all locations in the `aqi_location` table
  - Saves measurement data to `aqi_5_minute_history` table
  - Prevents duplicate data insertion
  - Logs all activity to `task_logs` table

- **30-Minute Data Aggregation** (`aggregate_30_minute_data`):
  - Runs every 30 minutes
  - Aggregates 5-minute AQI data into 30-minute averages
  - Averages key fields: rco2_corrected, atmp, tvoc, tvocIndex, rhum_corrected, pm02_corrected
  - Includes 30-minute buffer to ensure complete 5-minute data availability
  - Stores aggregated data in `aqi_30_minute_history` table
  - Rounds averaged values to 2 decimal places for consistency

### Adding New Scheduled Tasks

To add a new scheduled task:

1. Define your task function in the appropriate module under `app/tasks/`
2. Register it in `app/tasks/scheduled.py` in the `register_scheduled_tasks()` function
3. Choose scheduling type:
   - Interval: `scheduler.add_job(func, 'interval', hours=1)`
   - Cron: `scheduler.add_job(func, 'cron', hour=0, minute=0)`
   - Date: `scheduler.add_job(func, 'date', run_date=datetime(...))`

### Manual Task Execution

CLI runners are available for manual task execution:
- `python run_airgradient_task.py`: Manually pull AirGradient data
- `python run_aggregation_task.py`: Manually run 30-minute data aggregation

## Testing

Run tests using pytest:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_health.py
pytest tests/test_locations.py  
pytest tests/test_history.py

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

### AQI 30-Minute History (`aqi_30_minute_history`)
Stores aggregated AQI measurement data at 30-minute intervals:
- `id`: Primary key
- `measure_time`: Timestamp of 30-minute window start (indexed for performance)
- `aqi_location_id`: Foreign key to `aqi_location.id`
- `measure_data`: JSONB field containing averaged measurement values
- `created_at`, `updated_at`: Automatic timestamps
- Data is automatically aggregated from 5-minute history by scheduled tasks

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

## Useful links - deployment
https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-22-04  
https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-20-04  
https://hereiskunalverma.medium.com/how-to-deploy-fastapi-python-on-digital-ocean-droplet-54193bf469a1  
https://www.femiadigun.com/devops/cicd/do  
https://code2deploy.com/blog/comprehensive-guide-to-setting-up-postgresql-in-a-production-environment/  
https://learnsql.com/blog/postgresql-cheat-sheet/postgresql-cheat-sheet-a4.pdf  
https://santoshm.com.np/2024/02/15/deploying-a-fastapi-project-on-a-linux-server-with-nginx-and-systemd-service-a-simplified-guide-with-uvicorn-and-hot-reload/  