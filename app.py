"""
GitHub Maintainer Activity Dashboard - Flask Application

This is the main entry point for the Flask web application that displays
GitHub maintainer activity metrics.
"""

from flask import Flask, render_template
from config import Config

# Initialize Flask application
app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Validate required configuration
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your .env file and ensure GITHUB_TOKEN is set.")
    # Continue running for development, but warn user
    if not Config.DEBUG:
        raise

# Register blueprints
from api import api_bp
app.register_blueprint(api_bp)


@app.route('/')
def index():
    """
    Main dashboard page.
    
    Returns:
        str: Rendered HTML template for the main page
    """
    return render_template('index.html')


@app.route('/health')
def health():
    """
    Basic health check endpoint.
    
    Returns:
        str: Simple health status message
    """
    return "OK"


if __name__ == '__main__':
    # Run the Flask development server
    print("=" * 60)
    print("GitHub Maintainer Activity Dashboard")
    print("=" * 60)
    print(f"Server running at: http://localhost:5001")
    print(f"Debug mode: {app.config['DEBUG']}")
    print(f"Target repository: {app.config['GITHUB_OWNER']}/{app.config['GITHUB_REPO']}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=app.config['DEBUG'])
