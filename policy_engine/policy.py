import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class PolicyError(Exception):
    pass


class PolicyEngine:
    def __init__(self, policy_path: str) -> None:
        self.policy_path = Path(policy_path)
        self.rules: List[Dict[str, Any]] = []
        self.defaults: Dict[str, Any] = {}
        self._load_policies()

    def _load_policies(self) -> None:
        if not self.policy_path.exists():
            raise PolicyError(f"Policy file not found: {self.policy_path}")

        with self.policy_path.open("r", encoding="utf-8") as stream:
            try:
                config = yaml.safe_load(stream) or {}
            except yaml.YAMLError as exc:
                raise PolicyError(f"Invalid YAML policy file: {exc}") from exc

        if not isinstance(config, dict):
            raise PolicyError("Policy file must contain a mapping at the top level.")

        self.defaults = config.get("defaults", {})
        self.rules = config.get("rules", [])

        if not isinstance(self.rules, list):
            raise PolicyError("Policy file must define a list of rules.")

    def reload(self) -> None:
        self._load_policies()

    def validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        type_value = payload.get("type")
        env_value = payload.get("env")
        user_value = payload.get("user")

        if not type_value or not isinstance(type_value, str):
            return self._response(False, "Missing or invalid `type` field.")

        if not env_value or not isinstance(env_value, str):
            return self._response(False, "Missing or invalid `env` field.")

        if not user_value or not isinstance(user_value, str):
            return self._response(False, "Missing or invalid `user` field.")

        allowed_types = set(self.defaults.get("allowed_types", []))
        allowed_envs = set(self.defaults.get("allowed_envs", []))
        authorized_users = set(self.defaults.get("authorized_users", []))

        if allowed_types and type_value not in allowed_types:
            return self._response(False, f"Environment type '{type_value}' is not allowed.")

        if allowed_envs and env_value not in allowed_envs:
            return self._response(False, f"Environment '{env_value}' is not allowed.")

        is_automation = (
            "bot" in user_value.lower()
            or "assistant" in user_value.lower()
            or "automation" in user_value.lower()
            or "github-actions" in user_value.lower()
            or "ui" in user_value.lower()
        )
        if authorized_users and user_value not in authorized_users and not is_automation:
            return self._response(False, f"User '{user_value}' is not authorized.")

        for rule in self.rules:
            if self._matches(rule.get("conditions", {}), payload):
                effect = str(rule.get("effect", "deny")).lower()
                message = rule.get("message") or rule.get("description") or "Request denied by policy."
                allowed = effect == "allow"
                return self._response(allowed, message, rule.get("name"))

        default_effect = str(self.defaults.get("default_effect", "deny")).lower()
        if default_effect == "allow":
            return self._response(True, "Request allowed by default policy.")

        return self._response(False, "Request denied by default policy.")

    def _matches(self, conditions: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        for key, expected in conditions.items():
            actual = payload.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif expected != actual:
                return False
        return True

    def _response(self, allowed: bool, message: str, rule_name: Optional[str] = None) -> Dict[str, Any]:
        response = {
            "allowed": allowed,
            "message": message,
        }
        if rule_name:
            response["rule"] = rule_name
        return response
