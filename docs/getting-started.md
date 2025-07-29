# Getting Started

This guide provides a quick start for setting up and using the MCP Microservices project.

## Prerequisites

Before you begin, you will need to have the following installed:

*   Docker
*   Docker Compose
*   Python 3.11+

## Setup

To set up the project, run the following command:

```bash
make quick-start-a2a
```

This will start all the services and run the database migrations.

## Usage

Once the project is set up, you can start using it to create and manage plans, execute workflows, and collaborate with agents.

### Create a Plan

To create a plan, send a POST request to the `/api/plan-management/` endpoint.

### Execute a Workflow

To execute a workflow, send a POST request to the `/api/workflow/` endpoint.

### Collaborate with Agents

To collaborate with agents, you can use the A2A communication system. For more information, see the [A2A Communication Guide](a2a-communication-guide.md).
