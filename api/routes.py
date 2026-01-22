"""
API routes for the GitHub Maintainer Activity Dashboard.

This module defines all API endpoints for retrieving maintainer
activity metrics.
"""

from flask import jsonify, request, current_app
from datetime import datetime
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
        days (int, optional): Number of days to look back (1-180, default: 7)
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
        days_str = request.args.get('days', '7')
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

        # Validate and parse days parameter
        try:
            days = int(days_str)
        except ValueError:
            logger.warning(f"Invalid days parameter: {days_str}")
            return jsonify({
                'error': {
                    'code': 'INVALID_PARAMETER',
                    'message': f'Invalid days parameter: must be an integer',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            }), 400

        # Validate days range
        if days < 1 or days > 180:
            logger.warning(f"Days parameter out of range: {days}")
            return jsonify({
                'error': {
                    'code': 'INVALID_PARAMETER',
                    'message': 'Days parameter must be between 1 and 180',
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
        logger.info(f"Fetching metrics for user={user}, days={days}, repo={owner}/{repo}")

        # Call github_events module to get contributions
        try:
            raw_data = github_events.contributions_by(
                actor_login=user,
                days_back=days,
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
        formatted_response = format_metrics_response(raw_data, user, days, owner, repo)

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
