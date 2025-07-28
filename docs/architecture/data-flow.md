# Data flow

Incoming requests are routed by Nginx to the workflow orchestrator or directly to the individual services. The orchestrator invokes the other services in turn, storing shared state in PostgreSQL and publishing events to Redis.

Metrics and logs are exported to Prometheus and Elastic Stack for analysis.
