#!/usr/bin/env python3
"""Handle a GitHub issue event inside CI: validate, generate infra, and open PR.

This script is intended to be run inside GitHub Actions. It reads the event
payload (JSON) from `--event-path` or the `GITHUB_EVENT_PATH` env var.
If the issue is labeled `auto-provision` it will validate the request via
the local `PolicyEngine` and, if approved, generate infra and open a PR.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from policy_engine.policy import PolicyEngine
from automation.ai_analysis import _parse_request_from_issue
import automation.create_pr as create_pr


def load_event(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", default=os.getenv("GITHUB_EVENT_PATH"))
    parser.add_argument("--live", action="store_true", help="Run live automation and create PR")
    parser.add_argument("--dry-run", action="store_true", help="Do not push or create PR; just simulate")
    args = parser.parse_args()

    # Default to dry-run unless --live is specified, or if --dry-run is explicitly specified
    dry_run = args.dry_run or not args.live

    if not args.event_path:
        print("GITHUB event path must be provided via --event-path or GITHUB_EVENT_PATH", file=sys.stderr)
        sys.exit(2)

    event = load_event(args.event_path)
    issue = event.get("issue") or {}
    labels = [l.get("name") for l in issue.get("labels", [])]
    action = event.get("action")

    if "auto-provision" not in labels:
        print("Label `auto-provision` not present; skipping.")
        return

    title = issue.get("title", "")
    body = issue.get("body", "")
    author = issue.get("user", {}).get("login")

    req = _parse_request_from_issue(title, body, author)

    policy_path = Path(__file__).resolve().parent.parent / "policy_engine" / "policies.yaml"
    engine = PolicyEngine(str(policy_path))
    result = engine.validate(req)
    print("Policy result:", result)

    if not result.get("allowed"):
        print("Request denied by policy; adding comment or skipping.")
        return

    # Generate only the requested env/type
    env_type = req.get("type")
    env_name = req.get("env")
    issue_number = issue.get("number", 0)

    print(f"Generating infra for {env_type}/{env_name}...")
    # Generate with unique identifier per request issue to guarantee changes are detected
    generated_files = create_pr.generate_infra_files(
        env_types=[env_type], 
        env_names=[env_name],
        identifier=f"req{issue_number}"
    )

    branch_name = create_pr.git_branch_name()
    print(f"Branch name would be: {branch_name}")

    if dry_run:
        print("Dry run enabled — not creating branch, committing, or opening PR.")
        print("Generated files:")
        for p in generated_files:
            print(" -", p)
        return

    print(f"Creating branch {branch_name}")
    create_pr.create_git_branch(branch_name)

    print("Committing generated files")
    has_changes = create_pr.commit_generated_files(generated_files, branch_name)
    if not has_changes:
        print("No new changes detected. Skipping PR creation to avoid invalid branch reference.")
        return

    pr_title = f"Auto: add {env_type} {env_name} environment"
    pr_body = f"Generated from issue #{issue_number} by automation. Policy: {result.get('message')}"
    print("Creating PR...")
    create_pr.create_pull_request(branch_name, pr_title, pr_body, base_branch=os.getenv("BASE_BRANCH", "main"))


if __name__ == "__main__":
    main()
