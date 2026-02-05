# GitHub Maintainer Activity Dashboard - Architecture Document

**Version:** 1.5
**Last Updated:** February 4, 2026
**Status:** Phase 1 Complete + Team Engagement Feature - Production Ready
**Purpose:** Internal tool for tracking individual maintainer contributions and team engagement metrics for PowerShell repository

**Recent Updates:**
- **v1.6 (Feb 5, 2026):** Added Copy Summary feature for Individual Activity
  - **Copy to Clipboard button:** One-click button in Activity Summary section
  - **Plain text format:** Generates compact YAML-like summary with username, date range, and activity counts
  - **Smart filtering:** Only includes categories and subcategories with non-zero counts
  - **Visual feedback:** Green toast notification confirms successful copy
  - **Clipboard API:** Uses modern `navigator.clipboard.writeText()` for reliable copying
  - **Data structure:** Accesses subcategory counts from `data.issue_triage` and `data.code_reviews` arrays
- **v1.5 (Feb 4, 2026):** Enhanced team engagement with detail view modals
  - **Interactive metric cards:** Click on 6 metric cards to view detailed lists
  - **Modal overlays:** Show lists of issues/PRs with status, dates, and actors
  - **Detailed information:** Issue/PR numbers (linked), status (color-coded), closure/merge actors
  - **Backend enhancements:** Added `closed_at` for issues, `merged_by` for PRs in API responses
  - **UI improvements:** Hover effects, smooth transitions, Escape key/click-outside to close
- **v1.4 (Feb 4, 2026):** Implemented team engagement metrics dashboard
  - New `/api/team-engagement` endpoint for team and contributor engagement data
  - Tab-based UI: "Individual Activity" and "Team Engagement" views
  - Parallel queries for PS_TEAM_MEMBERS and PS_CONTRIBUTORS
  - Metrics cards with bar charts (Chart.js) for issues and PRs
  - Distinct color coding: purple for team, orange for contributors
  - New JavaScript component: `team-engagement.js`
- **v1.3 (Feb 3, 2026):** Implemented timezone-aware date handling
  - Frontend auto-detects user's timezone (IANA format) and sends with API requests
  - Backend interprets date boundaries in user's local timezone, then converts to UTC
  - Fixes issue where users' contributions on boundary dates were missing
  - Date range display shows dates in user's local timezone
  - Added 11 new timezone validation tests
- **v1.2 (Feb 2, 2026):** Implemented custom date range feature
  - Changed API from `days` parameter to `from_date`/`to_date` parameters
  - Added comprehensive date validation (format, range, future dates, max 200 days)
  - Frontend transparently converts days to date ranges
  - Updated test coverage to 66 tests (26 new date range tests)
- **v1.1 (Jan 23, 2026):** Reflected actual implementation details from completed Phase 1
- Updated API response formats to match code
- Added security features documentation

---

## Implementation Status

### ✅ Completed Features (Phase 1)

**Backend:**
- Flask application with modular structure
- `/api/health` endpoint for health checks
- `/api/metrics` endpoint with custom date range support
- `/api/team-engagement` endpoint for team engagement metrics
- **Date Range Features:**
  - Accepts `from_date` and `to_date` in YYYY-MM-DD format
  - Accepts optional `timezone` parameter (IANA timezone name, default: "UTC")
  - Interprets date boundaries in user's timezone, converts to UTC for processing
  - Comprehensive validation: format, range order, future dates, max 200 days, invalid timezones
  - Returns date range metadata in ISO 8601 format with 'Z' suffix
- Integration with existing `github_events.py` module
- Response formatter (`api/response_formatter.py`) for data transformation
- Robust error handling with sanitization
- Configuration management via environment variables

**Frontend:**
- Single-page application with vanilla JavaScript
- **Tab-based UI:**
  - "Individual Activity" tab: User-specific contributions
  - "Team Engagement" tab: Team and contributor engagement metrics
- **Individual Activity View:**
  - Search interface with username input
  - Time period selection (1, 3, 7, 14, 30, 60, 90, 180 days)
  - Custom date range picker with validation
  - Four main activity categories with collapsible UI
  - Sub-sections for Issue Triage and Code Reviews
  - **Copy Summary button:** Generates and copies plain text summary to clipboard
    - Compact format showing only non-zero activity counts
    - Includes username, date range, and total actions
    - Shows subcategory breakdowns (comments, labeled, closed, reviews, merged)
    - Toast notification for copy confirmation
- **Team Engagement View:**
  - Date range selection (quick select or custom)
  - Metrics cards for issues and PRs (total, team engaged, contributors engaged, closed/finished)
  - Horizontal bar charts using Chart.js for visualization
  - Distinct color coding: purple (team), orange (contributors), blue (total), green (PRs)
  - Parallel API queries for PS_TEAM_MEMBERS and PS_CONTRIBUTORS
- **Timezone-Aware Date Handling:**
  - Auto-detects user's timezone using Intl.DateTimeFormat API
  - Sends timezone parameter with all API requests
  - Displays date ranges in user's local timezone
  - Converts days to `from_date`/`to_date` before API calls
- Loading states and error messaging
- State persistence via localStorage
- Responsive design with Tailwind CSS

**Security:**
- Error message sanitization (tokens, paths, env vars)
- Input validation (username, date format, timezone)
- **Date Range Validation:**
  - Format: YYYY-MM-DD (ISO 8601)
  - Range order: `from_date` ≤ `to_date`
  - No future dates allowed
  - Maximum range: 200 days
- **Timezone Validation:**
  - Only IANA timezone names accepted (e.g., "America/Los_Angeles")
  - Abbreviations (PST, EST) rejected for consistency
  - Invalid timezones return 400 error with helpful message
- Parameter sanitization and type checking

**Testing:**
- **77 automated tests (100% passing)**
- **Date Range Test Coverage:**
  - 10 date validation tests (format, range, future dates, max days)
  - 3 response metadata tests (ISO format, days calculation)
  - 7 date-specific error handling tests
  - 2 integration tests with date ranges
- **Timezone Test Coverage:**
  - 9 timezone parameter tests (valid/invalid timezones, defaults)
  - 2 timezone boundary conversion tests (UTC vs PST differences)
