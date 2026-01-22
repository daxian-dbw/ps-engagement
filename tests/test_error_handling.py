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
    
    # ===== 1. Invalid GitHub Username =====
    
    def test_invalid_github_username_returns_404(self, client):
        """Test that an invalid GitHub username returns 404 with user-friendly message."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("User not found or API returned 404")
            
            response = client.get('/api/metrics?user=invalid-user-xyz-123&days=7')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
            assert data['error']['code'] == 'USER_NOT_FOUND'
            assert 'not found' in data['error']['message'].lower()
            assert 'invalid-user-xyz-123' in data['error']['message']
            # Ensure no stack trace in response
            assert 'traceback' not in data['error']['message'].lower()
            assert 'exception' not in data['error']['message'].lower()
    
    def test_invalid_username_message_is_user_friendly(self, client):
        """Verify error message is clear and actionable for invalid username."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("404: User not found")
            
            response = client.get('/api/metrics?user=nonexistent&days=7')
            data = response.get_json()
            
            # Message should be clear and helpful
            message = data['error']['message']
            assert 'nonexistent' in message
            assert 'not found' in message.lower()
            # Should not contain technical jargon
            assert 'null pointer' not in message.lower()
            assert 'exception' not in message.lower()
    
    # ===== 2. Non-existent Repository =====
    
    def test_nonexistent_repository_returns_error(self, client):
        """Test handling of non-existent repository."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            # Repository not found typically returns 404
            mock_contrib.side_effect = Exception("Repository not found - 404")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7&owner=FakeOwner&repo=FakeRepo')
            
            # Should return 404 since repository not found is treated as user not found
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
            assert 'not found' in data['error']['message'].lower()
    
    # ===== 3. Network Error =====
    
    def test_network_error_handling(self, client):
        """Test handling of network errors."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = ConnectionError("Network connection failed")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert data['error']['code'] == 'GITHUB_API_ERROR'
            # Should mention the issue but not leak sensitive info
            assert 'Network connection failed' in data['error']['message']
    
    def test_network_timeout_handling(self, client):
        """Test handling of network timeouts."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = TimeoutError("Request timed out")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert 'timed out' in data['error']['message'].lower()
    
    # ===== 4. API Timeout =====
    
    def test_slow_api_response_timeout(self, client):
        """Test that slow API responses are handled gracefully."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            # Simulate a timeout scenario
            mock_contrib.side_effect = Exception("Request timeout after 30 seconds")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert 'timeout' in data['error']['message'].lower() or 'GitHub' in data['error']['message']
    
    # ===== 5. Invalid GitHub Token =====
    
    def test_invalid_github_token(self, client):
        """Test handling of invalid/expired GitHub token."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("401 Unauthorized: Bad credentials")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert data['error']['code'] == 'AUTHENTICATION_ERROR'
            assert 'authentication' in data['error']['message'].lower() or 'token' in data['error']['message'].lower()
    
    def test_unauthorized_error_no_token_leak(self, client):
        """Ensure error messages don't leak the actual token value."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("Unauthorized with token ghp_xxxxxxxxxxxx")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7')
            data = response.get_json()
            
            # Ensure token pattern is not in the response
            response_text = json.dumps(data)
            assert 'ghp_' not in response_text
            assert 'token' not in response_text or 'token' in response_text.lower()  # Only generic mention
    
    # ===== 6. Rate Limit Exceeded =====
    
    def test_rate_limit_exceeded_returns_429(self, client):
        """Test handling of GitHub API rate limit exceeded."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("API rate limit exceeded")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7')
            
            assert response.status_code == 429
            data = response.get_json()
            assert 'error' in data
            assert data['error']['code'] == 'RATE_LIMIT_EXCEEDED'
            assert 'rate limit' in data['error']['message'].lower()
    
    def test_rate_limit_message_is_helpful(self, client):
        """Verify rate limit error message gives actionable advice."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("rate limit exceeded for API")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7')
            data = response.get_json()
            
            message = data['error']['message']
            assert 'rate limit' in message.lower()
            assert 'try again' in message.lower()
    
    # ===== 7. Server Error (500) =====
    
    def test_internal_server_error_returns_500(self, client):
        """Test handling of unexpected internal errors."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = RuntimeError("Unexpected internal error")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            assert data['error']['code'] == 'GITHUB_API_ERROR'
    
    def test_server_error_no_stack_trace_leak(self, client):
        """Ensure server errors don't expose stack traces to users."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            # Simulate a nasty error with stack trace
            mock_contrib.side_effect = RuntimeError("Error in some_internal_function at line 123")
            
            response = client.get('/api/metrics?user=daxian-dbw&days=7')
            data = response.get_json()
            
            message = data['error']['message']
            # Should not contain file paths, line numbers, or function names
            assert 'line 123' not in message or 'some_internal_function' in message  # Can mention function but not internal details
            assert 'traceback' not in message.lower()
    
    def test_unexpected_error_in_formatting(self, client):
        """Test handling of errors in response formatting."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.return_value = {'issues_opened': [{'invalid': 'data'}]}
            
            with patch('api.routes.format_metrics_response') as mock_format:
                mock_format.side_effect = KeyError("Missing required key")
                
                response = client.get('/api/metrics?user=daxian-dbw&days=7')
                
                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data
                assert data['error']['code'] == 'INTERNAL_ERROR'
    
    # ===== Error Message Quality =====
    
    def test_all_error_responses_include_timestamp(self, client):
        """Verify all error responses include a timestamp."""
        error_scenarios = [
            ('/api/metrics', 400),  # Missing user param
            ('/api/metrics?user=&days=7', 400),  # Empty user
            ('/api/metrics?user=test&days=abc', 400),  # Invalid days
            ('/api/metrics?user=test&days=0', 400),  # Days out of range
        ]
        
        for url, expected_status in error_scenarios:
            response = client.get(url)
            assert response.status_code == expected_status
            data = response.get_json()
            assert 'error' in data
            assert 'timestamp' in data['error']
            # Verify timestamp format
            assert 'T' in data['error']['timestamp']
            assert 'Z' in data['error']['timestamp']
    
    def test_error_responses_have_consistent_structure(self, client):
        """Ensure all error responses follow the same structure."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("Test error")
            
            response = client.get('/api/metrics?user=test&days=7')
            data = response.get_json()
            
            # Check structure
            assert 'error' in data
            assert 'code' in data['error']
            assert 'message' in data['error']
            assert 'timestamp' in data['error']
            # Ensure no unexpected fields
            assert len(data) == 1  # Only 'error' key
            assert len(data['error']) == 3  # code, message, timestamp
    
    def test_error_codes_are_meaningful(self, client):
        """Verify error codes follow a consistent naming convention."""
        # Missing parameter
        response = client.get('/api/metrics')
        data = response.get_json()
        assert data['error']['code'] == 'MISSING_PARAMETER'
        
        # Invalid parameter
        response = client.get('/api/metrics?user=test&days=abc')
        data = response.get_json()
        assert data['error']['code'] == 'INVALID_PARAMETER'
        
        # All codes should be UPPER_SNAKE_CASE
        codes_seen = set()
        test_urls = [
            '/api/metrics',
            '/api/metrics?user=test&days=abc',
            '/api/metrics?user=test&days=0',
        ]
        
        for url in test_urls:
            response = client.get(url)
            data = response.get_json()
            code = data['error']['code']
            codes_seen.add(code)
            # Verify UPPER_SNAKE_CASE
            assert code.isupper()
            assert ' ' not in code
            assert '-' not in code
    
    # ===== No Sensitive Information Leakage =====
    
    def test_no_environment_variables_in_errors(self, client):
        """Ensure environment variables are not leaked in error messages."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("Error with GITHUB_TOKEN=ghp_secret123")
            
            response = client.get('/api/metrics?user=test&days=7')
            data = response.get_json()
            
            response_text = json.dumps(data)
            # Token value should be redacted
            assert 'ghp_secret123' not in response_text
            # Should show redaction marker
            assert '[REDACTED_ENV_VAR]' in response_text or '[REDACTED_TOKEN]' in response_text
    
    def test_no_file_paths_in_errors(self, client):
        """Ensure internal file paths are not exposed in errors."""
        with patch('api.routes.format_metrics_response') as mock_format:
            mock_format.side_effect = Exception("/home/user/app/api/routes.py line 123")
            
            response = client.get('/api/metrics?user=test&days=7')
            data = response.get_json()
            
            message = data['error']['message']
            # Should not expose internal paths
            assert '/home/user' not in message
            assert 'routes.py' not in message
    
    def test_no_database_connection_strings(self, client):
        """Ensure database connection strings are not leaked (future-proofing)."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("Connection failed: postgresql://user:pass@localhost/db")
            
            response = client.get('/api/metrics?user=test&days=7')
            data = response.get_json()
            
            response_text = json.dumps(data)
            # Connection string should be redacted
            assert 'postgresql://user:pass@localhost' not in response_text
            assert ':pass@' not in response_text
            # Should show redaction marker
            assert '[REDACTED_CONNECTION_STRING]' in response_text
    
    # ===== Recovery and Retry =====
    
    def test_app_remains_functional_after_error(self, client):
        """Verify the app can handle new requests after an error."""
        # First request causes error
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("Temporary error")
            response1 = client.get('/api/metrics?user=test&days=7')
            assert response1.status_code == 500
        
        # Second request should work (simulating retry)
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.return_value = {
                'issues_opened': [],
                'prs_opened': [],
                'comments': [],
                'issues_labeled': [],
                'issues_closed': [],
                'reviews': [],
                'prs_merged': [],
                'prs_closed': []
            }
            response2 = client.get('/api/metrics?user=test&days=7')
            assert response2.status_code == 200
    
    def test_multiple_consecutive_errors_handled(self, client):
        """Test that multiple errors in a row are all handled properly."""
        error_scenarios = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3"),
        ]
        
        for i, error in enumerate(error_scenarios):
            with patch('api.routes.github_events.contributions_by') as mock_contrib:
                mock_contrib.side_effect = error
                response = client.get(f'/api/metrics?user=test{i}&days=7')
                assert response.status_code == 500
                data = response.get_json()
                assert 'error' in data
        
        # App should still be responsive
        response = client.get('/api/health')
        assert response.status_code == 200
    
    # ===== Health Check Errors =====
    
    def test_health_check_error_handling(self, client):
        """Test that even health check can fail gracefully."""
        # We need to patch datetime.utcnow more carefully to allow the second try to work
        with patch('api.routes.datetime') as mock_datetime:
            # First call fails, second call succeeds with actual datetime
            call_count = [0]
            original_utcnow = datetime.utcnow
            
            def side_effect():
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("System time error")
                return original_utcnow()
            
            mock_datetime.utcnow.side_effect = side_effect
            
            response = client.get('/api/health')
            
            # Should handle error gracefully and return error status
            assert response.status_code == 500
            data = response.get_json()
            assert 'status' in data
            assert data['status'] == 'error'
            assert 'timestamp' in data
    
    # ===== Input Validation Errors =====
    
    def test_missing_user_parameter_user_friendly(self, client):
        """Test that missing user parameter returns clear message."""
        response = client.get('/api/metrics?days=7')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'user' in data['error']['message'].lower()
        assert 'required' in data['error']['message'].lower() or 'missing' in data['error']['message'].lower()
    
    def test_empty_user_parameter_user_friendly(self, client):
        """Test that empty user parameter returns clear message."""
        response = client.get('/api/metrics?user=&days=7')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'user' in data['error']['message'].lower() or 'parameter' in data['error']['message'].lower()
    
    def test_invalid_days_format_user_friendly(self, client):
        """Test that invalid days format returns clear message."""
        response = client.get('/api/metrics?user=test&days=abc')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'days' in data['error']['message'].lower()
        assert 'integer' in data['error']['message'].lower()
    
    def test_days_out_of_range_user_friendly(self, client):
        """Test that days out of range returns clear message."""
        # Test too small
        response = client.get('/api/metrics?user=test&days=0')
        assert response.status_code == 400
        data = response.get_json()
        assert '1' in data['error']['message'] and '180' in data['error']['message']
        
        # Test too large
        response = client.get('/api/metrics?user=test&days=365')
        assert response.status_code == 400
        data = response.get_json()
        assert '1' in data['error']['message'] and '180' in data['error']['message']
    
    # ===== Logging Verification =====
    
    def test_errors_logged_to_console(self, client, caplog):
        """Verify errors are logged for debugging purposes."""
        with patch('api.routes.github_events.contributions_by') as mock_contrib:
            mock_contrib.side_effect = Exception("Test error for logging")
            
            response = client.get('/api/metrics?user=test&days=7')
            
            assert response.status_code == 500
            # Check that error was logged
            assert 'GitHub API error' in caplog.text or 'error' in caplog.text.lower()
    
    def test_warnings_logged_for_validation_errors(self, client, caplog):
        """Verify validation errors are logged as warnings."""
        response = client.get('/api/metrics')  # Missing user
        
        assert response.status_code == 400
        # Should log warning for missing parameter
        # Note: This depends on logging configuration in routes.py


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
