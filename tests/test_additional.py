"""
Additional tests for improved coverage.
"""

import pytest
import json
from unittest.mock import patch
from api.response_formatter import _format_issue_triage, _format_code_reviews


class TestResponseFormatterEdgeCases:
    """Additional tests for response formatter edge cases."""
    
    def test_format_issue_triage_with_comments_structure(self):
        """Test _format_issue_triage handles comments with different structures."""
        raw_data = {
            'comments': [
                {
                    'url': 'https://github.com/test/repo/issues/123#issuecomment-1',
                    'issue': {'number': 123, 'title': 'Test Issue'},
                    'publishedAt': '2026-01-20T10:00:00Z'
                },
                {
                    # Comment without proper issue field
                    'url': 'https://github.com/test/repo/pull/456#issuecomment-2',
                    'publishedAt': '2026-01-20T11:00:00Z'
                }
            ],
            'issues_labeled': [],
            'issues_closed': []
        }
        
        result = _format_issue_triage(raw_data)
        # Should only include issue comments, not PR comments
        assert len(result['comments']) == 1
        assert result['comments'][0]['number'] == 123
    
    def test_format_code_reviews_with_nested_structures(self):
        """Test _format_code_reviews handles nested PR structures."""
        raw_data = {
            'comments': [
                {
                    'url': 'https://github.com/test/repo/pull/123#issuecomment-1',
                    'pullRequest': {'number': 123, 'title': 'Test PR'},
                    'publishedAt': '2026-01-20T10:00:00Z'
                }
            ],
            'reviews': [
                {
                    'pullRequest': {'number': 123, 'title': 'Test PR'},
                    'state': 'APPROVED',
                    'url': 'https://github.com/test/repo/pull/123#pullrequestreview-1',
                    'occurredAt': '2026-01-20T11:00:00Z'
                },
                {
                    # Review with different structure
                    'number': 456,
                    'title': 'Another PR',
                    'pullRequestReview': {
                        'state': 'CHANGES_REQUESTED',
                        'url': 'https://github.com/test/repo/pull/456#pullrequestreview-2'
                    },
                    'submittedAt': '2026-01-20T12:00:00Z'
                }
            ],
            'prs_merged': [
                {
                    'number': 789,
                    'title': 'Merged PR',
                    'url': 'https://github.com/test/repo/pull/789',
                    'mergedAt': '2026-01-20T13:00:00Z'
                }
            ],
            'prs_closed': [
                {
                    'number': 101,
                    'title': 'Closed PR',
                    'url': 'https://github.com/test/repo/pull/101',
                    'closedAt': '2026-01-20T14:00:00Z'
                }
            ]
        }
        
        result = _format_code_reviews(raw_data)
        assert len(result['comments']) == 1
        assert len(result['reviews']) == 2
        assert len(result['merged']) == 1
        assert len(result['closed']) == 1
    
    def test_format_issue_triage_with_label_dict(self):
        """Test _format_issue_triage handles label as dict."""
        raw_data = {
            'comments': [],
            'issues_labeled': [
                {
                    'number': 123,
                    'title': 'Test Issue',
                    'url': 'https://github.com/test/repo/issues/123',
                    'label': {'name': 'bug'},
                    'labeledAt': '2026-01-20T10:00:00Z'
                }
            ],
            'issues_closed': []
        }
        
        result = _format_issue_triage(raw_data)
        assert len(result['labeled']) == 1
        assert result['labeled'][0]['label'] == 'bug'


