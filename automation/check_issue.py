#!/usr/bin/env python3
"""Check a GitHub issue's status using PyGithub.

Usage:
  python automation/check_issue.py --number 12
"""
from github import Github
import os
import sys


def get_issue(number: int, repo_full: str | None = None):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN not set in environment")

    repo_full = repo_full or os.getenv("GITHUB_REPOSITORY")
    if not repo_full:
        raise SystemExit("GITHUB_REPOSITORY not set and --repo not provided")

    gh = Github(token)
    repo = gh.get_repo(repo_full)
    issue = repo.get_issue(number)
    print(f"Issue #{issue.number}: {issue.title}\nState: {issue.state}\nURL: {issue.html_url}")
    if issue.labels:
        print("Labels:", ", ".join(l.name for l in issue.labels))
    return issue


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check a GitHub issue")
    parser.add_argument("--number", type=int, required=True)
    parser.add_argument("--repo", default=None, help="owner/repo override")

    args = parser.parse_args()
    try:
        get_issue(args.number, args.repo)
    except Exception as e:
        print("Error fetching issue:", e)
        raise