- Error handling validation documented
- Frontend integration test plan
- Mock GitHub API for consistent testing

**Documentation:**
- Architecture documentation (this file)
- Error handling validation report
- Testing documentation
- Comprehensive inline code comments

### ⏳ Planned Features (Phase 2+)
- Response caching (SQLite/Redis)
- Export to CSV/PDF
- Activity trend charts
- Email digest subscriptions

---

## Executive Summary

This document outlines the architecture for a web-based dashboard that displays GitHub maintainer activity metrics. The system will collect and present contribution data across 4 main categories: Issues Opened, Pull Requests Opened, Issue Triage/Investigation, and Code Reviews.

**Key Design Goals:**
- Simple to maintain and deploy
- Easy to expand with new features
- Minimal operational overhead
- Good performance for internal use (5-20 concurrent users)

---

## Timezone-Aware Date Handling

### Problem Statement

Prior to v1.3, date boundaries were interpreted as UTC on both frontend and backend. This caused confusion when users searched for contributions within specific dates in their local timezone.

**Example Issue:**
- User in PST selects date range "2026-02-01 to 2026-02-02"
- User assumes this means end of day on 2026-02-02 in PST (11:59 PM PST = 07:59 AM UTC on 2026-02-03)
- But system interpreted "2026-02-02" as UTC (11:59 PM UTC on 2026-02-02)
- User's contribution made at 5:06 PM PST on Feb 2 (01:06 AM UTC on Feb 3) was excluded from results

### Solution

**Frontend (JavaScript):**
- Auto-detects user's timezone using `Intl.DateTimeFormat().resolvedOptions().timeZone`
- Returns IANA timezone name (e.g., "America/Los_Angeles")
- Sends timezone parameter with all API requests
- Displays returned dates in local timezone when showing date range

**Backend (Python):**
- Accepts optional `timezone` parameter (defaults to "UTC" for backward compatibility)
- Validates timezone using `zoneinfo.ZoneInfo(timezone_str)`
- Parses YYYY-MM-DD dates and applies timezone to start/end of day
- Converts timezone-aware datetime to UTC for GitHub API queries
- Example: "2026-02-02" + "America/Los_Angeles" → "2026-02-02 00:00:00 PST" → "2026-02-02 08:00:00 UTC"

**Backend Processing (`github_events.py`):**
- Uses UTC datetime objects exclusively (as GitHub API returns UTC timestamps)
- All date comparisons done in UTC to avoid timezone conversion issues

### Result

Users can now select dates in their local timezone and see contributions correctly included, even when they occur near date boundaries.

---

## System Architecture

### High-Level Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │ ◄─────► │ Flask API    │ ◄─────► │  GitHub     │
│  (Frontend) │  HTTP   │  (Backend)   │  HTTPS  │   API       │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Cache      │
                        │  (Optional)  │
                        └──────────────┘
```

**Components:**
1. **Frontend**: Static HTML/CSS/JavaScript served by Flask
2. **Backend API**: Flask application exposing REST endpoints
3. **Data Collection**: Existing `github_events.py` module
4. **External API**: GitHub GraphQL API
5. **Cache** (Phase 2): Redis or SQLite for caching API responses

---

## Technology Stack

### Recommended Stack: **Flask + Vanilla JavaScript + Tailwind CSS**

#### Rationale

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Flask** | Backend framework | • Already using Python<br>• Lightweight and simple<br>• Easy to integrate with existing code<br>• Excellent for internal tools |
| **Vanilla JavaScript** | Frontend interactivity | • No build step required<br>• Easy to debug and maintain<br>• Sufficient for collapsible UI<br>• Can add Alpine.js later if needed |
| **Chart.js** | Data visualization | • Horizontal bar charts for team metrics<br>• Lightweight and responsive<br>• CDN-based, no build step<br>• Good documentation |
| **Tailwind CSS** (CDN) | Styling | • Rapid UI development<br>• Consistent design system<br>• No build step with CDN<br>• Easy to customize |
| **GitHub GraphQL API** | Data source | Already implemented |
| **SQLite** (Future) | Caching layer | • File-based, no separate server<br>• Good for internal tools |

#### Alternative Considerations

**Why NOT React/Vue?**
- Adds build complexity (npm, webpack, etc.)
- Overkill for simple collapsible lists
- Harder to maintain without JS expertise

**Why NOT Django?**
- Too heavy for this use case
- Unnecessary admin features

**Why Flask over FastAPI?**
- Simpler for serving static files
- More mature ecosystem
- FastAPI is better for async/high-performance APIs (not needed here)

---

## Project Structure

```
ps-engagement/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration (API keys, defaults)
├── requirements.txt            # Python dependencies
├── ARCHITECTURE.md             # This document
├── README.md                   # Setup and usage instructions
│
├── github_events/              # Existing data collection module
│   ├── __init__.py
│   └── github_events.py
│
├── api/                        # Flask API routes
│   ├── __init__.py
│   ├── routes.py               # API endpoints
│   └── response_formatter.py  # Transform data for frontend
│
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css           # Custom styles (tabs, colors)
│   ├── js/
│   │   ├── app.js              # Main application logic with tab switching
│   │   ├── api-client.js       # API interaction layer (metrics + team engagement)
│   │   ├── ui-components.js    # Collapsible sections, cards
│   │   └── team-engagement.js  # Team engagement component
│   └── favicon.ico
│
├── templates/                  # Jinja2 templates
│   ├── base.html               # Base template
│   └── index.html              # Main dashboard page
│
└── tests/                      # Unit and integration tests
    ├── test_api.py
    └── test_github_events.py
```

---

## API Design

### Endpoints

#### 1. **GET /api/health**
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-01-20T10:30:00Z"
}
```

---

#### 2. **GET /api/metrics**
Fetch maintainer activity metrics.

**Query Parameters:**
- `user` (required): GitHub username
- `from_date` (required): Start date in YYYY-MM-DD format
- `to_date` (required): End date in YYYY-MM-DD format
- `timezone` (optional, default="UTC"): IANA timezone name (e.g., "America/Los_Angeles", "America/New_York")
- `owner` (optional, default=PowerShell): Repository owner
- `repo` (optional, default=PowerShell): Repository name

