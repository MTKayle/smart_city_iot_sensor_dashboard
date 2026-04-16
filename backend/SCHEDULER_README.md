# Analytics Scheduler

## Overview

The Analytics Scheduler is a background task system that automatically calculates Clean Scores for all locations on a daily basis. It uses APScheduler to run scheduled jobs at specific times.

## Features

- **Daily Clean Score Calculation**: Runs at midnight (00:00) every day
- **Automatic Aggregation**: Aggregates telemetry data from MongoDB by location
- **Clean Score Computation**: Calculates environmental quality scores
- **Persistent Storage**: Stores daily summaries in Oracle database
- **Error Handling**: Gracefully handles errors and logs progress

## Architecture

### Components

1. **AnalyticsScheduler**: Main scheduler class that manages background jobs
2. **BackgroundScheduler**: APScheduler component for non-blocking execution
3. **CronTrigger**: Defines when jobs should run (midnight daily)

### Data Flow

```
Midnight Trigger
    ↓
Get All Locations (Oracle)
    ↓
For Each Location:
    ↓
    Get Sensors for Location (Oracle)
    ↓
    Query Telemetry Data (MongoDB)
    ↓
    Calculate Averages (CO2, Noise, Temperature)
    ↓
    Calculate Clean Score
    ↓
    Store Daily Summary (Oracle)
```

## Implementation Details

### Scheduled Job Configuration

```python
# Job runs at midnight (00:00) every day
scheduler.add_job(
    func=calculate_daily_clean_scores,
    trigger=CronTrigger(hour=0, minute=0),
    id='daily_clean_score_calculation',
    misfire_grace_time=3600  # 1 hour grace period
)
```

### Clean Score Formula

```
normalized_CO2 = (avgCO2 / 2000) * 100
normalized_Noise = (avgNoise / 100) * 100
Clean Score = 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)
```

Higher scores indicate better environmental quality.

### Aggregation Logic

For each location:
1. Query all sensors registered to that location
2. For each sensor, query telemetry data for the previous day
3. Collect all CO2, Noise, and Temperature values
4. Calculate arithmetic mean for each metric
5. Store aggregated data with Clean Score

## Integration

### FastAPI Application Startup

The scheduler is integrated into the FastAPI application lifecycle:

```python
# In app/main.py

from app.services.scheduler import get_analytics_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    analytics_scheduler = get_analytics_scheduler()
    analytics_scheduler.start()
    
    yield
    
    # Shutdown
    analytics_scheduler.shutdown()
```

### Singleton Pattern

The scheduler uses a singleton pattern to ensure only one instance exists:

```python
from app.services.scheduler import get_analytics_scheduler

scheduler = get_analytics_scheduler()
```

## Usage

### Starting the Scheduler

The scheduler starts automatically when the FastAPI application starts:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Manual Trigger (Testing)

For testing purposes, you can manually trigger the daily calculation:

```python
from app.services.scheduler import get_analytics_scheduler

scheduler = get_analytics_scheduler()
scheduler.calculate_daily_clean_scores()
```

### Viewing Scheduled Jobs

```python
scheduler = get_analytics_scheduler()
jobs = scheduler.scheduler.get_jobs()

for job in jobs:
    print(f"Job: {job.name}")
    print(f"Next run: {job.next_run_time}")
```

## Configuration

### Environment Variables

The scheduler uses the same database configuration as other services:

- `MONGODB_URI`: MongoDB connection string
- `ORACLE_USER`: Oracle database username
- `ORACLE_PASSWORD`: Oracle database password
- `ORACLE_DSN`: Oracle database DSN

### Job Schedule

To modify the schedule, edit the CronTrigger in `scheduler.py`:

```python
# Run at 2:00 AM instead of midnight
trigger=CronTrigger(hour=2, minute=0)

# Run every 6 hours
trigger=CronTrigger(hour='*/6')

# Run on specific days
trigger=CronTrigger(day_of_week='mon,wed,fri', hour=0, minute=0)
```

## Error Handling

The scheduler implements comprehensive error handling:

1. **Connection Failures**: Retries with exponential backoff
2. **Missing Data**: Logs warning and continues to next location
3. **Calculation Errors**: Logs error and continues processing
4. **Job Failures**: Logs error but doesn't crash the application

### Logging

All scheduler activities are logged:

```
INFO - Starting daily Clean Score calculation job...
INFO - Processing telemetry data for date: 2024-01-15
INFO - Found 50 locations to process
DEBUG - Processed location ward_001: {'avg_co2': 420.5, 'avg_noise': 55.2, 'avg_temperature': 26.3}
INFO - Daily Clean Score calculation completed: 48 successful, 2 errors
```

## Testing

### Unit Tests

Run the scheduler unit tests:

```bash
pytest backend/tests/test_scheduler.py -v
```

### Example Script

Run the example script to see the scheduler in action:

```bash
python backend/examples/example_scheduler.py
```

## Performance Considerations

### Scalability

- **Batch Processing**: Processes all locations in a single job
- **Connection Pooling**: Reuses database connections
- **Efficient Queries**: Uses indexes for fast data retrieval
- **Limit Handling**: Configurable limit for telemetry queries

### Resource Usage

- **Memory**: Minimal - processes one location at a time
- **CPU**: Low - simple arithmetic calculations
- **Database Load**: Moderate - queries run during off-peak hours (midnight)
- **Execution Time**: Depends on number of locations and data volume

### Optimization Tips

1. **Index Optimization**: Ensure MongoDB has indexes on (sensorId, timestamp)
2. **Query Limits**: Adjust telemetry query limit based on data volume
3. **Parallel Processing**: Consider parallel processing for large deployments
4. **Caching**: Cache location and sensor data to reduce queries

## Troubleshooting

### Scheduler Not Running

Check if the scheduler is started:

```python
scheduler = get_analytics_scheduler()
print(f"Running: {scheduler.scheduler.running}")
```

### Jobs Not Executing

1. Check job configuration:
   ```python
   jobs = scheduler.scheduler.get_jobs()
   print(jobs)
   ```

2. Check logs for errors
3. Verify database connections
4. Check system time and timezone

### Missing Data

If daily summaries are not being created:

1. Verify locations exist in Oracle
2. Verify sensors are registered to locations
3. Verify telemetry data exists in MongoDB
4. Check date range calculations
5. Review error logs

## Requirements Validation

This implementation validates:

- **Requirement 8.5**: System recalculates Clean Score for all locations daily at midnight
- **Requirement 8.3**: Daily Clean Score summaries stored in TELEMETRY_SUMMARY table
- **Requirement 8.1**: Clean Score calculation formula implemented correctly
- **Requirement 8.2**: CO2 and Noise normalization ranges applied

## Future Enhancements

Potential improvements:

1. **Parallel Processing**: Process multiple locations concurrently
2. **Incremental Updates**: Update only locations with new data
3. **Historical Backfill**: Job to calculate summaries for past dates
4. **Alerting**: Notify administrators of job failures
5. **Metrics**: Track job execution time and success rate
6. **Dashboard**: Web UI to view job status and history
