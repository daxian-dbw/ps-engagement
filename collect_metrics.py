"""Command-line entrypoint to collect GitHub activity metrics for a maintainer."""
from __future__ import annotations

import os
from typing import Iterable, Mapping

from github_events import (
    contributions_by,
    get_issue_and_pr_comments_by,
    get_pr_reviews_by,
    issue_activities_by,
    pr_activities_by,
    get_team_engagement,
    get_team_issue_engagement,
    get_team_pr_engagement,
)

DEFAULT_USER = os.getenv("METRICS_USER", "daxian-dbw")
DEFAULT_DAYS_BACK = int(os.getenv("METRICS_DAYS_BACK", "30"))


def _print_section(title: str, rows: Iterable[Mapping]):
    rows = list(rows)
    print(f"\n=== {title} ({len(rows)}) ===")
    if not rows:
        print("No data found.")
        return
    for row in rows:
        line = " | ".join(f"{key}={value}" for key, value in row.items())
        print(f"- {line}")


def _validate_individual_functions(user: str, days_back: int):
    comments = get_issue_and_pr_comments_by(user, days_back)
    reviews = get_pr_reviews_by(user, days_back)
    issue_activity = issue_activities_by(user, days_back)
    resolution_issues = issue_activity["label"]
    closed_issues = issue_activity["close"]
    prs = pr_activities_by(user, days_back)

    _print_section(
        "Issue / PR Comments",
        (
            {
                "publishedAt": comment.get("publishedAt"),
                "url": comment.get("url"),
                "issue": f"#{comment.get('issue', {}).get('number')} {comment.get('issue', {}).get('title')}",
            }
            for comment in comments
        ),
    )
    _print_section(
        "PR Reviews",
        (
            {
                "occurredAt": review.get("occurredAt"),
                "pr": f"#{review.get('pullRequest', {}).get('number')} {review.get('pullRequest', {}).get('title')}",
                "state": (review.get("pullRequestReview") or {}).get("state"),
                "url": (review.get("pullRequestReview") or {}).get("url"),
            }
            for review in reviews
        ),
    )
    _print_section(
        "Issues Labeled Resolution-*",
        (
            {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "label": issue.get("label"),
                "labeledAt": issue.get("labeledAt"),
                "url": issue.get("url"),
            }
            for issue in resolution_issues
        ),
    )
    _print_section(
        "Issues Closed",
        (
            {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "closedAt": issue.get("closedAt"),
                "url": issue.get("url"),
            }
            for issue in closed_issues
        ),
    )
    _print_section(
        "PRs Opened / Closed / Merged",
        (
            {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "action": pr.get("action"),
                "occurredAt": pr.get("occurredAt"),
                "url": pr.get("url"),
            }
            for pr in prs
        ),
    )


def _validate_contributions_by(user: str, days_back: int):
    # === Filtered contributions for comparison ===
    print("\n" + "="*80)
    print("FILTERED CONTRIBUTIONS (using contributions_by)")
    print("="*80)

    contributions = contributions_by(user, days_back)

    _print_section(
        "[FILTERED] Issue / PR Comments",
        (
            {
                "publishedAt": comment.get("publishedAt"),
                "url": comment.get("url"),
                ("pr" if comment.get("pullRequest") else "issue"): f"#{comment.get('issue', {}).get('number')} {comment.get('issue', {}).get('title')}",
            }
            for comment in contributions["comments"]
        ),
    )
    _print_section(
        "[FILTERED] PR Reviews",
        (
            {
                "occurredAt": review.get("occurredAt"),
                "pr": f"#{review.get('pullRequest', {}).get('number')} {review.get('pullRequest', {}).get('title')}",
                "state": (review.get("pullRequestReview") or {}).get("state"),
                "url": (review.get("pullRequestReview") or {}).get("url"),
            }
            for review in contributions["reviews"]
        ),
    )
    _print_section(
        "[FILTERED] Issues Closed",
        (
            {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "closedAt": issue.get("closedAt"),
                "url": issue.get("url"),
            }
            for issue in contributions["issues_closed"]
        ),
    )
    _print_section(
        "[FILTERED] PRs Opened",
        (
            {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "action": pr.get("action"),
                "occurredAt": pr.get("occurredAt"),
                "url": pr.get("url"),
                "state": pr.get("state"),
            }
            for pr in contributions["prs_opened"]
        ),
    )
    _print_section(
        "[FILTERED] PRs Merged",
        (
            {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "action": pr.get("action"),
                "occurredAt": pr.get("occurredAt"),
                "url": pr.get("url"),
            }
            for pr in contributions["prs_merged"]
        ),
    )
    _print_section(
        "[FILTERED] PRs Closed",
        (
            {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "action": pr.get("action"),
                "occurredAt": pr.get("occurredAt"),
                "url": pr.get("url"),
            }
            for pr in contributions["prs_closed"]
        ),
    )


