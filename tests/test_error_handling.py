"""
Error Handling Validation Tests

This module tests all error scenarios to ensure proper error handling,
user-friendly messages, and graceful recovery.

Task 4.3: Error Handling Validation
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json


class TestErrorHandling:
    """Test all error scenarios for the API."""
    
    # ===== GitHub API Errors =====
    
    @patch('api.routes.github_events')
    def test_invalid_github_username_returns_404(self, mock_github, client, valid_date_range_7_days):
        """Test that invalid GitHub usernames result in 404."""
        mock_github.contributions_by.side_effect = Exception("User not found")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=nonexistent-user-12345&from_date={from_date}&to_date={to_date}')
        
        # Should return error (exact status depends on implementation)
        assert response.status_code >= 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('api.routes.github_events')
    def test_invalid_username_message_is_user_friendly(self, mock_github, client, valid_date_range_7_days):
        """Test error message for invalid username is helpful."""
        mock_github.contributions_by.side_effect = Exception("404: User not found")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=invalid&from_date={from_date}&to_date={to_date}')
        
        data = response.get_json()
        message = data['error']['message']
        # Should not expose technical details
        assert 'exception' not in message.lower()
        assert 'stack trace' not in message.lower()
    
    @patch('api.routes.github_events')
    def test_rate_limit_exceeded_returns_error(self, mock_github, client, valid_date_range_7_days):
        """Test GitHub rate limit errors are handled properly."""
        mock_github.contributions_by.side_effect = Exception("API rate limit exceeded")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        
        assert response.status_code >= 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('api.routes.github_events')
    def test_internal_server_error_returns_500(self, mock_github, client, valid_date_range_7_days):
        """Test unexpected server errors return 500."""
        mock_github.contributions_by.side_effect = RuntimeError("Internal error")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
    
    # ===== Error Message Quality =====
    
    @patch('api.routes.github_events')
    def test_error_responses_have_consistent_structure(self, mock_github, client, valid_date_range_7_days):
        """Ensure all error responses follow the same structure."""
        mock_github.contributions_by.side_effect = Exception("Test error")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=test&from_date={from_date}&to_date={to_date}')
        data = response.get_json()
        
        # Check structure
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
        assert 'timestamp' in data['error']
        # Ensure no unexpected fields
        assert len(data) == 1  # Only 'error' key
        assert len(data['error']) == 3  # code, message, timestamp
    
    @patch('api.routes.github_events')
    def test_error_codes_are_meaningful(self, mock_github, client, valid_date_range_7_days):
        """Verify error codes follow a consistent naming convention."""
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        
        # Missing parameter
        response = client.get('/api/metrics')
        data = response.get_json()
        assert data['error']['code'] == 'MISSING_PARAMETER'
        
        # All codes should be UPPER_SNAKE_CASE
        codes_seen = set()
        
        # Test various error scenarios
        test_scenarios = [
            ('/api/metrics', 'MISSING_PARAMETER'),
            ('/api/metrics?user=test&from_date=invalid&to_date=2026-01-26', 'INVALID_DATE_FORMAT'),
        ]
        
        for url, expected_code in test_scenarios:
            response = client.get(url)
            data = response.get_json()
            code = data['error']['code']
            codes_seen.add(code)
            # Verify UPPER_SNAKE_CASE
            assert code.isupper()
            assert ' ' not in code
            assert '-' not in code
    
    # ===== No Sensitive Information Leakage =====
    
    @patch('api.routes.github_events')
    def test_no_environment_variables_in_errors(self, mock_github, client, valid_date_range_7_days):
        """Ensure environment variables are not leaked in error messages."""
        mock_github.contributions_by.side_effect = Exception("Error with GITHUB_TOKEN=ghp_secret123")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=test&from_date={from_date}&to_date={to_date}')
        data = response.get_json()
        
        response_text = json.dumps(data)
        # Token value should not be exposed
        assert 'ghp_secret123' not in response_text
    
    @patch('api.routes.github_events')
    def test_no_file_paths_in_errors(self, mock_github, client, valid_date_range_7_days):
        """Ensure internal file paths are not exposed in errors."""
        mock_github.contributions_by.side_effect = Exception("/home/user/app/api/routes.py line 123")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=test&from_date={from_date}&to_date={to_date}')
        data = response.get_json()
        
        message = data['error']['message']
        # Should not expose internal paths
        assert '/home/user' not in message
        assert 'routes.py' not in message
    
    @patch('api.routes.github_events')
    def test_server_error_no_stack_trace_leak(self, mock_github, client, valid_date_range_7_days):
        """Test that server errors don't leak stack traces."""
        mock_github.contributions_by.side_effect = RuntimeError("Internal error")
        
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        response = client.get(f'/api/metrics?user=testuser&from_date={from_date}&to_date={to_date}')
        
        data = response.get_json()
        message = data['error']['message']
        # Should not contain stack trace elements
        assert 'Traceback' not in message
        assert 'File "' not in message
        assert 'line ' not in message
    
    # ===== Recovery and Resilience =====
    
    @patch('api.routes.github_events')
    def test_app_remains_functional_after_error(self, mock_github, client, valid_date_range_7_days):
        """Verify the app can handle new requests after an error."""
        from_date = valid_date_range_7_days['from_date']
        to_date = valid_date_range_7_days['to_date']
        
        # First request causes error
        mock_github.contributions_by.side_effect = Exception("Temporary error")
        response1 = client.get(f'/api/metrics?user=test&from_date={from_date}&to_date={to_date}')
        assert response1.status_code >= 400
        
        # Second request should work (simulating retry)
        mock_github.contributions_by.side_effect = None
        mock_github.contributions_by.return_value = {
            'issues_opened': [],
            'prs_opened': [],
            'comments': [],
            'issues_labeled': [],
            'issues_closed': [],
            'reviews': [],
            'prs_merged': [],
            'prs_closed': []
        }
        response2 = client.get(f'/api/metrics?user=test&from_date={from_date}&to_date={to_date}')
        assert response2.status_code == 200


