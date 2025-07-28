# Production guide

Deployments should run behind a load balancer with TLS termination and persistent storage for PostgreSQL, Redis and logs. Monitor the services using the provided Prometheus configuration and configure backups for the plan management database.
