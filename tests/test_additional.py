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


class TestAPIEndpointsEdgeCases:
    """Additional API endpoint tests for edge cases."""
    
    @patch('api.routes.github_events')
    def test_metrics_rate_limit_error(self, mock_github, client):
        """Test metrics endpoint handles rate limit errors."""
        mock_github.contributions_by.side_effect = Exception("rate limit exceeded")
        
        response = client.get('/api/metrics?user=testuser&days=7')
        assert response.status_code == 429
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'RATE_LIMIT_EXCEEDED'
    
    @patch('api.routes.github_events')
    def test_metrics_user_not_found(self, mock_github, client):
        """Test metrics endpoint handles user not found errors."""
        mock_github.contributions_by.side_effect = Exception("User not found")
        
        response = client.get('/api/metrics?user=nonexistent&days=7')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'USER_NOT_FOUND'
        assert 'nonexistent' in data['error']['message']
    
    @patch('api.routes.github_events')
    def test_metrics_unauthorized_error(self, mock_github, client):
        """Test metrics endpoint handles authentication errors."""
        mock_github.contributions_by.side_effect = Exception("401 unauthorized")
        
        response = client.get('/api/metrics?user=testuser&days=7')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'AUTHENTICATION_ERROR'
    
    def test_metrics_invalid_owner_repo(self, client):
        """Test metrics endpoint validates owner and repo."""
        response = client.get('/api/metrics?user=testuser&days=7&owner=&repo=')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['error']['code'] == 'INVALID_PARAMETER'
        assert 'owner' in data['error']['message'].lower() or 'repo' in data['error']['message'].lower()


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
