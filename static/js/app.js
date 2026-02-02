/**
 * Main Application Controller for GitHub Maintainer Activity Dashboard
 * 
 * This module initializes and manages the dashboard application.
 */

/**
 * Dashboard class - Main application controller
 */
class Dashboard {
    constructor() {
        this.apiClient = new APIClient();
        this.currentUser = null;
        this.currentDays = 7;
        this.selectionMode = 'quick'; // 'quick' or 'custom'
        this.customRange = { from: null, to: null }; // ISO date strings
        this.expandedSections = {};
        
        // Cache DOM elements
        this.elements = {
            searchForm: null,
            usernameInput: null,
            searchButton: null,
            buttonText: null,
            buttonSpinner: null,
            errorMessage: null,
            errorMessageText: null,
            dayButtons: null,
            resultsContainer: null,
            summaryCard: null,
            summaryLoading: null,
            summaryContent: null,
            summaryEmpty: null,
            totalActions: null,
            summaryDays: null,
            summaryUser: null,
            summaryTimestamp: null,
            countIssuesOpened: null,
            countPRsOpened: null,
            countIssueTriage: null,
            countCodeReviews: null,
            categoriesContainer: null
        };
    }

    /**
     * Initialize the dashboard
     */
    init() {
        console.log('Initializing GitHub Maintainer Activity Dashboard...');
        
        // Cache DOM elements
        this.cacheElements();
        
        // Initialize Flatpickr for date inputs
        this.initializeDatePickers();
        
        // Load saved state from localStorage
        this.loadState();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Set up category listeners (will activate after categories are rendered)
        this.setupCategoryListeners();
        
        // Check API health
        this.checkAPIHealth();
        
        console.log('Dashboard initialized successfully');
    }

    /**
     * Cache DOM elements for performance
     */
    cacheElements() {
        this.elements.searchForm = document.getElementById('search-form');
        this.elements.usernameInput = document.getElementById('username-input');
        this.elements.searchButton = document.getElementById('search-button');
        this.elements.buttonText = document.getElementById('button-text');
        this.elements.buttonSpinner = document.getElementById('button-spinner');
        this.elements.errorMessage = document.getElementById('error-message');
        this.elements.errorMessageText = document.getElementById('error-message-text');
        this.elements.dayButtons = document.querySelectorAll('.day-button');
        
        // Custom date picker elements
        this.elements.customButton = document.getElementById('custom-button');
        this.elements.customDatePicker = document.getElementById('custom-date-picker');
        this.elements.fromDateInput = document.getElementById('from-date');
        this.elements.toDateInput = document.getElementById('to-date');
        this.elements.dateRangeError = document.getElementById('date-range-error');
        
        // Results and summary card elements
        this.elements.resultsContainer = document.getElementById('results-container');
        this.elements.summaryCard = document.getElementById('summary-card');
        this.elements.summaryLoading = document.getElementById('summary-loading');
        this.elements.summaryContent = document.getElementById('summary-content');
        this.elements.summaryEmpty = document.getElementById('summary-empty');
        this.elements.totalActions = document.getElementById('total-actions');
        this.elements.summaryDays = document.getElementById('summary-days');
        this.elements.summaryDateRange = document.getElementById('summary-date-range');
        this.elements.summaryUser = document.getElementById('summary-user');
        this.elements.summaryTimestamp = document.getElementById('summary-timestamp');
        this.elements.countIssuesOpened = document.getElementById('count-issues-opened');
        this.elements.countPRsOpened = document.getElementById('count-prs-opened');
        this.elements.countIssueTriage = document.getElementById('count-issue-triage');
        this.elements.countCodeReviews = document.getElementById('count-code-reviews');
        this.elements.categoriesContainer = document.getElementById('categories-container');
    }

