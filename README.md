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

## User interface
A simple UI is available at `ui/app.py` to let users submit provisioning requests through a web form.
It creates a GitHub issue labeled `auto-provision` so the existing workflow can run.

Run the UI locally with:

```powershell
$env:GITHUB_TOKEN = "ghp_xxx"
$env:GITHUB_REPOSITORY = "owner/repo"
py -3 -m uvicorn ui.app:app --reload --port 8002
```

Then open `http://localhost:8002` in your browser.

## Issue requests
Use the repository issue template `Auto Provision Request` to create a provisioning request.
The issue should include the requested environment type and name, and be labeled `auto-provision`.

Example request:

- Title: `Provision Docker dev`
- Body: `Please provision docker dev environment for alice.`

## Security
- Use fine-grained tokens and store them as repository secrets for Actions.
- Do not commit tokens or `.env` files with secrets.

## Apply workflow (optional/manual)

When a generated infra PR is merged into the repository, the workflow `.github/workflows/apply_infra.yml` is configured to run. For safety this job is bound to the `production` environment which requires a manual approval by a repository admin or environment approver before the job proceeds.

Notes:
- The current `apply_infra.yml` contains a placeholder step rather than running actual `terraform apply`. Replace the placeholder with your real deployment commands and ensure secrets and environment protections are configured in the repository settings.
- To enable automatic apply you can remove the `environment` requirement, but this is not recommended for production without safeguards.

Required setup to actually run Terraform in CI:

- Add your cloud credentials as repository secrets (example names): `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `GOOGLE_CREDENTIALS`, etc., depending on provider.
- Configure a `production` environment under the repository Settings → Environments and add one or more approvers. The `apply_infra.yml` job uses this environment to require manual approval before performing `terraform apply`.
- Ensure the `generated/` folder contains a valid Terraform configuration at merge time (the automation creates these files in the PR).

Local smoke test (recommended):

```powershell
# Start the policy engine
py -3 -m uvicorn policy_engine.main:app --reload --port 8001

# Run the handler in dry-run to see generated files
py -3 automation/handle_issue.py --event-path sample-event.json --dry-run

# Inspect the generated files
dir generated

# If you want to try terraform locally (requires terraform installed):
cd generated
terraform init
terraform plan
terraform apply -auto-approve
```

*** End Patch