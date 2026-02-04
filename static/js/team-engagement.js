/**
 * Team Engagement Component
 * 
 * Handles the team engagement metrics view including:
 * - Date range selection
 * - Fetching team and contributor engagement data
 * - Rendering metrics and charts
 */

class TeamEngagement {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.currentDays = 7;
        this.selectionMode = 'quick'; // 'quick' or 'custom'
        this.customRange = { from: null, to: null };
        this.charts = { issues: null, prs: null };
        
        // Cache DOM elements
        this.elements = {
            searchForm: null,
            searchButton: null,
            buttonText: null,
            buttonSpinner: null,
            errorMessage: null,
            errorMessageText: null,
            dayButtons: null,
            customButton: null,
            customDatePicker: null,
            fromDateInput: null,
            toDateInput: null,
            dateRangeError: null,
            resultsContainer: null,
            loading: null,
            summary: null
        };
    }

    /**
     * Initialize the team engagement component
     */
    init() {
        console.log('Initializing Team Engagement component...');
        
        // Cache DOM elements
        this.cacheElements();
        
        // Initialize date pickers
        this.initializeDatePickers();
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('Team Engagement component initialized');
    }

    /**
     * Cache DOM elements for performance
     */
    cacheElements() {
        this.elements.searchForm = document.getElementById('team-search-form');
        this.elements.searchButton = document.getElementById('team-search-button');
        this.elements.buttonText = document.getElementById('team-button-text');
        this.elements.buttonSpinner = document.getElementById('team-button-spinner');
        this.elements.errorMessage = document.getElementById('team-error-message');
        this.elements.errorMessageText = document.getElementById('team-error-message-text');
        this.elements.dayButtons = document.querySelectorAll('.team-day-button');
        this.elements.customButton = document.getElementById('team-custom-button');
        this.elements.customDatePicker = document.getElementById('team-custom-date-picker');
        this.elements.fromDateInput = document.getElementById('team-from-date');
        this.elements.toDateInput = document.getElementById('team-to-date');
        this.elements.dateRangeError = document.getElementById('team-date-range-error');
        this.elements.resultsContainer = document.getElementById('team-results-container');
        this.elements.loading = document.getElementById('team-loading');
        this.elements.summary = document.getElementById('team-summary');
    }

    /**
     * Initialize Flatpickr for date inputs
     */
    initializeDatePickers() {
        if (typeof flatpickr !== 'undefined') {
            flatpickr(this.elements.fromDateInput, {
                dateFormat: 'Y-m-d',
                maxDate: 'today',
                onChange: () => this.updateCustomRangeIfValid()
            });
            
            flatpickr(this.elements.toDateInput, {
                dateFormat: 'Y-m-d',
                maxDate: 'today',
                onChange: () => this.updateCustomRangeIfValid()
            });
        }
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Form submission
        this.elements.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSearchSubmit();
        });
        
        // Day buttons
        this.elements.dayButtons.forEach(button => {
            button.addEventListener('click', () => {
                if (button.id === 'team-custom-button') {
                    this.handleCustomButtonClick();
                } else {
                    this.handleDayButtonClick(button);
                }
            });
        });
    }

    /**
     * Handle day button click
     */
    handleDayButtonClick(clickedButton) {
        const days = parseInt(clickedButton.dataset.days);
        
        this.setQuickSelect(days);
        
        // Update button states
        this.elements.dayButtons.forEach(button => {
            button.classList.remove('selected', 'bg-blue-500', 'text-white');
            button.classList.add('border-gray-300');
        });
        
        clickedButton.classList.add('selected', 'bg-blue-500', 'text-white');
        clickedButton.classList.remove('border-gray-300');
        
        // Hide custom picker
        this.hideCustomDatePicker();
        
        console.log(`Team view: Selected ${days} days`);
    }

    /**
     * Handle custom button click
     */
    handleCustomButtonClick() {
        const isVisible = !this.elements.customDatePicker.classList.contains('hidden');
        
        if (isVisible) {
            this.hideCustomDatePicker();
        } else {
            this.showCustomDatePicker();
        }
    }

    /**
     * Show custom date picker
     */
    showCustomDatePicker() {
        this.elements.customDatePicker.classList.remove('hidden');
        
        // Set default values
        const today = new Date();
        const weekAgo = new Date(today);
        weekAgo.setDate(today.getDate() - 7);
        
        this.elements.fromDateInput.value = this.formatDateForInput(weekAgo);
        this.elements.toDateInput.value = this.formatDateForInput(today);
        
        // Mark custom button as selected
        this.elements.customButton.classList.add('selected', 'bg-blue-500', 'text-white');
        this.elements.customButton.classList.remove('border-gray-300');
        
        // Deselect day buttons
        this.elements.dayButtons.forEach(btn => {
            if (btn.id !== 'team-custom-button') {
                btn.classList.remove('selected', 'bg-blue-500', 'text-white');
                btn.classList.add('border-gray-300');
            }
        });
        
        this.hideDateRangeError();
        this.updateCustomRangeIfValid();
    }

    /**
     * Hide custom date picker
     */
    hideCustomDatePicker() {
        this.elements.customDatePicker.classList.add('hidden');
        this.hideDateRangeError();
    }

    /**
     * Update custom range if dates are valid
     */
    updateCustomRangeIfValid() {
        const fromDate = this.elements.fromDateInput.value;
        const toDate = this.elements.toDateInput.value;
        
        if (fromDate && toDate && this.validateCustomRange(fromDate, toDate)) {
            this.setCustomRange(fromDate, toDate);
            console.log(`Team view: Custom range set: ${fromDate} to ${toDate}`);
        }
    }

    /**
     * Validate custom date range
     */
    validateCustomRange(fromDate, toDate) {
        const from = new Date(fromDate);
        const to = new Date(toDate);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (from > to) {
            this.showDateRangeError('From date must be before or equal to To date');
            return false;
        }
        
        if (to > today) {
            this.showDateRangeError('To date cannot be in the future');
            return false;
        }
        
        const daysDiff = Math.ceil((to - from) / (1000 * 60 * 60 * 24));
        if (daysDiff > 200) {
            this.showDateRangeError('Date range cannot exceed 200 days');
            return false;
        }
        
        this.hideDateRangeError();
        return true;
    }

    /**
     * Show date range error
     */
    showDateRangeError(message) {
        this.elements.dateRangeError.textContent = message;
        this.elements.dateRangeError.classList.remove('hidden');
    }

    /**
     * Hide date range error
     */
    hideDateRangeError() {
        this.elements.dateRangeError.classList.add('hidden');
    }

    /**
     * Format date for input
     */
    formatDateForInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    /**
     * Set quick select mode
     */
    setQuickSelect(days) {
        this.selectionMode = 'quick';
        this.currentDays = days;
        this.customRange = { from: null, to: null };
    }

    /**
     * Set custom range mode
     */
    setCustomRange(fromDate, toDate) {
        this.selectionMode = 'custom';
        this.customRange = { from: fromDate, to: toDate };
    }

    /**
     * Get current selection parameters
     */
    getCurrentSelection() {
        if (this.selectionMode === 'custom') {
            return {
                from_date: this.customRange.from,
                to_date: this.customRange.to
            };
        } else {
            return { days: this.currentDays };
        }
    }

    /**
     * Handle search form submission
     */
    async handleSearchSubmit() {
        this.clearError();
        
        const params = this.getCurrentSelection();
        
        if (params.days) {
            await this.loadData(params.days);
        } else if (params.from_date && params.to_date) {
            await this.loadDataWithDateRange(params.from_date, params.to_date);
        }
    }

    /**
     * Load data with days parameter
     */
    async loadData(days) {
        // Use yesterday as the end date to avoid "future date" errors
        const toDate = new Date();
        toDate.setDate(toDate.getDate() - 1); // Yesterday
        const fromDate = new Date(toDate);
        fromDate.setDate(toDate.getDate() - (days - 1)); // days - 1 because we're already 1 day back
        
        const fromDateStr = this.formatDateForInput(fromDate);
        const toDateStr = this.formatDateForInput(toDate);
        
        await this.loadDataWithDateRange(fromDateStr, toDateStr);
    }

    /**
     * Load data with date range
     */
    async loadDataWithDateRange(fromDate, toDate) {
        this.showLoading();
        
        try {
            const data = await this.apiClient.getTeamEngagement(fromDate, toDate);
            this.renderResults(data);
        } catch (error) {
            this.showError(error.message || 'Failed to load team engagement data');
            this.hideLoading();
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        this.elements.resultsContainer.classList.remove('hidden');
        this.elements.loading.classList.remove('hidden');
        this.elements.summary.classList.add('hidden');
        
        // Disable button
        this.elements.searchButton.disabled = true;
        this.elements.buttonText.classList.add('opacity-50');
        this.elements.buttonSpinner.classList.remove('hidden');
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        this.elements.loading.classList.add('hidden');
        
        // Enable button
        this.elements.searchButton.disabled = false;
        this.elements.buttonText.classList.remove('opacity-50');
        this.elements.buttonSpinner.classList.add('hidden');
    }

    /**
     * Show error message
     */
    showError(message) {
        this.elements.errorMessageText.textContent = message;
        this.elements.errorMessage.classList.remove('hidden');
        
        // Scroll to error
        this.elements.errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Clear error message
     */
    clearError() {
        this.elements.errorMessage.classList.add('hidden');
    }

    /**
     * Render results
     */
    renderResults(data) {
        this.hideLoading();
        this.elements.summary.classList.remove('hidden');
        
        // Update header
        const fromDate = data.meta.from_date;
        const toDate = data.meta.to_date;
        document.getElementById('team-summary-date-range').textContent = 
            `${fromDate} to ${toDate}`;
        document.getElementById('team-summary-timestamp').textContent = 
            new Date(data.meta.timestamp).toLocaleString();
        
        // Render issues metrics
        this.renderIssuesMetrics(data.team.issue, data.contributors.issue);
        
        // Render PRs metrics
        this.renderPRsMetrics(data.team.pr, data.contributors.pr);
        
        console.log('Team engagement data rendered successfully');
    }

    /**
     * Render issues metrics
     */
    renderIssuesMetrics(teamData, contribData) {
        const total = teamData.total_issues;
        
        // Total
        document.getElementById('team-issues-total').textContent = total;
        
        // Team engagement
        const teamCount = teamData.team_engaged;
        const teamPct = Math.round(teamData.engagement_ratio * 100);
        document.getElementById('team-issues-team-count').textContent = teamCount;
        document.getElementById('team-issues-team-pct').textContent = teamPct;
        
        // Contributors engagement
        const contribCount = contribData.team_engaged;
        const contribPct = Math.round(contribData.engagement_ratio * 100);
        document.getElementById('team-issues-contrib-count').textContent = contribCount;
        document.getElementById('team-issues-contrib-pct').textContent = contribPct;
        
        // Closed issues
        const closedTotal = teamData.manually_closed + teamData.pr_triggered_closed;
        const closedPct = Math.round(teamData.closed_ratio * 100);
        document.getElementById('team-issues-closed-total').textContent = closedTotal;
        document.getElementById('team-issues-closed-pct').textContent = closedPct;
        document.getElementById('team-issues-closed-manual').textContent = teamData.manually_closed;
        document.getElementById('team-issues-closed-pr').textContent = teamData.pr_triggered_closed;
        
        // Render chart
        this.renderIssuesChart(total, teamCount, contribCount, closedTotal);
    }

    /**
     * Render PRs metrics
     */
    renderPRsMetrics(teamData, contribData) {
        const total = teamData.total_prs;
        
        // Total
        document.getElementById('team-prs-total').textContent = total;
        
        // Team engagement
        const teamCount = teamData.team_engaged;
        const teamPct = Math.round(teamData.engagement_ratio * 100);
        document.getElementById('team-prs-team-count').textContent = teamCount;
        document.getElementById('team-prs-team-pct').textContent = teamPct;
        
        // Contributors engagement
        const contribCount = contribData.team_engaged;
        const contribPct = Math.round(contribData.engagement_ratio * 100);
        document.getElementById('team-prs-contrib-count').textContent = contribCount;
        document.getElementById('team-prs-contrib-pct').textContent = contribPct;
        
        // Finished PRs
        const finishedTotal = teamData.merged + teamData.closed;
        const finishedPct = Math.round(teamData.finish_ratio * 100);
        document.getElementById('team-prs-finished-total').textContent = finishedTotal;
        document.getElementById('team-prs-finished-pct').textContent = finishedPct;
        document.getElementById('team-prs-merged').textContent = teamData.merged;
        document.getElementById('team-prs-closed').textContent = teamData.closed;
        
        // Render chart
        this.renderPRsChart(total, teamCount, contribCount, finishedTotal);
    }

    /**
     * Render issues chart
     */
    renderIssuesChart(total, teamEngaged, contribEngaged, closed) {
        const ctx = document.getElementById('issues-chart');
        
        // Destroy existing chart if it exists
        if (this.charts.issues) {
            this.charts.issues.destroy();
        }
        
        this.charts.issues = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Total', 'Team Engaged', 'Contributors Engaged', 'Closed'],
                datasets: [{
                    label: 'Issues',
                    data: [total, teamEngaged, contribEngaged, closed],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.7)',  // blue
                        'rgba(147, 51, 234, 0.7)',   // purple
                        'rgba(249, 115, 22, 0.7)',   // orange
                        'rgba(107, 114, 128, 0.7)'   // gray
                    ],
                    borderColor: [
                        'rgb(59, 130, 246)',
                        'rgb(147, 51, 234)',
                        'rgb(249, 115, 22)',
                        'rgb(107, 114, 128)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Issues Engagement Overview',
                        font: { size: 16, weight: 'bold' }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }

    /**
     * Render PRs chart
     */
    renderPRsChart(total, teamEngaged, contribEngaged, finished) {
        const ctx = document.getElementById('prs-chart');
        
        // Destroy existing chart if it exists
        if (this.charts.prs) {
            this.charts.prs.destroy();
        }
        
        this.charts.prs = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Total', 'Team Engaged', 'Contributors Engaged', 'Finished'],
                datasets: [{
                    label: 'Pull Requests',
                    data: [total, teamEngaged, contribEngaged, finished],
                    backgroundColor: [
                        'rgba(34, 197, 94, 0.7)',    // green
                        'rgba(147, 51, 234, 0.7)',   // purple
                        'rgba(249, 115, 22, 0.7)',   // orange
                        'rgba(107, 114, 128, 0.7)'   // gray
                    ],
                    borderColor: [
                        'rgb(34, 197, 94)',
                        'rgb(147, 51, 234)',
                        'rgb(249, 115, 22)',
                        'rgb(107, 114, 128)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Pull Requests Engagement Overview',
                        font: { size: 16, weight: 'bold' }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
}
