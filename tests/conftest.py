"""
Pytest configuration and shared fixtures.
"""

import pytest
from app import app as flask_app
from datetime import datetime, timedelta


@pytest.fixture
def app():
    """Create and configure a Flask app instance for testing."""
    flask_app.config['TESTING'] = True
    flask_app.config['GITHUB_TOKEN'] = 'test_token_12345'
    flask_app.config['GITHUB_OWNER'] = 'PowerShell'
    flask_app.config['GITHUB_REPO'] = 'PowerShell'
    yield flask_app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


@pytest.fixture
def mock_github_data():
    """Mock data structure returned by github_events.contributions_by()."""
    return {
        'issues_opened': [
            {
                'number': 12345,
                'title': 'Test Issue 1',
                'url': 'https://github.com/PowerShell/PowerShell/issues/12345',
                'created_at': '2026-01-20T10:00:00Z',
                'labels': ['bug', 'needs-triage']
            },
            {
                'number': 12346,
                'title': 'Test Issue 2',
                'url': 'https://github.com/PowerShell/PowerShell/issues/12346',
                'created_at': '2026-01-19T15:30:00Z',
                'labels': []
            }
        ],
        'prs_opened': [
            {
                'number': 12347,
                'title': 'Test PR 1',
                'url': 'https://github.com/PowerShell/PowerShell/pull/12347',
                'created_at': '2026-01-18T09:00:00Z',
                'state': 'OPEN',
                'labels': ['enhancement']
            }
        ],
        'issue_comments': [
            {
                'issue_number': 12340,
                'issue_title': 'Existing Issue',
                'comment_url': 'https://github.com/PowerShell/PowerShell/issues/12340#issuecomment-1',
                'created_at': '2026-01-17T14:20:00Z'
            }
        ],
        'issues_labeled': [
            {
                'number': 12341,
                'title': 'Labeled Issue',
                'url': 'https://github.com/PowerShell/PowerShell/issues/12341',
                'label': 'bug',
                'created_at': '2026-01-16T11:00:00Z'
            }
        ],
        'issues_closed': [
            {
                'number': 12342,
                'title': 'Closed Issue',
                'url': 'https://github.com/PowerShell/PowerShell/issues/12342',
                'closed_at': '2026-01-15T16:45:00Z'
            }
        ],
        'pr_comments': [
            {
                'pr_number': 12343,
                'pr_title': 'Commented PR',
                'comment_url': 'https://github.com/PowerShell/PowerShell/pull/12343#issuecomment-2',
                'created_at': '2026-01-14T10:30:00Z'
            }
        ],
        'pr_reviews': [
            {
                'pr_number': 12344,
                'pr_title': 'Reviewed PR',
                'review_url': 'https://github.com/PowerShell/PowerShell/pull/12344#pullrequestreview-1',
                'state': 'APPROVED',
                'submitted_at': '2026-01-13T09:15:00Z'
            }
        ],
        'prs_merged': [],
        'prs_closed': []
    }


@pytest.fixture
def empty_github_data():
    """Mock empty data structure (no activity)."""
    return {
        'issues_opened': [],
        'prs_opened': [],
        'issue_comments': [],
        'issues_labeled': [],
        'issues_closed': [],
        'pr_comments': [],
        'pr_reviews': [],
        'prs_merged': [],
        'prs_closed': []
    }


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    return datetime(2026, 1, 21, 12, 0, 0)


@pytest.fixture
def valid_date_range_7_days():
    """Valid 7-day date range ending today."""
    # Use dates in the past relative to actual current date
    to_date = datetime.utcnow() - timedelta(days=1)  # Yesterday
    from_date = to_date - timedelta(days=7)
    return {
        'from_date': from_date.strftime('%Y-%m-%d'),
        'to_date': to_date.strftime('%Y-%m-%d'),
        'from_date_obj': from_date,
        'to_date_obj': to_date
    }


@pytest.fixture
def valid_date_range_1_day():
    """Valid 1-day date range (same day)."""
    date = datetime.utcnow() - timedelta(days=1)  # Yesterday
    return {
        'from_date': date.strftime('%Y-%m-%d'),
        'to_date': date.strftime('%Y-%m-%d'),
        'from_date_obj': date,
        'to_date_obj': date
    }


@pytest.fixture
def valid_date_range_200_days():
    """Valid 200-day date range (maximum allowed)."""
    to_date = datetime.utcnow() - timedelta(days=1)  # Yesterday
    from_date = to_date - timedelta(days=200)
    return {
        'from_date': from_date.strftime('%Y-%m-%d'),
        'to_date': to_date.strftime('%Y-%m-%d'),
        'from_date_obj': from_date,
        'to_date_obj': to_date
    }


@pytest.fixture
def invalid_date_range_reversed():
    """Invalid date range where from_date > to_date."""
    return {
        'from_date': '2026-02-01',
        'to_date': '2026-01-01'
    }


@pytest.fixture
def invalid_date_range_too_large():
    """Invalid date range exceeding 200 days."""
    to_date = datetime.utcnow() - timedelta(days=1)  # Yesterday
    from_date = to_date - timedelta(days=201)
    return {
        'from_date': from_date.strftime('%Y-%m-%d'),
        'to_date': to_date.strftime('%Y-%m-%d')
    }


@pytest.fixture
def invalid_date_range_future():
    """Invalid date range with future dates."""
    from_date = datetime.utcnow() + timedelta(days=10)  # Future
    to_date = datetime.utcnow() + timedelta(days=20)  # Future
    return {
        'from_date': from_date.strftime('%Y-%m-%d'),
        'to_date': to_date.strftime('%Y-%m-%d')
    }


@pytest.fixture
def invalid_date_format():
    """Date ranges with invalid formats."""
    return {
        'us_format': {'from_date': '01-26-2026', 'to_date': '02-02-2026'},
        'european_format': {'from_date': '26/01/2026', 'to_date': '02/02/2026'},
        'no_leading_zeros': {'from_date': '2026-1-26', 'to_date': '2026-2-2'},
        'invalid_values': {'from_date': '2026-13-45', 'to_date': '2026-02-02'}
    }
