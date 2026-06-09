#!/usr/bin/env python3
"""Create a GitHub issue using PyGithub.

Requires environment variables:
- GITHUB_TOKEN: personal access token or repo token with issues scope
- GITHUB_REPOSITORY: owner/repo (optional if passed via --repo)

Usage:
  python automation/create_issue.py --title "My Issue" --body "Details" --labels bug todo
"""
from github import Github
import os
import sys


def create_issue(title: str, body: str = "", labels=None, repo_full: str | None = None):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN not set in environment")

    repo_full = repo_full or os.getenv("GITHUB_REPOSITORY")
    if not repo_full:
        raise SystemExit("GITHUB_REPOSITORY not set and --repo not provided")

    gh = Github(token)
    repo = gh.get_repo(repo_full)
    issue = repo.create_issue(title=title, body=body, labels=labels or [])
    print(issue.html_url)
    return issue.number


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a GitHub issue for the current repository")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--labels", nargs="*", default=None)
    parser.add_argument("--repo", default=None, help="owner/repo override")

    args = parser.parse_args()
    try:
        num = create_issue(args.title, args.body, args.labels, args.repo)
        print(f"Created issue #{num}")
    except Exception as e:
        print("Error creating issue:", e)
        raise
