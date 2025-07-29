# Multi-Agent Review Example

This script demonstrates a multi-agent code review process.

import requests
import json

# Assuming the Verification & Feedback service is running at http://localhost:8005
VERIFICATION_FEEDBACK_URL = "http://localhost:8005"

def submit_code_for_review(code_content: str, review_type: str = "quality"):
    """Submits code content for multi-agent review."""
    payload = {
        "name": f"Code Review - {review_type}",
        "description": f"Automated review for {review_type} aspects.",
        "target_type": "code",
        "target_id": "unique-code-id-123", # In a real system, this would be dynamic
        "target_content": code_content,
        "rule_categories": [review_type] # e.g., "security", "performance", "quality"
    }
    url = f"{VERIFICATION_FEEDBACK_URL}/verify"
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Code submitted for review. Verification ID: {response.json().get("id")}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error submitting code for review: {e}")
        return None

if __name__ == "__main__":
    sample_code = """
def calculate_sum(a, b):
    # This is a simple function
    return a + b

# Potential security flaw: direct use of user input in SQL query
def get_user_data(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    # execute(query)
"""

    print("Submitting sample code for quality review...")
    quality_review_result = submit_code_for_review(sample_code, "quality")
    if quality_review_result:
        print("Quality review initiated.")

    print("\nSubmitting sample code for security review...")
    security_review_result = submit_code_for_review(sample_code, "security")
    if security_review_result:
        print("Security review initiated.")