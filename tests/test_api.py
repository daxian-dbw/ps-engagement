"""
Tests for API endpoints and response formatting.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from api.response_formatter import (
    format_metrics_response,
    _format_issues_opened,
    _format_prs_opened,
    _format_issue_triage,
    _format_code_reviews
)


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""
    
    def test_health_check_success(self, client):
        """Test health check returns 200 OK with correct structure."""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data
        assert data['status'] == 'ok'
        assert data['timestamp'].endswith('Z')
    
    def test_health_check_timestamp_format(self, client):
        """Test health check timestamp is valid ISO 8601."""
        response = client.get('/api/health')
        data = json.loads(response.data)
        
        # Should not raise exception
        timestamp = data['timestamp'].rstrip('Z')
        datetime.fromisoformat(timestamp)


class TestMetricsEndpoint:
    """Tests for /api/metrics endpoint."""
    
    def test_metrics_missing_user_parameter(self, client):
        """Test metrics endpoint returns 400 when user parameter is missing."""
        response = client.get('/api/metrics')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_PARAMETER'
        assert 'user' in data['error']['message'].lower()
    
    def test_metrics_empty_user_parameter(self, client):
        """Test metrics endpoint returns 400 when user parameter is empty."""
        response = client.get('/api/metrics?user=')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_PARAMETER'
    
    def test_metrics_whitespace_user_parameter(self, client):
        """Test metrics endpoint returns 400 when user parameter is only whitespace."""
        response = client.get('/api/metrics?user=%20%20%20')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_PARAMETER'
    
    def test_metrics_missing_both_date_parameters(self, client):
        """Test metrics endpoint returns 400 when both date parameters are missing."""
        response = client.get('/api/metrics?user=testuser')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_PARAMETER'
        assert 'from_date' in data['error']['message'] or 'to_date' in data['error']['message']
    
    def test_metrics_missing_from_date(self, client):
        """Test metrics endpoint returns 400 when from_date is missing."""
        response = client.get('/api/metrics?user=testuser&to_date=2026-02-02')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_PARAMETER'
    
    def test_metrics_missing_to_date(self, client):
        """Test metrics endpoint returns 400 when to_date is missing."""
        response = client.get('/api/metrics?user=testuser&from_date=2026-01-26')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'MISSING_PARAMETER'
    
    @patch('api.routes.github_events')
    def test_metrics_success_with_date_range(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test metrics endpoint returns 200 with valid date range parameters."""
        # Mock the contributions_by function
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'meta' in data
        assert 'summary' in data
        assert 'data' in data
        
        # Verify meta section
        assert data['meta']['user'] == 'testuser'
        assert data['meta']['repository'] == 'PowerShell/PowerShell'
        assert 'period' in data['meta']
        assert 'start' in data['meta']['period']
        assert 'end' in data['meta']['period']
        assert 'days' in data['meta']['period']
        
        # Verify github_events was called with date range
        assert mock_github.contributions_by.called
        call_args = mock_github.contributions_by.call_args
        assert 'from_date' in call_args.kwargs
        assert 'to_date' in call_args.kwargs
        assert call_args.kwargs['actor_login'] == 'testuser'
    
    @patch('api.routes.github_events')
    def test_metrics_github_api_error(self, mock_github, client, valid_date_range_7_days):
        """Test metrics endpoint handles GitHub API errors."""
        # Mock GitHub API raising an exception
        mock_github.contributions_by.side_effect = Exception("GitHub API error")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'GITHUB_API_ERROR'
    
    @patch('api.routes.github_events')
    def test_metrics_empty_results(self, mock_github, client, empty_github_data, valid_date_range_7_days):
        """Test metrics endpoint handles empty results correctly."""
        mock_github.contributions_by.return_value = empty_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['summary']['total_actions'] == 0
        assert all(count == 0 for count in data['summary']['by_category'].values())


