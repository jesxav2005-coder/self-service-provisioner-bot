import os
from typing import Optional

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from github import Github

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
ISSUE_LABEL = "auto-provision"

if GITHUB_TOKEN and GITHUB_REPOSITORY:
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(GITHUB_REPOSITORY)
else:
    gh = None
    repo = None
    if not GITHUB_REPOSITORY:
        GITHUB_REPOSITORY = "your-org/your-repo"


def create_issue(title: str, body: str):
    if not repo:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_TOKEN and GITHUB_REPOSITORY are required to create issues. Set them before submitting."
        )
    return repo.create_issue(title=title, body=body, labels=[ISSUE_LABEL])


@app.get("/", response_class=HTMLResponse)
def index():
    if repo:
        total_requests = len(list(repo.get_issues(state="all", labels=[ISSUE_LABEL])))
        open_requests = len(list(repo.get_issues(state="open", labels=[ISSUE_LABEL])))
        closed_requests = total_requests - open_requests
        open_prs = len(list(repo.get_pulls(state="open")))
    else:
        total_requests = 0
        open_requests = 0
        closed_requests = 0
        open_prs = 0

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Self-Service Provisioner Bot</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.4/css/all.min.css" rel="stylesheet" integrity="sha512-ZG4t9GkN6+/+V7dMj3+GVhaEhD+Rcv+/IYxKlBbL4xXyM3tq1W/zKcAhTsy3EZErUnp/yY0i2lKwpPqjv4jUSg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
  <style>
    :root {{ font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; color: #111827; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%); }}
    a {{ color: #2563eb; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .page {{ width: min(1200px, 100%); margin: 0 auto; padding: 2rem 1rem 3rem; }}
    .hero {{ background: linear-gradient(135deg, #2563eb, #9333ea); border-radius: 32px; color: white; padding: 2.25rem 2rem; box-shadow: 0 35px 90px rgba(37, 99, 235, 0.18); margin-bottom: 2rem; position: relative; overflow: hidden; }}
    .hero::before {{ content: ''; position: absolute; top: -30px; right: -30px; width: 220px; height: 220px; background: rgba(255,255,255,0.12); border-radius: 50%; }}
    .hero-header {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: 1rem; align-items: flex-start; }}
    .hero-title {{ margin: 0; font-size: clamp(2.5rem, 3.5vw, 3.4rem); line-height: 1.02; }}
    .hero-subtitle {{ margin: 1rem 0 0; color: rgba(255,255,255,0.88); max-width: 720px; font-size: 1.05rem; }}
    .stats-grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 1.75rem; }}
    .stat-card {{ border-radius: 26px; padding: 1.5rem; background: rgba(255,255,255,0.1); backdrop-filter: blur(18px); border: 1px solid rgba(255,255,255,0.24); box-shadow: 0 30px 60px rgba(15, 23, 42, 0.1); }}
    .stat-card h3 {{ margin: 0 0 0.75rem; font-size: 0.95rem; color: rgba(255,255,255,0.86); }}
    .stat-card p {{ margin: 0; font-size: 2.05rem; font-weight: 800; color: white; }}
    .grid {{ display: grid; gap: 1.5rem; grid-template-columns: 1.6fr 1fr; }}
    .section {{ border-radius: 32px; background: white; padding: 1.75rem; box-shadow: 0 30px 80px rgba(15, 23, 42, 0.05); border: 1px solid #e2e8f0; }}
    .section h2 {{ margin: 0 0 0.5rem; font-size: 1.5rem; }}
    .section p {{ margin: 0; color: #475569; }}
    .option-row {{ display: grid; gap: 1rem; grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .option-card {{ cursor: pointer; border: 1px solid #e2e8f0; border-radius: 22px; padding: 1.15rem 1rem; background: #ffffff; transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease; display: grid; grid-template-columns: auto 1fr; gap: 0.95rem; align-items: center; }}
    .option-card:hover {{ transform: translateY(-2px); box-shadow: 0 16px 38px rgba(15, 23, 42, 0.08); }}
    .option-card.active {{ border-color: #2563eb; background: #eff6ff; }}
    .option-icon {{ width: 3rem; height: 3rem; display: grid; place-items: center; border-radius: 16px; background: #e0efff; color: #2563eb; font-size: 1.1rem; }}
    .field-label {{ display: block; margin-bottom: 0.75rem; font-weight: 700; color: #0f172a; }}
    .form-control, .form-textarea {{ width: 100%; border-radius: 18px; border: 1px solid #cbd5e1; padding: 1rem 1.1rem; font-size: 0.98rem; color: #0f172a; background: #ffffff; }}
    .form-textarea {{ min-height: 160px; resize: vertical; }}
    .hint {{ margin-top: 0.5rem; color: #64748b; font-size: 0.92rem; }}
    .button-row {{ display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; margin-top: 1.5rem; }}
    .btn-primary {{ display: inline-flex; align-items: center; gap: 0.75rem; background: #2563eb; color: white; border: none; border-radius: 18px; padding: 0.95rem 1.5rem; font-weight: 700; cursor: pointer; transition: transform 0.2s ease, background 0.2s ease; }}
    .btn-primary:hover {{ background: #1d4ed8; }}
    .btn-secondary {{ color: #2563eb; font-weight: 700; }}
    .workflow-card {{ position: relative; overflow: hidden; }}
    .workflow-header {{ display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 1.25rem; }}
    .progress-track {{ width: 100%; height: 0.8rem; border-radius: 999px; background: #e2e8f0; overflow: hidden; }}
    .progress-fill {{ height: 100%; background: #2563eb; width: 30%; transition: width 0.4s ease; }}
    .stepper {{ display: grid; gap: 0.9rem; }}
    .step-item {{ display: grid; grid-template-columns: auto 1fr; gap: 1rem; align-items: flex-start; padding: 1rem 1rem; border-radius: 22px; border: 1px solid #e2e8f0; background: #f8fafc; }}
    .step-item.active {{ border-color: #2563eb; background: #eff6ff; }}
    .step-item.completed {{ border-color: #22c55e; background: #ecfdf5; }}
    .step-marker {{ width: 2.4rem; height: 2.4rem; border-radius: 999px; display: grid; place-items: center; color: white; font-weight: 700; }}
    .step-marker.complete {{ background: #22c55e; }}
    .step-marker.current {{ background: #2563eb; }}
    .step-marker.pending {{ background: #9ca3af; }}
    .step-details h3 {{ margin: 0; font-size: 1rem; }}
    .step-details p {{ margin: 0.35rem 0 0; color: #475569; font-size: 0.95rem; }}
    .footer {{ text-align: center; color: #64748b; margin-top: 2rem; font-size: 0.95rem; }}
    .overlay {{ display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.4); z-index: 20; align-items: center; justify-content: center; }}
    .spinner {{ width: 3rem; height: 3rem; border: 4px solid rgba(255,255,255,0.25); border-top-color: #ffffff; border-radius: 50%; animation: spin 0.8s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @media (max-width: 1080px) {{ .stats-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
    @media (max-width: 820px) {{ .grid, .stats-grid {{ grid-template-columns: 1fr; }} .hero-header {{ flex-direction: column; align-items: flex-start; }} }}
  </style>
</head>
<body>
  <div class="overlay" id="loadingOverlay"><div class="spinner"></div></div>
  <main class="page">
    <section class="hero">
      <div class="hero-header">
        <div>
          <p class="eyebrow">Self-Service Provisioner Bot</p>
          <h1 class="hero-title">Automated Infrastructure Provisioning Platform</h1>
          <p class="hero-subtitle">A modern enterprise dashboard for submitting environment requests, tracking progress, and letting DevOps automation handle the backend.</p>
        </div>
        <a class="btn-secondary" href="/track"><i class="fas fa-search"></i> Track requests</a>
      </div>
      <div class="stats-grid">
        <article class="stat-card"><h3>Total Requests</h3><p>{total_requests:,}</p></article>
        <article class="stat-card"><h3>Approved Requests</h3><p>{closed_requests:,}</p></article>
        <article class="stat-card"><h3>Pending Requests</h3><p>{open_requests:,}</p></article>
        <article class="stat-card"><h3>Pull Requests Created</h3><p>{open_prs:,}</p></article>
      </div>
    </section>

    <div class="grid">
      <section class="section">
        <div class="workflow-header">
          <div>
            <p class="eyebrow">Request form</p>
            <h2>Provision request</h2>
          </div>
          <span style="padding:0.75rem 1rem; border-radius:999px; background:#eff6ff; color:#1d4ed8; font-weight:700;">Modern DevOps portal</span>
        </div>
        <form id="requestForm" action="/submit" method="post" novalidate>
          <div>
            <p class="field-label">Environment type</p>
            <input type="hidden" name="env_type" id="envTypeInput" value="docker" />
            <div class="option-row">
              <div class="option-card active" data-value="docker" onclick="selectOption('env_type', this)"><div class="option-icon"><i class="fab fa-docker"></i></div><div><strong>Docker</strong><p class="hint">Container-based release</p></div></div>
              <div class="option-card" data-value="aws" onclick="selectOption('env_type', this)"><div class="option-icon"><i class="fas fa-cloud"></i></div><div><strong>AWS</strong><p class="hint">Cloud deployment</p></div></div>
              <div class="option-card" data-value="terraform" onclick="selectOption('env_type', this)"><div class="option-icon"><i class="fas fa-server"></i></div><div><strong>Terraform</strong><p class="hint">Infrastructure code</p></div></div>
            </div>
          </div>

          <div style="margin-top:1.5rem;">
            <p class="field-label">Environment name</p>
            <input type="hidden" name="env_name" id="envNameInput" value="dev" />
            <div class="option-row">
              <div class="option-card active" data-value="dev" onclick="selectOption('env_name', this)"><div class="option-icon"><i class="fas fa-code-branch"></i></div><div><strong>Dev</strong><p class="hint">Development testing</p></div></div>
              <div class="option-card" data-value="qa" onclick="selectOption('env_name', this)"><div class="option-icon"><i class="fas fa-vial"></i></div><div><strong>QA</strong><p class="hint">Quality assurance</p></div></div>
              <div class="option-card" data-value="staging" onclick="selectOption('env_name', this)"><div class="option-icon"><i class="fas fa-layer-group"></i></div><div><strong>Staging</strong><p class="hint">Pre-production review</p></div></div>
              <div class="option-card" data-value="prod" onclick="selectOption('env_name', this)"><div class="option-icon"><i class="fas fa-rocket"></i></div><div><strong>Prod</strong><p class="hint">Live deployment</p></div></div>
            </div>
          </div>

          <div style="margin-top:1.5rem;">
            <label for="request_details" class="field-label">Request details</label>
            <textarea id="request_details" name="request_details" class="form-textarea" placeholder="Describe the environment request in plain language." required></textarea>
            <div class="hint">Share business context, team needs, or special requirements.</div>
            <div id="detailsError" style="color:#ef4444;display:none;margin-top:0.5rem;font-size:0.92rem;"></div>
          </div>

          <div style="margin-top:1.5rem;">
            <label for="requester" class="field-label">Requester name</label>
            <input id="requester" name="requester" type="text" class="form-control" placeholder="Your name or team" required />
            <div class="hint">This helps the team know who submitted the request.</div>
            <div id="requesterError" style="color:#ef4444;display:none;margin-top:0.5rem;font-size:0.92rem;"></div>
          </div>

          <div class="button-row">
            <button type="submit" class="btn-primary" id="submitButton"><i class="fas fa-paper-plane"></i> Submit Request</button>
            <a class="btn-secondary" href="/track"><i class="fas fa-search"></i> Track request progress</a>
          </div>
        </form>
      </section>

      <section class="section workflow-card">
        <div class="workflow-header">
          <div>
            <p class="eyebrow">Workflow visualization</p>
            <h2>Provisioning pipeline</h2>
          </div>
          <div class="progress-track"><div class="progress-fill"></div></div>
        </div>
        <div class="stepper">
          <div class="step-item completed"><div class="step-marker complete">1</div><div class="step-details"><h3><i class="fas fa-paper-plane"></i> Request Submitted</h3><p>Request ticket created and labeled.</p></div></div>
          <div class="step-item active"><div class="step-marker current">2</div><div class="step-details"><h3><i class="fas fa-shield-alt"></i> Policy Validation</h3><p>Automated checks verify compliance.</p></div></div>
          <div class="step-item"><div class="step-marker pending">3</div><div class="step-details"><h3><i class="fas fa-cogs"></i> Infrastructure Generation</h3><p>Required templates are generated in the repository.</p></div></div>
          <div class="step-item"><div class="step-marker pending">4</div><div class="step-details"><h3><i class="fab fa-github"></i> Pull Request Creation</h3><p>A PR will be opened for review.</p></div></div>
          <div class="step-item"><div class="step-marker pending">5</div><div class="step-details"><h3><i class="fas fa-clock"></i> Approval Pending</h3><p>Awaiting approval before deployment.</p></div></div>
          <div class="step-item"><div class="step-marker pending">6</div><div class="step-details"><h3><i class="fas fa-rocket"></i> Deployment Ready</h3><p>Resources are ready once approval is complete.</p></div></div>
        </div>
      </section>
    </div>

    <footer class="footer">
      <p>Team Name · <a href="https://github.com/{GITHUB_REPOSITORY}" target="_blank">GitHub Repository</a> · Version 1.0</p>
    </footer>
  </main>
  <script>
    const loadingOverlay = document.getElementById('loadingOverlay');
    const form = document.getElementById('requestForm');
    const detailsEl = document.getElementById('request_details');
    const requesterEl = document.getElementById('requester');
    const submitButton = document.getElementById('submitButton');
    const detailsError = document.getElementById('detailsError');
    const requesterError = document.getElementById('requesterError');

    function setFieldError(fieldEl, errorEl, msg) {{
      if (msg) {{
        errorEl.textContent = msg;
        errorEl.style.display = 'block';
        fieldEl.style.borderColor = '#ef4444';
      }} else {{
        errorEl.textContent = '';
        errorEl.style.display = 'none';
        fieldEl.style.borderColor = '#cbd5e1';
      }}
    }}

    function validateForm() {{
      let valid = true;
      const details = detailsEl.value.trim();
      const requester = requesterEl.value.trim();

      if (!requester) {{
        setFieldError(requesterEl, requesterError, 'Please enter your name or team.');
        valid = false;
      }} else if (requester.length < 2) {{
        setFieldError(requesterEl, requesterError, 'Name is too short.');
        valid = false;
      }} else if (requester.length > 100) {{
        setFieldError(requesterEl, requesterError, 'Name is too long (max 100).');
        valid = false;
      }} else {{
        setFieldError(requesterEl, requesterError, '');
      }}

      if (!details) {{
        setFieldError(detailsEl, detailsError, 'Please describe the request.');
        valid = false;
      }} else if (details.length < 10) {{
        setFieldError(detailsEl, detailsError, 'Please provide more detail (min 10 characters).');
        valid = false;
      }} else if (details.length > 5000) {{
        setFieldError(detailsEl, detailsError, 'Request details are too long.');
        valid = false;
      }} else {{
        setFieldError(detailsEl, detailsError, '');
      }}

      submitButton.disabled = !valid;
      return valid;
    }}

    function selectOption(field, card) {{
      document.querySelectorAll('.option-card[data-value]').forEach(el => el.classList.remove('active'));
      card.classList.add('active');
      if (field === 'env_type') {{
        document.getElementById('envTypeInput').value = card.dataset.value;
      }}
      if (field === 'env_name') {{
        document.getElementById('envNameInput').value = card.dataset.value;
      }}
      validateForm();
    }}

    // Real-time validation
    [detailsEl, requesterEl].forEach(el => el.addEventListener('input', validateForm));

    // Initialize validation state on page load
    document.addEventListener('DOMContentLoaded', () => {{
      validateForm();
    }});

    form.addEventListener('submit', event => {{
      if (!validateForm()) {{
        event.preventDefault();
        return;
      }}
      loadingOverlay.style.display = 'flex';
    }});
  </script>
</body>
</html>"""

@app.post("/submit", response_class=HTMLResponse)
def submit(
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

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Request Created</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.4/css/all.min.css" rel="stylesheet" integrity="sha512-ZG4t9GkN6+/+V7dMj3+GVhaEhD+Rcv+/IYxKlBbL4xXyM3tq1W/zKcAhTsy3EZErUnp/yY0i2lKwpPqjv4jUSg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
  <style>
    body {{ margin: 0; padding: 0; font-family: Inter, system-ui, sans-serif; background: #f8fafc; color: #111827; }}
    .page {{ min-height: 100vh; display: grid; place-items: center; padding: 2rem; }}
    .alert {{ width: min(100%, 760px); background: white; border-radius: 28px; padding: 2.5rem; box-shadow: 0 30px 80px rgba(15, 23, 42, 0.08); border: 1px solid #e2e8f0; }}
    .status-badge {{ display: inline-flex; gap: 0.5rem; align-items: center; background: #eff6ff; color: #1d4ed8; padding: 0.75rem 1rem; border-radius: 999px; font-weight: 700; margin-bottom: 1.25rem; }}
    h1 {{ margin: 0 0 0.75rem; font-size: 2rem; }}
    p {{ margin: 0; color: #475569; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1.75rem; }}
    .btn-primary {{ display: inline-flex; align-items: center; gap: 0.75rem; background: #2563eb; color: white; border: none; border-radius: 18px; padding: 0.95rem 1.5rem; font-weight: 700; text-decoration: none; }}
    .btn-secondary {{ color: #2563eb; font-weight: 700; text-decoration: none; }}
    .stepper {{ margin-top: 1.5rem; display: grid; gap: 0.85rem; }}
    .step-item {{ display: grid; grid-template-columns: auto 1fr; gap: 1rem; align-items: center; padding: 1rem 1rem; border-radius: 20px; border: 1px solid #e2e8f0; background: #f8fafc; }}
    .step-marker {{ width: 2.2rem; height: 2.2rem; border-radius: 999px; display: grid; place-items: center; color: white; font-weight: 700; }}
    .step-marker.complete {{ background: #22c55e; }}
    .step-marker.current {{ background: #2563eb; }}
    .step-marker.pending {{ background: #9ca3af; }}
  </style>
</head>
<body>
  <main class="page">
    <section class="alert">
      <span class="status-badge"><i class="fas fa-paper-plane"></i> Request Submitted</span>
      <h1>Provision request created</h1>
      <p>Your request has been captured. The automation workflow will now validate, generate infrastructure, and open a pull request.</p>
      <div class="stepper">
        <div class="step-item"><div class="step-marker complete">1</div><div><strong>Request Submitted</strong><p>Ticket created and labeled.</p></div></div>
        <div class="step-item"><div class="step-marker current">2</div><div><strong>Policy Validation</strong><p>Automated policies are validating the request.</p></div></div>
        <div class="step-item"><div class="step-marker pending">3</div><div><strong>Infrastructure Generation</strong><p>Infrastructure files will be generated automatically.</p></div></div>
        <div class="step-item"><div class="step-marker pending">4</div><div><strong>Pull Request Creation</strong><p>A PR will be opened for review and approval.</p></div></div>
      </div>
      <div class="actions">
        <a href="/" class="btn-primary"><i class="fas fa-plus"></i> Submit another request</a>
        <a href="{issue.html_url}" target="_blank" class="btn-secondary">View request in GitHub</a>
      </div>
    </section>
  </main>
</body>
</html>""".format(issue=issue)


@app.get("/track", response_class=HTMLResponse)
@app.get("/requests", response_class=HTMLResponse)
def track_requests():
    if repo:
        issues = list(repo.get_issues(state="open", labels=[ISSUE_LABEL]))
        pulls = list(repo.get_pulls(state="all"))
    else:
        issues = []
        pulls = []
    rows = ""
    for issue in issues:
        title_text = issue.title.replace("Provision ", "") if issue.title.startswith("Provision ") else issue.title
        chunks = title_text.split(" ")
        request_type = chunks[0] if len(chunks) > 0 else "Unknown"
        environment = chunks[1] if len(chunks) > 1 else "Unknown"
        pr_url = ""
        for pr in pulls:
            if f"#{issue.number}" in (pr.title or "") or str(issue.number) in (pr.title or "") or issue.title in (pr.title or ""):
                pr_url = pr.html_url
                break
        status_label = "Pending"
        badge_class = "badge-warning"
        if issue.state == "closed":
            status_label = "Completed"
            badge_class = "badge-success"
        elif pr_url:
            status_label = "In Review"
            badge_class = "badge-primary"

        rows += f"""
          <tr data-status=\"{status_label}\" data-request=\"{request_type}\" data-env=\"{environment.lower()}\">
            <td><a href=\"{issue.html_url}\" target=\"_blank\">#{issue.number}</a></td>
            <td>{request_type}</td>
            <td>{environment}</td>
            <td><span class=\"badge {badge_class}\">{status_label}</span></td>
            <td>{issue.created_at.strftime('%Y-%m-%d %H:%M')}</td>
            <td>{f'<a href=\"{pr_url}\" target=\"_blank\">View PR</a>' if pr_url else '<span style=\"color:#64748b;\">Pending</span>'}</td>
          </tr>
        """

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Request Tracker</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.4/css/all.min.css" rel="stylesheet" integrity="sha512-ZG4t9GkN6+/+V7dMj3+GVhaEhD+Rcv+/IYxKlBbL4xXyM3tq1W/zKcAhTsy3EZErUnp/yY0i2lKwpPqjv4jUSg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
  <style>
    :root {{ font-family: Inter, system-ui, sans-serif; background: #f8fafc; color: #111827; }}
    body {{ margin: 0; min-height: 100vh; background: #f8fafc; }}
    .page {{ width: min(1200px, 100%); margin: 0 auto; padding: 2.5rem 1rem 3rem; }}
    .card {{ background: white; border-radius: 28px; border: 1px solid #e2e8f0; box-shadow: 0 30px 80px rgba(15, 23, 42, 0.06); padding: 2rem; }}
    .toolbar {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: 1rem; align-items: center; margin-bottom: 1.5rem; }}
    h1 {{ margin: 0; font-size: clamp(2rem, 3vw, 2.5rem); }}
    .subtitle {{ margin: 0.5rem 0 0; color: #475569; max-width: 70ch; }}
    .filters {{ display: grid; grid-template-columns: repeat(3, minmax(200px, 1fr)); gap: 1rem; margin-top: 1.5rem; }}
    .form-control {{ width: 100%; border-radius: 18px; border: 1px solid #cbd5e1; padding: 0.9rem 1rem; font-size: 0.95rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; }}
    th, td {{ padding: 1rem; border-bottom: 1px solid #e2e8f0; text-align: left; }}
    th {{ color: #475569; font-weight: 700; }}
    tr:hover {{ background: #f8fafc; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.55rem 0.85rem; border-radius: 999px; font-size: 0.85rem; font-weight: 700; }}
    .badge-primary {{ background: #dbeafe; color: #1d4ed8; }}
    .badge-success {{ background: #dcfce7; color: #166534; }}
    .badge-warning {{ background: #fef9c3; color: #92400e; }}
    .toolbar a {{ color: #2563eb; font-weight: 700; }}
    .footer {{ text-align: center; margin-top: 2rem; color: #64748b; font-size: 0.95rem; }}
    @media (max-width: 920px) {{ .filters {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main class="page">
    <section class="card">
      <div class="toolbar">
        <div>
          <h1>Request Tracking</h1>
          <p class="subtitle">Search and filter active provisioning requests with status badges and pull request links.</p>
        </div>
        <a href="/">Return to dashboard</a>
      </div>
      <div class="filters">
        <input id="searchInput" class="form-control" type="text" placeholder="Search by request ID, type, or environment" oninput="filterRequests()" />
        <select id="statusFilter" class="form-control" onchange="filterRequests()">
          <option value="all">All statuses</option>
          <option value="Pending">Pending</option>
          <option value="In Review">In Review</option>
          <option value="Completed">Completed</option>
        </select>
        <select id="envFilter" class="form-control" onchange="filterRequests()">
          <option value="all">All environments</option>
          <option value="dev">Dev</option>
          <option value="qa">QA</option>
          <option value="staging">Staging</option>
          <option value="prod">Prod</option>
        </select>
      </div>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Request ID</th>
              <th>Request Type</th>
              <th>Environment</th>
              <th>Status</th>
              <th>Created Time</th>
              <th>Pull Request</th>
            </tr>
          </thead>
          <tbody id="requestTable">
            {rows}
          </tbody>
        </table>
      </div>
      <div class="footer">
        <p>Team Name · <a href="https://github.com/{GITHUB_REPOSITORY}" target="_blank">GitHub Repository</a> · Version 1.0</p>
      </div>
    </section>
  </main>
  <script>
    function filterRequests() {{
      const searchValue = document.getElementById('searchInput').value.toLowerCase();
      const statusValue = document.getElementById('statusFilter').value;
      const envValue = document.getElementById('envFilter').value;
      document.querySelectorAll('#requestTable tr').forEach(row => {{
        const text = row.innerText.toLowerCase();
        const status = row.dataset.status;
        const env = row.dataset.env.toLowerCase();
        const matchSearch = text.includes(searchValue);
        const matchStatus = statusValue === 'all' || status === statusValue;
        const matchEnv = envValue === 'all' || env === envValue;
        row.style.display = matchSearch && matchStatus && matchEnv ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>""".format(rows=rows, GITHUB_REPOSITORY=GITHUB_REPOSITORY)