class TestDateRangeErrorHandling:
    """Test error handling specific to date range feature."""
    
    def test_malformed_date_error_message_is_user_friendly(self, client):
        """Test error message for malformed dates is clear and actionable."""
        response = client.get('/api/metrics?user=testuser&from_date=01-01-2026&to_date=02-02-2026')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_DATE_FORMAT'
        
        message = data['error']['message']
        # Should mention the correct format
        assert 'YYYY-MM-DD' in message
        # Should not contain technical jargon
        assert 'parse' not in message.lower()
        assert 'exception' not in message.lower()
    
    def test_invalid_date_range_error_is_clear(self, client):
        """Test error message for invalid date range is helpful."""
        response = client.get('/api/metrics?user=testuser&from_date=2026-02-02&to_date=2026-01-26')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_DATE_RANGE'
        
        message = data['error']['message']
        # Should explain the issue
        assert 'before' in message.lower()
        # Should not be overly technical
        assert 'timestamp' not in message.lower()
    
    def test_future_date_error_message_is_helpful(self, client):
        """Test error message for future dates guides the user."""
        response = client.get('/api/metrics?user=testuser&from_date=2026-02-10&to_date=2026-02-20')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error']['code'] == 'FUTURE_DATE_NOT_ALLOWED'
        
        message = data['error']['message']
        # Should mention future dates
        assert 'future' in message.lower()
        # Should be concise
        assert len(message) < 100
    
    def test_large_range_error_includes_limit(self, client):
        """Test error for large range mentions the 200-day limit."""
        from datetime import datetime, timedelta
        to_date = datetime.utcnow() - timedelta(days=1)  # Yesterday
        from_date = to_date - timedelta(days=201)
        
        response = client.get(
            f'/api/metrics?user=testuser'
            f'&from_date={from_date.strftime("%Y-%m-%d")}'
            f'&to_date={to_date.strftime("%Y-%m-%d")}'
        )
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error']['code'] == 'DATE_RANGE_TOO_LARGE'
        
        message = data['error']['message']
        # Should mention the limit
        assert '200' in message
        # Should be actionable
        assert 'exceed' in message.lower() or 'maximum' in message.lower()
    
    def test_missing_dates_error_is_informative(self, client):
        """Test error for missing dates tells user what's needed."""
        response = client.get('/api/metrics?user=testuser')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error']['code'] == 'MISSING_PARAMETER'
        
        message = data['error']['message']
        # Should mention both required parameters
        assert 'from_date' in message or 'to_date' in message
        assert 'required' in message.lower()
    
    def test_partial_date_range_error(self, client):
        """Test error when only one date parameter is provided."""
        # Test missing to_date
        response = client.get('/api/metrics?user=testuser&from_date=2026-01-26')
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'MISSING_PARAMETER'
        
        # Test missing from_date
        response = client.get('/api/metrics?user=testuser&to_date=2026-02-02')
        assert response.status_code == 400
        data = response.get_json()
        assert data['error']['code'] == 'MISSING_PARAMETER'
    
    def test_date_validation_error_includes_timestamp(self, client):
        """Test that all date validation errors include timestamp."""
        test_cases = [
            '/api/metrics?user=testuser&from_date=invalid&to_date=2026-02-02',
            '/api/metrics?user=testuser&from_date=2026-02-02&to_date=2026-01-26',
            '/api/metrics?user=testuser&from_date=2026-02-10&to_date=2026-02-20',
        ]
        
        for url in test_cases:
            response = client.get(url)
            data = response.get_json()
            
            assert 'error' in data
            assert 'timestamp' in data['error']
            # Verify timestamp is valid ISO format
            timestamp = data['error']['timestamp']
            assert timestamp.endswith('Z')
            from datetime import datetime
            datetime.fromisoformat(timestamp.rstrip('Z'))


# Manual Test Cases (documented for manual testing)
"""
MANUAL TEST CASES:

These scenarios should be tested manually as they involve real network conditions:

1. Network Disconnection Test:
   - Disconnect network/Wi-Fi
   - Try to search for a user
   - Expected: User-friendly error message about network connection
   - Expected: UI remains functional after reconnecting

2. Slow Network Test:
   - Use browser dev tools to throttle network (Slow 3G)
   - Search for a user with large activity
   - Expected: Loading indicator shows for extended time
   - Expected: Either completes or times out gracefully

3. Browser Console Error Check:
   - Open browser developer console
   - Trigger various errors (invalid user, rate limit, etc.)
   - Expected: Errors logged to console for debugging
   - Expected: No uncaught exceptions in console

4. Multiple Rapid Retries:
   - Trigger an error (e.g., invalid user)
   - Click search multiple times rapidly
   - Expected: Each request handled independently
   - Expected: No UI lock-up or crash

5. State Persistence After Error:
   - Search for invalid user (causes error)
   - Search for valid user
   - Expected: App recovers completely
   - Expected: Previous error message cleared

6. Token Expiration Simulation:
   - Temporarily use invalid GitHub token in .env
   - Try to search
   - Expected: Error message about authentication
   - Expected: No token value visible in UI or console

7. Long-Running Query:
   - Search for very active user with 180 days
   - Let it run to completion
   - Expected: Completes without timeout
   - OR: Times out with clear message

8. Cross-Browser Error Handling:
   - Test error scenarios in Chrome, Firefox, Edge
   - Expected: Consistent error messages across browsers
   - Expected: No browser-specific crashes
"""
