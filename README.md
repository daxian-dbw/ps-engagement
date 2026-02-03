# GitHub Maintainer Activity Dashboard

A web dashboard for visualizing GitHub maintainer activity across issues, pull requests, code reviews, and issue triage.

## Features

- **Single User Search**: Search for any GitHub user's activity in a repository
- **Time Period Selection**: View activity over 1, 3, 7, 14, 30, 90, or 180 days
- **Timezone-Aware**: Automatically detects your timezone and interprets date boundaries correctly
- **Four Activity Categories**:
  - 📝 Issues Opened
  - 🚀 Pull Requests Opened
  - 🔧 Issue Triage & Investigation (comments, labels, closures)
  - 👀 Code Reviews (comments, reviews, PR merges/closures)
- **Collapsible UI**: Expand/collapse categories for better organization
- **Persistent State**: Remembers your search preferences across sessions

## Prerequisites

- Python 3.8 or higher
- GitHub Personal Access Token ([create one here](https://github.com/settings/tokens))
- Git (for cloning the repository)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ps-engagement
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   
   Windows (PowerShell):
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
   
   Windows (Command Prompt):
   ```cmd
   .venv\Scripts\activate.bat
   ```
   
   Linux/macOS:
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GITHUB_TOKEN=your_github_token_here
   GITHUB_OWNER=PowerShell
   GITHUB_REPO=PowerShell
   DEFAULT_DAYS_BACK=7
   ```

   **Required:**
   - `GITHUB_TOKEN`: Your GitHub Personal Access Token (needs `repo` and `read:org` scopes)
   
   **Optional:**
   - `GITHUB_OWNER`: Default repository owner (default: "PowerShell")
   - `GITHUB_REPO`: Default repository name (default: "PowerShell")
   - `DEFAULT_DAYS_BACK`: Default time period in days (default: 7)

## Running the Application

1. **Ensure your virtual environment is activated**

2. **Start the Flask development server**
   ```bash
   python app.py
   ```

3. **Open your browser**
   
   Navigate to: [http://localhost:5001](http://localhost:5001)

4. **Use the dashboard**
   - Enter a GitHub username in the search box
   - Select a time period (default is 7 days)
   - Click "Go" to view activity
   - Click category headers to expand/collapse details

## Troubleshooting

### GitHub Token Issues

**Error: "Configuration Error: GITHUB_TOKEN is required"**
- Ensure your `.env` file exists and contains `GITHUB_TOKEN=your_token`
- Verify the token has the required scopes (`repo`, `read:org`)
- Check that the `.env` file is in the project root directory

### Rate Limiting

**Error: "Rate limit exceeded"**
- GitHub API has rate limits (5,000 requests/hour for authenticated requests)
- Wait a few minutes before trying again
- Check your rate limit status: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit`

### User Not Found

**Error: "User not found"**
- Verify the username is spelled correctly
- Ensure the user has public activity in the repository
- Check that the user exists on GitHub

### Port Already in Use

**Error: "Address already in use"**
- Another application is using port 5001
- Stop the other application or change the port in [app.py](app.py) by modifying `app.run(port=5001)`

### No Activity Displayed

- The user may not have activity in the selected time period
- Try a longer time period (e.g., 30 or 90 days)
- Verify the user has activity in the repository by checking GitHub directly

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

With coverage report:
```bash
pytest tests/ --cov=api --cov=app --cov-report=term-missing -v
```

## Project Structure

```
ps-engagement/
├── app.py                  # Flask application entry point
├── config.py              # Configuration management
├── collect_metrics.py     # Metrics collection module
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── api/                   # API endpoints
│   ├── routes.py          # API route definitions
│   └── response_formatter.py  # Response formatting
├── github_events/         # GitHub API integration
│   └── github_events.py   # Event collection logic
├── static/                # Static assets
│   ├── css/
│   └── js/
├── templates/             # HTML templates
│   ├── base.html
│   └── index.html
└── tests/                 # Test suite
    ├── test_api.py
    └── test_error_handling.py
```

## Known Limitations

- **Single Repository**: Phase 1 focuses on activity within one repository at a time
- **Public Activity Only**: Only displays public GitHub activity
- **No User Authentication**: Anyone with the URL can access the dashboard
- **Rate Limits**: Subject to GitHub API rate limits (5,000 requests/hour)

## License

[Specify license information]

## Contributing

[Specify contribution guidelines]
