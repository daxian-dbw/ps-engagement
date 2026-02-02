"""
API routes for the GitHub Maintainer Activity Dashboard.

This module defines all API endpoints for retrieving maintainer
activity metrics.
"""

from flask import jsonify, request, current_app
from datetime import datetime, timedelta
import logging
from . import api_bp
from .response_formatter import format_metrics_response
from github_events import github_events

# Configure logging
logger = logging.getLogger(__name__)


def sanitize_error_message(error_msg):
    """
    Sanitize error messages to remove sensitive information.

    Removes:
    - GitHub tokens (ghp_*, gho_*, etc.)
    - Database connection strings
    - File paths
    - Environment variable values

    Args:
        error_msg (str): Original error message

    Returns:
        str: Sanitized error message
    """
    import re

    # Remove GitHub tokens
    error_msg = re.sub(r'gh[pousr]_[a-zA-Z0-9]{36,}', '[REDACTED_TOKEN]', error_msg)

    # Remove potential connection strings
    error_msg = re.sub(r'\w+://[^\s]+@[^\s]+', '[REDACTED_CONNECTION_STRING]', error_msg)

    # Remove environment variable assignments
    error_msg = re.sub(r'\b[A-Z_]+=[^\s]+', '[REDACTED_ENV_VAR]', error_msg)

    # Remove file paths (Windows and Unix)
    error_msg = re.sub(r'[A-Za-z]:\\[^\s]+\.py', '[FILE_PATH]', error_msg)
    error_msg = re.sub(r'/[^\s]+\.py', '[FILE_PATH]', error_msg)

    return error_msg


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns a simple JSON response indicating the API is operational.

    Returns:
        tuple: JSON response with status and timestamp, HTTP status code 200
        
    Example Response:
        {
            "status": "ok",
            "timestamp": "2026-01-21T10:30:00Z"
        }
    """
    try:
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    except Exception as e:
        # Even health check errors should be handled gracefully
        logger.error(f"Health check error: {str(e)}")
        try:
            # Try to get timestamp one more time
            timestamp = datetime.utcnow().isoformat() + 'Z'
        except:
            # If even datetime fails, use a static placeholder
            timestamp = 'unavailable'
        return jsonify({
            'status': 'error',
            'timestamp': timestamp,
            'message': 'Health check failed'
        }), 500


@api_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Get maintainer activity metrics for a GitHub user.

    Query Parameters:
        user (str, required): GitHub username
        from_date (str, required): Start date in YYYY-MM-DD format
        to_date (str, required): End date in YYYY-MM-DD format
        owner (str, optional): Repository owner (default from config)
        repo (str, optional): Repository name (default from config)

    Returns:
        tuple: JSON response with metrics data, HTTP status code

    Success Response (200):
        {
            "meta": {...},
            "summary": {...},
            "data": {...}
        }

    Error Response:
        {
            "error": {
                "code": "ERROR_CODE",
                "message": "Human-readable error message",
                "timestamp": "2026-01-21T10:30:00Z"
            }
        }
    """
    try:
        # Extract query parameters
        user = request.args.get('user', '').strip()
        from_date_str = request.args.get('from_date', '').strip()
        to_date_str = request.args.get('to_date', '').strip()
        owner = request.args.get('owner', current_app.config.get('GITHUB_OWNER', 'PowerShell'))
        repo = request.args.get('repo', current_app.config.get('GITHUB_REPO', 'PowerShell'))

        # Validate required parameter: user
        if not user:
            logger.warning("Metrics request missing required parameter: user")
            return jsonify({
                'error': {
                    'code': 'MISSING_PARAMETER',
                    'message': 'Missing required parameter: user',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 400

        # Validate required parameters: from_date and to_date
        if not from_date_str or not to_date_str:
            logger.warning(f"Metrics request missing date parameters: from_date={from_date_str}, to_date={to_date_str}")
            return jsonify({
                'error': {
                    'code': 'MISSING_PARAMETER',
                    'message': 'Both from_date and to_date parameters are required',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 400

        # Parse and validate date format
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
        except ValueError as e:
            logger.warning(f"Invalid date format: from_date={from_date_str}, to_date={to_date_str}, error={str(e)}")
            return jsonify({
                'error': {
                    'code': 'INVALID_DATE_FORMAT',
                    'message': 'Dates must be in YYYY-MM-DD format',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 400

        # Validate date range: from_date <= to_date
        if from_date > to_date:
            logger.warning(f"Invalid date range: from_date={from_date_str} > to_date={to_date_str}")
            return jsonify({
                'error': {
                    'code': 'INVALID_DATE_RANGE',
                    'message': 'From date must be before or equal to to date',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 400

        # Validate dates are not in the future
        now = datetime.utcnow()
        if to_date.replace(hour=23, minute=59, second=59) > now:
            logger.warning(f"Future date not allowed: to_date={to_date_str}")
            return jsonify({
                'error': {
                    'code': 'FUTURE_DATE_NOT_ALLOWED',
                    'message': 'Cannot select future dates',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 400

        # Validate max range (200 days)
        days_diff = (to_date - from_date).days
        if days_diff > 200:
            logger.warning(f"Date range too large: {days_diff} days (max 200)")
            return jsonify({
                'error': {
                    'code': 'DATE_RANGE_TOO_LARGE',
                    'message': 'Date range cannot exceed 200 days',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 400

        # Validate owner and repo
        if not owner or not repo:
            logger.warning(f"Invalid owner/repo: {owner}/{repo}")
            return jsonify({
                'error': {
                    'code': 'INVALID_PARAMETER',
                    'message': 'Owner and repo must be non-empty strings',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 400

        # Log the request
        logger.info(f"Fetching metrics for user={user}, from_date={from_date_str}, to_date={to_date_str}, repo={owner}/{repo}")

        # Call github_events module to get contributions
        try:
            # Set time to start and end of day in UTC
            from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
            to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=0)
            
            raw_data = github_events.contributions_by(
                actor_login=user,
                from_date=from_date,
                to_date=to_date,
                owner=owner,
                repo=repo
            )
        except Exception as github_error:
            error_msg = str(github_error)
            logger.error(f"GitHub API error for user {user}: {error_msg}")

            # Check for specific error types
            if 'rate limit' in error_msg.lower():
                return jsonify({
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': 'GitHub API rate limit exceeded. Please try again later.',
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                }), 429
            elif 'not found' in error_msg.lower() or '404' in error_msg:
                return jsonify({
                    'error': {
                        'code': 'USER_NOT_FOUND',
                        'message': f'GitHub user "{user}" not found',
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                }), 404
            elif 'unauthorized' in error_msg.lower() or '401' in error_msg:
                return jsonify({
                    'error': {
                        'code': 'AUTHENTICATION_ERROR',
                        'message': 'GitHub authentication failed. Check your token.',
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                }), 500
            else:
                # Sanitize error message to remove sensitive information
                sanitized_msg = sanitize_error_message(error_msg)
                return jsonify({
                    'error': {
                        'code': 'GITHUB_API_ERROR',
                        'message': f'Error fetching data from GitHub: {sanitized_msg}',
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                }), 500

        # Format the response
        formatted_response = format_metrics_response(raw_data, user, from_date, to_date, owner, repo)

        logger.info(f"Successfully retrieved metrics for {user}: {formatted_response['summary']['total_actions']} total actions")

        return jsonify(formatted_response), 200

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in get_metrics: {str(e)}", exc_info=True)
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }), 500
    # Placeholder implementation
    # Will be implemented in Task 2.4
    return jsonify({
        'message': 'Metrics endpoint - to be implemented'
    }), 501
