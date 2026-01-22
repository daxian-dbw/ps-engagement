/**
 * API Client for GitHub Maintainer Activity Dashboard
 * 
 * This module handles all communication with the backend API.
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.timeout = 30000; // 30 seconds
    }

    /**
     * Fetch metrics for a GitHub user
     * @param {string} user - GitHub username
     * @param {number} days - Number of days to look back
     * @param {string} owner - Repository owner (optional)
     * @param {string} repo - Repository name (optional)
     * @returns {Promise<Object>} Metrics data
     */
    async fetchMetrics(user, days = 7, owner = null, repo = null) {
        const params = new URLSearchParams({ user, days: days.toString() });
        if (owner) params.append('owner', owner);
        if (repo) params.append('repo', repo);

        const url = `${this.baseURL}/api/metrics?${params.toString()}`;
        
        try {
            const response = await this._fetchWithTimeout(url);
            return await this._handleResponse(response, user);
        } catch (error) {
            console.error('Error fetching metrics:', error);
            throw error;
        }
    }

    /**
     * Check API health
     * @returns {Promise<Object>} Health status
     */
    async checkHealth() {
        const url = `${this.baseURL}/api/health`;
        
        try {
            const response = await this._fetchWithTimeout(url);
            return await response.json();
        } catch (error) {
            console.error('Error checking health:', error);
            throw new Error('Failed to connect to API');
        }
    }

    /**
     * Fetch with timeout
     * @private
     */
    async _fetchWithTimeout(url) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout. Please try again.');
            }
            throw new Error('Network error. Please check your connection.');
        }
    }

    /**
     * Handle API response
     * @private
     */
    async _handleResponse(response, username = '') {
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = this._getErrorMessage(response.status, errorData, username);
            throw new Error(errorMessage);
        }

        return await response.json();
    }

    /**
     * Get user-friendly error message based on status code
     * @private
     */
    _getErrorMessage(status, errorData, username) {
        const message = errorData?.error?.message;

        switch (status) {
            case 400:
                return message || 'Invalid parameters. Please check your input.';
            case 404:
                return message || `User '${username}' not found on GitHub.`;
            case 429:
                return message || 'Rate limit exceeded. Please try again in a few minutes.';
            case 500:
                return message || 'Server error. Please try again later.';
            default:
                return message || `An error occurred (${status}). Please try again.`;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}
