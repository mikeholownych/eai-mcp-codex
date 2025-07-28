# Verification feedback API

The Verification Feedback service simulates result checks from automated code review tools. It accepts a numeric identifier and returns a simple record summarizing the verification output.

## Endpoints

- `GET /feedback/{id}` – fetch verification results for a given identifier.
- `GET /health` – readiness probe.