**Date Range Constraints:**
- Format: YYYY-MM-DD (ISO 8601)
- `from_date` must be ≤ `to_date`
- Neither date can be in the future
- Maximum range: 200 days
- Timezone must be valid IANA timezone name (abbreviations like "PST" not accepted)

**Request Example:**
```
GET /api/metrics?user=daxian-dbw&from_date=2026-01-26&to_date=2026-02-02&timezone=America/Los_Angeles
```

**Timezone Behavior:**
- Dates are interpreted as start/end of day in the specified timezone
- `from_date=2026-02-01` with `timezone=America/Los_Angeles` means 2026-02-01 00:00:00 PST
- Backend converts to UTC (2026-02-01 08:00:00 UTC) for GitHub API queries
- This ensures user contributions made in their local timezone are correctly included

**Legacy Note:** The API previously accepted a `days` parameter. This is no longer supported at the API level. Frontend applications should convert days to date ranges before making API calls.

**Response Structure:**
```json
{
  "meta": {
    "user": "daxian-dbw",
    "repository": "PowerShell/PowerShell",
    "period": {
      "days": 8,
      "start": "2026-01-26T00:00:00Z",
      "end": "2026-02-02T00:00:00Z"
    },
    "fetched_at": "2026-01-20T10:30:00Z"
  },
  "summary": {
    "total_actions": 23,
    "by_category": {
      "issues_opened": 3,
      "prs_opened": 2,
      "issue_triage": 12,
      "code_reviews": 6
    }
  },
  "data": {
    "issues_opened": [
      {
        "number": 12345,
        "title": "Fix parameter validation issue",
        "url": "https://github.com/PowerShell/PowerShell/issues/12345",
        "created_at": "2026-01-18T14:30:00Z"
      }
    ],
    "prs_opened": [
      {
        "number": 23456,
        "title": "Implement new cmdlet",
        "url": "https://github.com/PowerShell/PowerShell/pull/23456",
        "action": "opened",
        "state": "OPEN",
        "timestamp": "2026-01-17T09:15:00Z"
      }
    ],
    "issue_triage": {
      "comments": [
        {
          "number": 11111,
          "title": "Bug in Get-Process",
          "url": "https://github.com/PowerShell/PowerShell/issues/11111#issuecomment-123456",
          "timestamp": "2026-01-19T16:20:00Z"
        }
      ],
      "labeled": [
        {
          "number": 11112,
          "title": "Feature request",
          "label": "Resolution-Fixed",
          "url": "https://github.com/PowerShell/PowerShell/issues/11112",
          "timestamp": "2026-01-18T11:00:00Z"
        }
      ],
      "closed": [
        {
          "number": 11113,
          "title": "Old issue",
          "url": "https://github.com/PowerShell/PowerShell/issues/11113",
          "timestamp": "2026-01-16T14:00:00Z"
        }
      ]
    },
    "code_reviews": {
      "comments": [
        {
          "number": 22222,
          "title": "Update documentation",
          "url": "https://github.com/PowerShell/PowerShell/pull/22222#discussion_r123456",
          "timestamp": "2026-01-19T10:00:00Z"
        }
      ],
      "reviews": [
        {
          "number": 22223,
          "title": "Fix memory leak",
          "state": "APPROVED",
          "url": "https://github.com/PowerShell/PowerShell/pull/22223#pullrequestreview-789",
          "timestamp": "2026-01-18T15:30:00Z"
        }
      ],
      "merged": [
        {
          "number": 22224,
          "title": "Performance improvement",
          "action": "merged",
          "url": "https://github.com/PowerShell/PowerShell/pull/22224",
          "timestamp": "2026-01-17T13:45:00Z"
        }
      ],
      "closed": [
        {
          "number": 22225,
          "title": "Duplicate PR",
          "action": "closed",
          "url": "https://github.com/PowerShell/PowerShell/pull/22225",
          "timestamp": "2026-01-16T09:00:00Z"
        }
      ]
    }
  }
}
```

**Error Response:**
```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "GitHub user 'invalid-user' not found",
    "timestamp": "2026-01-20T10:30:00Z"
  }
}
```

**Status Codes:**
- 200: Success
- 400: Bad request (invalid parameters)
  - Error codes: `MISSING_PARAMETER`, `INVALID_PARAMETER`, `INVALID_DATE_FORMAT`, `INVALID_DATE_RANGE`, `DATE_RANGE_TOO_LARGE`, `FUTURE_DATE_NOT_ALLOWED`
- 404: User not found
  - Error code: `USER_NOT_FOUND`
- 429: Rate limit exceeded
  - Error code: `RATE_LIMIT_EXCEEDED`
- 500: Server error
  - Error codes: `AUTHENTICATION_ERROR`, `GITHUB_API_ERROR`, `INTERNAL_ERROR`

---

#### 3. **GET /api/team-engagement**
Fetch team engagement metrics for issues and pull requests.

**Query Parameters:**
- `from_date` (required): Start date in YYYY-MM-DD format
- `to_date` (required): End date in YYYY-MM-DD format
- `timezone` (optional, default="UTC"): IANA timezone name
- `owner` (optional, default=PowerShell): Repository owner
- `repo` (optional, default=PowerShell): Repository name

**Request Example:**
```
GET /api/team-engagement?from_date=2026-01-28&to_date=2026-02-03&timezone=America/Los_Angeles
```

**Response Structure:**
```json
{
  "team": {
    "issue": {
      "total_issues": 6,
      "team_engaged": 4,
      "team_unattended": 2,
      "engagement_ratio": 0.67,
      "manually_closed": 3,
      "pr_triggered_closed": 0,
      "closed_ratio": 0.5,
      "engaged_issues": [...],
      "unattended_issues": [...],
      "manually_closed_issues": [...],
      "pr_triggered_closed_issues": [...]
    },
    "pr": {
      "total_prs": 8,
      "team_engaged": 2,
      "team_unattended": 6,
      "engagement_ratio": 0.25,
      "merged": 2,
      "closed": 0,
      "finish_ratio": 0.25,
      "engaged_prs": [...],
      "unattended_prs": [...],
      "merged_prs": [...],
      "closed_prs": [...]
    }
  },
  "contributors": {
    "issue": { /* same structure as team.issue */ },
    "pr": { /* same structure as team.pr */ }
  },
  "meta": {
    "from_date": "2026-01-28",
    "to_date": "2026-02-03",
    "timezone": "America/Los_Angeles",
    "repository": "PowerShell/PowerShell",
    "timestamp": "2026-02-04T10:30:00Z"
  }
}
```

