"""Command-line entrypoint to collect GitHub activity metrics for a maintainer."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Iterable, Mapping

DEFAULT_USER = os.getenv("METRICS_USER", "daxian-dbw")
DEFAULT_DAYS_BACK = int(os.getenv("METRICS_DAYS_BACK", "10"))

MODULE_PATH = Path(__file__).with_name("github-events.py")
MODULE_SPEC = importlib.util.spec_from_file_location("github_events", MODULE_PATH)
if MODULE_SPEC is None or MODULE_SPEC.loader is None:
    raise ImportError(f"Unable to load github-events module from {MODULE_PATH}")
github_events = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(github_events)  # type: ignore[attr-defined]


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

    comments = github_events.get_issue_and_pr_comments_by(user, days_back)
    reviews = github_events.get_pr_reviews_by(user, days_back)
    resolution_issues = github_events.issues_labeled_resolution_by(user, days_back)
    closed_issues = github_events.issues_closed_by(user, days_back)
    prs = github_events.prs_closed_or_merged_by(user, days_back)

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


if __name__ == "__main__":
    main()
