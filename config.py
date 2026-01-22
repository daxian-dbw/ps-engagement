"""
Configuration management for GitHub Maintainer Activity Dashboard.

This module handles loading configuration from environment variables
with sensible defaults for development.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Application configuration class.
    
    Loads configuration from environment variables with fallback defaults.
    """
    
    # GitHub API Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_OWNER = os.getenv('GITHUB_OWNER', 'PowerShell')
    GITHUB_REPO = os.getenv('GITHUB_REPO', 'PowerShell')
    
    # Application Settings
    DEFAULT_DAYS_BACK = int(os.getenv('DEFAULT_DAYS_BACK', '7'))
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Cache Configuration (for future use)
    CACHE_TTL_MINUTES = int(os.getenv('CACHE_TTL_MINUTES', '10'))
    
    # Flask Settings
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    @classmethod
    def validate(cls):
        """
        Validate required configuration values.
        
        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.GITHUB_TOKEN:
            raise ValueError(
                "GITHUB_TOKEN environment variable is required. "
                "Please set it in your .env file or environment."
            )
