/**
 * API Client for GitHub Maintainer Activity Dashboard
 * 
 * This module handles all communication with the backend API.
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.timeout = 90000; // 90 seconds - increased for large date ranges
    }

    /**
     * Get user's IANA timezone name (e.g., 'America/Los_Angeles')
     * @returns {string} IANA timezone identifier
     */
    getUserTimezone() {
        try {
            return Intl.DateTimeFormat().resolvedOptions().timeZone;
        } catch (error) {
            console.warn('Could not detect timezone, defaulting to UTC:', error);
            return 'UTC';
        }
    }

    /**
     * Fetch metrics for a GitHub user
     * @param {string} user - GitHub username
     * @param {Object|number} options - Either {from_date: string, to_date: string} or a number (days)
     * @param {string} owner - Repository owner (optional)
     * @param {string} repo - Repository name (optional)
     * @returns {Promise<Object>} Metrics data
     */
    async fetchMetrics(user, options = 7, owner = null, repo = null) {
        const params = new URLSearchParams({ user });
        
        // Handle both object (date range) and number (days) formats
        if (typeof options === 'object' && options.from_date && options.to_date) {
            // Custom date range mode
            params.append('from_date', options.from_date);
            params.append('to_date', options.to_date);
        } else {
            // Quick select mode - convert days to date range
            // Use yesterday as the end date to avoid "future date" errors
            const days = typeof options === 'number' ? options : 7;
            const to = new Date();
            to.setDate(to.getDate() - 1); // Yesterday
            const from = new Date(to);
            from.setDate(to.getDate() - (days - 1)); // days - 1 because we're already 1 day back
            
            params.append('from_date', this._formatDate(from));
            params.append('to_date', this._formatDate(to));
        }
        
        // Always include user's timezone for accurate date filtering
        params.append('timezone', this.getUserTimezone());
        
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
     * Format date as YYYY-MM-DD
     * @private
     */
    _formatDate(date) {
        return date.toISOString().split('T')[0];
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

    /**
     * Get team engagement metrics
     * @param {string} fromDate - Start date in YYYY-MM-DD format
     * @param {string} toDate - End date in YYYY-MM-DD format
     * @param {string} owner - Repository owner (optional)
     * @param {string} repo - Repository name (optional)
     * @returns {Promise<Object>} Team engagement data
     */
    async getTeamEngagement(fromDate, toDate, owner = null, repo = null) {
        const params = new URLSearchParams({
            from_date: fromDate,
            to_date: toDate,
            timezone: this.getUserTimezone()
        });
        
        if (owner) params.append('owner', owner);
        if (repo) params.append('repo', repo);

        const url = `${this.baseURL}/api/team-engagement?${params.toString()}`;
        
        try {
            const response = await this._fetchWithTimeout(url);
            return await this._handleResponse(response);
        } catch (error) {
            console.error('Error fetching team engagement:', error);
            throw error;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}
