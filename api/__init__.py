"""
API package for GitHub Maintainer Activity Dashboard.

This package contains the Flask blueprint for API endpoints
and response formatting utilities.
"""

from flask import Blueprint

# Create the API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes to register them with the blueprint
from . import routes
