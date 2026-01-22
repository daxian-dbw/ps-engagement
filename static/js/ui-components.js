/**
 * UI Components for GitHub Maintainer Activity Dashboard
 * 
 * This module provides reusable UI components and helper functions.
 */

/**
 * Helper Functions
 */

/**
 * Format timestamp to relative time (e.g., "2 days ago")
 * @param {string} timestamp - ISO 8601 timestamp
 * @returns {string} Relative time string
 */
function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Unknown';

    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} day${days !== 1 ? 's' : ''} ago`;
    
    const weeks = Math.floor(days / 7);
    if (weeks < 4) return `${weeks} week${weeks !== 1 ? 's' : ''} ago`;
    
    const months = Math.floor(days / 30);
    return `${months} month${months !== 1 ? 's' : ''} ago`;
}

/**
 * Format timestamp to readable date/time
 * @param {string} timestamp - ISO 8601 timestamp
 * @returns {string} Formatted date string
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength = 100) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
}

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * UI Component Classes
 */

/**
 * CollapsibleSection component
 */
class CollapsibleSection {
    constructor(data, options = {}) {
        this.data = data;
        this.title = data.title || 'Section';
        this.emoji = data.emoji || '';
        this.count = data.count || 0;
        this.items = data.items || [];
        this.isExpanded = options.isExpanded || false;
        this.onToggle = options.onToggle || null;
        this.categoryName = data.categoryName || '';
    }

    /**
     * Toggle expand/collapse state
     */
    toggle() {
        this.isExpanded = !this.isExpanded;
        if (this.onToggle) {
            this.onToggle(this.isExpanded);
        }
    }

    /**
     * Render the component
     * @returns {HTMLElement} DOM element
     */
    render() {
        const section = document.createElement('div');
        section.className = 'category-section bg-white rounded-lg shadow-md overflow-hidden';
        section.dataset.category = this.categoryName;
        
        // Create header
        const header = document.createElement('div');
        header.className = 'category-header cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors duration-200 p-4 flex items-center justify-between';
        header.setAttribute('tabindex', '0');
        header.setAttribute('role', 'button');
        header.setAttribute('aria-expanded', this.isExpanded.toString());
        
        // Header content
        const headerContent = document.createElement('div');
        headerContent.className = 'flex items-center space-x-3';
        
        if (this.emoji) {
            const emojiSpan = document.createElement('span');
            emojiSpan.className = 'text-2xl';
            emojiSpan.textContent = this.emoji;
            headerContent.appendChild(emojiSpan);
        }
        
        const titleHeading = document.createElement('h3');
        titleHeading.className = 'text-lg font-semibold text-gray-800';
        titleHeading.textContent = this.title;
        headerContent.appendChild(titleHeading);
        
        const countBadge = document.createElement('span');
        countBadge.className = 'count-badge inline-flex items-center justify-center px-3 py-1 text-sm font-bold leading-none text-blue-800 bg-blue-200 rounded-full';
        countBadge.textContent = this.count.toString();
        headerContent.appendChild(countBadge);
        
        header.appendChild(headerContent);
        
        // Arrow icon
        const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        arrow.setAttribute('class', 'arrow-icon w-6 h-6 text-gray-600 transform transition-transform duration-300');
        arrow.setAttribute('fill', 'none');
        arrow.setAttribute('stroke', 'currentColor');
        arrow.setAttribute('viewBox', '0 0 24 24');
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('d', 'M9 5l7 7-7 7');
        arrow.appendChild(path);
        
        if (this.isExpanded) {
            arrow.style.transform = 'rotate(90deg)';
        }
        
        header.appendChild(arrow);
        
        // Click handler
        header.addEventListener('click', () => {
            this.toggle();
            const content = section.querySelector('.category-content');
            if (this.isExpanded) {
                content.style.maxHeight = content.scrollHeight + 'px';
                arrow.style.transform = 'rotate(90deg)';
                header.setAttribute('aria-expanded', 'true');
            } else {
                content.style.maxHeight = '0';
                arrow.style.transform = 'rotate(0deg)';
                header.setAttribute('aria-expanded', 'false');
            }
        });
        
        section.appendChild(header);
        
        // Create content area
        const content = document.createElement('div');
        content.className = 'category-content collapsible-content max-h-0 overflow-hidden transition-all duration-300 ease-in-out';
        
        const contentInner = document.createElement('div');
        contentInner.className = 'p-4 bg-gray-50';
        
        const itemsContainer = document.createElement('div');
        itemsContainer.className = 'items-container space-y-3';
        
        if (this.items.length === 0) {
            const emptyMessage = document.createElement('p');
            emptyMessage.className = 'text-gray-500 text-sm';
            emptyMessage.textContent = 'No items to display';
            itemsContainer.appendChild(emptyMessage);
        } else {
            this.items.forEach(item => {
                const itemCard = new ItemCard(item, this.categoryName);
                itemsContainer.appendChild(itemCard.render());
            });
        }
        
        contentInner.appendChild(itemsContainer);
        content.appendChild(contentInner);
        
        if (this.isExpanded) {
            content.style.maxHeight = content.scrollHeight + 'px';
        }
        
        section.appendChild(content);
        
        return section;
    }
}

/**
 * ItemCard component
 */
class ItemCard {
    constructor(item, type = 'default') {
        this.item = item;
        this.type = type;
    }

    /**
     * Render the component
     * @returns {HTMLElement} DOM element
     */
    render() {
        const card = document.createElement('div');
        card.className = 'item-card bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-all duration-200';
        
        // Main container
        const mainContainer = document.createElement('div');
        mainContainer.className = 'flex items-start justify-between gap-3';
        
        // Content container
        const contentContainer = document.createElement('div');
        contentContainer.className = 'flex-1 min-w-0';
        
        // Top row with link and badges
        const topRow = document.createElement('div');
        topRow.className = 'flex items-center gap-2 flex-wrap';
        
        // Create link
        const link = document.createElement('a');
        link.href = this.item.url || '#';
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.className = 'text-blue-600 hover:text-blue-800 hover:underline font-semibold text-sm inline-flex items-center';
        
        const number = this.item.number || this.item.id || 'N/A';
        link.textContent = `#${number}`;
        
        // Add external link icon
        const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        icon.setAttribute('class', 'w-3 h-3 ml-1');
        icon.setAttribute('fill', 'none');
        icon.setAttribute('stroke', 'currentColor');
        icon.setAttribute('viewBox', '0 0 24 24');
        
        const iconPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        iconPath.setAttribute('stroke-linecap', 'round');
        iconPath.setAttribute('stroke-linejoin', 'round');
        iconPath.setAttribute('stroke-width', '2');
        iconPath.setAttribute('d', 'M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14');
        icon.appendChild(iconPath);
        link.appendChild(icon);
        
        topRow.appendChild(link);
        
        // Add review state badge if applicable
        if (this.item.state && (this.type === 'reviews' || this.item.type === 'review')) {
            const stateBadge = this.createReviewStateBadge(this.item.state);
            topRow.appendChild(stateBadge);
        }
        
        // Add action badge if applicable
        if (this.item.action && this.item.action !== 'opened') {
            const actionBadge = this.createActionBadge(this.item.action);
            topRow.appendChild(actionBadge);
        }
        
        contentContainer.appendChild(topRow);
        
        // Title
        const title = document.createElement('p');
        title.className = 'text-gray-800 mt-1 text-sm leading-relaxed';
        const titleText = this.item.title || 'No title';
        title.textContent = truncateText(titleText, 80);
        contentContainer.appendChild(title);
        
        // Labels
        if (this.item.labels && Array.isArray(this.item.labels) && this.item.labels.length > 0) {
            const labelsContainer = document.createElement('div');
            labelsContainer.className = 'flex flex-wrap gap-1 mt-2';
            
            this.item.labels.slice(0, 5).forEach(label => {
                const labelName = typeof label === 'string' ? label : (label.name || '');
                const labelColor = typeof label === 'object' ? label.color : null;
                const labelBadge = this.createLabelBadge(labelName, labelColor);
                labelsContainer.appendChild(labelBadge);
            });
            
            if (this.item.labels.length > 5) {
                const moreSpan = document.createElement('span');
                moreSpan.className = 'text-xs text-gray-500';
                moreSpan.textContent = `+${this.item.labels.length - 5} more`;
                labelsContainer.appendChild(moreSpan);
            }
            
            contentContainer.appendChild(labelsContainer);
        }
        
        mainContainer.appendChild(contentContainer);
        card.appendChild(mainContainer);
        
        // Footer with timestamp
        const footer = document.createElement('div');
        footer.className = 'flex items-center justify-between mt-3 pt-3 border-t border-gray-100';
        
        const timestamp = document.createElement('span');
        timestamp.className = 'text-xs text-gray-500';
        const time = this.item.created_at || this.item.timestamp || this.item.updated_at;
        timestamp.textContent = formatRelativeTime(time);
        footer.appendChild(timestamp);
        
        card.appendChild(footer);
        
        return card;
    }
    
    /**
     * Create a label badge
     * @private
     */
    createLabelBadge(name, color) {
        const badge = document.createElement('span');
        badge.className = 'label-badge inline-flex items-center px-2 py-0.5 rounded text-xs font-medium';
        
        const bgColor = color ? `#${color}` : '#6B7280';
        const textColor = this.getContrastColor(bgColor);
        
        badge.style.backgroundColor = bgColor;
        badge.style.color = textColor;
        badge.style.border = '1px solid rgba(0, 0, 0, 0.1)';
        badge.textContent = name;
        
        return badge;
    }
    
    /**
     * Create a review state badge
     * @private
     */
    createReviewStateBadge(state) {
        const badge = document.createElement('span');
        badge.className = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium';
        
        const stateMap = {
            'APPROVED': { text: 'Approved', class: 'bg-green-100 text-green-800', icon: '✓' },
            'CHANGES_REQUESTED': { text: 'Changes Requested', class: 'bg-red-100 text-red-800', icon: '✗' },
            'COMMENTED': { text: 'Commented', class: 'bg-blue-100 text-blue-800', icon: '💬' },
            'DISMISSED': { text: 'Dismissed', class: 'bg-gray-100 text-gray-800', icon: '−' },
            'PENDING': { text: 'Pending', class: 'bg-yellow-100 text-yellow-800', icon: '○' }
        };
        
        const stateInfo = stateMap[state] || { text: state, class: 'bg-gray-100 text-gray-800', icon: '' };
        badge.className += ' ' + stateInfo.class;
        
        if (stateInfo.icon) {
            const iconSpan = document.createElement('span');
            iconSpan.className = 'mr-1';
            iconSpan.textContent = stateInfo.icon;
            badge.appendChild(iconSpan);
        }
        
        const textNode = document.createTextNode(stateInfo.text);
        badge.appendChild(textNode);
        
        return badge;
    }
    
    /**
     * Create an action badge
     * @private
     */
    createActionBadge(action) {
        const badge = document.createElement('span');
        badge.className = 'inline-flex items-center px-2 py-1 rounded text-xs font-medium';
        
        const actionMap = {
            'merged': { text: 'Merged', class: 'bg-purple-100 text-purple-800' },
            'closed': { text: 'Closed', class: 'bg-red-100 text-red-800' },
            'labeled': { text: 'Labeled', class: 'bg-blue-100 text-blue-800' },
            'reopened': { text: 'Reopened', class: 'bg-yellow-100 text-yellow-800' }
        };
        
        const actionInfo = actionMap[action] || { text: action, class: 'bg-gray-100 text-gray-800' };
        badge.className += ' ' + actionInfo.class;
        badge.textContent = actionInfo.text;
        
        return badge;
    }
    
    /**
     * Get contrasting text color for a background color
     * @private
     */
    getContrastColor(hexColor) {
        const hex = hexColor.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return luminance > 0.5 ? '#000000' : '#FFFFFF';
    }
}

