import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from policy_engine.policy import PolicyEngine


def run_case(engine, payload):
    result = engine.validate(payload)
    print("REQUEST:", payload)
    print("RESULT:", result)
    print("-")


def main():
    engine = PolicyEngine("policy_engine/policies.yaml")

    print("Running policy engine smoke tests...\n")

    run_case(engine, {"type": "docker", "env": "dev", "user": "alice"})
    run_case(engine, {"type": "aws", "env": "test", "user": "alice"})
    run_case(engine, {"type": "aws", "env": "qa", "user": "alice"})
    run_case(engine, {"type": "gcp", "env": "dev", "user": "alice"})

    print("Done.")


if __name__ == "__main__":
    main()
