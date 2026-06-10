from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from terraform_generator.generator import generate


class IssuePayload(BaseModel):
    title: str
    body: str
    author: str | None = None
    issue_number: int | None = None


app = FastAPI()

POLICY_URL = os.getenv("POLICY_ENGINE_URL", "http://127.0.0.1:8001/validate")


def _parse_request_from_issue(title: str, body: str, author: str | None):
    text = f"{title}\n\n{body}".lower()
    if "docker" in text:
        t = "docker"
    elif "terraform" in text or "aws" in text:
        t = "terraform"
    else:
        t = "docker"

    env = "dev"
    if "prod" in text:
        env = "prod"
    elif "staging" in text:
        env = "staging"
    elif "qa" in text:
        env = "qa"
    elif "test" in text:
        env = "test"

    user = author or "unknown"
    return {"type": t, "env": env, "user": user}


@app.post("/validate")
def validate_issue(payload: IssuePayload):
    policy_req = _parse_request_from_issue(payload.title, payload.body, payload.author)
    try:
        r = requests.post(POLICY_URL, json=policy_req, timeout=10)
        r.raise_for_status()
        pr = r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"policy engine error: {e}")

    allowed = pr.get("allowed", False)
    if allowed:
        template = generate(policy_req["type"], policy_req["env"])
        return {"approved": True, "policy": pr, "template": template}
    else:
        return {"approved": False, "policy": pr}
import pathlib
import yaml

from policy_engine.policy import PolicyEngine

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_policy_summary(policy_path: pathlib.Path) -> str:
    engine = PolicyEngine(str(policy_path))
    allowed_types = sorted(engine.defaults.get("allowed_types", []))
    allowed_envs = sorted(engine.defaults.get("allowed_envs", []))
    authorized_users = sorted(engine.defaults.get("authorized_users", []))
    default_effect = engine.defaults.get("default_effect", "deny")

    summary = [
        "Policy engine analysis summary:",
        f"- Allowed types: {', '.join(allowed_types) if allowed_types else 'none'}",
        f"- Allowed environments: {', '.join(allowed_envs) if allowed_envs else 'none'}",
        f"- Authorized users: {', '.join(authorized_users) if authorized_users else 'none'}",
        f"- Default effect: {default_effect}",
        "- Rules:",
    ]

    for rule in engine.rules:
        summary.append(
            f"  - {rule.get('name', '<unnamed>')} -> {rule.get('effect')} when {rule.get('conditions')}"
        )

    if default_effect != "allow":
        summary.append(
            "Suggestion: consider adding an explicit allow rule for production-safe workflows if you want default behavior to permit selected requests."
        )

    return "\n".join(summary)


def analyze_environment_templates() -> str:
    templates = []
    for template_path in (ROOT / "terraform_generator" / "templates").glob("*.tpl"):
        content = template_path.read_text(encoding="utf-8")
        templates.append(f"- {template_path.name}: {len(content.splitlines())} lines")

    return "Template analysis:\n" + "\n".join(templates)


def generate_report() -> str:
    policy_path = ROOT / "policy_engine" / "policies.yaml"
    return f"{load_policy_summary(policy_path)}\n\n{analyze_environment_templates()}"


if __name__ == "__main__":
    print(generate_report())
