import sys
import types

import pytest

# Provide a minimal mocked discord library for test import-time compatibility.
discord_module = types.ModuleType("discord")

class DummyIntents:
    @staticmethod
    def default():
        intent = types.SimpleNamespace()
        intent.message_content = False
        return intent

class DummyClient:
    def __init__(self, *, intents=None):
        self.intents = intents

    def event(self, func=None):
        def decorator(fn):
            return fn

        if func is None:
            return decorator
        return func

class DummyTree:
    def __init__(self, client):
        self.client = client

    def command(self, *args, **kwargs):
        def decorator(fn):
            return fn

        return decorator

    @staticmethod
    def describe(*args, **kwargs):
        def decorator(fn):
            return fn

        return decorator

class DummyAppCommands(types.ModuleType):
    pass

app_commands_module = types.ModuleType("discord.app_commands")
app_commands_module.CommandTree = DummyTree
app_commands_module.describe = DummyTree.describe

discord_module.app_commands = app_commands_module
discord_module.Intents = DummyIntents
discord_module.Client = DummyClient
sys.modules["discord"] = discord_module
sys.modules["discord.app_commands"] = app_commands_module

import bot


class DummyResponse:
    def __init__(self, json_data=None, status_code=200):
        self._json_data = json_data or {}
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP error")

    def json(self):
        return self._json_data


def test_get_policy_result_success(monkeypatch):
    def fake_post(url, json, timeout):
        assert url == bot.POLICY_URL
        assert json == {"type": "docker", "env": "dev", "user": "alice"}
        assert timeout == 30
        return DummyResponse({"allowed": True, "message": "ok"})

    monkeypatch.setattr(bot.requests, "post", fake_post)
    result = bot.get_policy_result("docker", "dev", "alice")
    assert result["allowed"] is True
    assert result["message"] == "ok"


def test_get_policy_result_fails_gracefully(monkeypatch):
    def fake_post(url, json, timeout):
        raise bot.requests.RequestException("failed")

    monkeypatch.setattr(bot.requests, "post", fake_post)
    result = bot.get_policy_result("docker", "dev", "alice")
    assert result["allowed"] is False
    assert "unavailable" in result["message"].lower()


def test_format_provision_message_allows(monkeypatch):
    monkeypatch.setattr(bot, "generate", lambda env_type, env_name: "generated-template")
    result = {"allowed": True, "message": "Allowed!"}
    msg = bot.format_provision_message("docker", "dev", result)
    assert "Provision Request Received" in msg
    assert "generated-template" in msg
    assert "Allowed!" in msg


def test_format_provision_message_denies():
    result = {"allowed": False, "message": "Denied by policy."}
    msg = bot.format_provision_message("docker", "dev", result)
    assert "Provision request denied" in msg
    assert "Denied by policy." in msg
