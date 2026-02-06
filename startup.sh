#!/bin/bash
# Azure App Service startup script for Flask application

# Number of worker processes (adjust based on your App Service tier)
# Rule of thumb: (2 x num_cores) + 1
WORKERS=4

# Timeout in seconds (GitHub API calls can take time)
TIMEOUT=600

# Start Gunicorn
gunicorn --bind=0.0.0.0:8000 \
         --workers=$WORKERS \
         --timeout=$TIMEOUT \
         --access-logfile=- \
         --error-logfile=- \
         app:app
