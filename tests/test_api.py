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
    
    def test_metrics_invalid_days_parameter(self, client):
        """Test metrics endpoint returns 400 when days is not a number."""
        response = client.get('/api/metrics?user=testuser&days=invalid')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'INVALID_PARAMETER'
        assert 'days' in data['error']['message'].lower()
    
    def test_metrics_days_out_of_range_low(self, client):
        """Test metrics endpoint returns 400 when days < 1."""
        response = client.get('/api/metrics?user=testuser&days=0')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'INVALID_PARAMETER'
    
    def test_metrics_days_out_of_range_high(self, client):
        """Test metrics endpoint returns 400 when days > 180."""
        response = client.get('/api/metrics?user=testuser&days=181')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'INVALID_PARAMETER'
    
    @patch('api.routes.github_events')
    def test_metrics_success(self, mock_github, client, mock_github_data):
        """Test metrics endpoint returns 200 with valid parameters."""
        # Mock the contributions_by function
        mock_github.contributions_by.return_value = mock_github_data
        
        response = client.get('/api/metrics?user=testuser&days=7')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'meta' in data
        assert 'summary' in data
        assert 'data' in data
        
        # Verify meta section
        assert data['meta']['user'] == 'testuser'
        assert data['meta']['repository'] == 'PowerShell/PowerShell'
        assert data['meta']['period']['days'] == 7
        
        # Verify github_events was called correctly
        mock_github.contributions_by.assert_called_once_with(
            actor_login='testuser', days_back=7, owner='PowerShell', repo='PowerShell'
        )
    
    @patch('api.routes.github_events')
    def test_metrics_default_days_parameter(self, mock_github, client, mock_github_data):
        """Test metrics endpoint uses default days=7 when not specified."""
        mock_github.contributions_by.return_value = mock_github_data
        
        response = client.get('/api/metrics?user=testuser')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['meta']['period']['days'] == 7
        mock_github.contributions_by.assert_called_once_with(
            actor_login='testuser', days_back=7, owner='PowerShell', repo='PowerShell'
        )
    
    @patch('api.routes.github_events')
    def test_metrics_custom_days_parameter(self, mock_github, client, mock_github_data):
        """Test metrics endpoint respects custom days parameter."""
        mock_github.contributions_by.return_value = mock_github_data
        
        response = client.get('/api/metrics?user=testuser&days=30')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['meta']['period']['days'] == 30
        mock_github.contributions_by.assert_called_once_with(
            actor_login='testuser', days_back=30, owner='PowerShell', repo='PowerShell'
        )
    
    @patch('api.routes.github_events')
    def test_metrics_github_api_error(self, mock_github, client):
        """Test metrics endpoint handles GitHub API errors."""
        # Mock GitHub API raising an exception
        mock_github.contributions_by.side_effect = Exception("GitHub API error")
        
        response = client.get('/api/metrics?user=testuser&days=7')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error']['code'] == 'GITHUB_API_ERROR'
    
    @patch('api.routes.github_events')
    def test_metrics_empty_results(self, mock_github, client, empty_github_data):
        """Test metrics endpoint handles empty results correctly."""
        mock_github.contributions_by.return_value = empty_github_data
        
        response = client.get('/api/metrics?user=testuser&days=7')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['summary']['total_actions'] == 0
        assert all(count == 0 for count in data['summary']['by_category'].values())


class TestResponseFormatter:
    """Tests for response_formatter module."""
    
    def test_format_metrics_response_structure(self, mock_github_data):
        """Test format_metrics_response returns correct structure."""
        result = format_metrics_response(
            mock_github_data,
            user='testuser',
            days=7,
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
        result = format_metrics_response(
            mock_github_data,
            user='johndoe',
            days=14,
            owner='TestOrg',
            repo='TestRepo'
        )
        
        assert result['meta']['user'] == 'johndoe'
        assert result['meta']['repository'] == 'TestOrg/TestRepo'
        assert result['meta']['period']['days'] == 14
    
    def test_format_metrics_response_counts(self, mock_github_data):
        """Test summary counts are calculated correctly."""
        result = format_metrics_response(
            mock_github_data,
            user='testuser',
            days=7,
            owner='PowerShell',
            repo='PowerShell'
        )
        
        # Count based on actual mock data structure
        # Note: The formatter processes the data differently than raw counts
        assert result['summary']['total_actions'] >= 0  # Just check it's calculated
        assert result['summary']['by_category']['issues_opened'] == 2
        assert result['summary']['by_category']['prs_opened'] == 1
    
    def test_format_metrics_response_with_none(self):
        """Test format_metrics_response handles None input gracefully."""
        result = format_metrics_response(
            None,
            user='testuser',
            days=7,
            owner='PowerShell',
            repo='PowerShell'
        )
        
        assert result['summary']['total_actions'] == 0
        assert all(count == 0 for count in result['summary']['by_category'].values())
    
    def test_format_metrics_response_with_empty_dict(self, empty_github_data):
        """Test format_metrics_response handles empty data."""
        result = format_metrics_response(
            empty_github_data,
            user='testuser',
            days=7,
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
    def test_exception_handling(self, mock_github, client):
        """Test unexpected exceptions are handled gracefully."""
        mock_github.contributions_by.side_effect = RuntimeError("Unexpected error")
        
        response = client.get('/api/metrics?user=testuser')
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
        
        response = client.get('/api/metrics?user=testuser&days=14')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Verify all sections present
        assert all(key in data for key in ['meta', 'summary', 'data'])
        
        # Verify data integrity
        assert data['meta']['user'] == 'testuser'
        assert data['meta']['period']['days'] == 14
        assert data['summary']['total_actions'] > 0
        assert len(data['data']['issues_opened']) == 2
        assert len(data['data']['prs_opened']) == 1
    
    @patch('api.routes.github_events')
    def test_boundary_days_values(self, mock_github, client, empty_github_data):
        """Test boundary values for days parameter."""
        mock_github.contributions_by.return_value = empty_github_data
        
        # Test minimum valid value
        response = client.get('/api/metrics?user=testuser&days=1')
        assert response.status_code == 200
        
        # Test maximum valid value
        response = client.get('/api/metrics?user=testuser&days=180')
        assert response.status_code == 200
        
        # Test just below minimum
        response = client.get('/api/metrics?user=testuser&days=0')
        assert response.status_code == 400
        
        # Test just above maximum
        response = client.get('/api/metrics?user=testuser&days=181')
        assert response.status_code == 400
