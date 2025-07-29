# Basic Workflow Example

# This script demonstrates a basic workflow using the MCP Microservices.

import requests

# Assuming the Workflow Orchestrator is running at http://localhost:8004
WORKFLOW_ORCHESTRATOR_URL = "http://localhost:8004"


def start_basic_workflow(workflow_id: str):
    """Starts a basic workflow by calling the Workflow Orchestrator API."""
    url = f"{WORKFLOW_ORCHESTRATOR_URL}/workflow/{workflow_id}"
    try:
        response = requests.post(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print(f"Workflow {workflow_id} started successfully: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error starting workflow {workflow_id}: {e}")


if __name__ == "__main__":
    # Example: Start a workflow with a specific ID
    # In a real scenario, workflow_id would be defined or retrieved from a system
    example_workflow_id = "my-first-workflow"
    print(f"Attempting to start basic workflow: {example_workflow_id}")
    start_basic_workflow(example_workflow_id)
