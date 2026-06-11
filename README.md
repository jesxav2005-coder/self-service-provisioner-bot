# Self-Service Provisioner Bot

An AI-powered developer portal for self-service infrastructure provisioning. It translates natural language environment requests into working Docker Compose configurations or AWS Terraform setups, handles GitOps code submissions (GitHub Issues & Pull Requests), and automates notification flows.

---

## Features
- **Modern Developer Dashboard**: Glassmorphism stats cards, responsive forms, and live status tracking.
- **Interactive AI Chat Assistant**: Floating assistant widget with quick suggested action chips to guide developers.
- **Policy Engine Guardrails**: Validates configurations against `policy.yaml` limits (allowed stages, types, and max service limits).
- **Auto Code Generation**: Outputs fully functional multi-service `docker-compose.yml` configurations or AWS Terraform (`main.tf`, `variables.tf`, `provider.tf`) script layouts.
- **GitOps GitHub API Integration**: Auto-creates tracking Issues labeled `auto-provision` and opens Pull Requests (PRs) with the generated files.
- **Auto-Deployment Pipeline**: A GitHub Actions workflow (`deploy.yml`) runs on merges to validate code and call the backend deployment webhook.
- **Double Email Notifications**:
  - **Dev Team Notification**: Alert sent upon request submission (with links to PR and Issue).
  - **Requester Notification**: Alert sent to the developer once the PR is merged and deployed successfully.

---

## Setup & Run

### 1. Installation
```bash
cd provisioner-bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure Environment Variables
Open the `.env` file and set the keys:
```env
# Hugging Face AI
HF_API_KEY=your_key  # Optional: defaults to keyword matching if empty
HF_MODEL=google/flan-t5-small

# GitHub integration
GITHUB_TOKEN=your_token
GITHUB_REPO=owner/repo-name

# Resend Email Integration (Recommended)
RESEND_API_KEY=your_resend_api_key
ADMIN_EMAIL=admin@yourdomain.com
REQUESTER_EMAIL=tester@yourdomain.com

# Alternate SMTP Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@provisionerbot.com
DEV_TEAM_EMAIL=devteam@yourcompany.com
```

### 3. Run Application
```bash
uvicorn app:app --reload --port 8000
```
Visit dashboard at: **http://127.0.0.1:8000**

### 4. Run Tests
```bash
pytest tests/test_api.py -v
```

---

## API Documentation

| Method | Endpoint                    | Description |
|--------|-----------------------------|-------------|
| **GET** | `/`                         | Serves Dashboard portal |
| **GET** | `/requests`                 | Serves Request tracker log view |
| **GET** | `/api/requests`             | Returns list of all requests in SQLite database |
| **GET** | `/api/status`               | Returns active integrations and Mock Mode status |
| **POST**| `/api/validate`             | Validates types/stages against security policies |
| **POST**| `/api/parse`                | AI/keyword parser endpoint |
| **POST**| `/api/chat`                 | Chat assistant interface (with mock keywords) |
| **POST**| `/api/submit`               | Submission workflow (engine check, code gen, Issue/PR, Dev Email) |
| **POST**| `/api/complete/{request_id}`| Webhook called by CI/CD to flag complete and email requester |

---

## GitOps Deployment Webhook Callbacks

When a Pull Request is merged into `main`, the `.github/workflows/deploy.yml` runner validates syntax and hits the callback endpoint to send the completion email:
```bash
# Handled automatically inside deploy.yml:
curl -s -X POST "http://localhost:8000/api/complete/{request_id}"
```
To test this callback locally, run:
```bash
python -c "import requests; requests.post('http://localhost:8000/api/complete/{request_id}')"
```
