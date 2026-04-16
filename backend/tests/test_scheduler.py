"""
Unit tests for analytics scheduler module.

Tests scheduled job configuration and daily Clean Score calculation logic.
"""

import pytest
import sys
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock

# Mock cx_Oracle before importing any modules that depend on it
sys.modules['cx_Oracle'] = MagicMock()

from app.services.scheduler import AnalyticsScheduler, get_analytics_scheduler


class TestAnalyticsScheduler:
    """Test suite for AnalyticsScheduler class."""
    
    @patch('app.services.scheduler.get_analytics_service')
    @patch('app.services.scheduler.get_mongodb_client')
    @patch('app.services.scheduler.get_oracle_client')
    def test_scheduler_initialization(self, mock_oracle, mock_mongo, mock_analytics):
        """Test scheduler initializes with correct configuration."""
        scheduler = AnalyticsScheduler()
        
        assert scheduler.scheduler is not None
        assert scheduler.analytics_service is not None
        assert scheduler.mongodb_client is not None
        assert scheduler.oracle_client is not None
        
        # Verify job is configured
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == 'daily_clean_score_calculation'
    
    @patch('app.services.scheduler.get_analytics_service')
    @patch('app.services.scheduler.get_mongodb_client')
    @patch('app.services.scheduler.get_oracle_client')
    def test_calculate_daily_clean_scores_no_locations(self, mock_oracle, mock_mongo, mock_analytics):
        """Test daily calculation handles empty location list gracefully."""
        # Setup mocks
        mock_oracle_instance = Mock()
        mock_oracle_instance.get_location_hierarchy.return_value = []
        mock_oracle.return_value = mock_oracle_instance
        
        scheduler = AnalyticsScheduler()
        
        # Execute job
        scheduler.calculate_daily_clean_scores()
        
        # Verify no errors and appropriate logging
        mock_oracle_instance.get_location_hierarchy.assert_called_once()
    
    @patch('app.services.scheduler.get_analytics_service')
    @patch('app.services.scheduler.get_mongodb_client')
    @patch('app.services.scheduler.get_oracle_client')
    def test_calculate_daily_clean_scores_with_data(self, mock_oracle, mock_mongo, mock_analytics):
        """Test daily calculation processes locations with telemetry data."""
        # Setup mocks
        mock_oracle_instance = Mock()
        mock_oracle_instance.get_location_hierarchy.return_value = [
            {'locationid': 'ward_001', 'name': 'Ward 1'},
            {'locationid': 'ward_002', 'name': 'Ward 2'}
        ]
        mock_oracle_instance.get_sensors.return_value = [
            {'sensorid': 'sensor_001'}
        ]
        mock_oracle.return_value = mock_oracle_instance
        
        mock_mongo_instance = Mock()
        mock_mongo_instance.query_telemetry.return_value = [
            {'co2': 450.0, 'noise': 60.0, 'temperature': 25.0},
            {'co2': 460.0, 'noise': 65.0, 'temperature': 26.0}
        ]
        mock_mongo.return_value = mock_mongo_instance
        
        mock_analytics_instance = Mock()
        mock_analytics_instance.store_daily_summary.return_value = True
        mock_analytics.return_value = mock_analytics_instance
        
        scheduler = AnalyticsScheduler()
        
        # Execute job
        scheduler.calculate_daily_clean_scores()
        
        # Verify calls
        assert mock_oracle_instance.get_location_hierarchy.called
        assert mock_oracle_instance.get_sensors.call_count == 2
        assert mock_mongo_instance.query_telemetry.call_count == 2
        assert mock_analytics_instance.store_daily_summary.call_count == 2
    
    @patch('app.services.scheduler.get_analytics_service')
    @patch('app.services.scheduler.get_mongodb_client')
    @patch('app.services.scheduler.get_oracle_client')
    def test_aggregate_location_telemetry_no_sensors(self, mock_oracle, mock_mongo, mock_analytics):
        """Test aggregation returns None when location has no sensors."""
        mock_oracle_instance = Mock()
        mock_oracle_instance.get_sensors.return_value = []
        mock_oracle.return_value = mock_oracle_instance
        
        scheduler = AnalyticsScheduler()
        
        yesterday = date.today() - timedelta(days=1)
        start_time = datetime.combine(yesterday, datetime.min.time())
        end_time = datetime.combine(yesterday, datetime.max.time())
        
        result = scheduler._aggregate_location_telemetry('ward_001', start_time, end_time)
        
        assert result is None
    
    @patch('app.services.scheduler.get_analytics_service')
    @patch('app.services.scheduler.get_mongodb_client')
    @patch('app.services.scheduler.get_oracle_client')
    def test_aggregate_location_telemetry_with_data(self, mock_oracle, mock_mongo, mock_analytics):
        """Test aggregation calculates correct averages from telemetry data."""
        mock_oracle_instance = Mock()
        mock_oracle_instance.get_sensors.return_value = [
            {'sensorid': 'sensor_001'},
            {'sensorid': 'sensor_002'}
        ]
        mock_oracle.return_value = mock_oracle_instance
        
        mock_mongo_instance = Mock()
        mock_mongo_instance.query_telemetry.side_effect = [
            [
                {'co2': 400.0, 'noise': 50.0, 'temperature': 20.0},
                {'co2': 500.0, 'noise': 60.0, 'temperature': 25.0}
            ],
            [
                {'co2': 450.0, 'noise': 55.0, 'temperature': 22.0}
            ]
        ]
        mock_mongo.return_value = mock_mongo_instance
        
        scheduler = AnalyticsScheduler()
        
        yesterday = date.today() - timedelta(days=1)
        start_time = datetime.combine(yesterday, datetime.min.time())
        end_time = datetime.combine(yesterday, datetime.max.time())
        
        result = scheduler._aggregate_location_telemetry('ward_001', start_time, end_time)
        
        assert result is not None
        # Average of [400, 500, 450] = 450
        assert result['avg_co2'] == 450.0
        # Average of [50, 60, 55] = 55
        assert result['avg_noise'] == 55.0
        # Average of [20, 25, 22] = 22.33
        assert result['avg_temperature'] == 22.33
    
    @patch('app.services.scheduler.get_analytics_service')
    @patch('app.services.scheduler.get_mongodb_client')
    @patch('app.services.scheduler.get_oracle_client')
    def test_scheduler_start_and_shutdown(self, mock_oracle, mock_mongo, mock_analytics):
        """Test scheduler can be started and shutdown gracefully."""
        scheduler = AnalyticsScheduler()
        
        # Start scheduler
        scheduler.start()
        assert scheduler.scheduler.running
        
        # Shutdown scheduler
        scheduler.shutdown()
        assert not scheduler.scheduler.running
    
    @patch('app.services.scheduler.get_analytics_service')
    @patch('app.services.scheduler.get_mongodb_client')
    @patch('app.services.scheduler.get_oracle_client')
    def test_singleton_pattern(self, mock_oracle, mock_mongo, mock_analytics):
        """Test get_analytics_scheduler returns singleton instance."""
        scheduler1 = get_analytics_scheduler()
        scheduler2 = get_analytics_scheduler()
        
        assert scheduler1 is scheduler2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
