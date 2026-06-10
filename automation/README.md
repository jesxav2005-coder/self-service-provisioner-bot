# Automation / Member 4

This folder contains prototype automation for generated infrastructure and analysis.

## Files

- `create_pr.py`: generates infra files, commits them on a new branch, and opens a GitHub pull request.
- `ai_analysis.py`: provides a simple policy and template analysis report.

## Usage

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Run the analysis prototype:

```bash
python automation/ai_analysis.py
```

3. Create a generated PR locally (requires GitHub credentials and repo access):

```bash
export GITHUB_TOKEN=...            # or set in your environment
export GITHUB_REPOSITORY=owner/repo
python automation/create_pr.py
```

## GitHub Actions

A workflow is included at `.github/workflows/pr_automation.yml` to run this script automatically from GitHub.
