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
PS_TEAM_MEMBERS: set[str] = {"SeeminglyScience", "TravisEz13", "adityapatwardhan", "daxian-dbw", "jshigetomi", "SteveL-MSFT", "anamnavi", "sdwheeler", "theJasonHelmick"}
PS_CONTRIBUTORS: set[str] = {"iSazonov", "jborean93", "MartinGC94", "mklement0", "kilasuit", "237dmitry", "jhoneill", "doctordns" }


# --- GraphQL documents -----------------------------------------------------
# Query to fetch issue and PR comments made by a specific user.
# Uses backward pagination (last/before) to retrieve comments in reverse chronological order.
# Returns comment metadata including the associated issue/PR details and repository information.
#
# The default order for 'issueComments' in the GitHub GraphQL API is typically sorted by creation
# time in ascending order (oldest comments first). So, I use `last` and `before` to get the most
# recent records first.
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

# Query to fetch PR review contributions made by a specific user within a date range.
# Retrieves reviews from the user's contributions collection with forward pagination (first/after).
# Uses server-side date filtering via contributionsCollection(from, to) for efficient querying.
# Returns review metadata including PR details, review state, and repository information.
#
# The pullRequestReviewContributions field is a connection that orders contributions by default in
# descending chronological order (most recent contributions first). So, I use `first` and `after` to
# get the most recent records first.
PR_REVIEW_QUERY_PAGINATED = """
query($username: String!, $fromDate: DateTime!, $toDate: DateTime!, $count: Int = 100, $after: String) {
  user(login: $username) {
    contributionsCollection(from: $fromDate, to: $toDate) {
      pullRequestReviewContributions(first: $count, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
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

# Query to search for issues in a repository within a date range using the GitHub search API.
# Uses search query syntax for server-side date range filtering (updated:FROM..TO).
# Returns issue details including timeline events for label and close actions.
ISSUE_ACTIVITY_QUERY = """
query($searchQuery: String!, $pageSize: Int = 100, $cursor: String) {
  search(query: $searchQuery, type: ISSUE, first: $pageSize, after: $cursor) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Issue {
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
              closer {
                __typename
                ... on PullRequest {
                  number
                  url
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

# Query to search for pull requests in a repository within a date range using the GitHub search API.
# Uses search query syntax for server-side date range filtering (updated:FROM..TO).
# Returns PR details including timeline events for close and merge actions.
PR_ACTIVITY_QUERY = """
query($searchQuery: String!, $pageSize: Int = 100, $cursor: String) {
  search(query: $searchQuery, type: ISSUE, first: $pageSize, after: $cursor) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on PullRequest {
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

# Query to search for issues in a repository created within a date range for team engagement analysis.
# Uses GitHub search API with server-side date range filtering (created:FROM..TO).
# Returns issue details including comments and timeline events (labels, closes) needed for team engagement metrics.
TEAM_ISSUES_ENGAGEMENT_QUERY = """
query($searchQuery: String!, $pageSize: Int = 100, $cursor: String) {
  search(query: $searchQuery, type: ISSUE, first: $pageSize, after: $cursor) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Issue {
        number
        title
        url
        createdAt
        state
        author {
          login
        }
        
        comments(first: 100) {
          nodes {
            author { login }
            createdAt
          }
        }
        
        timelineItems(first: 100, itemTypes: [LABELED_EVENT, CLOSED_EVENT]) {
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
              closer {
                __typename
                ... on PullRequest {
                  number
                  url
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


# Query to search for PRs in a repository created within a date range for team engagement analysis.
# Uses GitHub search API with server-side date range filtering (created:FROM..TO).
# Returns PR details including comments, reviews, and timeline events (merged, closed) needed for team engagement metrics.
TEAM_PRS_ENGAGEMENT_QUERY = """
query($searchQuery: String!, $pageSize: Int = 100, $cursor: String) {
  search(query: $searchQuery, type: ISSUE, first: $pageSize, after: $cursor) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on PullRequest {
        number
        title
        url
        createdAt
        author {
          login
        }
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
    """Convert date string into a naive datetime object.
    
    Args:
        date_str: Date string in the format of '2026-01-12T18:44:56Z'.
    
    Returns:
        A naive datetime (no timezone info)
    """
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")


def _check_issue_engagement(issue: Dict, team_members: set[str], debug: bool = False) -> bool:
    """
    Check if an issue has team engagement and collect close information.
    
    Criteria for engagement:
    - Has comment from any team member
    - Has "Resolution-*" label applied by any team member
    - Was closed by any team member
    
    Args:
        issue: Issue data from GraphQL
        team_members: Set of team member GitHub usernames
        debug: If True, print debugging messages about engagement found
    
    Returns:
        True if issue has team engagement, False otherwise
    """
    issue_number = issue.get("number")
    
    # Check labels (Resolution-* labels) and close events
    timeline = issue.get("timelineItems", {}).get("nodes", [])
    for event in timeline:
        event_type = event.get("__typename")
        
        if event_type == "LabeledEvent":
            actor = event.get("actor", {}).get("login")
            label_name = event.get("label", {}).get("name", "")
            # An issue reviewed by WG is considered engaged by the team.
            if label_name == "WG-Reviewed":
                if debug:
                    print(f"Issue #{issue_number}: engagement='label', actor='{actor}', label='WG-Reviewed'")
                return True
            
            if actor in team_members and label_name.startswith("Resolution-"):
                if debug:
                    print(f"Issue #{issue_number}: engagement='label', actor='{actor}', label='{label_name}'")
                return True
        
        elif event_type == "ClosedEvent":
            actor = event.get("actor", {}).get("login")
            if actor in team_members:
                if debug:
                    print(f"Issue #{issue_number}: engagement='close', actor='{actor}'")
                return True
    
    # Check comments
    comments = issue.get("comments", {}).get("nodes", [])
    for comment in comments:
        author = comment.get("author", {}).get("login")
        if author in team_members:
            if debug:
                print(f"Issue #{issue_number}: engagement='comment', actor='{author}'")
            return True
    
    return False


def _check_pr_engagement(pr: Dict, team_members: set[str], debug: bool = False) -> bool:
    """
    Check if a PR has team engagement.
    
    Criteria:
    - Has comment from any team member
    - Has review from any team member
    - Was merged by any team member
    - Was closed by any team member
    
    Args:
        pr: PR data from GraphQL
        team_members: Set of team member GitHub usernames
        debug: If True, print debugging messages about engagement found
    
    Returns:
        True if PR has team engagement, False otherwise
    """
    pr_number = pr.get("number")
    
    # Check merge/close events
    timeline = pr.get("timelineItems", {}).get("nodes", [])
    for event in timeline:
        event_type = event.get("__typename")
        if event_type in ["MergedEvent", "ClosedEvent"]:
            actor = event.get("actor", {}).get("login")
            if actor in team_members:
                if debug:
                    action = "merged" if event_type == "MergedEvent" else "closed"
                    print(f"PR #{pr_number}: engagement='{action}', actor='{actor}'")
                return True
    
    # Check comments
    comments = pr.get("comments", {}).get("nodes", [])
    for comment in comments:
        author = comment.get("author", {}).get("login")
        if author in team_members:
            if debug:
                print(f"PR #{pr_number}: engagement='comment', actor='{author}'")
            return True
    
    # Check reviews
    reviews = pr.get("reviews", {}).get("nodes", [])
    for review in reviews:
        author = review.get("author", {}).get("login")
        if author in team_members:
            if debug:
                review_state = review.get("state", "")
                print(f"PR #{pr_number}: engagement='review', actor='{author}', state='{review_state}'")
            return True
    
    return False


# --- Issue comment queries --------------------------------------------------
def get_issue_and_pr_comments_by(
    actor_login: str,
    from_date: datetime,
    to_date: datetime,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> List[Dict]:
    """Fetch issue and PR comments by `actor_login` within a date range.
    
    Args:
        actor_login: GitHub username to fetch comments for
        from_date: Start of date range (inclusive) - required
        to_date: End of date range (inclusive) - required
        owner: Repository owner
        repo: Repository name
        
    Returns:
        List of comment dictionaries within the specified date range
        
    Example:
        from datetime import datetime, timedelta
        from_dt = datetime.utcnow() - timedelta(days=30)
        to_dt = datetime.utcnow()
        comments = get_issue_and_pr_comments_by("username", from_dt, to_dt)
    """
    collected: List[Dict] = []
    cursor: Optional[str] = None
    repo_full = f"{owner}/{repo}"
    actor = actor_login.lower()

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
            # Ignore comments in other repos.
            issue = comment.get("issue", {})
            if issue.get("repository", {}).get("nameWithOwner") != repo_full:
                continue
            
            published_at = comment.get("publishedAt")
            if not published_at:
                continue
            
            comment_dt = _parse_date(published_at)
            
            # Check if before start date - stop pagination
            if comment_dt < from_date:
                stop_paging = True
                continue
            
            # Check if after end date - skip but continue pagination
            if comment_dt > to_date:
                continue
            
            pr = comment.get("pullRequest")
            if pr:
                # This is a PR comment - check if user is the PR author.
                # We need to check the issue field for author info.
                issue_author = (issue.get("author") or {}).get("login")
                # Skip comment on user's own PR.
                if issue_author and issue_author.lower() == actor:
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
    from_date: datetime,
    to_date: datetime,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> List[Dict]:
    """Fetch PR reviews by `actor_login` within a date range.
    
    Args:
        actor_login: GitHub username to fetch reviews for
        from_date: Start of date range (inclusive) - required
        to_date: End of date range (inclusive) - required
        owner: Repository owner
        repo: Repository name
        
    Returns:
        List of review dictionaries within the specified date range
        
    Note:
        Uses server-side date filtering for efficient querying.
    """
    collected: List[Dict] = []
    cursor: Optional[str] = None
    repo_full = f"{owner}/{repo}"
    actor = actor_login.lower()
    
    # Convert datetime to ISO format for GraphQL
    from_iso = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_iso = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    while True:
        variables = {
            "username": actor_login,
            "fromDate": from_iso,
            "toDate": to_iso,
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
        
        # Server-side filtering handles date range, only filter by repository
        for review in nodes:
            # Skip reviews in other repos.
            if review.get("repository", {}).get("nameWithOwner") != repo_full:
                continue
            
            pr = review.get("pullRequest") or {}
            pr_author = (pr.get("author") or {}).get("login")
            # Skip review on the user's own PR.
            if pr_author and pr_author.lower() == actor:
                continue
            
            collected.append(review)
        
        page_info = conn.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    
    return collected


# --- Repository activity helpers -------------------------------------------
def _fetch_recent_issues(owner: str, repo: str, from_date: datetime, page_size: int = 50) -> List[Dict]:
    """Fetch issues updated since the specified date using GitHub search API.
    
    Args:
        owner: Repository owner
        repo: Repository name
        from_date: Start of date range (inclusive)
        page_size: Number of results per page
        
    Returns:
        List of issue dictionaries matching the date range
    """
    cursor: Optional[str] = None
    results: List[Dict] = []
    
    # Format dates for GitHub search query
    from_iso = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Construct search query: 'repo:owner/repo type:issue sort:updated-desc updated:>=FROM'
    # Note: Using only lower bound (>=from_date) because GitHub's updated filter checks the last
    # update time. An issue could have relevant activity within our date range but been updated
    # again later. Client-side filtering on timeline events handles the upper bound.
    # Not specifying state qualifier includes both open and closed issues.
    # sort:updated-desc ensures results are ordered by UPDATED_AT in descending order.
    search_query = f"repo:{owner}/{repo} type:issue sort:updated-desc updated:>={from_iso}"
    
    while True:
        variables = {
            "searchQuery": search_query,
            "pageSize": page_size,
            "cursor": cursor,
        }
        data = _graphql_request(ISSUE_ACTIVITY_QUERY, variables)
        search_data = data.get("search")
        if not search_data:
            break
        
        nodes = search_data.get("nodes") or []
        results.extend(nodes)
        
        page_info = search_data.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    
    return results


def _fetch_recent_prs(owner: str, repo: str, from_date: datetime, page_size: int = 50) -> List[Dict]:
    """Fetch pull requests updated within a date range using GitHub search API.
    
    Args:
        owner: Repository owner
        repo: Repository name
        from_date: Start of date range (inclusive)
        page_size: Number of results per page
        
    Returns:
        List of PR dictionaries matching the date range
    """
    cursor: Optional[str] = None
    results: List[Dict] = []
    
    # Format dates for GitHub search query
    from_iso = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Construct search query: repo:owner/repo type:pr sort:updated-desc updated:>=FROM
    # Note: Using only lower bound (>=from_date) because GitHub's updated filter checks the last
    # update time. A PR could have relevant activity within our date range but been updated
    # again later. Client-side filtering on timeline events handles the upper bound.
    # Not specifying state qualifier includes all states (open, closed, merged).
    # sort:updated-desc ensures results are ordered by UPDATED_AT in descending order
    search_query = f"repo:{owner}/{repo} type:pr sort:updated-desc updated:>={from_iso}"
    
    while True:
        variables = {
            "searchQuery": search_query,
            "pageSize": page_size,
            "cursor": cursor,
        }
        data = _graphql_request(PR_ACTIVITY_QUERY, variables)
        search_data = data.get("search")
        if not search_data:
            break
        
        nodes = search_data.get("nodes") or []
        results.extend(nodes)
        
        page_info = search_data.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    
    return results


def issue_activities_by(
    actor_login: str,
    from_date: datetime,
    to_date: datetime,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> Dict[str, List[Dict]]:
    """Fetch issues opened, labeled Resolution-*/WG-*, and closed by `actor_login` within a date range.
    
    Args:
        actor_login: GitHub username to fetch activities for
        from_date: Start of date range (inclusive) - required
        to_date: End of date range (inclusive) - required
        owner: Repository owner
        repo: Repository name

    Returns:
        Dict with keys 'open', 'label', and 'close', each containing a list of matching issues.
        Note: Label and close events are not collected for issues opened by the same user.
    """
    actor = actor_login.lower()
    opened_matches: List[Dict] = []
    labeled_matches: List[Dict] = []
    closed_matches: List[Dict] = []

    for issue in _fetch_recent_issues(owner, repo, from_date):
        issue_created_at = issue.get("createdAt")
        if not issue_created_at:
          continue

        # If the issue was opened after the upper bound, ignore it.
        issue_created_dt = _parse_date(issue_created_at)
        if issue_created_dt > to_date:
            continue

        # Check if user is the author of the issue
        issue_author = (issue.get("author") or {}).get("login")
        if issue_author and issue_author.lower() == actor and issue_created_dt >= from_date:
            # If user opened the issue, add to opened_matches
            opened_matches.append(
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "url": issue["url"],
                    "createdAt": issue_created_at,
                }
            )
            # Continue to collect label/close events for issues opened by the user

        # Check for label/close events
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
                        if created_at:
                            created_dt = _parse_date(created_at)
                            if from_date <= created_dt <= to_date:
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

            # Check for closure (exclude PR-triggered closes)
            elif typename == "ClosedEvent" and not closed_found:
                event_actor = (event.get("actor") or {}).get("login")
                if event_actor and event_actor.lower() == actor:
                    # Skip PR-triggered closes
                    closer = event.get("closer")
                    if closer and closer.get("__typename") == "PullRequest":
                        continue
                    
                    created_at = event.get("createdAt")
                    if created_at:
                        created_dt = _parse_date(created_at)
                        if from_date <= created_dt <= to_date:
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


def pr_activities_by(
    actor_login: str,
    from_date: datetime,
    to_date: datetime,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> List[Dict]:
    """Fetch PRs opened, closed, and merged by `actor_login` within a date range.
    
    Args:
        actor_login: GitHub username to fetch activities for
        from_date: Start of date range (inclusive) - required
        to_date: End of date range (inclusive) - required
        owner: Repository owner
        repo: Repository name
        
    Returns:
        List of PR activity dictionaries with action type and occurrence timestamp
        
    Example:
        from datetime import datetime, timedelta
        from_dt = datetime.utcnow() - timedelta(days=30)
        to_dt = datetime.utcnow()
        activities = pr_activities_by("username", from_dt, to_dt)
    """
    actor = actor_login.lower()
    matches: List[Dict] = []
    for pr in _fetch_recent_prs(owner, repo, from_date):
        pr_created_at = pr.get("createdAt")
        if not pr_created_at:
            continue
        
        # If the PR was opened after the upper bound, ignore it.
        pr_created_dt = _parse_date(pr_created_at)
        if pr_created_dt > to_date:
            continue

        # Check if user is the author of the PR
        pr_author = (pr.get("author") or {}).get("login")
        if pr_author and pr_author.lower() == actor and pr_created_dt >= from_date:
            matches.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr["url"],
                    "action": "opened",
                    "state": pr["state"],
                    "occurredAt": pr_created_at,
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
            
            created_at = event.get("createdAt")
            if not created_at:
                continue
            
            created_dt = _parse_date(created_at)
            if not (from_date <= created_dt <= to_date):
                continue
            
            matches.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr["url"],
                    "action": "merged" if typename == "MergedEvent" else "closed",
                    "occurredAt": created_at,
                }
            )
            break

    return matches


def contributions_by(
    actor_login: str,
    from_date: datetime,
    to_date: datetime,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
) -> Dict[str, List[Dict]]:
    """Aggregate all contribution data for a user.
    
    Args:
        actor_login: GitHub username to fetch contributions for
        from_date: Start of date range (inclusive) - required
        to_date: End of date range (inclusive) - required
        owner: Repository owner
        repo: Repository name

    Returns:
        Dict with keys:
        - 'comments': Issue/PR comments
        - 'reviews': PR reviews
        - 'issues_opened': Issues opened by the user
        - 'issues_labeled': Issues labeled Resolution-*/WG-* by the user
        - 'issues_closed': Issues manually closed by the user
        - 'prs_opened': PRs opened by the user
        - 'prs_merged': PRs merged by the user
        - 'prs_closed': PRs closed by the user
        
    Example:
        from datetime import datetime, timedelta
        from_dt = datetime.utcnow() - timedelta(days=30)
        to_dt = datetime.utcnow()
        data = contributions_by("username", from_dt, to_dt)
    """
    # Collect all raw data in parallel for better performance
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all independent data collection tasks
        future_comments = executor.submit(get_issue_and_pr_comments_by, actor_login, from_date, to_date, owner, repo)
        future_reviews = executor.submit(get_pr_reviews_by, actor_login, from_date, to_date, owner, repo)
        future_issue_activities = executor.submit(issue_activities_by, actor_login, from_date, to_date, owner, repo)
        future_pr_activities = executor.submit(pr_activities_by, actor_login, from_date, to_date, owner, repo)

        # Wait for all results to complete
        comments = future_comments.result()
        reviews = future_reviews.result()
        issue_activities = future_issue_activities.result()
        pr_activities = future_pr_activities.result()

    # Separate PR activities by action type
    prs_opened = []
    prs_merged = []
    prs_closed = []

    for pr_activity in pr_activities:
        action = pr_activity.get("action")
        if action == "opened":
            prs_opened.append(pr_activity)
        elif action == "merged":
            prs_merged.append(pr_activity)
        elif action == "closed":
            prs_closed.append(pr_activity)

    return {
        "comments": comments,
        "reviews": reviews,
        "issues_opened": issue_activities.get("open", []),
        "issues_labeled": issue_activities.get("label", []),
        "issues_closed": issue_activities.get("close", []),
        "prs_opened": prs_opened,
        "prs_merged": prs_merged,
        "prs_closed": prs_closed,
    }


# --- Team engagement functions ---------------------------------------------
def get_team_issue_engagement(
    from_date: datetime,
    to_date: datetime,
    team_members: set[str] = PS_TEAM_MEMBERS,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Calculate team engagement ratio for issues created within a date range.
    
    Args:
        team_members: Set of GitHub usernames for team members
        from_date: Start of date range (inclusive) - required
        to_date: End of date range (inclusive) - required
        owner: Repository owner
        repo: Repository name
        debug: If True, print debugging messages about engagement found
    
    Returns:
        Dictionary with:
        - total_issues: Total issues opened in timeframe
        - team_engaged: Number of issues with team engagement
        - team_unattended: Number of issues without team engagement
        - engagement_ratio: Ratio of engaged issues (0.0 to 1.0)
        - manually_closed: Number of issues manually closed by team
        - pr_triggered_closed: Number of issues closed by PR merge
        - closed_ratio: Ratio of closed issues (manual + PR-triggered) to total (0.0 to 1.0)
        - engaged_issues: List of engaged issue details
        - unattended_issues: List of unattended issue details
        - manually_closed_issues: List of manually closed issue details
        - pr_triggered_closed_issues: List of PR-triggered closed issue details
    """
    all_issues = []
    cursor = None

    # Format dates for GitHub search query
    from_iso = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_iso = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Construct search query: includes both open and closed issues, ordered by created DESC
    # created:FROM..TO filters by creation date range
    search_query = f"repo:{owner}/{repo} type:issue created:{from_iso}..{to_iso} sort:created-desc"
    
    # Fetch all issues created in timeframe using search API
    while True:
        variables = {
            "searchQuery": search_query,
            "pageSize": 100,
            "cursor": cursor,
        }
        data = _graphql_request(TEAM_ISSUES_ENGAGEMENT_QUERY, variables)
        search_data = data.get("search")
        if not search_data:
            break
        
        nodes = search_data.get("nodes") or []
        all_issues.extend(nodes)
        
        page_info = search_data.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    
    # Analyze engagement and close types
    engaged_issues = []
    unattended_issues = []
    manually_closed_issues = []
    pr_triggered_closed_issues = []
    
    for issue in all_issues:
        is_engaged = _check_issue_engagement(issue, team_members, debug)
        
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
        
        # Check for close events (only if issue is currently closed)
        # We want to collect metrics about closed issues (manually vs. PR merge, by anyone).
        if issue.get("state") == "CLOSED":
            # Find the LAST ClosedEvent by a team member (issue could be closed/reopened multiple times)
            timeline = issue.get("timelineItems", {}).get("nodes", [])
            last_close_event = None
            
            for event in timeline:
                if event.get("__typename") == "ClosedEvent":
                    # Store this event (will keep the last one)
                    last_close_event = event
            
            # Process the last close event if found
            if last_close_event:
                actor = last_close_event.get("actor", {}).get("login")
                closer = last_close_event.get("closer")
                
                close_info = {
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "url": issue.get("url"),
                    "closed_by": actor
                }
                
                # Check if closed by PR or manually
                if closer and closer.get("__typename") == "PullRequest":
                    # PR-triggered close
                    close_info["pr_number"] = closer.get("number")
                    close_info["pr_url"] = closer.get("url")
                    pr_triggered_closed_issues.append(close_info)
                else:
                    # Manual close
                    manually_closed_issues.append(close_info)
    
    total = len(all_issues)
    engaged = len(engaged_issues)
    unattended = len(unattended_issues)
    ratio = engaged / total if total > 0 else 0.0
    manually_closed = len(manually_closed_issues)
    pr_triggered_closed = len(pr_triggered_closed_issues)
    total_closed = manually_closed + pr_triggered_closed
    closed_ratio = total_closed / total if total > 0 else 0.0
    
    return {
        "total_issues": total,
        "team_engaged": engaged,
        "team_unattended": unattended,
        "engagement_ratio": ratio,
        "manually_closed": manually_closed,
        "pr_triggered_closed": pr_triggered_closed,
        "closed_ratio": closed_ratio,
        "engaged_issues": engaged_issues,
        "unattended_issues": unattended_issues,
        "manually_closed_issues": manually_closed_issues,
        "pr_triggered_closed_issues": pr_triggered_closed_issues
    }


def get_team_pr_engagement(
    from_date: datetime,
    to_date: datetime,
    team_members: set[str] = PS_TEAM_MEMBERS,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Calculate team engagement ratio for PRs created within a date range.
    
    Args:
        team_members: Set of GitHub usernames for team members
        from_date: Start of date range (inclusive) - required
        to_date: End of date range (inclusive) - required
        owner: Repository owner
        repo: Repository name
        debug: If True, print debugging messages about engagement found
    
    Returns:
        Dictionary with:
        - total_prs: Total PRs opened in timeframe
        - team_engaged: Number of PRs with team engagement
        - team_unattended: Number of PRs without team engagement
        - engagement_ratio: Ratio of engaged PRs (0.0 to 1.0)
        - merged: Number of PRs merged by team
        - closed: Number of PRs closed (without merge) by team
        - engaged_prs: List of engaged PR details
        - unattended_prs: List of unattended PR details
        - merged_prs: List of merged PR details
        - closed_prs: List of closed PR details
    """
    # Format dates for GitHub search query
    from_iso = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_iso = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Construct search query: includes open, closed, and merged PRs, ordered by created DESC
    # created:FROM..TO filters by creation date range
    search_query = f"repo:{owner}/{repo} type:pr created:{from_iso}..{to_iso} sort:created-desc"
    
    all_prs = []
    cursor = None
    
    # Fetch all PRs created in timeframe using search API
    while True:
        variables = {
            "searchQuery": search_query,
            "pageSize": 100,
            "cursor": cursor,
        }
        data = _graphql_request(TEAM_PRS_ENGAGEMENT_QUERY, variables)
        search_data = data.get("search")
        if not search_data:
            break
        
        nodes = search_data.get("nodes") or []
        all_prs.extend(nodes)
        
        page_info = search_data.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
    
    # Analyze engagement and merge/close actions
    engaged_prs = []
    unattended_prs = []
    merged_prs = []
    closed_prs = []
    
    for pr in all_prs:
        is_engaged = _check_pr_engagement(pr, team_members, debug)
        
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
        
        # Check PR state to categorize merged vs closed, by anyone
        state = pr.get("state")
        if state == "MERGED":
            merged_prs.append(pr_info)
        elif state == "CLOSED":
            closed_prs.append(pr_info)
    
    total = len(all_prs)
    engaged = len(engaged_prs)
    unattended = len(unattended_prs)
    ratio = engaged / total if total > 0 else 0.0
    merged = len(merged_prs)
    closed = len(closed_prs)
    finish_ratio = (closed + merged) / total if total > 0 else 0.0
    
    return {
        "total_prs": total,
        "team_engaged": engaged,
        "team_unattended": unattended,
        "engagement_ratio": ratio,
        "merged": merged,
        "closed": closed,
        "finish_ratio": finish_ratio,
        "engaged_prs": engaged_prs,
        "unattended_prs": unattended_prs,
        "merged_prs": merged_prs,
        "closed_prs": closed_prs
    }


def get_team_engagement(
    from_date: datetime,
    to_date: datetime,
    team_members: set[str] = PS_TEAM_MEMBERS,
    owner: str = TARGET_OWNER,
    repo: str = TARGET_REPO,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Calculate team engagement for both issues and PRs in parallel.
    
    Args:
        from_date: Start of date range (inclusive) - required
        to_date: End of date range (inclusive) - required
        team_members: Set of GitHub usernames for team members
        owner: Repository owner
        repo: Repository name
        debug: If True, print debugging messages about engagement found
    
    Returns:
        Dictionary with:
        - issue: Results from get_team_issue_engagement
        - pr: Results from get_team_pr_engagement
    """
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_issues = executor.submit(get_team_issue_engagement, from_date, to_date, team_members, owner, repo, debug)
        future_prs = executor.submit(get_team_pr_engagement, from_date, to_date, team_members, owner, repo, debug)
        
        issue_engagement = future_issues.result()
        pr_engagement = future_prs.result()
    
    return {
        "issue": issue_engagement,
        "pr": pr_engagement
    }


__all__ = [
    "PS_TEAM_MEMBERS",
    "PS_CONTRIBUTORS",
    "get_issue_and_pr_comments_by",
    "get_pr_reviews_by",
    "issue_activities_by",
    "pr_activities_by",
    "contributions_by",
    "get_team_issue_engagement",
    "get_team_pr_engagement",
    "get_team_engagement",
]