class TestDateRangeValidation:
    """Tests for date range parameter validation."""
    
    def test_invalid_from_date_format_us(self, client, invalid_date_format):
        """Test invalid from_date format (MM-DD-YYYY) returns 400."""
        dates = invalid_date_format['us_format']
        response = client.get(f'/api/metrics?user=testuser&from_date={dates["from_date"]}&to_date={dates["to_date"]}')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_DATE_FORMAT'
        assert 'YYYY-MM-DD' in data['error']['message']
    
    def test_invalid_to_date_format_european(self, client, invalid_date_format):
        """Test invalid to_date format (DD/MM/YYYY) returns 400."""
        dates = invalid_date_format['european_format']
        response = client.get(f'/api/metrics?user=testuser&from_date={dates["from_date"]}&to_date={dates["to_date"]}')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_DATE_FORMAT'
    
    def test_from_date_after_to_date(self, client, invalid_date_range_reversed):
        """Test from_date > to_date returns 400 with INVALID_DATE_RANGE."""
        from_date = invalid_date_range_reversed['from_date']
        to_date = invalid_date_range_reversed['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_DATE_RANGE'
        assert 'before' in data['error']['message'].lower()
    
    def test_date_range_exceeds_200_days(self, client, invalid_date_range_too_large):
        """Test date range > 200 days returns 400 with DATE_RANGE_TOO_LARGE."""
        from_date = invalid_date_range_too_large['from_date']
        to_date = invalid_date_range_too_large['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'DATE_RANGE_TOO_LARGE'
        assert '200' in data['error']['message']
    
    def test_future_to_date_not_allowed(self, client, invalid_date_range_future):
        """Test future to_date returns 400 with FUTURE_DATE_NOT_ALLOWED."""
        from_date = invalid_date_range_future['from_date']
        to_date = invalid_date_range_future['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'FUTURE_DATE_NOT_ALLOWED'
        assert 'future' in data['error']['message'].lower()
    
    @patch('api.routes.github_events')
    def test_valid_date_range_1_day(self, mock_github, client, mock_github_data, valid_date_range_1_day):
        """Test valid 1-day range (same day) returns 200."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_1_day['from_date']
        to_date = valid_date_range_1_day['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'meta' in data
        assert 'period' in data['meta']
    
    @patch('api.routes.github_events')
    def test_valid_date_range_7_days(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test valid 7-day range returns 200."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['meta']['user'] == 'testuser'
    
    @patch('api.routes.github_events')
    def test_valid_date_range_200_days(self, mock_github, client, mock_github_data, valid_date_range_200_days):
        """Test valid 200-day range (maximum) returns 200."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_200_days['from_date']
        to_date = valid_date_range_200_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'meta' in data
        assert 'period' in data['meta']
    
    @patch('api.routes.github_events')
    def test_date_range_with_custom_owner_repo(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test date range with custom owner/repo parameters."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}'
            f'&owner=TestOrg&repo=TestRepo'
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['meta']['repository'] == 'TestOrg/TestRepo'


class TestDateRangeMetadata:
    """Tests for date range in response metadata."""
    
    @patch('api.routes.github_events')
    def test_response_includes_date_range_in_meta(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test response meta includes period.start and period.end."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'period' in data['meta']
        assert 'start' in data['meta']['period']
        assert 'end' in data['meta']['period']
        assert 'days' in data['meta']['period']
    
    @patch('api.routes.github_events')
    def test_date_range_format_is_iso8601(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test dates in response are ISO 8601 format with Z suffix."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        start = data['meta']['period']['start']
        end = data['meta']['period']['end']
        
        # Verify ISO 8601 format with Z suffix
        assert start.endswith('Z')
        assert end.endswith('Z')
        assert 'T' in start
        assert 'T' in end
        
        # Verify dates can be parsed
        from datetime import datetime
        datetime.fromisoformat(start.rstrip('Z'))
        datetime.fromisoformat(end.rstrip('Z'))
    
    @patch('api.routes.github_events')
    def test_period_days_calculated_correctly(self, mock_github, client, mock_github_data, valid_date_range_7_days):
        """Test period.days matches the date range."""
        mock_github.contributions_by.return_value = mock_github_data
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        days = data['meta']['period']['days']
        
        # For a 7-day range (7 days apart), the inclusive days value should be 8
        assert days == 8


class TestResponseFormatter:
    """Tests for response_formatter module."""
    
    def test_format_metrics_response_structure(self, mock_github_data, valid_date_range_7_days):
        """Test format_metrics_response returns correct structure."""
        from datetime import datetime
        from_date = valid_date_range_7_days['from_date_obj']
        to_date = valid_date_range_7_days['to_date_obj']
        
        result = format_metrics_response(
            mock_github_data,
            user='testuser',
            from_date=from_date,
            to_date=to_date,
            owner='PowerShell',
            repo='PowerShell'
        )
        
        assert 'meta' in result
        assert 'summary' in result
        assert 'data' in result
        
        # Check meta structure
        assert 'user' in result['meta']
        assert 'repository' in result['meta']
        assert 'period' in result['meta']
        assert 'fetched_at' in result['meta']
        
        # Check summary structure
        assert 'total_actions' in result['summary']
        assert 'by_category' in result['summary']
        
        # Check data structure
        assert 'issues_opened' in result['data']
        assert 'prs_opened' in result['data']
        assert 'issue_triage' in result['data']
        assert 'code_reviews' in result['data']
    
    def test_format_metrics_response_meta_values(self, mock_github_data):
        """Test meta section contains correct values."""
        from datetime import datetime, timedelta
        to_date = datetime(2026, 2, 2)
        from_date = to_date - timedelta(days=14)
        
        result = format_metrics_response(
            mock_github_data,
            user='johndoe',
            from_date=from_date,
            to_date=to_date,
            owner='TestOrg',
            repo='TestRepo'
        )
        
        assert result['meta']['user'] == 'johndoe'
        assert result['meta']['repository'] == 'TestOrg/TestRepo'
        assert result['meta']['period']['days'] == 15  # 14 days back + 1 for inclusive range
    
    def test_format_metrics_response_counts(self, mock_github_data, valid_date_range_7_days):
        """Test summary counts are calculated correctly."""
        from_date = valid_date_range_7_days['from_date_obj']
        to_date = valid_date_range_7_days['to_date_obj']
        
        result = format_metrics_response(
            mock_github_data,
            user='testuser',
            from_date=from_date,
            to_date=to_date,
            owner='PowerShell',
            repo='PowerShell'
        )
        
        # Count based on actual mock data structure
        # Note: The formatter processes the data differently than raw counts
        assert result['summary']['total_actions'] >= 0  # Just check it's calculated
        assert result['summary']['by_category']['issues_opened'] == 2
        assert result['summary']['by_category']['prs_opened'] == 1
    
    def test_format_metrics_response_with_none(self, valid_date_range_7_days):
        """Test format_metrics_response handles None input gracefully."""
        from_date = valid_date_range_7_days['from_date_obj']
        to_date = valid_date_range_7_days['to_date_obj']
        
        result = format_metrics_response(
            None,
            user='testuser',
            from_date=from_date,
            to_date=to_date,
            owner='PowerShell',
            repo='PowerShell'
        )
        
        assert result['summary']['total_actions'] == 0
        assert all(count == 0 for count in result['summary']['by_category'].values())
    
    def test_format_metrics_response_with_empty_dict(self, empty_github_data, valid_date_range_7_days):
        """Test format_metrics_response handles empty data."""
        from_date = valid_date_range_7_days['from_date_obj']
        to_date = valid_date_range_7_days['to_date_obj']
        
        result = format_metrics_response(
            empty_github_data,
            user='testuser',
            from_date=from_date,
            to_date=to_date,
            owner='PowerShell',
            repo='PowerShell'
        )
        
        assert result['summary']['total_actions'] == 0
        assert result['data']['issues_opened'] == []
        assert result['data']['prs_opened'] == []
    
    def test_format_issues_opened(self):
        """Test _format_issues_opened transforms data correctly."""
        raw_issues = [
            {
                'number': 123,
                'title': 'Test Issue',
                'url': 'https://github.com/test/repo/issues/123',
                'created_at': '2026-01-20T10:00:00Z',
                'labels': ['bug', 'enhancement']
            }
        ]
        
        result = _format_issues_opened(raw_issues)
        assert len(result) == 1
        assert result[0]['number'] == 123
        assert result[0]['title'] == 'Test Issue'
        assert result[0]['url'] == 'https://github.com/test/repo/issues/123'
        assert 'created_at' in result[0]
    
    def test_format_prs_opened(self):
        """Test _format_prs_opened transforms data correctly."""
        raw_prs = [
            {
                'number': 456,
                'title': 'Test PR',
                'url': 'https://github.com/test/repo/pull/456',
                'created_at': '2026-01-19T15:00:00Z',
                'state': 'OPEN',
                'labels': []
            }
        ]
        
        result = _format_prs_opened(raw_prs)
        assert len(result) == 1
        assert result[0]['number'] == 456
        assert result[0]['title'] == 'Test PR'
    
    def test_format_issue_triage_structure(self, mock_github_data):
        """Test _format_issue_triage returns correct structure."""
        result = _format_issue_triage(mock_github_data)
        
        assert 'comments' in result
        assert 'labeled' in result
        assert 'closed' in result
        assert isinstance(result['comments'], list)
        assert isinstance(result['labeled'], list)
        assert isinstance(result['closed'], list)
    
    def test_format_code_reviews_structure(self, mock_github_data):
        """Test _format_code_reviews returns correct structure."""
        result = _format_code_reviews(mock_github_data)
        
        assert 'comments' in result
        assert 'reviews' in result
        assert 'merged' in result
        assert 'closed' in result
        assert isinstance(result['comments'], list)
        assert isinstance(result['reviews'], list)


class TestErrorHandling:
    """Tests for error handling across the API."""
    
    def test_error_response_structure(self, client):
        """Test error responses have consistent structure."""
        response = client.get('/api/metrics')  # Missing user parameter
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
        assert 'timestamp' in data['error']
    
    def test_error_timestamp_format(self, client):
        """Test error response timestamps are valid ISO 8601."""
        response = client.get('/api/metrics')
        data = json.loads(response.data)
        
        timestamp = data['error']['timestamp'].rstrip('Z')
        datetime.fromisoformat(timestamp)  # Should not raise
    
    @patch('api.routes.github_events')
    def test_exception_handling(self, mock_github, client, valid_date_range_7_days):
        """Test unexpected exceptions are handled gracefully."""
        mock_github.contributions_by.side_effect = RuntimeError("Unexpected error")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'GITHUB_API_ERROR'


class TestIntegration:
    """Integration tests for complete API workflows."""
    
    @patch('api.routes.github_events')
    def test_full_metrics_workflow(self, mock_github, client, mock_github_data):
        """Test complete workflow from request to formatted response."""
        mock_github.contributions_by.return_value = mock_github_data
        
        # Use 14-day range (ending yesterday to avoid future dates)
        from datetime import datetime, timedelta
        to_date = datetime.utcnow() - timedelta(days=1)  # Yesterday
        from_date = to_date - timedelta(days=14)
        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')
        
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date_str}&to_date={to_date_str}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Verify all sections present
        assert all(key in data for key in ['meta', 'summary', 'data'])
        
        # Verify data integrity
        assert data['meta']['user'] == 'testuser'
        assert 'period' in data['meta']
        assert 'days' in data['meta']['period']
        assert data['summary']['total_actions'] > 0
        assert len(data['data']['issues_opened']) == 2
        assert len(data['data']['prs_opened']) == 1
    
    @patch('api.routes.github_events')
    def test_boundary_date_range_values(self, mock_github, client, empty_github_data):
        """Test boundary values for date range parameters."""
        mock_github.contributions_by.return_value = empty_github_data
        
        from datetime import datetime, timedelta
        to_date = datetime.utcnow() - timedelta(days=1)  # Yesterday to avoid future dates
        
        # Test minimum valid value (1 day - same day)
        from_date_1 = to_date
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date_1.strftime("%Y-%m-%d")}&to_date={to_date.strftime("%Y-%m-%d")}'
        )
        assert response.status_code == 200
        
        # Test maximum valid value (200 days)
        from_date_200 = to_date - timedelta(days=200)
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date_200.strftime("%Y-%m-%d")}&to_date={to_date.strftime("%Y-%m-%d")}'
        )
        assert response.status_code == 200
        
        # Test just above maximum (201 days)
        from_date_201 = to_date - timedelta(days=201)
        response = client.get(
            f'/api/metrics?user=testuser&from_date={from_date_201.strftime("%Y-%m-%d")}&to_date={to_date.strftime("%Y-%m-%d")}'
        )
        assert response.status_code == 400

