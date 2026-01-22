# GitHub Maintainer Activity Dashboard - Architecture Document

**Version:** 1.0  
**Date:** January 20, 2026  
**Status:** Initial Design  
**Purpose:** Internal tool for tracking maintainer contributions to PowerShell repository

---

## Executive Summary

This document outlines the architecture for a web-based dashboard that displays GitHub maintainer activity metrics. The system will collect and present contribution data across 4 main categories: Issues Opened, Pull Requests Opened, Issue Triage/Investigation, and Code Reviews.

**Key Design Goals:**
- Simple to maintain and deploy
- Easy to expand with new features
- Minimal operational overhead
- Good performance for internal use (5-20 concurrent users)

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
│   │   └── style.css           # Custom styles (minimal)
│   ├── js/
│   │   ├── app.js              # Main application logic
│   │   ├── api-client.js       # API interaction layer
│   │   └── ui-components.js    # Collapsible sections, cards
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
- `days` (optional, default=7): Number of days to look back (1-180)
- `owner` (optional, default=PowerShell): Repository owner
- `repo` (optional, default=PowerShell): Repository name

**Request Example:**
```
GET /api/metrics?user=daxian-dbw&days=7
```

**Response Structure:**
```json
{
  "meta": {
    "user": "daxian-dbw",
    "repository": "PowerShell/PowerShell",
    "period": {
      "days": 7,
      "start": "2026-01-13T00:00:00Z",
      "end": "2026-01-20T10:30:00Z"
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
        "createdAt": "2026-01-18T14:30:00Z"
      }
    ],
    "prs_opened": [
      {
        "number": 23456,
        "title": "Implement new cmdlet",
        "url": "https://github.com/PowerShell/PowerShell/pull/23456",
        "action": "opened",
        "occurredAt": "2026-01-17T09:15:00Z"
      }
    ],
    "issue_triage": {
      "comments": [
        {
          "issue_number": 11111,
          "issue_title": "Bug in Get-Process",
          "url": "https://github.com/PowerShell/PowerShell/issues/11111#issuecomment-123456",
          "publishedAt": "2026-01-19T16:20:00Z"
        }
      ],
      "labeled": [
        {
          "number": 11112,
          "title": "Feature request",
          "label": "Resolution-Fixed",
          "url": "https://github.com/PowerShell/PowerShell/issues/11112",
          "labeledAt": "2026-01-18T11:00:00Z"
        }
      ],
      "closed": [
        {
          "number": 11113,
          "title": "Old issue",
          "url": "https://github.com/PowerShell/PowerShell/issues/11113",
          "closedAt": "2026-01-16T14:00:00Z"
        }
      ]
    },
    "code_reviews": {
      "comments": [
        {
          "pr_number": 22222,
          "pr_title": "Update documentation",
          "url": "https://github.com/PowerShell/PowerShell/pull/22222#discussion_r123456",
          "publishedAt": "2026-01-19T10:00:00Z"
        }
      ],
      "reviews": [
        {
          "pr_number": 22223,
          "pr_title": "Fix memory leak",
          "state": "APPROVED",
          "url": "https://github.com/PowerShell/PowerShell/pull/22223#pullrequestreview-789",
          "occurredAt": "2026-01-18T15:30:00Z"
        }
      ],
      "prs_merged": [
        {
          "number": 22224,
          "title": "Performance improvement",
          "action": "merged",
          "url": "https://github.com/PowerShell/PowerShell/pull/22224",
          "occurredAt": "2026-01-17T13:45:00Z"
        }
      ],
      "prs_closed": [
        {
          "number": 22225,
          "title": "Duplicate PR",
          "action": "closed",
          "url": "https://github.com/PowerShell/PowerShell/pull/22225",
          "occurredAt": "2026-01-16T09:00:00Z"
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
    "code": "INVALID_USER",
    "message": "GitHub user 'invalid-user' not found",
    "timestamp": "2026-01-20T10:30:00Z"
  }
}
```

**Status Codes:**
- 200: Success
- 400: Bad request (invalid parameters)
- 404: User not found
- 429: Rate limit exceeded
- 500: Server error

---

## Frontend Design

### Page Layout

