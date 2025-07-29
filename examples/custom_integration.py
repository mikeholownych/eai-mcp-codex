# Custom Integration Example

This script demonstrates how to integrate with external systems.

import requests
import json

# This example simulates sending data to an external analytics service
# In a real scenario, this would be a third-party API endpoint
EXTERNAL_ANALYTICS_SERVICE_URL = "https://api.example.com/analytics" # Placeholder URL

def send_data_to_analytics(event_name: str, data: dict):
    """Sends custom event data to an external analytics service."""
    payload = {
        "event": event_name,
        "timestamp": requests.utils.default_json_encoder.datetime_to_iso_format(requests.utils.datetime.datetime.utcnow()),
        "properties": data
    }
    try:
        print(f"Sending event '{event_name}' to external analytics...")
        response = requests.post(EXTERNAL_ANALYTICS_SERVICE_URL, json=payload)
        response.raise_for_status() # Raise an exception for HTTP errors
        print(f"Successfully sent data. Response: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to analytics service: {e}")
        return False

if __name__ == "__main__":
    # Example 1: Log a workflow completion event
    workflow_data = {
        "workflow_id": "plan-execution-123",
        "status": "completed",
        "duration_ms": 15000,
        "triggered_by": "developer_agent"
    }
    send_data_to_analytics("workflow_completed", workflow_data)

    print("\n")

    # Example 2: Log an agent decision event
    decision_data = {
        "agent_id": "planner_agent_1",
        "decision_type": "task_breakdown",
        "chosen_option": "microservice_architecture",
        "alternatives_considered": ["monolith", "serverless"]
    }
    send_data_to_analytics("agent_decision_made", decision_data)