"""Simple smoke test for all services."""

import requests

SERVICES = {
    "model-router": 8001,
    "plan-management": 8002,
    "git-worktree": 8003,
    "workflow-orchestrator": 8004,
    "verification-feedback": 8005,
}


if __name__ == "__main__":
    for name, port in SERVICES.items():
        resp = requests.get(f"http://localhost:{port}/health", timeout=3)
        resp.raise_for_status()
        print(f"{name}: {resp.json()['status']}")