**Engagement Criteria:**
- **Issues:** Team member commented, applied Resolution-* label, or closed the issue
- **PRs:** Team member commented, reviewed, merged, or closed the PR

**Implementation Details:**
- Queries `PS_TEAM_MEMBERS` and `PS_CONTRIBUTORS` in parallel using ThreadPoolExecutor
- Uses `get_team_engagement()` from `github_events` module
- Returns engagement data for both groups to compare team vs contributor engagement
- **Enhanced response fields:**
  - Issues: Added `closed_at` field to closed issues for detailed timestamps
  - PRs: Added `merged_by` field from GraphQL `mergedBy` to show who merged each PR

**Interactive Detail Views:**
Six metric cards are clickable to show detailed modal views:
1. **Closed Issues:** Shows manually closed vs PR-closed issues with closure actors
2. **Team Engaged Issues:** Lists issues with team member engagement
3. **Contributors Engaged Issues:** Lists issues with contributor engagement
4. **Finished PRs:** Shows merged vs closed PRs with merge actors
5. **Team Engaged PRs:** Lists PRs with team member engagement
6. **Contributors Engaged PRs:** Lists PRs with contributor engagement

**Modal Display Format:**
- Issue/PR number (hyperlinked to GitHub)
- Status with color coding:
  - Issues: Orange (manually closed), Purple (closed by PR)
  - PRs: Green (merged), Gray (closed)
- Actor information: "by <username>"
- Creation date
- Modal controls: Close button, click-outside, Escape key

**Status Codes:**
- 200: Success
- 400: Bad request (same error codes as `/api/metrics`)
- 500: Server error

---

## Frontend Design

### Page Layout

**Main Dashboard with Tabs:**
```
┌─────────────────────────────────────────────────────┐
│  GitHub Maintainer Activity Dashboard               │
├─────────────────────────────────────────────────────┤
│  [👤 Individual Activity]  [👥 Team Engagement]     │
├─────────────────────────────────────────────────────┤
```

**Individual Activity Tab (Default):**
```
│  ┌────────────────────────────────────────────┐     │
│  │  Search Panel                              │     │
│  │  ┌──────────────────┐  ┌──────┐            │     │
│  │  │ GitHub Username  │  │  Go  │            │     │
│  │  └──────────────────┘  └──────┘            │     │
│  │  Days: [1][3][7][14][30][90][180]          │     │
│  └────────────────────────────────────────────┘     │
│                                                     │
│  ┌────────────────────────────────────────────┐     │
│  │  Summary (Loading... / Results)            │     │
│  │  23 total actions over 7 days              │     │
│  └────────────────────────────────────────────┘     │
│                                                     │
│  ▼ 📝 Issues Opened (3)                             │
│     [Expanded: shows list of issues]                │
│                                                     │
│  ▶ 🚀 Pull Requests Opened (2)                      │
│  ▶ 🔧 Issue Triage & Investigation (12)             │
│  ▶ 👀 Code Reviews (6)                              │
└─────────────────────────────────────────────────────┘
```

**Team Engagement Tab:**
```
│  ┌────────────────────────────────────────────┐     │
│  │  Query Team Engagement Metrics             │     │
│  │  Days: [1][3][7][14][30][Custom]  ┌──────┐ │     │
│  │                                   │  Go  │ │     │
│  │                                   └──────┘ │     │
│  └────────────────────────────────────────────┘     │
│                                                     │
│  📝 ISSUES (Clickable cards for detail view)        │
│  ┌──────────────┐  ┌──────────────┐                │
│  │📊 Total: 6   │  │✅ Closed: 3  │ ← Click to see │
│  └──────────────┘  └──────────────┘    details     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │🎯 Team: 4    │  │🤝 Contrib: 5 │ ← Click to see │
│  │   (67%)      │  │    (83%)     │    details     │
│  └──────────────┘  └──────────────┘                │
│  [Bar Chart Visualization]                          │
│                                                     │
│  🚀 PULL REQUESTS                                   │
│  [Similar layout to Issues]                         │
│                                                     │
│  Detail View Modal (shown when card clicked):       │
│  ┌──────────────────────────────────────────┐      │
│  │ Closed Issues                        [X] │      │
│  ├──────────────────────────────────────────┤      │
│  │ #26733 Manually closed, by user   1/13/26│      │
│  │ #26732 Closed by PR, by user      1/12/26│      │
│  │ ...                                      │      │
│  └──────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

### UI Components

#### 1. Search Panel
- Text input for username (with validation)
- Quick-select buttons for common time periods (1, 3, 7, 14, 30, 90, 180 days)
- "Go" button with loading spinner
- Error message display area

#### 2. Summary Card
- Total actions count
- Breakdown by category
- Time period display
- Timestamp of data fetch
- **Copy Summary button** with clipboard icon
  - Positioned in top-right corner of Activity Summary section
  - Generates plain text summary format:
    ```
    GitHub Activity: username (YYYY-MM-DD to YYYY-MM-DD)
    Total: X actions

    Issues Opened: X
    Pull Requests Opened: X
    Issue Triage & Investigation: X
      - Comments: X
      - Labeled: X
      - Closed: X
    Code Reviews: X
      - Reviews: X
      - Comments: X
      - Merged: X
      - Closed: X
    ```
  - Only includes categories/subcategories with counts > 0
  - Shows toast notification on successful copy

#### 3. Collapsible Category Sections
**Structure for each category:**
```html
<div class="category-section">
  <div class="category-header" onclick="toggleSection()"
       tabindex="0" role="button" aria-expanded="false">
    <span class="icon">▶</span>
    <span class="emoji">📝</span>
    <span class="title">Issues Opened</span>
    <span class="count">(3)</span>
  </div>

  <div class="category-content collapsible-content max-h-0">
    <!-- Sub-sections for complex categories (Issue Triage, Code Reviews) -->
    <div class="sub-section" data-subsection="comments">
      <h4 class="sub-section-header" tabindex="0" role="button"
          aria-expanded="false">
        <span class="mr-2">💬</span>
        Comments
        <span class="sub-count-badge">5</span>
      </h4>
      <div class="sub-section-content max-h-0 overflow-hidden">
        <div class="items-container space-y-3">
          <!-- Individual items -->
        </div>
      </div>
    </div>
  </div>
