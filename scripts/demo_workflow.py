# scripts/demo_workflow.py - Demonstration Workflow
#!/usr/bin/env python3
"""
Demonstration workflow to show MCP microservices in action
"""
import asyncio

import requests
from typing import Any


class MCPClient:
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "MCP-Demo-Client/1.0"}
        )

    def call_service(
        self, service: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Call a microservice endpoint"""
        url = f"{self.base_url}/api/{service}{endpoint}"

        try:
            if data:
                response = self.session.post(url, json=data, timeout=30)
            else:
                response = self.session.get(url, timeout=30)

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            return {"error": str(e), "status": "failed"}


async def run_demo_workflow():
    """Run a complete demonstration workflow"""
    client = MCPClient()

    print("🚀 Starting MCP Microservices Demo Workflow")
    print("=" * 50)

    # Step 1: Start a workflow
    print("\n📋 Step 1: Starting workflow...")
    workflow_data = {
        "task_description": "Create a simple REST API for user management with authentication",
        "project_path": "/demo/user-api",
        "title": "Demo User API",
        "priority": "medium",
    }

    workflow_result = client.call_service("workflow", "/start_workflow", workflow_data)

    if "error" in workflow_result:
        print(f"❌ Failed to start workflow: {workflow_result['error']}")
        return

    workflow_id = workflow_result.get("id")
    print(f"✅ Workflow started with ID: {workflow_id}")

    # Step 2: Monitor workflow progress
    print("\n👀 Step 2: Monitoring workflow progress...")

    max_attempts = 20
    attempt = 0

    while attempt < max_attempts:
        status_result = client.call_service(
            "workflow", "/get_workflow_status", {"workflow_id": workflow_id}
        )

        if "error" in status_result:
            print(f"❌ Error checking status: {status_result['error']}")
            break

        current_status = status_result.get("status", "unknown")
        current_step = None

        # Find current step
        for step in status_result.get("steps", []):
            if step.get("status") == "in_progress":
                current_step = step.get("name")
                break

        print(
            f"📊 Status: {current_status}"
            + (f" | Current Step: {current_step}" if current_step else "")
        )

        if current_status in ["completed", "failed"]:
            break

        await asyncio.sleep(10)  # Wait 10 seconds
        attempt += 1

    # Step 3: Show final results
    print("\n📈 Step 3: Final Results")

    final_status = client.call_service(
        "workflow", "/get_workflow_status", {"workflow_id": workflow_id}
    )

    if "error" not in final_status:
        print(f"Final Status: {final_status.get('status')}")
        print(f"Total Steps: {len(final_status.get('steps', []))}")

        # Show step details
        for i, step in enumerate(final_status.get("steps", []), 1):
            status_emoji = {
                "completed": "✅",
                "failed": "❌",
                "in_progress": "🔄",
                "pending": "⏳",
            }.get(step.get("status"), "❓")

            print(
                f"  {status_emoji} Step {i}: {step.get('name')} ({step.get('status')})"
            )

    # Step 4: Show metrics
    print("\n📊 Step 4: System Metrics")

    metrics_result = client.call_service(
        "workflow", "/get_workflow_metrics", {"timeframe_days": 1}
    )

    if "error" not in metrics_result:
        print(f"Total Workflows Today: {metrics_result.get('total_workflows', 0)}")
        print(f"Completed: {metrics_result.get('completed_workflows', 0)}")
        print(f"Completion Rate: {metrics_result.get('completion_rate_percent', 0)}%")
        print(
            f"Average Duration: {metrics_result.get('average_duration_seconds', 0):.1f}s"
        )

    print("\n🎉 Demo workflow completed!")
    print("Check Grafana at http://localhost:3000 for detailed metrics")


def test_all_services():
    """Test that all services are responding"""
    client = MCPClient()

    services = [
        ("model-router", "/health"),
        ("plan-management", "/health"),
        ("git-worktree", "/health"),
        ("workflow", "/health"),
        ("verification", "/health"),
    ]

    print("🔍 Testing all services...")
    all_healthy = True

    for service, endpoint in services:
        result = client.call_service(service, endpoint)
        if "error" in result:
            print(f"❌ {service}: {result['error']}")
            all_healthy = False
        else:
            print(f"✅ {service}: Healthy")

    return all_healthy


if __name__ == "__main__":
    print("MCP Microservices Demo")
    print("=====================")

    # First test all services
    if not test_all_services():
        print("\n❌ Some services are not healthy. Please check the setup.")
        exit(1)

    # Run the demo workflow
    asyncio.run(run_demo_workflow())
