# Self-Service Provisioner Bot

This repository contains automation to accept issue-based requests, validate them against a policy engine, generate infrastructure templates, and open PRs with the generated files.

## Quick start (local)

1. Create and export a GitHub token (for local testing only):

```powershell
$env:GITHUB_TOKEN = "ghp_xxx"
$env:GITHUB_REPOSITORY = "owner/repo"
```

2. Start the policy engine:

```powershell
py -3 -m uvicorn policy_engine.main:app --reload --port 8001
```

3. Run the automation handler in dry-run mode (safe):

```powershell
py -3 automation/handle_issue.py --event-path sample-event.json --dry-run
```

4. To perform an actual run (will push and open PR), ensure `GITHUB_TOKEN` and `GITHUB_REPOSITORY` are set and run without `--dry-run`.

## GitHub Actions
The workflow `.github/workflows/auto_provision.yml` triggers on issues labeled `auto-provision` and runs the handler in the Actions runner.

## Security
- Use fine-grained tokens and store them as repository secrets for Actions.
- Do not commit tokens or `.env` files with secrets.

*** End Patch