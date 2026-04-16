"""
Example script demonstrating the analytics scheduler functionality.

This script shows how to:
1. Initialize the analytics scheduler
2. Manually trigger the daily Clean Score calculation
3. View scheduled jobs
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scheduler import get_analytics_scheduler


def main():
    """
    Demonstrate analytics scheduler functionality.
    """
    print("=" * 60)
    print("Analytics Scheduler Example")
    print("=" * 60)
    
    # Get scheduler instance
    print("\n1. Initializing analytics scheduler...")
    scheduler = get_analytics_scheduler()
    print("   ✓ Scheduler initialized")
    
    # View configured jobs
    print("\n2. Viewing scheduled jobs:")
    jobs = scheduler.scheduler.get_jobs()
    for job in jobs:
        print(f"   - Job ID: {job.id}")
        print(f"     Name: {job.name}")
        print(f"     Trigger: {job.trigger}")
        print(f"     Next run: {job.next_run_time}")
    
    # Start scheduler
    print("\n3. Starting scheduler...")
    scheduler.start()
    print("   ✓ Scheduler started")
    print(f"   ✓ Scheduler running: {scheduler.scheduler.running}")
    
    # Manually trigger the daily calculation (for testing)
    print("\n4. Manually triggering daily Clean Score calculation...")
    print("   (This would normally run automatically at midnight)")
    
    try:
        scheduler.calculate_daily_clean_scores()
        print("   ✓ Daily calculation completed")
    except Exception as e:
        print(f"   ✗ Error during calculation: {e}")
        print("   (This is expected if databases are not running)")
    
    # Show what the job does
    print("\n5. Job Details:")
    print("   The daily Clean Score calculation job:")
    print("   - Runs at midnight (00:00) every day")
    print("   - Gets all locations from Oracle database")
    print("   - For each location:")
    print("     * Queries all sensors for that location")
    print("     * Aggregates telemetry data from MongoDB for previous day")
    print("     * Calculates average CO2, Noise, and Temperature")
    print("     * Computes Clean Score using the formula:")
    print("       Clean Score = 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)")
    print("     * Stores daily summary in Oracle TELEMETRY_SUMMARY table")
    
    # Shutdown scheduler
    print("\n6. Shutting down scheduler...")
    scheduler.shutdown()
    print("   ✓ Scheduler shutdown")
    print(f"   ✓ Scheduler running: {scheduler.scheduler.running}")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
