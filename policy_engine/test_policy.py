from policy_engine.policy import PolicyEngine


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


def test_policy_engine_requires_user_field():
    engine = PolicyEngine("policy_engine/policies.yaml")
    result = engine.validate({"type": "docker", "env": "dev"})
    assert result["allowed"] is False
    assert "user" in result["message"].lower()
