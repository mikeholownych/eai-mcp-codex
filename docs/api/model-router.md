# Model router API

The Model Router exposes endpoints that select a Claude model based on text length and return the processed result.

## Endpoints

- `POST /model/route` – route a text prompt and obtain the answer.
- `GET /health` – service health status for monitoring systems.

Responses follow the schemas in `src/model_router/models.py`.