</div>
```

#### 4. Item Cards
```html
<div class="item-card">
  <div class="item-header">
    <a href="..." target="_blank">#12345</a>
    <span class="item-title">Fix parameter validation</span>
  </div>
  <div class="item-meta">
    <span class="timestamp">2 days ago</span>
    <span class="label">Resolution-Fixed</span>
  </div>
</div>
```

### JavaScript Architecture

#### Module Structure

**1. api-client.js** - API communication
```javascript
class APIClient {
  async fetchMetrics(user, days) {
    // Converts days to from_date/to_date
    const toDate = new Date();
    const fromDate = new Date();
    fromDate.setDate(toDate.getDate() - days);
    // Sends: ?user=X&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD
  }
  handleError(error) { ... }
}
```

**2. ui-components.js** - UI building blocks
```javascript
class CollapsibleSection {
  constructor(data, isExpanded) { ... }
  toggle() { ... }
  render() { ... }
}

class ItemCard {
  constructor(item, type) { ... }
  render() { ... }
}
```

**3. app.js** - Main application logic
```javascript
class Dashboard {
  constructor() {
    this.lastData = null;  // Store last API response for copy functionality
    // ... other properties
  }
  
  init() { ... }
  loadData(user, days) { 
    // Stores response in this.lastData
  }
  renderCategories(data) { ... }
  
  // Copy Summary feature methods
  generateTextSummary(data) {
    // Generates plain text from data
    // Accesses subcategories from data.issue_triage and data.code_reviews arrays
    // Returns formatted string with only non-zero counts
  }
  
  async copyToClipboard(text) {
    // Uses navigator.clipboard.writeText() API
    // Calls showCopyNotification() for feedback
  }
  
  showCopyNotification(success) {
    // Creates toast notification element
    // Shows green success or red error message
    // Auto-removes after 3 seconds with fade animation
  }
  
  handleCopySummaryClick() {
    // Event handler for copy button
    // Generates text and copies to clipboard
  }
  
  showLoading() { ... }
  showError(message) { ... }
}
```

### State Management

For Phase 1, use simple JavaScript objects:
```javascript
const appState = {
  currentUser: null,
  currentDays: 7,
  data: null,
  expandedSections: {
    'issues_opened': false,
    'prs_opened': false,
    'issue_triage': false,
    'code_reviews': false
  }
};
```

Store in `localStorage` for persistence across sessions.

---

## Data Flow

### User Journey: Load Activity Data

1. **User enters username and selects time period**
   - Frontend validates input (non-empty, reasonable days)
   - Shows loading spinner

2. **Frontend sends API request**
   - User selects days (e.g., 7)
   - Frontend detects user's timezone:
     ```javascript
     const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone; // e.g., "America/Los_Angeles"
     ```
   - Frontend converts to date range in local timezone:
     ```javascript
     const toDate = new Date().toISOString().split('T')[0];
     const fromDate = new Date(Date.now() - 7*24*60*60*1000).toISOString().split('T')[0];
     ```
   - Sends with timezone parameter:
     ```javascript
     GET /api/metrics?user=daxian-dbw&from_date=2026-01-26&to_date=2026-02-02&timezone=America/Los_Angeles
     ```

3. **Backend receives request**
   - Validates required parameters (`user`, `from_date`, `to_date`)
   - **Timezone handling:**
     - Validates timezone using `ZoneInfo(timezone_str)` (defaults to "UTC" if not provided)
     - Parses YYYY-MM-DD dates and applies timezone (start/end of day)
     - Example: `2026-02-01` in `America/Los_Angeles` → `2026-02-01 00:00:00 PST`
     - Converts to UTC: `2026-02-01 08:00:00 UTC`
   - **Date validation:**
     - Checks `from_date` ≤ `to_date`
     - Checks no future dates (compares in UTC)
     - Checks range ≤ 200 days
   - Calls `contributions_by()` from `github_events` module with UTC datetime objects
   - Formats response using `response_formatter.py`

4. **Backend fetches from GitHub API**
   - Existing `github_events.py` code handles GraphQL queries
   - Filters and processes data
   - Returns structured data

5. **Backend sends response**
   - JSON response with meta, summary, and data sections

6. **Frontend receives response**
   - Hides loading spinner
   - Updates summary card
   - Renders collapsible sections
   - Updates localStorage with current state

7. **User interacts with sections**
   - Click to expand/collapse
   - Click links to open GitHub items in new tab
   - All interactions are client-side (no new API calls)

---

## Deployment Strategy

### Phase 1: Local Development

**Prerequisites:**
- Python 3.10+
- Git
- GitHub personal access token with `repo` scope

**Setup:**
```bash
# Clone and setup
cd ps-engagement
python -m venv .venv
.venv\Scripts\activate
pip install flask python-dotenv

# Configure
echo "GITHUB_TOKEN=your_token_here" > .env

