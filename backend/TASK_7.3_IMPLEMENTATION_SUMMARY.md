# Task 7.3 Implementation Summary

## Task Description
Implement scheduled analytics task to calculate Clean Score for all locations daily at midnight.

## Requirements
- **Requirement 8.5**: System SHALL recalculate Clean Score for all locations daily at midnight

## Implementation Overview

### Files Created

1. **backend/app/services/scheduler.py** (New)
   - Main scheduler module with `AnalyticsScheduler` class
   - Implements daily Clean Score calculation job
   - Uses APScheduler with CronTrigger for midnight execution
   - Aggregates telemetry data by location from MongoDB
   - Stores daily summaries in Oracle TELEMETRY_SUMMARY table

2. **backend/tests/test_scheduler.py** (New)
   - Comprehensive unit tests for scheduler functionality
   - Tests job configuration, data aggregation, and error handling
   - Mocks database dependencies for isolated testing

3. **backend/examples/example_scheduler.py** (New)
   - Example script demonstrating scheduler usage
   - Shows how to manually trigger jobs for testing
   - Documents job configuration and behavior

4. **backend/SCHEDULER_README.md** (New)
   - Complete documentation for the scheduler system
   - Architecture overview and data flow diagrams
   - Configuration, usage, and troubleshooting guides

### Files Modified

1. **backend/app/main.py**
   - Added import for `get_analytics_scheduler`
   - Added global `analytics_scheduler` variable
   - Integrated scheduler startup in `lifespan` function
   - Integrated scheduler shutdown in `lifespan` function

## Technical Details

### Scheduler Configuration

```python
# Job runs at midnight (00:00) every day
scheduler.add_job(
    func=calculate_daily_clean_scores,
    trigger=CronTrigger(hour=0, minute=0),
    id='daily_clean_score_calculation',
    misfire_grace_time=3600  # 1 hour grace period
)
```

### Daily Calculation Algorithm

1. **Get Locations**: Query all locations from Oracle using `get_location_hierarchy()`
2. **For Each Location**:
   - Get all sensors registered to the location
   - Query telemetry data from MongoDB for previous day
   - Aggregate CO2, Noise, and Temperature values
   - Calculate arithmetic mean for each metric
3. **Calculate Clean Score**: Use existing `calculate_clean_score()` method
4. **Store Summary**: Use existing `store_daily_summary()` method

### Data Aggregation Logic

```python
def _aggregate_location_telemetry(location_id, start_time, end_time):
    # Get sensors for location
    sensors = oracle_client.get_sensors(location_id)
    
    # Collect telemetry from all sensors
    all_co2_values = []
    all_noise_values = []
    all_temperature_values = []
    
    for sensor in sensors:
        telemetry_docs = mongodb_client.query_telemetry(
            sensor_id=sensor['sensorid'],
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        for doc in telemetry_docs:
            all_co2_values.append(doc['co2'])
            all_noise_values.append(doc['noise'])
            all_temperature_values.append(doc['temperature'])
    
    # Calculate averages
    return {
        'avg_co2': mean(all_co2_values),
        'avg_noise': mean(all_noise_values),
        'avg_temperature': mean(all_temperature_values)
    }
```

### Integration with FastAPI

The scheduler is integrated into the FastAPI application lifecycle:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    analytics_scheduler = get_analytics_scheduler()
    analytics_scheduler.start()
    logger.info("Analytics scheduler started successfully")
    
    yield
    
    # Shutdown
    analytics_scheduler.shutdown()
    logger.info("Analytics scheduler shutdown")
```

## Key Features

1. **Automatic Execution**: Runs daily at midnight without manual intervention
2. **Comprehensive Aggregation**: Processes all locations and their sensors
3. **Error Handling**: Gracefully handles missing data and connection failures
4. **Logging**: Detailed logging of job execution and progress
5. **Singleton Pattern**: Ensures only one scheduler instance exists
6. **Graceful Shutdown**: Properly cleans up resources on application shutdown

## Dependencies

- **APScheduler 3.10.4**: Already in requirements.txt
- **Existing Services**:
  - `AnalyticsService`: For Clean Score calculation and storage
  - `MongoDBClient`: For telemetry data queries
  - `OracleClient`: For location and sensor queries

## Testing

### Unit Tests
- Test scheduler initialization
- Test job configuration
- Test data aggregation logic
- Test error handling
- Test singleton pattern

### Manual Testing
Run the example script:
```bash
python backend/examples/example_scheduler.py
```

### Integration Testing
Start the FastAPI application and verify:
1. Scheduler starts on application startup
2. Job is configured with correct trigger
3. Scheduler shuts down gracefully on application shutdown

## Validation

This implementation validates:

- ✅ **Requirement 8.5**: System recalculates Clean Score for all locations daily at midnight
- ✅ **Requirement 8.3**: Daily summaries stored in TELEMETRY_SUMMARY table
- ✅ **Requirement 8.1**: Clean Score formula correctly applied
- ✅ **Requirement 8.2**: CO2 and Noise normalization ranges used

## Usage

### Starting the Application
```bash
# Scheduler starts automatically with the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Manual Trigger (Testing)
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
    print(f"Job: {job.name}, Next run: {job.next_run_time}")
```

## Performance Considerations

- **Execution Time**: Depends on number of locations and data volume
- **Database Load**: Runs during off-peak hours (midnight)
- **Memory Usage**: Minimal - processes one location at a time
- **Connection Pooling**: Reuses existing database connections

## Error Handling

The scheduler handles various error scenarios:

1. **No Locations**: Logs warning and exits gracefully
2. **No Sensors**: Skips location and continues
3. **No Telemetry Data**: Logs debug message and continues
4. **Database Errors**: Logs error and continues to next location
5. **Calculation Errors**: Logs error and continues processing

## Logging Output

```
INFO - Starting daily Clean Score calculation job...
INFO - Processing telemetry data for date: 2024-01-15
INFO - Found 50 locations to process
DEBUG - Processed location ward_001: {'avg_co2': 420.5, 'avg_noise': 55.2, 'avg_temperature': 26.3}
INFO - Stored daily summary for location ward_001 on 2024-01-15: CO2=420.50, Noise=55.20, Temp=26.30, CleanScore=68.09
INFO - Daily Clean Score calculation completed: 48 successful, 2 errors
```

## Future Enhancements

Potential improvements:
1. Parallel processing for multiple locations
2. Incremental updates (only locations with new data)
3. Historical backfill job
4. Job execution metrics and monitoring
5. Admin dashboard for job management

## Conclusion

Task 7.3 has been successfully implemented with:
- ✅ Scheduled daily job at midnight
- ✅ Aggregation of telemetry data by location
- ✅ Clean Score calculation and storage
- ✅ Comprehensive error handling and logging
- ✅ Integration with FastAPI application lifecycle
- ✅ Unit tests and example scripts
- ✅ Complete documentation

The scheduler is production-ready and meets all requirements specified in the task.
