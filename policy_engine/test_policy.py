import tempfile
from pathlib import Path
import yaml
import pytest

from fastapi.testclient import TestClient

from policy_engine.main import app
from policy_engine.policy import PolicyEngine, PolicyError


def test_policy_engine_allows_docker():
    engine = PolicyEngine("policy_engine/policies.yaml")
    result = engine.validate({"type": "docker", "env": "dev", "user": "alice"})
    assert result["allowed"] is True
    assert "Docker provisioning is allowed" in result["message"]


def test_policy_engine_denies_invalid_env():
    engine = PolicyEngine("policy_engine/policies.yaml")
    result = engine.validate({"type": "docker", "env": "prod", "user": "alice"})
    assert result["allowed"] is False
    assert "not allowed" in result["message"].lower()


def test_policy_engine_denies_unauthorized_user():
    engine = PolicyEngine("policy_engine/policies.yaml")
    result = engine.validate({"type": "docker", "env": "dev", "user": "unauthorized_user"})
    assert result["allowed"] is False
    assert "not authorized" in result["message"].lower()


def test_policy_engine_allows_automation_user():
    engine = PolicyEngine("policy_engine/policies.yaml")
    result = engine.validate({"type": "docker", "env": "dev", "user": "assistant-bot"})
    assert result["allowed"] is True


def test_policy_engine_requires_user_field():
    engine = PolicyEngine("policy_engine/policies.yaml")
    result = engine.validate({"type": "docker", "env": "dev"})
    assert result["allowed"] is False
    assert "user" in result["message"].lower()


def test_policy_engine_default_deny_when_no_rule_matches():
    engine = PolicyEngine("policy_engine/policies.yaml")
    result = engine.validate({"type": "aws", "env": "qa", "user": "alice"})
    assert result["allowed"] is False
    assert "denied by default" in result["message"].lower()


def test_policy_engine_reload_updates_rules(tmp_path):
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text(
        yaml.dump({
            "version": 1,
            "defaults": {
                "allowed_types": ["docker"],
                "allowed_envs": ["dev"],
                "authorized_users": ["alice"],
                "default_effect": "deny",
            },
            "rules": [
                {
                    "name": "allow_docker",
                    "conditions": {"type": ["docker"]},
                    "effect": "allow",
                    "message": "Docker allowed",
                }
            ],
        })
    )

    engine = PolicyEngine(str(policy_file))
    result = engine.validate({"type": "docker", "env": "dev", "user": "alice"})
    assert result["allowed"] is True
    assert "docker allowed" in result["message"].lower()

    policy_file.write_text(
        yaml.dump({
            "version": 1,
            "defaults": {
                "allowed_types": ["docker"],
                "allowed_envs": ["dev"],
                "authorized_users": ["alice"],
                "default_effect": "deny",
            },
            "rules": [
                {
                    "name": "deny_docker",
                    "conditions": {"type": ["docker"]},
                    "effect": "deny",
                    "message": "Docker denied",
                }
            ],
        })
    )
    engine.reload()
    result = engine.validate({"type": "docker", "env": "dev", "user": "alice"})
    assert result["allowed"] is False
    assert "docker denied" in result["message"].lower()


def test_policy_engine_invalid_policy_file_raises_error(tmp_path):
    policy_file = tmp_path / "invalid_policies.yaml"
    policy_file.write_text("not: a: valid: yaml")
    with pytest.raises(PolicyError):
        PolicyEngine(str(policy_file))


def test_validate_endpoint_allows_request():
    client = TestClient(app)
    response = client.post(
        "/validate",
        json={"type": "docker", "env": "dev", "user": "alice"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is True
    assert "Docker provisioning is allowed" in payload["message"]


def test_reload_endpoint_updates_engine(tmp_path, monkeypatch):
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text(
        yaml.dump({
            "version": 1,
            "defaults": {
                "allowed_types": ["docker"],
                "allowed_envs": ["dev"],
                "authorized_users": ["alice"],
                "default_effect": "deny",
            },
            "rules": [
                {
                    "name": "allow_docker",
                    "conditions": {"type": ["docker"]},
                    "effect": "allow",
                    "message": "Docker allowed",
                }
            ],
        })
    )

    engine = PolicyEngine(str(policy_file))
    monkeypatch.setattr("policy_engine.main.engine", engine)

    response = TestClient(app).post("/reload")
    assert response.status_code == 200
    assert response.json()["status"] == "reloaded"

    response = TestClient(app).post(
        "/validate",
        json={"type": "docker", "env": "dev", "user": "alice"},
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is True
    assert "docker allowed" in response.json()["message"].lower()