# Run
python app.py
# Opens at http://localhost:5001
```

### Phase 2: Internal Server Deployment

**Option A: Simple VM Deployment**
- Deploy to Windows Server or Linux VM
- Use `waitress` (Windows) or `gunicorn` (Linux) as WSGI server
- Nginx reverse proxy (optional, for HTTPS)
- systemd service for auto-start

**Option B: Azure App Service** (Recommended for Microsoft environment)
- Push to Azure App Service
- Configure environment variables in portal
- Built-in HTTPS and authentication
- Easy scaling if needed

**Option C: Docker Container**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

### Security Considerations

1. **GitHub Token Management**
   - Store token in environment variable (never commit)
   - Use Azure Key Vault for production
   - Rotate tokens regularly

2. **Error Message Sanitization** ✅ IMPLEMENTED
   - GitHub tokens (ghp_*, gho_*, ghu_*, ghs_*) redacted
   - Database connection strings removed
   - File paths sanitized
   - Environment variables redacted
   - See `sanitize_error_message()` in `api/routes.py`

3. **Rate Limiting**
   - Implement basic rate limiting on API endpoints
   - Cache responses to reduce GitHub API calls

4. **CORS**
   - Not needed if frontend served by same Flask app
   - Configure if separating frontend later

---

## Performance Considerations

### Expected Load
- **Users:** 5-20 concurrent users (internal team)
- **API Calls:** ~10-20 per hour during work hours
- **Data Volume:** Small (JSON responses < 100KB)

### Optimization Strategies

#### 1. Response Caching (Phase 2)
```python
# Cache structure
{
  "cache_key": "user:daxian-dbw:days:7",
  "data": {...},
  "expires_at": "2026-01-20T11:30:00Z"
}
```

- Cache for 5-15 minutes (configurable)
- Use SQLite or Redis
- Invalidate on explicit refresh request

#### 2. GitHub API Rate Limits
- GitHub allows 5,000 requests/hour with token
- Each user query = 3-5 GraphQL requests
- Can handle ~1,000 user queries per hour (well above needs)

#### 3. Frontend Performance
- Lazy rendering: Only render expanded sections
- Debounce search input
- Use browser caching for static assets

---

## Testing Strategy

### Unit Tests ✅ 66/66 PASSING

**Test Coverage:**
- **Date Range Validation (13 tests):**
  - Invalid date formats (US, European)
  - Date range order validation
  - Future date rejection
  - Max range (200 days) enforcement
  - Missing date parameter detection
  - Valid date ranges (1 day, 7 days, 200 days)
- **Response Metadata (3 tests):**
  - Date range in response metadata
  - ISO 8601 format with 'Z' suffix
  - Days calculation accuracy
- **Error Handling (17 tests):**
  - Date-specific error messages (7 tests)
  - GitHub API errors (4 tests)
  - Security and sanitization (3 tests)
  - Error message quality (3 tests)
- Response formatting (18 tests)
- API endpoint validation (12 tests)
- Integration workflows (2 tests)
- Edge cases (empty data, None handling)

**Test Files:**
- `tests/test_api.py` - API endpoint and date range validation tests (49 tests)
- `tests/test_error_handling.py` - Error handling and date validation (17 tests)
- `tests/test_additional.py` - Response formatter edge cases (12 tests)

**Sample Tests:**
```python
# tests/test_api.py - Date Range Validation
def test_invalid_date_format():
    response = client.get('/api/metrics?user=test&from_date=01-26-2026&to_date=02-02-2026')
    assert response.status_code == 400
    assert response.json['error']['code'] == 'INVALID_DATE_FORMAT'

def test_date_range_exceeds_200_days():
    to_date = datetime.utcnow() - timedelta(days=1)
    from_date = to_date - timedelta(days=201)
    response = client.get(f'/api/metrics?user=test&from_date={from_date:%Y-%m-%d}&to_date={to_date:%Y-%m-%d}')
    assert response.status_code == 400
    assert response.json['error']['code'] == 'DATE_RANGE_TOO_LARGE'

def test_future_date_not_allowed():
    response = client.get('/api/metrics?user=test&from_date=2026-02-10&to_date=2026-02-20')
    assert response.status_code == 400
    assert response.json['error']['code'] == 'FUTURE_DATE_NOT_ALLOWED'

# tests/test_error_handling.py - Error Message Quality
def test_no_github_token_leakage():
    # Validates error sanitization
    assert 'ghp_' not in error_message
```

### Integration Tests
- Test full flow: API → GitHub → Response formatting
- Mock GitHub API responses for consistent testing
- Comprehensive error scenario coverage

### Manual Testing Documentation
- See `docs/TESTING.md` for frontend integration tests
- See `docs/ERROR_HANDLING_VALIDATION.md` for error handling validation

---

## Future Expansion Path

### Phase 1 (MVP) - ✅ COMPLETED
- ✅ Single user search
- ✅ 4 main categories with collapsible UI (with sub-sections)
- ✅ **Custom date range support:**
  - API accepts `from_date` and `to_date` (YYYY-MM-DD format)
  - Frontend converts days to date ranges transparently
  - Comprehensive date validation (format, range, future dates, max 200 days)
  - Date range metadata in ISO 8601 format
- ✅ **Timezone-aware date handling:**
  - Auto-detects user's timezone and sends with API requests
  - Backend interprets dates in user's timezone
- ✅ **Team engagement dashboard:**
  - Tab-based UI (Individual Activity vs Team Engagement)
  - Parallel queries for PS_TEAM_MEMBERS and PS_CONTRIBUTORS
  - Metrics cards with bar chart visualizations (Chart.js)
  - Issues and PRs engagement tracking
  - **Interactive detail views:** Click metric cards to see detailed lists in modal overlays
- ✅ Comprehensive error handling and validation
- ✅ Time period selection (1, 3, 7, 14, 30, 60, 90, 180 days)
- ✅ Security: Error message sanitization
- ✅ State persistence via localStorage
- ✅ **Comprehensive test coverage (77 automated tests)**

### Phase 2 - Enhanced Features (3-6 months)
- Response caching (SQLite)
- Export to CSV/PDF
- Dark mode toggle
- Share link functionality
- Activity timeline view (chronological list)
- ✅ **Detailed drill-down lists for team engagement** (completed in v1.5)

### Phase 3 - Advanced Features (6-12 months)
- Multi-user comparison
- Activity trend charts over time
- Email digest subscriptions
- Slack/Teams integration

### Phase 4 - Advanced Analytics (12+ months)
- Machine learning for activity patterns
- Contribution quality metrics
- Workload balancing insights
- Custom reporting

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GitHub API rate limits exceeded | Low | Medium | Implement caching, monitor usage |
| Token expiration/revocation | Medium | High | Use secure storage, implement refresh |
| User enters malicious input | Low | Low | Input validation, parameterized queries |
| Server downtime | Low | Low | Deploy to reliable hosting (Azure) |
| Scalability issues as team grows | Low | Medium | Architecture supports caching/scaling |

---

## Dependencies

### Python (requirements.txt)
```
# Web Framework
flask>=3.0.0

