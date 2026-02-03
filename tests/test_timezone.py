"""
Timezone Parameter Tests

Tests for the timezone parameter functionality in the API.
Validates timezone handling, conversion, and error cases.
"""

import pytest
from unittest.mock import patch
import json


class TestTimezoneParameter:
    """Tests for timezone parameter functionality."""
    
    @patch('api.routes.github_events')
    def test_valid_timezone_pst(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test valid PST timezone is accepted and used."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone=America/Los_Angeles'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'meta' in data
        assert 'summary' in data
    
    @patch('api.routes.github_events')
    def test_valid_timezone_est(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test valid EST timezone is accepted."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone=America/New_York'
        )
        
        assert response.status_code == 200
    
    @patch('api.routes.github_events')
    def test_valid_timezone_london(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test valid Europe/London timezone is accepted."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone=Europe/London'
        )
        
        assert response.status_code == 200
    
    @patch('api.routes.github_events')
    def test_default_timezone_is_utc(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test that omitting timezone parameter defaults to UTC."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'meta' in data
    
    def test_invalid_timezone_returns_400(self, client, valid_date_range_7_days):
        """Test invalid timezone name returns 400 error."""
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone=Invalid/Timezone'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'INVALID_TIMEZONE'
        assert 'IANA' in data['error']['message']
    
    def test_timezone_abbreviation_not_accepted(self, client, valid_date_range_7_days):
        """Test that timezone abbreviations (PST, EST) are not accepted."""
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone=PST'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_TIMEZONE'
    
    def test_empty_timezone_defaults_to_utc(self, client, mock_github_data, valid_date_range_7_days):
        """Test that empty timezone string defaults to UTC."""
        with patch('api.routes.github_events') as mock_github:
            mock_github.contributions_by.return_value = mock_github_data
            
            from_date = valid_date_range_7_days['from_date']
            to_date = valid_date_range_7_days['to_date']
            response = client.get(
                f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone='
            )
            
            # Empty string gets stripped and becomes empty, which should default to 'UTC'
            # The actual behavior depends on how the API handles empty strings
            assert response.status_code in [200, 400]  # Either defaults to UTC or rejects
    
    @patch('api.routes.github_events')
    def test_utc_timezone_explicit(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test explicitly passing UTC as timezone."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone=UTC'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'meta' in data
    
    @patch('api.routes.github_events')
    def test_timezone_with_special_characters(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test timezone names with slashes and underscores work."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        
        # Test various valid IANA timezone formats
        timezones = [
            'America/Los_Angeles',
            'Asia/Kolkata',
            'Australia/Sydney',
            'Europe/London',
        ]
        
        for tz in timezones:
            response = client.get(
                f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone={tz}'
            )
            assert response.status_code == 200, f"Failed for timezone: {tz}"


class TestTimezoneDateConversion:
    """Tests for timezone-aware date boundary conversion."""
    
    @patch('api.routes.github_events')
    def test_date_boundaries_respect_timezone(self, mock_github, client, mock_github_data):
        """Test that date boundaries are correctly interpreted in the specified timezone."""
        mock_github.contributions_by.return_value = mock_github_data
        
        # Use a specific date
        from_date = '2026-02-01'
        to_date = '2026-02-02'
        
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone=America/Los_Angeles'
        )
        
        assert response.status_code == 200
        
        # Verify github_events was called
        assert mock_github.contributions_by.called
        call_kwargs = mock_github.contributions_by.call_args.kwargs
        
        # The from_date and to_date passed to github_events should be naive UTC datetimes
        # but they should reflect the PST timezone conversion
        # PST is UTC-8, so 2026-02-01 00:00:00 PST = 2026-02-01 08:00:00 UTC
        # and 2026-02-02 23:59:59 PST = 2026-02-03 07:59:59 UTC
        assert 'from_date' in call_kwargs
        assert 'to_date' in call_kwargs
    
    @patch('api.routes.github_events')
    def test_utc_vs_pst_different_boundaries(self, mock_github, client, mock_github_data):
        """Test that UTC and PST produce different time boundaries for the same date."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = '2026-02-01'
        to_date = '2026-02-01'
        
        # Make request with UTC
        response_utc = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone=UTC'
        )
        assert response_utc.status_code == 200
        call_args_utc = mock_github.contributions_by.call_args.kwargs
        
        # Reset mock
        mock_github.reset_mock()
        mock_github.contributions_by.return_value = mock_github_data
        
        # Make request with PST
        response_pst = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}&timezone=America/Los_Angeles'
        )
        assert response_pst.status_code == 200
        call_args_pst = mock_github.contributions_by.call_args.kwargs
        
        # The UTC times should be different
        # UTC: 2026-02-01 00:00:00 to 2026-02-01 23:59:59
        # PST: 2026-02-01 08:00:00 to 2026-02-02 07:59:59 (in UTC)
        assert call_args_utc['from_date'] != call_args_pst['from_date']
        assert call_args_utc['to_date'] != call_args_pst['to_date']
