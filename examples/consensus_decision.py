# Consensus Building Example

# This script demonstrates how agents can build consensus on a decision.

import requests
import time

# Assuming a Collaboration Orchestrator service that handles consensus
# For this example, we'll simulate a simple consensus process via a generic API call
COLLABORATION_ORCHESTRATOR_URL = "http://localhost:8012"  # Placeholder URL


def initiate_consensus(decision_topic: str, options: list, agents_involved: list):
    """Initiates a consensus building process among agents."""
    payload = {
        "topic": decision_topic,
        "options": options,
        "agents": agents_involved,
        "timeout": 60,  # seconds
    }
    # In a real system, this would call a specific endpoint like /consensus/initiate
    url = f"{COLLABORATION_ORCHESTRATOR_URL}/collaborate"  # Generic collaboration endpoint
    try:
        print(f"Initiating consensus on: {decision_topic}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        print(
            f"Consensus initiated. Collaboration ID: {result.get('collaboration_id')}"
        )
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error initiating consensus: {e}")
        return None


def get_consensus_status(collaboration_id: str):
    """Fetches the current status of a consensus process."""
    # In a real system, this would call a specific endpoint like /consensus/status/{id}
    url = f"{COLLABORATION_ORCHESTRATOR_URL}/status/{collaboration_id}"  # Generic status endpoint
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching consensus status: {e}")
        return None


if __name__ == "__main__":
    topic = "Best programming language for new microservice"
    options = ["Python", "Go", "Node.js", "Java"]
    agents = ["planner_agent_1", "developer_agent_1", "architect_agent_1"]

    consensus_init_result = initiate_consensus(topic, options, agents)

    if consensus_init_result:
        collaboration_id = consensus_init_result.get("collaboration_id")
        if collaboration_id:
            print("Waiting for consensus...")
            # Simulate waiting and checking status
            for i in range(5):
                time.sleep(5)  # Wait 5 seconds
                status = get_consensus_status(collaboration_id)
                if status:
                    print(
                        f"Current status ({i+1}/5): {status.get('status')}, Result: {status.get('result', 'N/A')}"
                    )
                    if status.get("status") == "completed":
                        break
            print("\nConsensus process finished.")
            final_status = get_consensus_status(collaboration_id)
            if final_status:
                print(
                    f"Final Consensus Result: {final_status.get('result', 'No consensus reached')}"
                )
        else:
            print("Could not get collaboration ID to track consensus.")