# Environment Configuration
python-dotenv>=1.0.0

# HTTP Requests (GitHub API)
requests>=2.31.0

# Testing
pytest>=8.0.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
```

### Frontend (CDN)
```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Chart.js (for team engagement visualizations) -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.js"></script>

<!-- Flatpickr (for date pickers) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
<script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
```

---

## Configuration Management

### Environment Variables
```bash
# Required
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Optional (with defaults)
GITHUB_OWNER=PowerShell
GITHUB_REPO=PowerShell
DEFAULT_DAYS_BACK=7
FLASK_ENV=development  # or production
FLASK_SECRET_KEY=random_secret_key_here
CACHE_TTL_MINUTES=10
```

### config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_OWNER = os.getenv('GITHUB_OWNER', 'PowerShell')
    GITHUB_REPO = os.getenv('GITHUB_REPO', 'PowerShell')
    DEFAULT_DAYS_BACK = int(os.getenv('DEFAULT_DAYS_BACK', '7'))
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    CACHE_TTL_MINUTES = int(os.getenv('CACHE_TTL_MINUTES', '10'))
```

---

## Monitoring and Logging

### Logging Strategy
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Log examples:
# - API requests with user and parameters
# - GitHub API calls and response times
# - Errors with stack traces
# - Cache hits/misses (Phase 2)
```

### Metrics to Track (Phase 2)
- Request count per endpoint
- Average response time
- GitHub API call count
- Error rate
- Most queried users
- Cache hit rate

---

## Documentation Deliverables

### For End Users
1. ✅ **README.md** - Setup and usage guide
2. ⚠️ **In-app help** - Tooltips and FAQs (Future)

### For Developers
1. ✅ **ARCHITECTURE.md** - This document (comprehensive architecture)
2. ✅ **ERROR_HANDLING_VALIDATION.md** - Error handling test results
3. ✅ **TESTING.md** - Frontend integration testing guide
4. ✅ **Tasks.md** - Development task tracking
5. ✅ **Inline code comments** - Comprehensive docstrings and comments
6. ⚠️ **CONTRIBUTING.md** - How to contribute (Future)

### Additional Documentation
- Comprehensive docstrings in all Python modules
- JSDoc-style comments in JavaScript files
- Test documentation with expected behaviors

---

## Success Criteria

### MVP Launch (Phase 1) - ✅ ACHIEVED
- ✅ Dashboard loads in < 3 seconds for 7-day queries
- ✅ UI is intuitive (no training required)
- ✅ Handles concurrent users (tested with mock load)
- ✅ Zero security vulnerabilities - error sanitization implemented
- ✅ **66/66 automated tests passing (100% pass rate)**
- ✅ Comprehensive error handling with user-friendly messages
- ✅ **Custom date range support with validation**
- ⏳ Production uptime tracking (pending deployment)

### User Satisfaction (In Progress)
- ⏳ 80%+ of team uses it regularly (pending rollout)
- ⏳ < 5 bug reports per month (pending usage)
- ⏳ Positive feedback on usability (pending user testing)

---

## Appendix A: Category Mapping

| Display Name | Data Source | Sub-categories |
|--------------|-------------|----------------|
| **Issues Opened** | `contributions_by()['issues_opened']` | Direct list |
| **Pull Requests Opened** | `contributions_by()['prs_opened']` | Direct list |
| **Issue Triage & Investigation** | Multiple sources | • Issue Comments<br>• Issues Labeled<br>• Issues Closed |
| **Code Reviews** | Multiple sources | • Review Comments<br>• Reviews Submitted<br>• PRs Merged<br>• PRs Closed |

### Detailed Mapping

**Issue Triage & Investigation:**
- Comments (💬) → `contributions_by()['comments']` (filtered for issues only)
- Labeled (🏷️) → `contributions_by()['issues_labeled']`
- Closed (✅) → `contributions_by()['issues_closed']`

**Code Reviews:**
- Comments (💬) → `contributions_by()['comments']` (filtered for PRs only)
- Reviews (📋) → `contributions_by()['reviews']`
- Merged (🔀) → `contributions_by()['prs_merged']` (API returns as 'merged')
- Closed (✅) → `contributions_by()['prs_closed']` (API returns as 'closed')

---

## Appendix B: Example Queries

### Get activity for user over 30 days
```bash
curl "http://localhost:5001/api/metrics?user=daxian-dbw&from_date=2026-01-03&to_date=2026-02-02"
```

### Get activity for different repository
```bash
curl "http://localhost:5001/api/metrics?user=daxian-dbw&from_date=2026-01-26&to_date=2026-02-02&owner=Microsoft&repo=vscode"
```

### Get activity for custom date range
```bash
curl "http://localhost:5001/api/metrics?user=daxian-dbw&from_date=2025-12-01&to_date=2026-01-01"
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.4 | 2026-02-04 | GitHub Copilot | **Team Engagement Feature**<br>• Added `/api/team-engagement` endpoint documentation<br>• Tab-based UI: Individual Activity and Team Engagement<br>• Parallel queries for PS_TEAM_MEMBERS and PS_CONTRIBUTORS<br>• Chart.js integration for bar chart visualizations<br>• Updated project structure with new files<br>• Updated test count: 77 tests<br>• Color-coded metrics (purple for team, orange for contributors) |
| 1.0 | 2026-01-20 | GitHub Copilot | Initial architecture document |
| 1.1 | 2026-01-23 | GitHub Copilot | Updated to reflect actual implementation<br>• Corrected API response formats<br>• Added security documentation<br>• Added test coverage details<br>• Updated phase completion status<br>• Added implementation status section |
| 1.2 | 2026-02-02 | GitHub Copilot | **Custom Date Range Feature**<br>• Changed API from `days` to `from_date`/`to_date` parameters<br>• Added comprehensive date validation documentation<br>• Updated test coverage: 28 → 66 tests<br>• Added date range constraints and error codes<br>• Updated all examples and queries<br>• Documented frontend date conversion logic |