```
┌─────────────────────────────────────────────────────┐
│  GitHub Maintainer Activity Dashboard               │
├─────────────────────────────────────────────────────┤
│                                                     │
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
│                                                     │
│  ▶ 🔧 Issue Triage & Investigation (12)             │
│                                                     │
│  ▶ 👀 Code Reviews (6)                              │
│                                                     │
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

#### 3. Collapsible Category Sections
**Structure for each category:**
```html
<div class="category-section">
  <div class="category-header" onclick="toggleSection()">
    <span class="icon">▶</span>
    <span class="emoji">📝</span>
    <span class="title">Issues Opened</span>
    <span class="count">(3)</span>
  </div>
  
  <div class="category-content collapsed">
    <!-- Sub-sections for complex categories -->
    <div class="sub-section">
      <h4>- Issue Comments (5)</h4>
      <div class="item-list">
        <!-- Individual items -->
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
  async fetchMetrics(user, days) { ... }
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
  init() { ... }
  loadData(user, days) { ... }
  renderCategories(data) { ... }
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
   ```javascript
   GET /api/metrics?user=daxian-dbw&days=7
   ```

3. **Backend receives request**
   - Validates parameters
   - Calls `contributions_by()` from `github_events` module
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
# Opens at http://localhost:5000
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

2. **Authentication** (Phase 2)
   - Use Azure AD authentication for internal access
   - Flask-Login for session management
   - No public access initially

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

### Unit Tests
```python
# tests/test_api.py
def test_metrics_endpoint_valid_user():
    response = client.get('/api/metrics?user=daxian-dbw&days=7')
    assert response.status_code == 200
    assert 'data' in response.json

def test_metrics_endpoint_invalid_user():
    response = client.get('/api/metrics?user=invalid&days=7')
    assert response.status_code == 404
```

### Integration Tests
- Test full flow: API → GitHub → Response formatting
- Mock GitHub API responses for consistent testing

### Manual Testing Checklist
- [ ] Search with valid user loads data
- [ ] Search with invalid user shows error
- [ ] All collapsible sections work
- [ ] Links open in new tabs
- [ ] Loading states display correctly
- [ ] Error messages are helpful
- [ ] Works in Chrome, Edge, Firefox
- [ ] Mobile responsive (stretch goal)

---

## Future Expansion Path

### Phase 1 (MVP) - Current Scope
- ✅ Single user search
- ✅ 4 main categories with collapsible UI
- ✅ Basic error handling
- ✅ Time period selection

### Phase 2 - Enhanced Features (3-6 months)
- Response caching (SQLite)
- Export to CSV/PDF
- Azure AD authentication
- Dark mode toggle
- Share link functionality
- Activity timeline view (chronological list)

### Phase 3 - Team Features (6-12 months)
- Multi-user comparison
- Team dashboard (aggregate stats)
- Activity trend charts (Chart.js)
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
flask>=3.0.0
python-dotenv>=1.0.0
requests>=2.31.0
waitress>=2.1.2  # For Windows deployment
```

### Frontend (CDN)
```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Optional: Alpine.js (if needed for complex interactions) -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
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
1. **README.md** - Setup and usage guide
2. **In-app help** - Tooltips and FAQs

### For Developers
1. **ARCHITECTURE.md** - This document
2. **API.md** - Detailed API documentation
3. **CONTRIBUTING.md** - How to contribute
4. **Inline code comments** - For complex logic

---

## Success Criteria

### MVP Launch (Phase 1)
- [ ] Dashboard loads in < 3 seconds for 7-day queries
- [ ] UI is intuitive (no training required)
- [ ] Handles 5 concurrent users without issues
- [ ] Zero security vulnerabilities in dependencies
- [ ] 100% uptime during work hours (9am-5pm PT)

### User Satisfaction
- [ ] 80%+ of team uses it regularly
- [ ] < 5 bug reports per month
- [ ] Positive feedback on usability

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
- Issue Comments → `contributions_by()['comments']` (filtered for issues only)
- Issues Labeled → `contributions_by()['issues_labeled']`
- Issues Closed → `contributions_by()['issues_closed']`

**Code Reviews:**
- Review Comments → `contributions_by()['comments']` (filtered for PRs only)
- Reviews Submitted → `contributions_by()['reviews']`
- PRs Merged → `contributions_by()['prs_merged']`
- PRs Closed → `contributions_by()['prs_closed']`

---

## Appendix B: Example Queries

### Get activity for user over 30 days
```bash
curl "http://localhost:5000/api/metrics?user=daxian-dbw&days=30"
```

### Get activity for different repository
```bash
curl "http://localhost:5000/api/metrics?user=daxian-dbw&days=7&owner=Microsoft&repo=vscode"
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | GitHub Copilot | Initial architecture document |

---

## Questions & Decisions Log

### Open Questions
- [ ] Should we support multiple repositories in one view?
- [ ] Do we need user authentication for Phase 1?
- [ ] Should cache be per-user or shared?

### Decisions Made
- ✅ Use Flask over FastAPI (simpler, better for static files)
- ✅ Vanilla JavaScript over React (easier to maintain)
- ✅ 4 categories (per user preference)
- ✅ No visualizations in Phase 1 (focus on functionality)
- ✅ Internal tool first (can expand later)
