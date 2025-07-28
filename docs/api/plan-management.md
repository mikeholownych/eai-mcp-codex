# Plan management API

This service stores and retrieves build plans. Plans are simple objects with an ID and name. They may later be extended to include scheduling and metadata.

## Endpoints

- `POST /plans/` – create a plan given a name and return the new object.
- `GET /plans/` – list all known plans.
- `GET /health` – health probe used by orchestration layers.