class TestResponseFormatterDateRange:
    """Test response formatter with date range parameters."""
    
    def test_format_metrics_with_date_range_objects(self, mock_github_data):
        """Test formatter accepts datetime objects for from_date and to_date."""
        from datetime import datetime, timedelta
        from api.response_formatter import format_metrics_response
        
        to_date = datetime(2026, 2, 2, 23, 59, 59)
        from_date = datetime(2026, 1, 26, 0, 0, 0)
        
        result = format_metrics_response(
            mock_github_data,
            user='testuser',
            from_date=from_date,
            to_date=to_date,
            owner='TestOrg',
            repo='TestRepo'
        )
        
        assert 'meta' in result
        assert 'period' in result['meta']
        assert 'start' in result['meta']['period']
        assert 'end' in result['meta']['period']
        assert 'days' in result['meta']['period']
    
    def test_period_metadata_structure_with_date_range(self, mock_github_data):
        """Test period.start, period.end, period.days structure."""
        from datetime import datetime
        from api.response_formatter import format_metrics_response
        
        from_date = datetime(2026, 1, 26, 0, 0, 0)
        to_date = datetime(2026, 2, 2, 23, 59, 59)
        
        result = format_metrics_response(
            mock_github_data,
            user='testuser',
            from_date=from_date,
            to_date=to_date,
            owner='PowerShell',
            repo='PowerShell'
        )
        
        period = result['meta']['period']
        
        # Verify all required fields exist
        assert 'start' in period
        assert 'end' in period
        assert 'days' in period
        
        # Verify types
        assert isinstance(period['start'], str)
        assert isinstance(period['end'], str)
        assert isinstance(period['days'], int)
    
    def test_date_range_iso_format_with_z_suffix(self, mock_github_data):
        """Test dates are returned as ISO 8601 with Z suffix."""
        from datetime import datetime
        from api.response_formatter import format_metrics_response
        
        from_date = datetime(2026, 1, 26)
        to_date = datetime(2026, 2, 2)
        
        result = format_metrics_response(
            mock_github_data,
            user='testuser',
            from_date=from_date,
            to_date=to_date,
            owner='PowerShell',
            repo='PowerShell'
        )
        
        start = result['meta']['period']['start']
        end = result['meta']['period']['end']
        
        # Verify ISO 8601 format
        assert start.endswith('Z')
        assert end.endswith('Z')
        assert 'T' in start
        assert 'T' in end
        
        # Verify can be parsed
        datetime.fromisoformat(start.rstrip('Z'))
        datetime.fromisoformat(end.rstrip('Z'))
    
    def test_days_calculation_from_date_range(self, mock_github_data):
        """Test period.days is correctly calculated from date range."""
        from datetime import datetime, timedelta
        from api.response_formatter import format_metrics_response
        
        # Test various ranges
        test_cases = [
            (datetime(2026, 2, 2), datetime(2026, 2, 2), 1),  # Same day
            (datetime(2026, 1, 26), datetime(2026, 2, 2), 8),  # 7 days apart = 8 days inclusive
            (datetime(2026, 1, 1), datetime(2026, 1, 31), 31),  # Full month
        ]
        
        for from_date, to_date, expected_days in test_cases:
            result = format_metrics_response(
                mock_github_data,
                user='testuser',
                from_date=from_date,
                to_date=to_date,
                owner='PowerShell',
                repo='PowerShell'
            )
            
            assert result['meta']['period']['days'] == expected_days
    
    def test_formatter_with_200_day_range(self, mock_github_data):
        """Test formatter handles maximum 200-day range."""
        from datetime import datetime, timedelta
        from api.response_formatter import format_metrics_response
        
        to_date = datetime(2026, 2, 2)
        from_date = to_date - timedelta(days=200)
        
        result = format_metrics_response(
            mock_github_data,
            user='testuser',
            from_date=from_date,
            to_date=to_date,
            owner='PowerShell',
            repo='PowerShell'
        )
        
        assert result['meta']['period']['days'] == 201  # 200 days back + 1 for inclusive
    
    def test_format_issue_triage_with_mixed_label_types(self):
        """Test _format_issue_triage handles both string and dict labels."""
        raw_data = {
            'comments': [],
            'issues_labeled': [
                {
                    'number': 123,
                    'title': 'Test Issue',
                    'url': 'https://github.com/test/repo/issues/123',
                    'label': {'name': 'bug'},
                    'labeledAt': '2026-01-20T10:00:00Z'
                },
                {
                    'number': 124,
                    'title': 'Test Issue 2',
                    'url': 'https://github.com/test/repo/issues/124',
                    'label': 'enhancement',  # String instead of dict
                    'createdAt': '2026-01-20T11:00:00Z'
                }
            ],
            'issues_closed': []
        }
        
        result = _format_issue_triage(raw_data)
        assert len(result['labeled']) == 2
        assert result['labeled'][0]['label'] == 'bug'
        assert result['labeled'][1]['label'] == 'enhancement'
    
    def test_format_with_none_items(self):
        """Test formatters handle None items in lists."""
        raw_data = {
            'comments': [None, {'url': 'https://github.com/test/repo/issues/123#issuecomment-1', 'publishedAt': '2026-01-20T10:00:00Z'}],
            'issues_labeled': [None],
            'issues_closed': [None]
        }
        
        result = _format_issue_triage(raw_data)
        # Should skip None items
        assert len(result['comments']) == 1
        assert len(result['labeled']) == 0
        assert len(result['closed']) == 0


class TestAppRoutes:
    """Tests for main app routes."""
    
    def test_index_route(self, client):
        """Test main index route returns HTML."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
    
    def test_health_route(self, client):
        """Test /health route."""
        response = client.get('/health')
        assert response.status_code == 200