---

## AI Context Summary

**For AI assistants working on this codebase:**

This is a Flask-based web dashboard with two main views: (1) Individual maintainer activity metrics, and (2) Team engagement metrics. Both query GitHub GraphQL API. The application is structured as follows:

**Key Files:**
- `app.py` - Flask app initialization and main routes
- `api/routes.py` - API endpoints (`/api/health`, `/api/metrics`, `/api/team-engagement`)
- `api/response_formatter.py` - Transforms GitHub data to frontend format
- `github_events/github_events.py` - GitHub GraphQL API integration (includes `get_team_engagement()`)
- `static/js/app.js` - Main frontend controller with tab switching
- `static/js/team-engagement.js` - Team engagement component
- `static/js/api-client.js` - API communication layer (metrics + team engagement)
- `static/js/ui-components.js` - UI component generators
- `templates/index.html` - Tab-based UI structure
- `tests/conftest.py` - Test fixtures for date ranges

**Data Flow (Individual Activity):**
1. User enters GitHub username and selects time period (days)
2. **Frontend converts days to date range:**
   - `toDate = yesterday` (to avoid timezone issues)
   - `fromDate = toDate - days`
   - Formats as YYYY-MM-DD
3. Frontend sends GET request to `/api/metrics?user=X&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&timezone=USER_TZ`
4. **Backend validates dates:**
   - Required: both `from_date` and `to_date`
   - Format: YYYY-MM-DD (parsed with `datetime.strptime`)
   - Range: `from_date` ≤ `to_date`
   - No future dates allowed
   - Max range: 200 days
5. Backend calls `github_events.contributions_by()` with datetime objects
6. GitHub data is fetched via GraphQL, formatted by `response_formatter`
7. JSON response returned with structure: `{meta, summary, data}`
8. Frontend renders collapsible categories with sub-sections

**Data Flow (Team Engagement):**
1. User selects time period in Team Engagement tab
2. Frontend converts days to date range (same as individual activity)
3. Frontend sends GET request to `/api/team-engagement?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&timezone=USER_TZ`
4. **Backend makes parallel queries:**
   - Calls `get_team_engagement(from_date, to_date, PS_TEAM_MEMBERS, ...)`
   - Calls `get_team_engagement(from_date, to_date, PS_CONTRIBUTORS, ...)`
   - Both run in ThreadPoolExecutor for performance
5. Backend returns engagement data for both team and contributors
6. Frontend renders:
   - Metrics cards (total, team engaged, contributors engaged, closed/finished)
   - Horizontal bar charts using Chart.js
   - Color-coded: purple (team), orange (contributors)

**API Response Structure:**
- `meta.period` - Contains `days` (calculated), `start` (ISO), `end` (ISO)
- `data.issues_opened[]` - Direct list of issues
- `data.prs_opened[]` - Direct list of PRs with state
- `data.issue_triage{}` - Object with `comments[]`, `labeled[]`, `closed[]`
- `data.code_reviews{}` - Object with `comments[]`, `reviews[]`, `merged[]`, `closed[]`
- All items use `timestamp` field (not `occurredAt`, `publishedAt`, etc.)
- Issue/PR numbers stored as `number`, titles as `title`
- All timestamps in ISO 8601 format with 'Z' suffix

**Error Handling:**
- All errors return `{error: {code, message, timestamp}}`
- **Error codes:** 
  - **Date validation:** `INVALID_DATE_FORMAT`, `INVALID_DATE_RANGE`, `DATE_RANGE_TOO_LARGE`, `FUTURE_DATE_NOT_ALLOWED`
  - **Parameters:** `MISSING_PARAMETER`, `INVALID_PARAMETER`
  - **GitHub:** `USER_NOT_FOUND`, `RATE_LIMIT_EXCEEDED`, `GITHUB_API_ERROR`, `AUTHENTICATION_ERROR`
  - **Server:** `INTERNAL_ERROR`
- Error sanitization removes tokens, paths, env vars

**Testing:**
- Run: `pytest tests/` (or `pytest tests/ -v -W ignore::DeprecationWarning` to suppress warnings)
- **66 tests** cover:
  - Date range validation (format, constraints)
  - API validation (parameters, responses)
  - Error handling (GitHub API, network)
  - Security (sanitization)
  - Response formatting (metadata, data structure)
- Test fixtures in `conftest.py` provide reusable date ranges
- Mocks used for GitHub API to ensure consistent tests

**Configuration:**
- Environment variables in `.env` file
- Required: `GITHUB_TOKEN`
- Optional: `GITHUB_OWNER`, `GITHUB_REPO`, `DEFAULT_DAYS_BACK`, `CACHE_TTL_MINUTES`

**Current Phase:** Phase 1 complete with custom date range support and team engagement dashboard, 77/77 tests passing, ready for deployment

**Important Implementation Details:**
- **Date Parameters:** API requires `from_date` and `to_date` (YYYY-MM-DD), NOT `days`
- **Frontend Conversion:** Frontend converts user-selected days to date ranges before API calls
- **Date Validation:** Backend validates format, range order, future dates, and max 200 days
- **Response Format:** `meta.period` includes `start`, `end` (ISO 8601 with 'Z'), and calculated `days`
- **No Legacy Support:** Old `days` parameter is not supported at API level

---

## Questions & Decisions Log

### Open Questions
- [ ] Should we support multiple repositories in one view? (Future consideration)
- [ ] When to implement caching? (Phase 2 - after usage patterns established)
- [ ] Deployment target: Azure App Service vs VM? (TBD)

### Decisions Made
- ✅ Use Flask over FastAPI (simpler, better for static files)
- ✅ Vanilla JavaScript over React (easier to maintain)
- ✅ 4 categories with sub-sections (per user preference)
- ✅ No visualizations in Phase 1 (focus on functionality)
- ✅ Internal tool first (can expand later)
- ✅ Error sanitization mandatory (security requirement)
- ✅ Time periods: 1, 3, 7, 14, 30, 60, 90, 180 days
- ✅ Comprehensive testing before deployment
- ✅ localStorage for state persistence (no backend session needed)
