"""Command-line entrypoint to collect GitHub activity metrics for a maintainer."""
from __future__ import annotations

import os
from typing import Iterable, Mapping

from github_events import (
    contributions_by,
    get_issue_and_pr_comments_by,
    get_pr_reviews_by,
    issue_activities_by,
    prs_opened_or_closed_or_merged_by,
)

DEFAULT_USER = os.getenv("METRICS_USER", "daxian-dbw")
DEFAULT_DAYS_BACK = int(os.getenv("METRICS_DAYS_BACK", "10"))


def _print_section(title: str, rows: Iterable[Mapping]):
    rows = list(rows)
    print(f"\n=== {title} ({len(rows)}) ===")
    if not rows:
        print("No data found.")
        return
    for row in rows:
        line = " | ".join(f"{key}={value}" for key, value in row.items())
        print(f"- {line}")


def main(user: str = DEFAULT_USER, days_back: int = DEFAULT_DAYS_BACK):
    print(f"Collecting GitHub activity for {user} over the past {days_back} days...")

    comments = get_issue_and_pr_comments_by(user, days_back)
    reviews = get_pr_reviews_by(user, days_back)
    issue_activity = issue_activities_by(user, days_back)
    resolution_issues = issue_activity["label"]
    closed_issues = issue_activity["close"]
    prs = prs_opened_or_closed_or_merged_by(user, days_back)

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
        "PRs Closed / Merged",
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


if __name__ == "__main__":
    main()
