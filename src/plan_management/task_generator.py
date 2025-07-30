"""Task generation utilities for plans."""

from typing import List, Dict, Any
import uuid


def generate_tasks_from_plan(
    plan_description: str, plan_type: str = "general"
) -> List[Dict[str, Any]]:
    """
    Generates a list of tasks based on the plan description and type.
    This is a more sophisticated task generation logic.
    """
    tasks_list = []

    if "web application" in plan_description.lower() or plan_type == "web_app":
        tasks_list.extend(
            [
                {
                    "title": "Design UI/UX",
                    "description": "Create wireframes and mockups",
                    "estimated_hours": 20,
                    "dependencies": [],
                },
                {
                    "title": "Develop Frontend",
                    "description": "Implement user interface components",
                    "estimated_hours": 40,
                    "dependencies": ["Design UI/UX"],
                },
                {
                    "title": "Develop Backend API",
                    "description": "Build RESTful APIs and business logic",
                    "estimated_hours": 30,
                    "dependencies": [],
                },
                {
                    "title": "Set up Database",
                    "description": "Design schema and configure database",
                    "estimated_hours": 15,
                    "dependencies": ["Develop Backend API"],
                },
                {
                    "title": "Integrate Frontend and Backend",
                    "description": "Connect UI with API endpoints",
                    "estimated_hours": 25,
                    "dependencies": ["Develop Frontend", "Develop Backend API"],
                },
                {
                    "title": "Write Unit Tests",
                    "description": "Create unit tests for all modules",
                    "estimated_hours": 20,
                    "dependencies": ["Integrate Frontend and Backend"],
                },
                {
                    "title": "Deploy to Staging",
                    "description": "Deploy the application to a staging environment",
                    "estimated_hours": 10,
                    "dependencies": ["Write Unit Tests"],
                },
                {
                    "title": "Perform User Acceptance Testing (UAT)",
                    "description": "Conduct UAT with stakeholders",
                    "estimated_hours": 15,
                    "dependencies": ["Deploy to Staging"],
                },
                {
                    "title": "Deploy to Production",
                    "description": "Release the application to production",
                    "estimated_hours": 10,
                    "dependencies": ["Perform User Acceptance Testing (UAT)"],
                },
            ]
        )
    elif "api service" in plan_description.lower() or plan_type == "api_service":
        tasks_list.extend(
            [
                {
                    "title": "Define API Endpoints",
                    "description": "Specify all API routes and request/response formats",
                    "estimated_hours": 10,
                    "dependencies": [],
                },
                {
                    "title": "Implement Core Logic",
                    "description": "Develop the main business logic for the API",
                    "estimated_hours": 30,
                    "dependencies": ["Define API Endpoints"],
                },
                {
                    "title": "Add Authentication/Authorization",
                    "description": "Implement security measures for API access",
                    "estimated_hours": 20,
                    "dependencies": ["Implement Core Logic"],
                },
                {
                    "title": "Write API Tests",
                    "description": "Create integration and end-to-end tests for the API",
                    "estimated_hours": 20,
                    "dependencies": ["Add Authentication/Authorization"],
                },
                {
                    "title": "Document API",
                    "description": "Generate OpenAPI/Swagger documentation",
                    "estimated_hours": 10,
                    "dependencies": ["Implement Core Logic"],
                },
                {
                    "title": "Deploy API Gateway",
                    "description": "Configure and deploy API gateway for the service",
                    "estimated_hours": 15,
                    "dependencies": ["Document API"],
                },
            ]
        )
    else:  # General project
        tasks_list.extend(
            [
                {
                    "title": "Gather Requirements",
                    "description": "Collect and document project requirements",
                    "estimated_hours": 10,
                    "dependencies": [],
                },
                {
                    "title": "Design System Architecture",
                    "description": "Create high-level and detailed system designs",
                    "estimated_hours": 15,
                    "dependencies": ["Gather Requirements"],
                },
                {
                    "title": "Develop Core Components",
                    "description": "Implement the main features of the project",
                    "estimated_hours": 40,
                    "dependencies": ["Design System Architecture"],
                },
                {
                    "title": "Test System",
                    "description": "Conduct various levels of testing (unit, integration, system)",
                    "estimated_hours": 25,
                    "dependencies": ["Develop Core Components"],
                },
                {
                    "title": "Prepare Documentation",
                    "description": "Write user manuals, technical docs, etc.",
                    "estimated_hours": 15,
                    "dependencies": ["Develop Core Components"],
                },
                {
                    "title": "Deploy Solution",
                    "description": "Set up and deploy the final solution",
                    "estimated_hours": 10,
                    "dependencies": ["Test System", "Prepare Documentation"],
                },
            ]
        )

    # Assign unique IDs and format for consistency
    formatted_tasks = []
    for task in tasks_list:
        task_id = str(uuid.uuid4())
        formatted_tasks.append(
            {
                "id": task_id,
                "title": task["title"],
                "description": task["description"],
                "estimated_hours": task["estimated_hours"],
                "dependencies": [
                    dep
                    for dep in task["dependencies"]
                    if dep in [t["title"] for t in tasks_list]
                ],  # Resolve dependencies by title
                "metadata": {},
            }
        )

    # Convert dependencies from titles to actual task IDs
    task_title_to_id = {task["title"]: task["id"] for task in formatted_tasks}
    for task in formatted_tasks:
        task["dependencies"] = [
            task_title_to_id[dep_title]
            for dep_title in task["dependencies"]
            if dep_title in task_title_to_id
        ]

    return formatted_tasks


def tasks(plan_id: str) -> List[str]:
    """
    Legacy function for backward compatibility.
    Returns a simplified list of task titles.
    """
    # This function now calls the more sophisticated generator
    generated_tasks = generate_tasks_from_plan(f"Plan {plan_id}", "general")
    return [task["title"] for task in generated_tasks]
