import os
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from github import Github

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
ISSUE_LABEL = "auto-provision"

if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
    raise RuntimeError(
        "GITHUB_TOKEN and GITHUB_REPOSITORY must be set as environment variables to run the UI."
    )

gh = Github(GITHUB_TOKEN)
repo = gh.get_repo(GITHUB_REPOSITORY)


def create_issue(title: str, body: str):
    issue = repo.create_issue(title=title, body=body, labels=[ISSUE_LABEL])
    return issue


# Templates & static
app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "repo": GITHUB_REPOSITORY, "label": ISSUE_LABEL},
    )


@app.post("/submit", response_class=HTMLResponse)
def submit(
    request: Request,
    env_type: str = Form(...),
    env_name: str = Form(...),
    request_details: Optional[str] = Form(""),
    requester: Optional[str] = Form(""),
):
    title = f"Provision {env_type} {env_name}"
    body = ""
    if request_details:
        body += request_details.strip() + "\n\n"
    body += f"Requested by: {requester or 'UI user'}"

    try:
        issue = create_issue(title, body)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "issue": issue, "repo": GITHUB_REPOSITORY},
    )


@app.get("/requests", response_class=HTMLResponse)
def list_requests(request: Request):
    # List recent open issues labeled auto-provision
    issues = list(repo.get_issues(state="open", labels=[ISSUE_LABEL]))
    return templates.TemplateResponse(
        "requests.html", {"request": request, "issues": issues, "repo": GITHUB_REPOSITORY}
    )
