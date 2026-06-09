# Policy Engine

This service validates provision requests from the Discord bot against a central YAML policy file.

## Member 2 Responsibilities

- Define policy rules in `policies.yaml`
- Check incoming request permissions
- Validate requests before infrastructure code is generated
- Provide a reusable validation API for the bot and GitHub workflow

## How It Works

- `policy_engine/main.py` starts a FastAPI service on port `8001`
- `policy_engine/policies.yaml` defines rules and default behavior
- `POST /validate` returns whether a request is allowed
- `GET /rules` exposes the loaded policy rules
- `POST /reload` reloads the YAML file at runtime

## Run Locally

```bash
python -m policy_engine.main
```

Then point the bot at `http://localhost:8001/validate`.

## Policy File Structure

- `defaults.allowed_types`: supported environment types
- `defaults.allowed_envs`: supported environment names
- `rules`: ordered rules evaluated in sequence
- Each rule includes `conditions`, `effect`, and `message`
