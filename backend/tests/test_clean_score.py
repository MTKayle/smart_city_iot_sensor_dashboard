"""
Unit tests for Clean Score calculation.

Tests the calculate_clean_score() function to ensure correct normalization
and scoring according to the formula:
- normalized_CO2 = (avgCO2 / 2000) * 100
- normalized_Noise = (avgNoise / 100) * 100
- cleanScore = 100 - (normalized_CO2 * 0.5 + normalized_Noise * 0.5)

Validates: Requirements 8.1, 8.2
"""

import pytest
from unittest.mock import Mock, patch


# Mock the database clients before importing the service
@patch('app.db.mongodb_client.get_mongodb_client')
@patch('app.db.oracle_client.get_oracle_client')
def test_clean_score_with_example_values(mock_oracle, mock_mongo):
    """Test Clean Score calculation with example values from design doc."""
    from app.services.analytics_service import AnalyticsService
    
    # Example from design: avgCO2=420.5, avgNoise=55.2
    # normalized_CO2 = (420.5 / 2000) * 100 = 21.025
    # normalized_Noise = (55.2 / 100) * 100 = 55.2
    # cleanScore = 100 - (21.025 * 0.5 + 55.2 * 0.5) = 100 - 38.1125 = 61.8875
    
    analytics_service = AnalyticsService()
    clean_score = analytics_service.calculate_clean_score(420.5, 55.2)
    
    # Expected: 61.89 (rounded to 2 decimal places)
    assert clean_score == 61.89


@patch('app.db.mongodb_client.get_mongodb_client')
@patch('app.db.oracle_client.get_oracle_client')
def test_clean_score_with_zero_values(mock_oracle, mock_mongo):
    """Test Clean Score with perfect conditions (zero pollution)."""
    from app.services.analytics_service import AnalyticsService
    
    # normalized_CO2 = (0 / 2000) * 100 = 0
    # normalized_Noise = (0 / 100) * 100 = 0
    # cleanScore = 100 - (0 * 0.5 + 0 * 0.5) = 100
    
    analytics_service = AnalyticsService()
    clean_score = analytics_service.calculate_clean_score(0, 0)
    
    assert clean_score == 100.0


@patch('app.db.mongodb_client.get_mongodb_client')
@patch('app.db.oracle_client.get_oracle_client')
def test_clean_score_with_max_values(mock_oracle, mock_mongo):
    """Test Clean Score with maximum pollution levels."""
    from app.services.analytics_service import AnalyticsService
    
    # normalized_CO2 = (2000 / 2000) * 100 = 100
    # normalized_Noise = (100 / 100) * 100 = 100
    # cleanScore = 100 - (100 * 0.5 + 100 * 0.5) = 100 - 100 = 0
    
    analytics_service = AnalyticsService()
    clean_score = analytics_service.calculate_clean_score(2000, 100)
    
    assert clean_score == 0.0


@patch('app.db.mongodb_client.get_mongodb_client')
@patch('app.db.oracle_client.get_oracle_client')
def test_clean_score_with_mid_range_values(mock_oracle, mock_mongo):
    """Test Clean Score with mid-range pollution levels."""
    from app.services.analytics_service import AnalyticsService
    
    # normalized_CO2 = (1000 / 2000) * 100 = 50
    # normalized_Noise = (50 / 100) * 100 = 50
    # cleanScore = 100 - (50 * 0.5 + 50 * 0.5) = 100 - 50 = 50
    
    analytics_service = AnalyticsService()
    clean_score = analytics_service.calculate_clean_score(1000, 50)
    
    assert clean_score == 50.0


@patch('app.db.mongodb_client.get_mongodb_client')
@patch('app.db.oracle_client.get_oracle_client')
def test_clean_score_high_co2_low_noise(mock_oracle, mock_mongo):
    """Test Clean Score with high CO2 but low noise."""
    from app.services.analytics_service import AnalyticsService
    
    # normalized_CO2 = (1500 / 2000) * 100 = 75
    # normalized_Noise = (20 / 100) * 100 = 20
    # cleanScore = 100 - (75 * 0.5 + 20 * 0.5) = 100 - 47.5 = 52.5
    
    analytics_service = AnalyticsService()
    clean_score = analytics_service.calculate_clean_score(1500, 20)
    
    assert clean_score == 52.5


@patch('app.db.mongodb_client.get_mongodb_client')
@patch('app.db.oracle_client.get_oracle_client')
def test_clean_score_low_co2_high_noise(mock_oracle, mock_mongo):
    """Test Clean Score with low CO2 but high noise."""
    from app.services.analytics_service import AnalyticsService
    
    # normalized_CO2 = (300 / 2000) * 100 = 15
    # normalized_Noise = (85 / 100) * 100 = 85
    # cleanScore = 100 - (15 * 0.5 + 85 * 0.5) = 100 - 50 = 50
    
    analytics_service = AnalyticsService()
    clean_score = analytics_service.calculate_clean_score(300, 85)
    
    assert clean_score == 50.0


@patch('app.db.mongodb_client.get_mongodb_client')
@patch('app.db.oracle_client.get_oracle_client')
def test_clean_score_returns_float(mock_oracle, mock_mongo):
    """Test that Clean Score returns a float value."""
    from app.services.analytics_service import AnalyticsService
    
    analytics_service = AnalyticsService()
    clean_score = analytics_service.calculate_clean_score(500, 60)
    
    assert isinstance(clean_score, float)


@patch('app.db.mongodb_client.get_mongodb_client')
@patch('app.db.oracle_client.get_oracle_client')
def test_clean_score_rounded_to_two_decimals(mock_oracle, mock_mongo):
    """Test that Clean Score is rounded to 2 decimal places."""
    from app.services.analytics_service import AnalyticsService
    
    # Use values that would produce many decimal places
    analytics_service = AnalyticsService()
    clean_score = analytics_service.calculate_clean_score(333.333, 66.666)
    
    # Check that result has at most 2 decimal places
    assert len(str(clean_score).split('.')[-1]) <= 2


@patch('app.db.mongodb_client.get_mongodb_client')
@patch('app.db.oracle_client.get_oracle_client')
def test_clean_score_equal_weighting(mock_oracle, mock_mongo):
    """Test that CO2 and Noise have equal weighting (50% each)."""
    from app.services.analytics_service import AnalyticsService
    
    analytics_service = AnalyticsService()
    
    # Test case 1: Only CO2 at max
    score_co2_only = analytics_service.calculate_clean_score(2000, 0)
    # cleanScore = 100 - (100 * 0.5 + 0 * 0.5) = 50
    assert score_co2_only == 50.0
    
    # Test case 2: Only Noise at max
    score_noise_only = analytics_service.calculate_clean_score(0, 100)
    # cleanScore = 100 - (0 * 0.5 + 100 * 0.5) = 50
    assert score_noise_only == 50.0
    
    # Both should contribute equally
    assert score_co2_only == score_noise_only


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

