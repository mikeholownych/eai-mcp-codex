# Workflow orchestrator API

The orchestrator coordinates multi-step workflows across the other microservices. It triggers the model router, plan manager, git worktree, and verification services.

## Endpoints

- `POST /workflow/{id}` – start a workflow with the provided identifier.
- `GET /health` – health endpoint for orchestrators.
