"""Utility functions for collecting GitHub activity metrics via GraphQL."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests


# --- Configuration ---------------------------------------------------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TARGET_OWNER = os.getenv("GITHUB_OWNER", "PowerShell")
TARGET_REPO = os.getenv("GITHUB_REPO", "PowerShell")
TARGET_REPO_FULL = f"{TARGET_OWNER}/{TARGET_REPO}"
DEFAULT_DAYS_BACK = int(os.getenv("GITHUB_DAYS_BACK", "30"))


# --- GraphQL documents -----------------------------------------------------
ISSUE_COMMENT_QUERY_PAGINATED = """
query($username: String!, $count: Int = 100, $before: String) {
  user(login: $username) {
    issueComments(last: $count, before: $before) {
      pageInfo {
        hasPreviousPage
        startCursor
      }
      nodes {
        publishedAt
        url
        issue {
          author {
            login
          }
          repository {
            nameWithOwner
          }
          publishedAt
          number
          title
        }
        pullRequest {
          merged
        }
      }
    }
  }
}
"""

PR_REVIEW_QUERY_PAGINATED = """
query($username: String!, $count: Int = 100, $after: String) {
  user(login: $username) {
    contributionsCollection {
      pullRequestReviewContributions(first: $count, after: $after) {
        pageInfo {
          hasPreviousPage
          startCursor
        }
        nodes {
          occurredAt
          pullRequest {
            author {
              login
            }
            publishedAt
            number
            title
            merged
          }
          pullRequestReview {
            url
            state
          }
          repository {
            nameWithOwner
          }
        }
      }
    }
  }
}
"""

REPO_ACTIVITY_QUERY = """
query(
  $owner: String!,
  $repo: String!,
  $since: DateTime!,
  $issuesPageSize: Int = 50,
  $issuesCursor: String,
  $prsPageSize: Int = 50,
  $prsCursor: String,
  $includeIssues: Boolean! = true,
  $includePRs: Boolean! = true
) {
  repository(owner: $owner, name: $repo) {
    issues(
      first: $issuesPageSize,
      after: $issuesCursor,
      orderBy: {field: UPDATED_AT, direction: DESC},
      filterBy: {since: $since}
    ) @include(if: $includeIssues) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        url
        createdAt
        updatedAt
        author {
          login
        }
        timelineItems(last: 50, itemTypes: [LABELED_EVENT, CLOSED_EVENT]) {
          nodes {
            __typename
            ... on LabeledEvent {
              createdAt
              actor { login }
              label { name }
            }
            ... on ClosedEvent {
              createdAt
              actor { login }
            }
          }
        }
      }
    }
    pullRequests(
      first: $prsPageSize,
      after: $prsCursor,
      orderBy: {field: UPDATED_AT, direction: DESC},
      states: [OPEN, CLOSED, MERGED]
    ) @include(if: $includePRs) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        url
        state
        createdAt
        updatedAt
        author {
          login
        }
        timelineItems(last: 50, itemTypes: [CLOSED_EVENT, MERGED_EVENT]) {
          nodes {
            __typename
            ... on ClosedEvent {
              createdAt
              actor { login }
            }
            ... on MergedEvent {
              createdAt
              actor { login }
            }
          }
        }
      }
    }
  }
}
"""

TEAM_ISSUES_ENGAGEMENT_QUERY = """
query(
  $owner: String!,
  $repo: String!,
  $since: DateTime!,
  $cursor: String,
  $pageSize: Int = 100
) {
  repository(owner: $owner, name: $repo) {
    issues(
      first: $pageSize,
      after: $cursor,
      filterBy: {since: $since},
      orderBy: {field: CREATED_AT, direction: DESC}
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        url
        createdAt
        author { login }
        
        comments(first: 100) {
          nodes {
            author { login }
            createdAt
          }
        }
        
        timelineItems(first: 100, itemTypes: [LABELED_EVENT]) {
          nodes {
            __typename
            ... on LabeledEvent {
              createdAt
              actor { login }
              label { name }
            }
          }
        }
      }
    }
  }
}
"""

TEAM_PRS_ENGAGEMENT_QUERY = """
query(
  $owner: String!,
  $repo: String!,
  $since: DateTime!,
  $cursor: String,
  $pageSize: Int = 100
) {
  repository(owner: $owner, name: $repo) {
    pullRequests(
      first: $pageSize,
      after: $cursor,
      orderBy: {field: CREATED_AT, direction: DESC}
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        url
        createdAt
        author { login }
        state
        
        comments(first: 100) {
          nodes {
            author { login }
            createdAt
          }
        }
        
        reviews(first: 100) {
          nodes {
            author { login }
            createdAt
            state
          }
        }
        
        timelineItems(first: 50, itemTypes: [MERGED_EVENT, CLOSED_EVENT]) {
          nodes {
            __typename
            ... on MergedEvent {
              createdAt
              actor { login }
            }
            ... on ClosedEvent {
              createdAt
              actor { login }
            }
          }
        }
      }
    }
  }
}
"""


# --- Helpers ----------------------------------------------------------------
def _require_token(token: str = GITHUB_TOKEN) -> str:
    if not token:
        raise RuntimeError("Set the GITHUB_TOKEN environment variable to call the GitHub API.")
    return token


def _graphql_request(query: str, variables: Dict, token: str | None = None) -> Dict:
    headers = {"Authorization": f"Bearer {_require_token(token or GITHUB_TOKEN)}"}
    response = requests.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"GraphQL query failed: {response.status_code} {response.text}")
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload.get("data", {})


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")


def _since_datetime(days_back: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days_back)


def _check_issue_engagement(issue: Dict, team_members: List[str]) -> bool:
    """
    Check if an issue has team engagement.
    
    Criteria:
    - Has comment from any team member
    - Has "Resolution-*" label applied by any team member
    
    Args:
        issue: Issue data from GraphQL
        team_members: List of team member GitHub usernames
    
    Returns:
        True if issue has team engagement, False otherwise
    """
    team_set = set(team_members)
    
    # Check comments
    comments = issue.get("comments", {}).get("nodes", [])
    for comment in comments:
        author = comment.get("author", {}).get("login")
        if author in team_set:
            return True
    
    # Check labels (Resolution-* labels)
    timeline = issue.get("timelineItems", {}).get("nodes", [])
    for event in timeline:
        if event.get("__typename") == "LabeledEvent":
            actor = event.get("actor", {}).get("login")
            label_name = event.get("label", {}).get("name", "")
            
            if actor in team_set and label_name.startswith("Resolution-"):
                return True
    
    return False


def _check_pr_engagement(pr: Dict, team_members: List[str]) -> bool:
    """
    Check if a PR has team engagement.
    
    Criteria:
    - Has comment from any team member
    - Has review from any team member
    - Was merged by any team member
    - Was closed by any team member
    
    Args:
        pr: PR data from GraphQL
        team_members: List of team member GitHub usernames
    
    Returns:
        True if PR has team engagement, False otherwise
    """
    team_set = set(team_members)
    
    # Check comments
    comments = pr.get("comments", {}).get("nodes", [])
    for comment in comments:
        author = comment.get("author", {}).get("login")
        if author in team_set:
            return True
    
    # Check reviews
    reviews = pr.get("reviews", {}).get("nodes", [])
    for review in reviews:
        author = review.get("author", {}).get("login")
        if author in team_set:
            return True
    
    # Check merge/close events
    timeline = pr.get("timelineItems", {}).get("nodes", [])
    for event in timeline:
        event_type = event.get("__typename")
        if event_type in ["MergedEvent", "ClosedEvent"]:
            actor = event.get("actor", {}).get("login")
            if actor in team_set:
                return True
    
    return False


# --- Issue comment queries --------------------------------------------------
def get_issue_and_pr_comments_by(
    actor_login: str,
    days_back: int = DEFAULT_DAYS_BACK,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> List[Dict]:
    """Fetch recent issue comments for `actor_login` limited by a time window."""
    collected: List[Dict] = []
    cursor: Optional[str] = None
    repo_full = f"{owner}/{repo}"
    since_dt = _since_datetime(days_back)
    while True:
        variables = {
            "username": actor_login,
            "count": 100,
            "before": cursor,
        }
        data = _graphql_request(ISSUE_COMMENT_QUERY_PAGINATED, variables)
        user = data.get("user")
        if not user:
            break
        conn = user["issueComments"]
        nodes = conn.get("nodes") or []
        stop_paging = False
        for comment in nodes:
            if comment.get("issue", {}).get("repository", {}).get("nameWithOwner") != repo_full:
                continue
            published_at = comment.get("publishedAt")
            if not published_at or _parse_date(published_at) < since_dt:
                stop_paging = True
                continue
            collected.append(comment)
        if stop_paging:
            break
        page_info = conn.get("pageInfo") or {}
        if not page_info.get("hasPreviousPage"):
            break
        cursor = page_info.get("startCursor")
    return collected


# --- PR review queries ------------------------------------------------------
def get_pr_reviews_by(
  actor_login: str,
  days_back: int = DEFAULT_DAYS_BACK,
  owner: str = TARGET_OWNER,
  repo: str = TARGET_REPO,
) -> List[Dict]:
  """Fetch PR reviews performed by `actor_login` within the requested window."""
  collected: List[Dict] = []
  cursor: Optional[str] = None
  repo_full = f"{owner}/{repo}"
  since_dt = _since_datetime(days_back)
  while True:
    variables = {
      "username": actor_login,
      "count": 100,
      "after": cursor,
    }
    data = _graphql_request(PR_REVIEW_QUERY_PAGINATED, variables)
    user = data.get("user")
    if not user:
      break
    contributions = user.get("contributionsCollection") or {}
    conn = contributions.get("pullRequestReviewContributions")
    if not conn:
      break
    nodes = conn.get("nodes") or []
    stop_paging = False
    for review in nodes:
      if review.get("repository", {}).get("nameWithOwner") != repo_full:
        continue
      occurred_at = review.get("occurredAt")
      if not occurred_at or _parse_date(occurred_at) < since_dt:
        stop_paging = True
        continue
      collected.append(review)
    if stop_paging:
      break
    page_info = conn.get("pageInfo") or {}
    if not page_info.get("hasPreviousPage"):
      break
    cursor = page_info.get("startCursor")
  return collected


# --- Repository activity helpers -------------------------------------------
def _fetch_recent_issues(owner: str, repo: str, since_dt: datetime, page_size: int = 50) -> List[Dict]:
    cursor: Optional[str] = None
    results: List[Dict] = []
    iso_since = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    while True:
        variables = {
            "owner": owner,
            "repo": repo,
            "since": iso_since,
            "issuesPageSize": page_size,
            "issuesCursor": cursor,
            "includeIssues": True,
            "includePRs": False,
        }
        data = _graphql_request(REPO_ACTIVITY_QUERY, variables)
        repo_data = data.get("repository")
        conn = repo_data.get("issues") if repo_data else None
        if not conn:
            break
        for issue in conn.get("nodes", []):
            if _parse_date(issue["updatedAt"]) < since_dt:
                return results
            results.append(issue)
        page_info = conn.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    return results


def _fetch_recent_prs(owner: str, repo: str, since_dt: datetime, page_size: int = 50) -> List[Dict]:
    cursor: Optional[str] = None
    results: List[Dict] = []
    iso_since = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    while True:
        variables = {
            "owner": owner,
            "repo": repo,
            "since": iso_since,
            "prsPageSize": page_size,
            "prsCursor": cursor,
            "includeIssues": False,
            "includePRs": True,
        }
        data = _graphql_request(REPO_ACTIVITY_QUERY, variables)
        repo_data = data.get("repository")
        conn = repo_data.get("pullRequests") if repo_data else None
        if not conn:
            break
        for pr in conn.get("nodes", []):
            if _parse_date(pr["updatedAt"]) < since_dt:
                return results
            results.append(pr)
        page_info = conn.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    return results


def issue_activities_by(
    actor_login: str,
    days_back: int = DEFAULT_DAYS_BACK,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> Dict[str, List[Dict]]:
    """Fetch issues opened, labeled Resolution-*/WG-*, and closed by `actor_login` in a single pass.

    Returns a dict with keys 'open', 'label', and 'close', each containing a list of matching issues.
    Note: Label and close events are not collected for issues opened by the same user.
    """
    since_dt = _since_datetime(days_back)
    actor = actor_login.lower()
    opened_matches: List[Dict] = []
    labeled_matches: List[Dict] = []
    closed_matches: List[Dict] = []

    for issue in _fetch_recent_issues(owner, repo, since_dt):
        # Check if user is the author of the issue
        issue_author = (issue.get("author") or {}).get("login")
        if issue_author and issue_author.lower() == actor:
            # If user opened the issue, add to opened_matches
            created_at = issue.get("createdAt")
            if created_at and _parse_date(created_at) >= since_dt:
                opened_matches.append(
                    {
                        "number": issue["number"],
                        "title": issue["title"],
                        "url": issue["url"],
                        "createdAt": created_at,
                    }
                )
            # Continue to collect label/close events for issues opened by the user

        # For issues not opened by the user, check for label/close events
        events = (issue.get("timelineItems") or {}).get("nodes") or []
        labeled_found = False
        closed_found = False

        for event in events:
            typename = event.get("__typename")

            # Check for Resolution-* or WG-* labeling
            if typename == "LabeledEvent" and not labeled_found:
                label = (event.get("label") or {}).get("name") or ""
                event_actor = (event.get("actor") or {}).get("login")
                if (label.startswith("Resolution-") or label.startswith("WG-")) and event_actor:
                    if event_actor.lower() == actor:
                        created_at = event.get("createdAt")
                        if created_at and _parse_date(created_at) >= since_dt:
                            labeled_matches.append(
                                {
                                    "number": issue["number"],
                                    "title": issue["title"],
                                    "url": issue["url"],
                                    "label": label,
                                    "labeledAt": created_at,
                                }
                            )
                            labeled_found = True

            # Check for closure
            elif typename == "ClosedEvent" and not closed_found:
                event_actor = (event.get("actor") or {}).get("login")
                if event_actor and event_actor.lower() == actor:
                    created_at = event.get("createdAt")
                    if created_at and _parse_date(created_at) >= since_dt:
                        closed_matches.append(
                            {
                                "number": issue["number"],
                                "title": issue["title"],
                                "url": issue["url"],
                                "closedAt": created_at,
                            }
                        )
                        closed_found = True

            # Early exit if both found
            if labeled_found and closed_found:
                break

    return {
        "open": opened_matches,
        "label": labeled_matches,
        "close": closed_matches,
    }

def prs_opened_or_closed_or_merged_by(
    actor_login: str,
    days_back: int = DEFAULT_DAYS_BACK,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> List[Dict]:
    since_dt = _since_datetime(days_back)
    actor = actor_login.lower()
    matches: List[Dict] = []
    for pr in _fetch_recent_prs(owner, repo, since_dt):
        # Check if user is the author of the PR
        pr_author = (pr.get("author") or {}).get("login")
        if pr_author and pr_author.lower() == actor:
            # Use createdAt for when the PR was opened
            created_at = pr.get("createdAt")
            if created_at and _parse_date(created_at) >= since_dt:
                matches.append(
                    {
                        "number": pr["number"],
                        "title": pr["title"],
                        "url": pr["url"],
                        "action": "opened",
                        "state": pr["state"],
                        "occurredAt": created_at,
                    }
                )
            # Continue to collect the close/merge event for prs opened by the user.

        # Check timeline for close/merge actions by the user
        events = (pr.get("timelineItems") or {}).get("nodes") or []
        for event in events:
            typename = event.get("__typename")
            if typename not in {"ClosedEvent", "MergedEvent"}:
                continue
            event_actor = (event.get("actor") or {}).get("login")
            if not event_actor or event_actor.lower() != actor:
                continue
            if _parse_date(event["createdAt"]) < since_dt:
                continue
            matches.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr["url"],
                    "action": "merged" if typename == "MergedEvent" else "closed",
                    "occurredAt": event["createdAt"],
                }
            )
            break
    return matches


def contributions_by(
    actor_login: str,
    days_back: int = DEFAULT_DAYS_BACK,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> Dict[str, List[Dict]]:
    """Aggregate all contribution data for a user with filtering rules applied.

    Returns a dict with keys:
    - 'comments': Issue/PR comments (excluding comments on user's own PRs)
    - 'reviews': PR reviews (excluding reviews on user's own PRs)
    - 'issues_opened': Issues opened by the user
    - 'issues_labeled': Issues labeled Resolution-*/WG-* by the user
    - 'issues_closed': Issues manually closed by the user (excluding PR-triggered closes)
    - 'prs_opened': PRs opened by the user
    - 'prs_merged': PRs merged by the user
    - 'prs_closed': PRs closed by the user
    """
    actor = actor_login.lower()

    # Collect all raw data in parallel for better performance
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all independent data collection tasks
        future_comments = executor.submit(get_issue_and_pr_comments_by, actor_login, days_back, owner, repo)
        future_reviews = executor.submit(get_pr_reviews_by, actor_login, days_back, owner, repo)
        future_issue_activities = executor.submit(issue_activities_by, actor_login, days_back, owner, repo)
        future_pr_activities = executor.submit(prs_opened_or_closed_or_merged_by, actor_login, days_back, owner, repo)

        # Wait for all results to complete
        comments = future_comments.result()
        reviews = future_reviews.result()
        issue_activities = future_issue_activities.result()
        pr_activities = future_pr_activities.result()

    # Filter PR comments: exclude comments on user's own PRs
    filtered_comments = []
    for comment in comments:
        pr = comment.get("pullRequest")
        if pr:
            # This is a PR comment - check if user is the PR author
            # We need to check the issue field for author info
            issue = comment.get("issue")
            if issue:
                issue_author = (issue.get("author") or {}).get("login")
                if issue_author and issue_author.lower() == actor:
                    continue  # Skip comment on user's own PR
        filtered_comments.append(comment)

    # Filter PR reviews: exclude reviews on user's own PRs
    filtered_reviews = []
    for review in reviews:
        pr = review.get("pullRequest") or {}
        pr_author = (pr.get("author") or {}).get("login")
        if pr_author and pr_author.lower() == actor:
            continue  # Skip review on user's own PR
        filtered_reviews.append(review)

    # Separate PR activities by action type
    prs_opened = []
    prs_merged = []
    prs_closed = []
    pr_merge_times = []  # Track merge times (as datetime objects) for filtering issue closes

    for pr_activity in pr_activities:
        action = pr_activity.get("action")
        if action == "opened":
            prs_opened.append(pr_activity)
        elif action == "merged":
            prs_merged.append(pr_activity)
            merge_time = pr_activity.get("occurredAt")
            if merge_time:
                pr_merge_times.append(_parse_date(merge_time))
        elif action == "closed":
            prs_closed.append(pr_activity)

    # Filter issue close events: exclude PR-triggered closes
    issues_closed = []
    for close_event in issue_activities.get("close", []):
        closed_at = close_event.get("closedAt")
        if closed_at and pr_merge_times:
            closed_dt = _parse_date(closed_at)
            is_pr_triggered = False

            for merge_dt in pr_merge_times:
                # Check if issue was closed within 3 seconds after PR merge
                time_diff = (closed_dt - merge_dt).total_seconds()
                if 0 <= time_diff <= 3:
                    is_pr_triggered = True
                    break

            if is_pr_triggered:
                continue  # Skip PR-triggered close

        issues_closed.append(close_event)

    return {
        "comments": filtered_comments,
        "reviews": filtered_reviews,
        "issues_opened": issue_activities.get("open", []),
        "issues_labeled": issue_activities.get("label", []),
        "issues_closed": issues_closed,
        "prs_opened": prs_opened,
        "prs_merged": prs_merged,
        "prs_closed": prs_closed,
    }


# --- Team engagement functions ---------------------------------------------
def get_team_issue_engagement(
    team_members: List[str],
    days_back: int = DEFAULT_DAYS_BACK,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> Dict[str, Any]:
    """
    Calculate team engagement ratio for issues opened in the past N days.
    
    Args:
        team_members: List of GitHub usernames for team members
        days_back: Number of days to look back
        owner: Repository owner
        repo: Repository name
    
    Returns:
        Dictionary with:
        - total_issues: Total issues opened in timeframe
        - team_engaged: Number of issues with team engagement
        - team_unattended: Number of issues without team engagement
        - engagement_ratio: Ratio of engaged issues (0.0 to 1.0)
        - engaged_issues: List of engaged issue details
        - unattended_issues: List of unattended issue details
    """
    since_dt = _since_datetime(days_back)
    iso_since = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    all_issues = []
    cursor = None
    
    # Fetch all issues created in timeframe
    while True:
        variables = {
            "owner": owner,
            "repo": repo,
            "since": iso_since,
            "cursor": cursor,
            "pageSize": 100
        }
        data = _graphql_request(TEAM_ISSUES_ENGAGEMENT_QUERY, variables)
        repo_data = data.get("repository", {})
        issues_conn = repo_data.get("issues", {})
        nodes = issues_conn.get("nodes", [])
        
        # Filter issues created after since_dt (filterBy might include updated)
        for issue in nodes:
            created_at = issue.get("createdAt")
            if created_at and _parse_date(created_at) >= since_dt:
                all_issues.append(issue)
        
        page_info = issues_conn.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    
    # Analyze engagement
    engaged_issues = []
    unattended_issues = []
    
    for issue in all_issues:
        is_engaged = _check_issue_engagement(issue, team_members)
        
        issue_info = {
            "number": issue.get("number"),
            "title": issue.get("title"),
            "url": issue.get("url"),
            "created_at": issue.get("createdAt"),
            "author": issue.get("author", {}).get("login")
        }
        
        if is_engaged:
            engaged_issues.append(issue_info)
        else:
            unattended_issues.append(issue_info)
    
    total = len(all_issues)
    engaged = len(engaged_issues)
    unattended = len(unattended_issues)
    ratio = engaged / total if total > 0 else 0.0
    
    return {
        "total_issues": total,
        "team_engaged": engaged,
        "team_unattended": unattended,
        "engagement_ratio": ratio,
        "engaged_issues": engaged_issues,
        "unattended_issues": unattended_issues
    }


def get_team_pr_engagement(
    team_members: List[str],
    days_back: int = DEFAULT_DAYS_BACK,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> Dict[str, Any]:
    """
    Calculate team engagement ratio for PRs opened in the past N days.
    
    Args:
        team_members: List of GitHub usernames for team members
        days_back: Number of days to look back
        owner: Repository owner
        repo: Repository name
    
    Returns:
        Dictionary with:
        - total_prs: Total PRs opened in timeframe
        - team_engaged: Number of PRs with team engagement
        - team_unattended: Number of PRs without team engagement
        - engagement_ratio: Ratio of engaged PRs (0.0 to 1.0)
        - engaged_prs: List of engaged PR details
        - unattended_prs: List of unattended PR details
    """
    since_dt = _since_datetime(days_back)
    iso_since = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    all_prs = []
    cursor = None
    
    # Fetch all PRs created in timeframe
    while True:
        variables = {
            "owner": owner,
            "repo": repo,
            "since": iso_since,
            "cursor": cursor,
            "pageSize": 100
        }
        data = _graphql_request(TEAM_PRS_ENGAGEMENT_QUERY, variables)
        repo_data = data.get("repository", {})
        prs_conn = repo_data.get("pullRequests", {})
        nodes = prs_conn.get("nodes", [])
        
        # Filter PRs created after since_dt
        for pr in nodes:
            created_at = pr.get("createdAt")
            if created_at and _parse_date(created_at) >= since_dt:
                all_prs.append(pr)
        
        page_info = prs_conn.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    
    # Analyze engagement
    engaged_prs = []
    unattended_prs = []
    
    for pr in all_prs:
        is_engaged = _check_pr_engagement(pr, team_members)
        
        pr_info = {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "url": pr.get("url"),
            "created_at": pr.get("createdAt"),
            "author": pr.get("author", {}).get("login"),
            "state": pr.get("state")
        }
        
        if is_engaged:
            engaged_prs.append(pr_info)
        else:
            unattended_prs.append(pr_info)
    
    total = len(all_prs)
    engaged = len(engaged_prs)
    unattended = len(unattended_prs)
    ratio = engaged / total if total > 0 else 0.0
    
    return {
        "total_prs": total,
        "team_engaged": engaged,
        "team_unattended": unattended,
        "engagement_ratio": ratio,
        "engaged_prs": engaged_prs,
        "unattended_prs": unattended_prs
    }


__all__ = [
    "get_issue_and_pr_comments_by",
    "get_pr_reviews_by",
    "issue_activities_by",
    "prs_opened_or_closed_or_merged_by",
    "contributions_by",
    "get_team_issue_engagement",
    "get_team_pr_engagement",
]
