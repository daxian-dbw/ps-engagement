"""
Response formatting utilities for API endpoints.

This module transforms raw data from github_events module into
the API response format expected by the frontend.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List


def format_metrics_response(
    raw_data: Optional[Dict[str, Any]],
    user: str,
    days: int,
    owner: str,
    repo: str
) -> Dict[str, Any]:
    """
    Transform GitHub activity data into API response format.
    
    Args:
        raw_data: Raw data from github_events.contributions_by()
        user: GitHub username
        days: Number of days queried
        owner: Repository owner
        repo: Repository name
    
    Returns:
        Formatted response dictionary with meta, summary, and data sections
        
    Example:
        {
            "meta": {"user": "...", "repository": "...", "period": {...}},
            "summary": {"total_actions": 23, "by_category": {...}},
            "data": {"issues_opened": [...], "prs_opened": [...], ...}
        }
    """
    if raw_data is None:
        raw_data = {}
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
    
    # Extract and format data
    issues_opened = _format_issues_opened(raw_data.get('issues_opened', []))
    prs_opened = _format_prs_opened(raw_data.get('prs_opened', []))
    issue_triage = _format_issue_triage(raw_data)
    code_reviews = _format_code_reviews(raw_data)
    
    # Calculate counts
    total_actions = (
        len(issues_opened) +
        len(prs_opened) +
        len(issue_triage.get('comments', [])) +
        len(issue_triage.get('labeled', [])) +
        len(issue_triage.get('closed', [])) +
        len(code_reviews.get('comments', [])) +
        len(code_reviews.get('reviews', [])) +
        len(code_reviews.get('merged', [])) +
        len(code_reviews.get('closed', []))
    )
    
    return {
        'meta': {
            'user': user,
            'repository': f'{owner}/{repo}',
            'period': {
                'days': days,
                'start': start_date.isoformat() + 'Z',
                'end': end_date.isoformat() + 'Z'
            },
            'fetched_at': datetime.utcnow().isoformat() + 'Z'
        },
        'summary': {
            'total_actions': total_actions,
            'by_category': {
                'issues_opened': len(issues_opened),
                'prs_opened': len(prs_opened),
                'issue_triage': (
                    len(issue_triage.get('comments', [])) +
                    len(issue_triage.get('labeled', [])) +
                    len(issue_triage.get('closed', []))
                ),
                'code_reviews': (
                    len(code_reviews.get('comments', [])) +
                    len(code_reviews.get('reviews', [])) +
                    len(code_reviews.get('merged', [])) +
                    len(code_reviews.get('closed', []))
                )
            }
        },
        'data': {
            'issues_opened': issues_opened,
            'prs_opened': prs_opened,
            'issue_triage': issue_triage,
            'code_reviews': code_reviews
        }
    }


def _format_issues_opened(issues: List[Dict]) -> List[Dict]:
    """Format issues opened data."""
    result = []
    for issue in issues:
        if not issue:
            continue
        result.append({
            'number': issue.get('number'),
            'title': issue.get('title', ''),
            'url': issue.get('url', ''),
            'created_at': issue.get('createdAt', issue.get('openedAt', ''))
        })
    return result


def _format_prs_opened(prs: List[Dict]) -> List[Dict]:
    """Format pull requests opened data."""
    result = []
    for pr in prs:
        if not pr:
            continue
        result.append({
            'number': pr.get('number'),
            'title': pr.get('title', ''),
            'url': pr.get('url', ''),
            'action': 'opened',
            'timestamp': pr.get('occurredAt', pr.get('openedAt', ''))
        })
    return result


def _format_issue_triage(raw_data: Dict) -> Dict[str, List[Dict]]:
    """
    Format issue triage data by combining comments (issues only),
    labeled events, and closed events.
    """
    # Filter comments for issues only (exclude PR comments)
    all_comments = raw_data.get('comments', [])
    issue_comments = []
    
    for comment in all_comments:
        if not comment:
            continue
        # Check if it's an issue comment (has 'issue' field or URL contains /issues/)
        url = comment.get('url', '')
        if '/pull/' not in url and '/issues/' in url:
            issue_data = comment.get('issue', {})
            issue_comments.append({
                'number': issue_data.get('number') if isinstance(issue_data, dict) else None,
                'title': issue_data.get('title', '') if isinstance(issue_data, dict) else '',
                'url': url,
                'timestamp': comment.get('publishedAt', '')
            })
    
    # Format labeled events
    labeled = []
    for item in raw_data.get('issues_labeled', []):
        if not item:
            continue
        labeled.append({
            'number': item.get('number'),
            'title': item.get('title', ''),
            'label': item.get('label', {}).get('name', '') if isinstance(item.get('label'), dict) else item.get('label', ''),
            'url': item.get('url', ''),
            'timestamp': item.get('labeledAt', item.get('createdAt', ''))
        })
    
    # Format closed events
    closed = []
    for item in raw_data.get('issues_closed', []):
        if not item:
            continue
        closed.append({
            'number': item.get('number'),
            'title': item.get('title', ''),
            'url': item.get('url', ''),
            'timestamp': item.get('closedAt', '')
        })
    
    return {
        'comments': issue_comments,
        'labeled': labeled,
        'closed': closed
    }


def _format_code_reviews(raw_data: Dict) -> Dict[str, List[Dict]]:
    """
    Format code review data by combining PR comments, reviews,
    PRs merged, and PRs closed.
    """
    # Filter comments for PRs only
    all_comments = raw_data.get('comments', [])
    pr_comments = []
    
    for comment in all_comments:
        if not comment:
            continue
        url = comment.get('url', '')
        if '/pull/' in url:
            # For PR comments, the issue field contains the PR number and title
            # (GitHub API treats PRs as issues)
            issue_data = comment.get('issue', {})
            pr_comments.append({
                'number': issue_data.get('number') if isinstance(issue_data, dict) else None,
                'title': issue_data.get('title', '') if isinstance(issue_data, dict) else '',
                'url': url,
                'timestamp': comment.get('publishedAt', '')
            })
    
    # Format reviews
    reviews = []
    for review in raw_data.get('reviews', []):
        if not review:
            continue
        reviews.append({
            'number': review.get('pullRequest', {}).get('number') if isinstance(review.get('pullRequest'), dict) else review.get('number'),
            'title': review.get('pullRequest', {}).get('title', '') if isinstance(review.get('pullRequest'), dict) else review.get('title', ''),
            'state': review.get('state', review.get('pullRequestReview', {}).get('state', '') if isinstance(review.get('pullRequestReview'), dict) else ''),
            'url': review.get('url', review.get('pullRequestReview', {}).get('url', '') if isinstance(review.get('pullRequestReview'), dict) else ''),
            'timestamp': review.get('occurredAt', review.get('submittedAt', ''))
        })
    
    # Format PRs merged
    prs_merged = []
    for pr in raw_data.get('prs_merged', []):
        if not pr:
            continue
        prs_merged.append({
            'number': pr.get('number'),
            'title': pr.get('title', ''),
            'action': 'merged',
            'url': pr.get('url', ''),
            'timestamp': pr.get('occurredAt', pr.get('mergedAt', ''))
        })
    
    # Format PRs closed
    prs_closed = []
    for pr in raw_data.get('prs_closed', []):
        if not pr:
            continue
        prs_closed.append({
            'number': pr.get('number'),
            'title': pr.get('title', ''),
            'action': 'closed',
            'url': pr.get('url', ''),
            'timestamp': pr.get('occurredAt', pr.get('closedAt', ''))
        })
    
    return {
        'comments': pr_comments,
        'reviews': reviews,
        'merged': prs_merged,
        'closed': prs_closed
    }



def format_error_response(
    error_code: str,
    message: str
) -> Dict[str, Any]:
    """
    Format error response.
    
    Args:
        error_code: Error code identifier
        message: Human-readable error message
    
    Returns:
        Formatted error response dictionary
    """
    return {
        'error': {
            'code': error_code,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    }
