import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from policy_engine.policy import PolicyEngine, PolicyError


default_policy_file = os.getenv("POLICY_FILE", "policy_engine/policies.yaml")

app = FastAPI(title="Policy Engine")
engine = PolicyEngine(default_policy_file)


class ProvisionRequest(BaseModel):
    type: str
    env: str
    user: Optional[str] = None


@app.get("/")
def status() -> dict:
    return {
        "status": "ok",
        "policy_file": str(engine.policy_path.resolve()),
        "loaded_rules": len(engine.rules),
    }


@app.get("/rules")
def get_rules() -> dict:
    return {
        "rules": engine.rules,
        "defaults": engine.defaults,
    }


@app.post("/validate")
def validate(request: ProvisionRequest) -> dict:
    try:
        result = engine.validate(request.dict())
        return result
    except PolicyError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/reload")
def reload_policies() -> dict:
    try:
        engine.reload()
        return {"status": "reloaded", "loaded_rules": len(engine.rules)}
    except PolicyError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("policy_engine.main:app", host="0.0.0.0", port=8001, reload=True)