    /**
     * Initialize Flatpickr date pickers
     */
    initializeDatePickers() {
        if (typeof flatpickr === 'undefined') {
            console.warn('Flatpickr not loaded, falling back to native date inputs');
            return;
        }

        const today = new Date();
        // Set maxDate to today (allow selection up to and including today)
        const maxDate = new Date(today);

        // Initialize From Date picker
        this.fromDatePicker = flatpickr(this.elements.fromDateInput, {
            dateFormat: 'Y-m-d',
            maxDate: maxDate,
            onChange: () => {
                this.validateDateRange();
                this.updateCustomRangeIfValid();
            }
        });

        // Initialize To Date picker
        this.toDatePicker = flatpickr(this.elements.toDateInput, {
            dateFormat: 'Y-m-d',
            maxDate: maxDate,
            onChange: () => {
                this.validateDateRange();
                this.updateCustomRangeIfValid();
            }
        });

        console.log('Flatpickr date pickers initialized');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Search form submission
        if (this.elements.searchForm) {
            this.elements.searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSearchSubmit();
            });
        }
        
        // Day button clicks
        if (this.elements.dayButtons) {
            this.elements.dayButtons.forEach(button => {
                // Skip the custom button (it has its own handler)
                if (button.id === 'custom-button') {
                    return;
                }
                button.addEventListener('click', () => {
                    this.handleDayButtonClick(button);
                });
            });
        }
        
        // Custom button click
        if (this.elements.customButton) {
            this.elements.customButton.addEventListener('click', () => {
                this.handleCustomButtonClick();
            });
        }
        
        // Date input validation
        if (this.elements.fromDateInput) {
            this.elements.fromDateInput.addEventListener('change', () => {
                this.validateDateRange();
                this.updateCustomRangeIfValid();
            });
        }
        if (this.elements.toDateInput) {
            this.elements.toDateInput.addEventListener('change', () => {
                this.validateDateRange();
                this.updateCustomRangeIfValid();
            });
        }
        
        // Enter key in username input
        if (this.elements.usernameInput) {
            this.elements.usernameInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.handleSearchSubmit();
                }
            });
        }
        
        // Window resize handler for responsive behavior
        let resizeTimer;
        window.addEventListener('resize', () => {
            // Debounce resize events
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                // Force a reflow to ensure responsive styles are applied
                document.body.style.display = 'none';
                document.body.offsetHeight; // Trigger reflow
                document.body.style.display = '';
            }, 250);
        });
        
        console.log('Event listeners set up successfully');
    }

    /**
     * Set up event listeners for category sections
     */
    setupCategoryListeners() {
        const categoryHeaders = document.querySelectorAll('.category-header');
        
        categoryHeaders.forEach(header => {
            // Click event
            header.addEventListener('click', (e) => {
                this.toggleCategory(header);
            });
            
            // Keyboard support (Enter and Space)
            header.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleCategory(header);
                }
            });
        });
        
        // Set up sub-section listeners
        const subSectionHeaders = document.querySelectorAll('.sub-section-header');

        subSectionHeaders.forEach(header => {
            // Click event
            header.addEventListener('click', (e) => {
                this.toggleSubSection(header);
            });

            // Keyboard support (Enter and Space)
            header.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleSubSection(header);
                }
            });
        });

        console.log('Category and sub-section listeners set up successfully');
    }

    /**
     * Toggle category section expand/collapse
     * @param {HTMLElement} header - Category header element
     */
    toggleCategory(header) {
        const section = header.closest('.category-section');
        const content = section.querySelector('.category-content');
        const arrow = header.querySelector('.arrow-icon');
        const category = section.dataset.category;
        
        const isExpanded = header.getAttribute('aria-expanded') === 'true';
        
        if (isExpanded) {
            // Collapse
            content.style.maxHeight = '0';
            arrow.style.transform = 'rotate(0deg)';
            header.setAttribute('aria-expanded', 'false');
            this.expandedSections[category] = false;
        } else {
            // Expand
            content.style.maxHeight = content.scrollHeight + 'px';
            arrow.style.transform = 'rotate(90deg)';
            header.setAttribute('aria-expanded', 'true');
            this.expandedSections[category] = true;
        }
        
        this.saveState();
        console.log(`Toggled category: ${category}, expanded: ${!isExpanded}`);
    }

    /**
     * Toggle sub-section expand/collapse
     * @param {HTMLElement} header - Sub-section header element
     */
    toggleSubSection(header) {
        const subSection = header.closest('.sub-section');
        const content = subSection.querySelector('.sub-section-content');
        const arrow = header.querySelector('.sub-arrow-icon');

        const isExpanded = header.getAttribute('aria-expanded') === 'true';

        if (isExpanded) {
            // Collapse
            content.style.maxHeight = '0';
            arrow.style.transform = 'rotate(0deg)';
            header.setAttribute('aria-expanded', 'false');
        } else {
            // Expand
            content.style.maxHeight = content.scrollHeight + 'px';
            arrow.style.transform = 'rotate(90deg)';
            header.setAttribute('aria-expanded', 'true');
        }

        // Update parent category's max-height to accommodate the change
        const categorySection = subSection.closest('.category-section');
        if (categorySection) {
            const categoryContent = categorySection.querySelector('.category-content');
            const categoryHeader = categorySection.querySelector('.category-header');

            // Only update if the parent category is expanded
            if (categoryHeader && categoryHeader.getAttribute('aria-expanded') === 'true') {
                // Use setTimeout to allow the sub-section animation to complete
                setTimeout(() => {
                    categoryContent.style.maxHeight = categoryContent.scrollHeight + 'px';
                }, 350); // Match the CSS transition duration (300ms) plus buffer
            }
        }

        console.log(`Toggled sub-section, expanded: ${!isExpanded}`);
    }

    /**
     * Collapse all category sections
     */
    collapseAllCategories() {
        const categoryHeaders = document.querySelectorAll('.category-header');

        categoryHeaders.forEach(header => {
            const section = header.closest('.category-section');
            const content = section.querySelector('.category-content');
            const arrow = header.querySelector('.arrow-icon');
            const category = section.dataset.category;

            // Collapse
            content.style.maxHeight = '0';
            arrow.style.transform = 'rotate(0deg)';
            header.setAttribute('aria-expanded', 'false');
            this.expandedSections[category] = false;
        });

        console.log('All categories collapsed');
    }

    /**
     * Handle day button click
     * @param {HTMLElement} clickedButton - The clicked button element
     */
    handleDayButtonClick(clickedButton) {
        const days = parseInt(clickedButton.dataset.days);
        
        // Set quick select mode
        this.setQuickSelect(days);
        
        // Remove 'selected' class from all buttons
        this.elements.dayButtons.forEach(button => {
            button.classList.remove('selected', 'bg-blue-500', 'text-white');
            button.classList.add('border-gray-300');
        });
        
        clickedButton.classList.add('selected', 'bg-blue-500', 'text-white');
        clickedButton.classList.remove('border-gray-300');
        
        // Hide custom picker
        this.hideCustomDatePicker();
        
        // Deselect custom button
        if (this.elements.customButton) {
            this.elements.customButton.classList.remove('selected', 'bg-blue-500', 'text-white');
            this.elements.customButton.classList.add('border-gray-300');
        }
        
        console.log(`Selected ${days} days`);
    }

    /**
     * Handle search form submission
     */
    async handleSearchSubmit() {
        const username = this.elements.usernameInput.value.trim();
        
        // Validate input
        if (!username) {
            this.showError('Please enter a GitHub username');
            return;
        }
        
        // Clear previous error
        this.clearError();
        
        // Store current user
        this.currentUser = username;
        
        // Get current selection (days or custom range)
        const params = this.getCurrentSelection();
        
        // Load data with appropriate parameters
        if (params.days) {
            await this.loadData(username, params.days);
        } else if (params.from_date && params.to_date) {
            await this.loadDataWithDateRange(username, params.from_date, params.to_date);
        }
        
        // Save state
        this.saveState();
    }

    /**
     * Check API health status
     */
    async checkAPIHealth() {
        try {
            const health = await this.apiClient.checkHealth();
            console.log('API Health:', health);
        } catch (error) {
            console.error('API health check failed:', error);
        }
    }

    /**
     * Handle custom button click
     */
    handleCustomButtonClick() {
        // Toggle date picker visibility
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
        // Show date picker
        this.elements.customDatePicker.classList.remove('hidden');
        
        // Set default values to current date range (last 7 days to today)
        // Always refresh to ensure current dates are shown
        const today = new Date();
        const weekAgo = new Date(today);
        weekAgo.setDate(today.getDate() - 7);
        
        this.elements.fromDateInput.value = this.formatDateForInput(weekAgo);
        this.elements.toDateInput.value = this.formatDateForInput(today);
        
        // Mark custom button as selected
        this.updateCustomButtonSelection();
        
        // Deselect day buttons
        this.elements.dayButtons.forEach(btn => {
            btn.classList.remove('selected', 'bg-blue-500', 'text-white');
            btn.classList.add('border-gray-300');
        });
        
        // Clear any previous errors
        this.hideDateRangeError();
        
        // Update custom range state with the default dates
        this.updateCustomRangeIfValid();
        
        console.log('Custom date picker shown');
    }

    /**
     * Hide custom date picker
     */
    hideCustomDatePicker() {
        this.elements.customDatePicker.classList.add('hidden');
        this.hideDateRangeError();
        console.log('Custom date picker hidden');
    }

    /**
     * Handle apply custom range
     */
    /**
     * Update custom range if dates are valid
     */
    updateCustomRangeIfValid() {
        const fromDate = this.elements.fromDateInput.value;
        const toDate = this.elements.toDateInput.value;
        
        // Only update if both dates are valid
        if (fromDate && toDate && this.validateCustomRange(fromDate, toDate)) {
            // Set custom range
            this.setCustomRange(fromDate, toDate);
            
            console.log(`Updated custom range: ${fromDate} to ${toDate}`);
        }
    }

    /**
     * Validate custom date range
     * @param {string} fromDate - From date (YYYY-MM-DD)
     * @param {string} toDate - To date (YYYY-MM-DD)
     * @returns {boolean} True if valid
     */
    validateCustomRange(fromDate, toDate) {
        // Check if both dates are provided
        if (!fromDate || !toDate) {
            this.showDateRangeError('Please select both from and to dates');
            return false;
        }
        
        // Parse dates
        const from = new Date(fromDate);
        const to = new Date(toDate);
        const today = new Date();
        today.setHours(23, 59, 59, 999);
        
        // Check if from < to
        if (from >= to) {
            this.showDateRangeError('From date must be before to date');
            return false;
        }
        
        // Check if dates are in the future
        if (to > today) {
            this.showDateRangeError('Cannot select future dates');
            return false;
        }
        
        // Check max range (200 days)
        const daysDiff = Math.ceil((to - from) / (1000 * 60 * 60 * 24));
        if (daysDiff > 200) {
            this.showDateRangeError('Date range cannot exceed 200 days');
            return false;
        }
        
        this.hideDateRangeError();
        return true;
    }

    /**
     * Validate date range (called on input change)
     */
    validateDateRange() {
        const fromDate = this.elements.fromDateInput.value;
        const toDate = this.elements.toDateInput.value;
        
        // Only validate if both dates are entered
        if (fromDate && toDate) {
            this.validateCustomRange(fromDate, toDate);
        }
    }

    /**
     * Show date range error
     * @param {string} message - Error message
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
     * Update custom button selection state
     */
    updateCustomButtonSelection() {
        this.elements.customButton.classList.add('selected', 'bg-blue-500', 'text-white');
        this.elements.customButton.classList.remove('border-gray-300');
    }

    /**
     * Format date range for display
     * @param {string} fromDate - From date (YYYY-MM-DD)
     * @param {string} toDate - To date (YYYY-MM-DD)
     * @returns {string} Formatted date range
     */
    formatDateRange(fromDate, toDate) {
        const from = new Date(fromDate);
        const to = new Date(toDate);
        
        const options = { month: 'short', day: 'numeric', year: 'numeric' };
        return `${from.toLocaleDateString('en-US', options)} - ${to.toLocaleDateString('en-US', options)}`;
    }

    /**
     * Format date for input (YYYY-MM-DD)
     * Uses local timezone to avoid UTC conversion issues
     * @param {Date} date - Date object
     * @returns {string} Formatted date string
     */
    formatDateForInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    /**
     * Load data for a user with date range
     * @param {string} user - GitHub username
     * @param {string} fromDate - From date (YYYY-MM-DD)
     * @param {string} toDate - To date (YYYY-MM-DD)
     */
    async loadDataWithDateRange(user, fromDate, toDate) {
        console.log(`Loading data for ${user} (${fromDate} to ${toDate})...`);
        
        try {
            this.showLoading();
            this.showSummaryLoading();
            
            // Collapse all categories immediately before loading new data
            this.collapseAllCategories();

            const data = await this.apiClient.fetchMetrics(user, { from_date: fromDate, to_date: toDate });
            
            console.log('Data loaded successfully:', data);
            
            // Update state
            this.currentUser = user;
            this.saveState();
            
            // Render data
            this.updateSummary(data);
            this.renderCategories(data);
            
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.hideLoading();
            this.showError(error.message);
        }
    }

    /**
     * Load data for a user
     * @param {string} user - GitHub username
     * @param {number} days - Number of days
     */
    async loadData(user, days) {
        console.log(`Loading data for ${user} (${days} days)...`);
        
        try {
            this.showLoading();
            this.showSummaryLoading();
            
            // Collapse all categories immediately before loading new data
            this.collapseAllCategories();

            const data = await this.apiClient.fetchMetrics(user, days);
            
            console.log('Data loaded successfully:', data);
            
            // Update state
            this.currentUser = user;
            this.currentDays = days;
            this.saveState();
            
            // Render data
            this.updateSummary(data);
            this.renderCategories(data);
            
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.hideLoading();
            this.showError(error.message);
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        if (this.elements.searchButton) {
            this.elements.searchButton.disabled = true;
        }
        if (this.elements.buttonText) {
            this.elements.buttonText.textContent = 'Loading...';
        }
        if (this.elements.buttonSpinner) {
            this.elements.buttonSpinner.classList.remove('hidden');
        }
        console.log('Showing loading state...');
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        if (this.elements.searchButton) {
            this.elements.searchButton.disabled = false;
        }
        if (this.elements.buttonText) {
            this.elements.buttonText.textContent = 'Go';
        }
        if (this.elements.buttonSpinner) {
            this.elements.buttonSpinner.classList.add('hidden');
        }
        console.log('Hiding loading state...');
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        if (this.elements.errorMessage) {
            this.elements.errorMessage.classList.remove('hidden');
        }
        if (this.elements.errorMessageText) {
            this.elements.errorMessageText.textContent = message;
        }
        console.error('Error:', message);
    }

    /**
     * Clear error message
     */
    clearError() {
        if (this.elements.errorMessage) {
            this.elements.errorMessage.classList.add('hidden');
        }
        console.log('Clearing error...');
    }

    /**
     * Update summary card with data
     * @param {Object} data - API response data
     */
    updateSummary(data) {
        console.log('Updating summary card...');
        
        // Show results container
        if (this.elements.resultsContainer) {
            this.elements.resultsContainer.classList.remove('hidden');
        }
        
        // Check if data is empty
        const totalActions = data.summary?.total_actions || 0;
        
        if (totalActions === 0) {
            // Show empty state
            this.showEmptySummary();
            return;
        }
        
        // Show summary content, hide loading and empty states
        if (this.elements.summaryLoading) {
            this.elements.summaryLoading.classList.add('hidden');
        }
        if (this.elements.summaryEmpty) {
            this.elements.summaryEmpty.classList.add('hidden');
        }
        if (this.elements.summaryContent) {
            this.elements.summaryContent.classList.remove('hidden');
        }
        
        // Update total actions
        if (this.elements.totalActions) {
            this.elements.totalActions.textContent = totalActions;
        }
        
        // Update days and date range
        if (this.elements.summaryDays) {
            this.elements.summaryDays.textContent = data.meta?.period?.days || this.currentDays;
        }
        
        // Update date range display
        if (this.elements.summaryDateRange) {
            const startDate = data.meta?.period?.start;
            const endDate = data.meta?.period?.end;
            if (startDate && endDate) {
                // Extract YYYY-MM-DD from ISO datetime strings
                const from = startDate.split('T')[0];
                const to = endDate.split('T')[0];
                this.elements.summaryDateRange.textContent = ` (${from} to ${to})`;
            } else {
                this.elements.summaryDateRange.textContent = '';
            }
        }
        
        // Update user
        if (this.elements.summaryUser) {
            this.elements.summaryUser.textContent = data.meta?.user || this.currentUser;
        }
        
        // Update timestamp
        if (this.elements.summaryTimestamp) {
            const timestamp = data.meta?.fetched_at;
            if (timestamp) {
                this.elements.summaryTimestamp.textContent = formatTimestamp(timestamp);
            }
        }
        
        // Update category counts
        const byCategory = data.summary?.by_category || {};
        
        if (this.elements.countIssuesOpened) {
            this.elements.countIssuesOpened.textContent = byCategory.issues_opened || 0;
        }
        
        if (this.elements.countPRsOpened) {
            this.elements.countPRsOpened.textContent = byCategory.prs_opened || 0;
        }
        
        if (this.elements.countIssueTriage) {
            this.elements.countIssueTriage.textContent = byCategory.issue_triage || 0;
        }
        
        if (this.elements.countCodeReviews) {
            this.elements.countCodeReviews.textContent = byCategory.code_reviews || 0;
        }
        
        console.log('Summary card updated successfully');
    }

    /**
     * Render category sections with data
     * @param {Object} data - API response data
     */
    renderCategories(data) {
        console.log('Rendering categories...');
        
        // Show categories container
        if (this.elements.categoriesContainer) {
            this.elements.categoriesContainer.classList.remove('hidden');
        }
        
        // Get category data
        const categories = data.data || {};
        
        // Render each category
        this.renderCategory('issues_opened', categories.issues_opened || []);
        this.renderCategory('prs_opened', categories.prs_opened || []);
        this.renderCategoryWithSubsections('issue_triage', categories.issue_triage || {});
        this.renderCategoryWithSubsections('code_reviews', categories.code_reviews || {});
        
        // Restore expanded state
        this.restoreExpandedState();
        
        console.log('Categories rendered successfully');
    }

    /**
     * Render a simple category (Issues Opened, PRs Opened)
     * @param {string} categoryName - Category name
     * @param {Array} items - Array of items
     */
    renderCategory(categoryName, items) {
        const section = document.querySelector(`[data-category="${categoryName}"]`);
        if (!section) return;
        
        const countBadge = section.querySelector('.count-badge');
        const itemsContainer = section.querySelector('.items-container');
        
        // Update count
        if (countBadge) {
            countBadge.textContent = items.length;
        }
        
        // Render items
        if (itemsContainer) {
            if (items.length === 0) {
                itemsContainer.innerHTML = '<p class="text-gray-500 text-sm">No items to display</p>';
            } else {
                itemsContainer.innerHTML = items.map(item => this.createItemCard(item, categoryName)).join('');
            }
        }
    }

    /**
     * Render a category with sub-sections (Issue Triage, Code Reviews)
     * @param {string} categoryName - Category name
     * @param {Object} subsections - Object with sub-section data
     */
    renderCategoryWithSubsections(categoryName, subsections) {
        const section = document.querySelector(`[data-category="${categoryName}"]`);
        if (!section) return;
        
        const countBadge = section.querySelector('.count-badge');
        
        // Calculate total count
        let totalCount = 0;
        Object.values(subsections).forEach(items => {
            if (Array.isArray(items)) {
                totalCount += items.length;
            }
        });
        
        // Update count
        if (countBadge) {
            countBadge.textContent = totalCount;
        }
        
        // Render each sub-section
        Object.keys(subsections).forEach(subsectionName => {
            const items = subsections[subsectionName] || [];
            this.renderSubsection(section, subsectionName, items);
        });
    }

    /**
     * Render a sub-section within a category
     * @param {HTMLElement} section - Parent category section
     * @param {string} subsectionName - Sub-section name
     * @param {Array} items - Array of items
     */
    renderSubsection(section, subsectionName, items) {
        const subsection = section.querySelector(`[data-subsection="${subsectionName}"]`);
        if (!subsection) return;
        
        const countBadge = subsection.querySelector('.sub-count-badge');
        const itemsContainer = subsection.querySelector('.items-container');
        
        // Update count
        if (countBadge) {
            countBadge.textContent = items.length;
        }
        
        // Render items
        if (itemsContainer) {
            if (items.length === 0) {
                itemsContainer.innerHTML = '<p class="text-gray-500 text-sm">No items to display</p>';
            } else {
                itemsContainer.innerHTML = items.map(item => this.createItemCard(item, subsectionName)).join('');
            }
        }
    }

    /**
     * Create an item card HTML
     * @param {Object} item - Item data
     * @param {string} context - Context (category or subsection name)
     * @returns {string} HTML string for item card
     */
    createItemCard(item, context) {
        const timestamp = item.created_at || item.timestamp || item.updated_at;
        const title = item.title || 'No title';
        const number = item.number || item.id || 'N/A';
        const url = item.url || '#';
        
        // Build labels HTML if labels exist
        let labelsHtml = '';
        if (item.labels && Array.isArray(item.labels) && item.labels.length > 0) {
            labelsHtml = `
                <div class="flex flex-wrap gap-1 mt-2">
                    ${item.labels.slice(0, 5).map(label => {
                        const labelName = typeof label === 'string' ? label : (label.name || '');
                        const labelColor = typeof label === 'object' ? label.color : null;
                        return this.createLabelBadge(labelName, labelColor);
                    }).join('')}
                    ${item.labels.length > 5 ? `<span class="text-xs text-gray-500">+${item.labels.length - 5} more</span>` : ''}
                </div>
            `;
        }

        // Build review state badge if applicable (for reviews)
        let reviewStateBadge = '';
        if (item.state && (context === 'reviews' || item.type === 'review')) {
            reviewStateBadge = this.createReviewStateBadge(item.state);
        }

        // Build PR state badge if applicable (for PRs opened)
        let prStateBadge = '';
        if (item.state && context === 'prs_opened') {
            prStateBadge = this.createPRStateBadge(item.state);
        }

        // Build label badge if applicable (for labeled items)
        let labelBadge = '';
        if (item.label && context === 'labeled') {
            labelBadge = this.createLabelBadge(item.label, null);
        }

        // Build action badge if applicable
        let actionBadge = '';
        if (item.action && item.action !== 'opened') {
            actionBadge = this.createActionBadge(item.action);
        }

        return `
            <div class="item-card bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-all duration-200">
                <div class="flex items-start justify-between gap-3">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 flex-wrap">
                            <a href="${escapeHtml(url)}" 
                               target="_blank" 
                               rel="noopener noreferrer" 
                               class="text-blue-600 hover:text-blue-800 hover:underline font-semibold text-sm inline-flex items-center">
                                #${escapeHtml(number.toString())}
                                <svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                                </svg>
                            </a>
                            ${reviewStateBadge}
                            ${prStateBadge}
                            ${labelBadge}
                            ${actionBadge}
                        </div>
                        <p class="text-gray-800 mt-1 text-sm leading-relaxed">${escapeHtml(title)}</p>
                        ${labelsHtml}
                    </div>
                </div>
                <div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                    <span class="text-xs text-gray-500">${formatRelativeTime(timestamp)}</span>
                </div>
            </div>
        `;
    }

    /**
     * Create a label badge HTML
     * @param {string} name - Label name
     * @param {string} color - Label color (hex without #)
     * @returns {string} HTML string for label badge
     */
    createLabelBadge(name, color) {
        // Default to gray if no color provided
        const bgColor = color ? `#${color}` : '#6B7280';
        const textColor = this.getContrastColor(bgColor);
        
        return `
            <span class="label-badge inline-flex items-center px-2 py-0.5 rounded text-xs font-medium" 
                  style="background-color: ${bgColor}; color: ${textColor};">
                ${escapeHtml(name)}
            </span>
        `;
    }

    /**
     * Create a review state badge HTML
     * @param {string} state - Review state (APPROVED, CHANGES_REQUESTED, COMMENTED, etc.)
     * @returns {string} HTML string for review state badge
     */
    createReviewStateBadge(state) {
        const stateMap = {
            'APPROVED': { text: 'Approved', class: 'bg-green-100 text-green-800', icon: '✓' },
            'CHANGES_REQUESTED': { text: 'Changes Requested', class: 'bg-red-100 text-red-800', icon: '✗' },
            'COMMENTED': { text: 'Commented', class: 'bg-blue-100 text-blue-800', icon: '💬' },
            'DISMISSED': { text: 'Dismissed', class: 'bg-gray-100 text-gray-800', icon: '−' },
            'PENDING': { text: 'Pending', class: 'bg-yellow-100 text-yellow-800', icon: '○' }
        };
        
        const stateInfo = stateMap[state] || { text: state, class: 'bg-gray-100 text-gray-800', icon: '' };
        
        return `
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${stateInfo.class}">
                <span class="mr-1">${stateInfo.icon}</span>
                ${escapeHtml(stateInfo.text)}
            </span>
        `;
    }

    /**
     * Create an action badge HTML
     * @param {string} action - Action type (merged, closed, labeled, etc.)
     * @returns {string} HTML string for action badge
     */
    createActionBadge(action) {
        const actionMap = {
            'merged': { text: 'Merged', class: 'bg-purple-100 text-purple-800' },
            'closed': { text: 'Closed', class: 'bg-red-100 text-red-800' },
            'labeled': { text: 'Labeled', class: 'bg-blue-100 text-blue-800' },
            'reopened': { text: 'Reopened', class: 'bg-yellow-100 text-yellow-800' }
        };
        
        const actionInfo = actionMap[action] || { text: action, class: 'bg-gray-100 text-gray-800' };
        
        return `
            <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium ${actionInfo.class}">
                ${escapeHtml(actionInfo.text)}
            </span>
        `;
    }

    /**
     * Create a PR state badge HTML
     * @param {string} state - PR state (OPEN, CLOSED, MERGED)
     * @returns {string} HTML string for PR state badge
     */
    createPRStateBadge(state) {
        const stateMap = {
            'OPEN': { text: 'Open', class: 'bg-green-100 text-green-800', icon: '●' },
            'CLOSED': { text: 'Closed', class: 'bg-red-100 text-red-800', icon: '✗' },
            'MERGED': { text: 'Merged', class: 'bg-purple-100 text-purple-800', icon: '✓' }
        };

        const stateInfo = stateMap[state] || { text: state, class: 'bg-gray-100 text-gray-800', icon: '○' };

        return `
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${stateInfo.class}">
                <span class="mr-1">${stateInfo.icon}</span>
                ${escapeHtml(stateInfo.text)}
            </span>
        `;
    }

    /**
     * Get contrasting text color (black or white) for a background color
     * @param {string} hexColor - Hex color code
     * @returns {string} 'black' or 'white'
     */
    getContrastColor(hexColor) {
        // Remove # if present
        const hex = hexColor.replace('#', '');
        
        // Convert to RGB
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        
        // Calculate luminance
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        
        // Return black for light backgrounds, white for dark backgrounds
        return luminance > 0.5 ? '#000000' : '#FFFFFF';
    }

    /**
     * Restore expanded state of categories from saved state
     */
    restoreExpandedState() {
        Object.keys(this.expandedSections).forEach(category => {
            if (this.expandedSections[category]) {
                const section = document.querySelector(`[data-category="${category}"]`);
                if (section) {
                    const header = section.querySelector('.category-header');
                    const content = section.querySelector('.category-content');
                    const arrow = header.querySelector('.arrow-icon');
                    
                    content.style.maxHeight = content.scrollHeight + 'px';
                    arrow.style.transform = 'rotate(90deg)';
                    header.setAttribute('aria-expanded', 'true');
                }
            }
        });
        
        console.log('Restored expanded state');
    }

    /**
     * Show empty summary state
     */
    showEmptySummary() {
        console.log('Showing empty summary state...');
        
        // Hide loading and content, show empty state
        if (this.elements.summaryLoading) {
            this.elements.summaryLoading.classList.add('hidden');
        }
        if (this.elements.summaryContent) {
            this.elements.summaryContent.classList.add('hidden');
        }
        if (this.elements.summaryEmpty) {
            this.elements.summaryEmpty.classList.remove('hidden');
        }
    }

    /**
     * Show summary loading state
     */
    showSummaryLoading() {
        console.log('Showing summary loading state...');
        
        // Show results container
        if (this.elements.resultsContainer) {
            this.elements.resultsContainer.classList.remove('hidden');
        }
        
        // Show loading, hide content and empty states
        if (this.elements.summaryLoading) {
            this.elements.summaryLoading.classList.remove('hidden');
        }
        if (this.elements.summaryContent) {
            this.elements.summaryContent.classList.add('hidden');
        }
        if (this.elements.summaryEmpty) {
            this.elements.summaryEmpty.classList.add('hidden');
        }
    }

    /**
     * Save state to localStorage
     */
    saveState() {
        try {
            const state = {
                currentUser: this.currentUser,
                currentDays: this.currentDays,
                selectionMode: this.selectionMode,
                customRange: this.customRange,
                expandedSections: this.expandedSections
            };
            localStorage.setItem('dashboardState', JSON.stringify(state));
            console.log('State saved to localStorage');
        } catch (error) {
            console.error('Failed to save state:', error);
        }
    }

    /**
     * Load state from localStorage
     */
    loadState() {
        try {
            const savedState = localStorage.getItem('dashboardState');
            if (savedState) {
                const state = JSON.parse(savedState);
                this.currentUser = state.currentUser || null;
                this.currentDays = state.currentDays || 7;
                this.selectionMode = state.selectionMode || 'quick';
                this.customRange = state.customRange || { from: null, to: null };
                this.expandedSections = state.expandedSections || {};
                
                // Restore UI state
                this.restoreUIState();
                
                console.log('State loaded from localStorage');
            }
        } catch (error) {
            console.error('Failed to load state:', error);
        }
    }

    /**
     * Restore UI state from loaded state
     */
    restoreUIState() {
        // Restore username
        if (this.currentUser && this.elements.usernameInput) {
            this.elements.usernameInput.value = this.currentUser;
        }
        
        // Restore day selection or custom range
        if (this.selectionMode === 'quick') {
            this.updateDayButtonSelection(this.currentDays);
        } else if (this.selectionMode === 'custom' && this.customRange.from && this.customRange.to) {
            // Will implement custom UI restoration in Task 4
            console.log('Custom range mode restored:', this.customRange);
        }
    }

    /**
     * Update day button selection
     * @param {number} days - Number of days to select
     */
    updateDayButtonSelection(days) {
        if (this.elements.dayButtons) {
            this.elements.dayButtons.forEach(btn => {
                const btnDays = parseInt(btn.dataset.days, 10);
                if (btnDays === days) {
                    btn.classList.add('selected', 'bg-blue-500', 'text-white');
                    btn.classList.remove('border-gray-300', 'hover:bg-gray-50');
                } else {
                    btn.classList.remove('selected', 'bg-blue-500', 'text-white');
                    btn.classList.add('border-gray-300', 'hover:bg-gray-50');
                }
            });
        }
    }

    /**
     * Set quick select mode
     * @param {number} days - Number of days
     */
    setQuickSelect(days) {
        this.selectionMode = 'quick';
        this.currentDays = days;
        this.customRange = { from: null, to: null };
        this.saveState();
        console.log(`Set quick select mode: ${days} days`);
    }

    /**
     * Set custom range mode
     * @param {string} fromDate - From date (YYYY-MM-DD)
     * @param {string} toDate - To date (YYYY-MM-DD)
     */
    setCustomRange(fromDate, toDate) {
        this.selectionMode = 'custom';
        this.customRange = { from: fromDate, to: toDate };
        this.currentDays = null;
        this.saveState();
        console.log(`Set custom range mode: ${fromDate} to ${toDate}`);
    }

    /**
     * Get current selection as API parameters
     * @returns {Object} Either {days: number} or {from_date: string, to_date: string}
     */
    getCurrentSelection() {
        if (this.selectionMode === 'custom' && this.customRange.from && this.customRange.to) {
            return {
                from_date: this.customRange.from,
                to_date: this.customRange.to
            };
        } else {
            return {
                days: this.currentDays || 7
            };
        }
    }
}

/**
 * Initialize the dashboard when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new Dashboard();
    dashboard.init();
    
    // Make dashboard available globally for debugging
    window.dashboard = dashboard;
});