def _validate_get_team_issue_engagement(days_back: int):
    # === Validate get_team_issue_engagement ===
    print("\n" + "="*80)
    print("VALIDATE get_team_issue_engagement")
    print("="*80)
    
    issue_engagement = get_team_issue_engagement(days_back=days_back)
    print(f"\nTotal Issues: {issue_engagement['total_issues']}")
    print(f"Team Engaged: {issue_engagement['team_engaged']}")
    print(f"Team Unattended: {issue_engagement['team_unattended']}")
    print(f"Engagement Ratio: {issue_engagement['engagement_ratio']:.2%}")
    print(f"Manually Closed: {issue_engagement['manually_closed']}")
    print(f"PR-Triggered Closed: {issue_engagement['pr_triggered_closed']}")
    print(f"Closed Ratio: {issue_engagement['closed_ratio']:.2%}")
    
    print(f"\n--- Engaged Issues ({len(issue_engagement['engaged_issues'])}) ---")
    for issue in issue_engagement['engaged_issues'][:5]:  # Show first 5
        title = issue['title'][:60] + ('...' if len(issue['title']) > 60 else '')
        print(f"  #{issue['number']}: {title} - {issue['url']}")
    
    print(f"\n--- Unattended Issues ({len(issue_engagement['unattended_issues'])}) ---")
    for issue in issue_engagement['unattended_issues'][:5]:  # Show first 5
        title = issue['title'][:60] + ('...' if len(issue['title']) > 60 else '')
        print(f"  #{issue['number']}: {title} - {issue['url']}")
    
    print(f"\n--- Manually Closed Issues ({len(issue_engagement['manually_closed_issues'])}) ---")
    for issue in issue_engagement['manually_closed_issues'][:5]:  # Show first 5
        title = issue['title'][:60] + ('...' if len(issue['title']) > 60 else '')
        print(f"  #{issue['number']}: {title} - Closed by {issue.get('closed_by', 'N/A')}")
    
    print(f"\n--- PR-Triggered Closed Issues ({len(issue_engagement['pr_triggered_closed_issues'])}) ---")
    for issue in issue_engagement['pr_triggered_closed_issues'][:5]:  # Show first 5
        title = issue['title'][:60] + ('...' if len(issue['title']) > 60 else '')
        print(f"  #{issue['number']}: {title} - Closed by PR #{issue.get('pr_number', 'N/A')}")


def _validate_get_team_pr_engagement(days_back: int):
    # === Validate get_team_pr_engagement ===
    print("\n" + "="*80)
    print("VALIDATE get_team_pr_engagement")
    print("="*80)
    
    pr_engagement = get_team_pr_engagement(days_back=days_back)
    print(f"\nTotal PRs: {pr_engagement['total_prs']}")
    print(f"Team Engaged: {pr_engagement['team_engaged']}")
    print(f"Team Unattended: {pr_engagement['team_unattended']}")
    print(f"Engagement Ratio: {pr_engagement['engagement_ratio']:.2%}")
    print(f"Merged: {pr_engagement['merged']}")
    print(f"Closed: {pr_engagement['closed']}")
    print(f"Finish Ratio: {pr_engagement['finish_ratio']:.2%}")
    
    print(f"\n--- Engaged PRs ({len(pr_engagement['engaged_prs'])}) ---")
    for pr in pr_engagement['engaged_prs'][:5]:  # Show first 5
        title = pr['title'][:60] + ('...' if len(pr['title']) > 60 else '')
        print(f"  #{pr['number']}: {title} - {pr['url']}")
    
    print(f"\n--- Unattended PRs ({len(pr_engagement['unattended_prs'])}) ---")
    for pr in pr_engagement['unattended_prs'][:5]:  # Show first 5
        title = pr['title'][:60] + ('...' if len(pr['title']) > 60 else '')
        print(f"  #{pr['number']}: {title} - {pr['url']}")
    
    print(f"\n--- Merged PRs ({len(pr_engagement['merged_prs'])}) ---")
    for pr in pr_engagement['merged_prs'][:5]:  # Show first 5
        title = pr['title'][:60] + ('...' if len(pr['title']) > 60 else '')
        print(f"  #{pr['number']}: {title} - {pr['url']}")
    
    print(f"\n--- Closed PRs ({len(pr_engagement['closed_prs'])}) ---")
    for pr in pr_engagement['closed_prs'][:5]:  # Show first 5
        title = pr['title'][:60] + ('...' if len(pr['title']) > 60 else '')
        print(f"  #{pr['number']}: {title} - {pr['url']}")


def _valdiate_get_team_engagement(days_back: int):
    # === Team Engagement ===
    print("\n" + "="*80)
    print("TEAM ENGAGEMENT")
    print("="*80)
    
    engagement = get_team_engagement(days_back=days_back)
    
    # Print Issue Engagement
    issue_data = engagement["issue"]
    print(f"\n--- Issue Engagement ---")
    print(f"Total Issues: {issue_data['total_issues']}")
    print(f"Team Engaged: {issue_data['team_engaged']}")
    print(f"Team Unattended: {issue_data['team_unattended']}")
    print(f"Engagement Ratio: {issue_data['engagement_ratio']:.2%}")
    print(f"Manually Closed: {issue_data['manually_closed']}")
    print(f"PR-Triggered Closed: {issue_data['pr_triggered_closed']}")
    print(f"Close Ratio: {issue_data['closed_ratio']:.2%}")
    
    # Print PR Engagement
    pr_data = engagement["pr"]
    print(f"\n--- PR Engagement ---")
    print(f"Total PRs: {pr_data['total_prs']}")
    print(f"Team Engaged: {pr_data['team_engaged']}")
    print(f"Team Unattended: {pr_data['team_unattended']}")
    print(f"Engagement Ratio: {pr_data['engagement_ratio']:.2%}")
    print(f"Merged: {pr_data['merged']}")
    print(f"Closed: {pr_data['closed']}")
    print(f"Finish Ratio: {pr_data['finish_ratio']:.2%}")


def main(user: str = DEFAULT_USER, days_back: int = DEFAULT_DAYS_BACK):
    print(f"Collecting GitHub activity for {user} over the past {days_back} days...")

    # _validate_individual_functions(user, days_back)
    # _validate_contributions_by(user, days_back)
    # _validate_get_team_issue_engagement(days_back)
    # _validate_get_team_pr_engagement(days_back)
    _valdiate_get_team_engagement(days_back)


if __name__ == "__main__":
    main()
