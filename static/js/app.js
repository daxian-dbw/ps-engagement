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
        
        // Results and summary card elements
        this.elements.resultsContainer = document.getElementById('results-container');
        this.elements.summaryCard = document.getElementById('summary-card');
        this.elements.summaryLoading = document.getElementById('summary-loading');
        this.elements.summaryContent = document.getElementById('summary-content');
        this.elements.summaryEmpty = document.getElementById('summary-empty');
        this.elements.totalActions = document.getElementById('total-actions');
        this.elements.summaryDays = document.getElementById('summary-days');
        this.elements.summaryUser = document.getElementById('summary-user');
        this.elements.summaryTimestamp = document.getElementById('summary-timestamp');
        this.elements.countIssuesOpened = document.getElementById('count-issues-opened');
        this.elements.countPRsOpened = document.getElementById('count-prs-opened');
        this.elements.countIssueTriage = document.getElementById('count-issue-triage');
        this.elements.countCodeReviews = document.getElementById('count-code-reviews');
        this.elements.categoriesContainer = document.getElementById('categories-container');
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
                button.addEventListener('click', () => {
                    this.handleDayButtonClick(button);
                });
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
     */
    handleDayButtonClick(clickedButton) {
        // Update selected state
        this.elements.dayButtons.forEach(btn => {
            btn.classList.remove('selected', 'bg-blue-500', 'text-white');
            btn.classList.add('border-gray-300');
        });
        
        clickedButton.classList.add('selected', 'bg-blue-500', 'text-white');
        clickedButton.classList.remove('border-gray-300');
        
        // Update current days
        this.currentDays = parseInt(clickedButton.dataset.days);
        
        console.log(`Selected ${this.currentDays} days`);
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
        
        // Load data
        await this.loadData(username, this.currentDays);
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
        
        // Update days
        if (this.elements.summaryDays) {
            this.elements.summaryDays.textContent = data.meta?.period?.days || this.currentDays;
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
                this.currentUser = state.currentUser;
                this.currentDays = state.currentDays || 7;
                this.expandedSections = state.expandedSections || {};
                
                // Restore UI state
                if (this.currentUser && this.elements.usernameInput) {
                    this.elements.usernameInput.value = this.currentUser;
                }
                
                // Restore selected day button
                if (this.elements.dayButtons) {
                    this.elements.dayButtons.forEach(btn => {
                        if (parseInt(btn.dataset.days) === this.currentDays) {
                            this.handleDayButtonClick(btn);
                        }
                    });
                }
                
                console.log('State loaded from localStorage');
            }
        } catch (error) {
            console.error('Failed to load state:', error);
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