/**
 * SummaryCard component
 */
class SummaryCard {
    constructor(data) {
        this.data = data;
    }

    /**
     * Render the component
     * @returns {HTMLElement} DOM element
     */
    render() {
        const card = document.createElement('div');
        card.className = 'summary-card bg-white rounded-lg shadow-md p-6 mb-6';
        
        // Check if we have data
        const totalActions = this.data?.summary?.total_actions || 0;
        
        if (totalActions === 0) {
            // Empty state
            const emptyContainer = document.createElement('div');
            emptyContainer.className = 'text-center py-8';
            
            const emptyIcon = document.createElement('div');
            emptyIcon.className = 'text-6xl mb-4';
            emptyIcon.textContent = '📭';
            emptyContainer.appendChild(emptyIcon);
            
            const emptyTitle = document.createElement('h3');
            emptyTitle.className = 'text-xl font-semibold text-gray-700 mb-2';
            emptyTitle.textContent = 'No Activity Found';
            emptyContainer.appendChild(emptyTitle);
            
            const emptyText = document.createElement('p');
            emptyText.className = 'text-gray-600';
            emptyText.textContent = 'No GitHub activity found for this user in the selected time period.';
            emptyContainer.appendChild(emptyText);
            
            card.appendChild(emptyContainer);
            return card;
        }
        
        // Success state - create title
        const title = document.createElement('h3');
        title.className = 'text-2xl font-bold text-gray-800 mb-4';
        title.textContent = 'Activity Summary';
        card.appendChild(title);
        
        // Total actions section
        const totalSection = document.createElement('div');
        totalSection.className = 'mb-6';
        
        const totalText = document.createElement('p');
        totalText.className = 'text-lg text-gray-700';
        
        const totalSpan = document.createElement('span');
        totalSpan.className = 'font-bold text-blue-600';
        totalSpan.textContent = totalActions.toString();
        totalText.appendChild(totalSpan);
        
        totalText.appendChild(document.createTextNode(' total actions over '));
        
        const daysSpan = document.createElement('span');
        daysSpan.className = 'font-semibold';
        daysSpan.textContent = (this.data?.meta?.period?.days || 7).toString();
        totalText.appendChild(daysSpan);
        
        totalText.appendChild(document.createTextNode(' days'));
        totalSection.appendChild(totalText);
        
        // User info
        const userText = document.createElement('p');
        userText.className = 'text-sm text-gray-500 mt-1';
        userText.textContent = 'User: ';
        
        const userSpan = document.createElement('span');
        userSpan.className = 'font-medium';
        userSpan.textContent = this.data?.meta?.user || '-';
        userText.appendChild(userSpan);
        
        totalSection.appendChild(userText);
        card.appendChild(totalSection);
        
        // Category breakdown grid
        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-1 md:grid-cols-2 gap-4';
        
        const categories = [
            { emoji: '📝', name: 'Issues Opened', key: 'issues_opened', color: 'blue' },
            { emoji: '🚀', name: 'Pull Requests Opened', key: 'prs_opened', color: 'green' },
            { emoji: '🔧', name: 'Issue Triage & Investigation', key: 'issue_triage', color: 'yellow' },
            { emoji: '👀', name: 'Code Reviews', key: 'code_reviews', color: 'purple' }
        ];
        
        categories.forEach(cat => {
            const catBox = document.createElement('div');
            catBox.className = `bg-${cat.color}-50 rounded-lg p-4 border border-${cat.color}-200`;
            
            const catInner = document.createElement('div');
            catInner.className = 'flex items-center justify-between';
            
            const catLeft = document.createElement('div');
            catLeft.className = 'flex items-center';
            
            const emojiSpan = document.createElement('span');
            emojiSpan.className = 'text-2xl mr-3';
            emojiSpan.textContent = cat.emoji;
            catLeft.appendChild(emojiSpan);
            
            const nameSpan = document.createElement('span');
            nameSpan.className = 'text-gray-700 font-medium';
            nameSpan.textContent = cat.name;
            catLeft.appendChild(nameSpan);
            
            catInner.appendChild(catLeft);
            
            const countSpan = document.createElement('span');
            countSpan.className = `text-2xl font-bold text-${cat.color}-600`;
            countSpan.textContent = (this.data?.summary?.by_category?.[cat.key] || 0).toString();
            catInner.appendChild(countSpan);
            
            catBox.appendChild(catInner);
            grid.appendChild(catBox);
        });
        
        card.appendChild(grid);
        
        // Timestamp footer
        const footer = document.createElement('div');
        footer.className = 'mt-4 pt-4 border-t border-gray-200';
        
        const timestampText = document.createElement('p');
        timestampText.className = 'text-sm text-gray-500';
        timestampText.textContent = 'Data fetched: ';
        
        const timestampSpan = document.createElement('span');
        timestampSpan.className = 'font-medium';
        const fetchedAt = this.data?.meta?.fetched_at;
        timestampSpan.textContent = fetchedAt ? formatTimestamp(fetchedAt) : '-';
        timestampText.appendChild(timestampSpan);
        
        footer.appendChild(timestampText);
        card.appendChild(footer);
        
        return card;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatRelativeTime,
        formatTimestamp,
        truncateText,
        escapeHtml,
        CollapsibleSection,
        ItemCard,
        SummaryCard
    };
}
