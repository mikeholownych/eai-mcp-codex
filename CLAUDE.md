# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
make setup                      # Initial project setup
make dev                       # Start development environment  
make dev-down                  # Stop development environment
make dev-clean                 # Clean development environment (remove volumes)
```

### Testing
```bash
make test                      # Run all tests using pytest
make test-unit                 # Run unit tests only
make test-integration          # Run integration tests
make test-performance          # Run performance tests
make test-service SERVICE=name # Test specific service
```

### Code Quality
```bash
make lint                      # Run flake8 and mypy linting
make format                    # Format code using black
make format-check              # Check code formatting
```

### Service Management
```bash
make build                     # Build all services
make up                        # Start all services
make down                      # Stop all services
make logs                      # Show logs for all services
make logs-service SERVICE=name # Show logs for specific service
make status                    # Show service status and health checks
```

### Database Operations
```bash
make db-migrate               # Run database migrations using alembic
make db-seed                  # Seed database with sample data
make db-backup                # Backup database
```

## Architecture Overview

This is a microservices-based system built with FastAPI services that communicate over HTTP and Redis. The system consists of five core services:

### Core Services
- **Model Router** (port 8001): Routes requests to appropriate AI models (Claude O3, Sonnet 4, Sonnet 3.7)
- **Plan Management** (port 8002): Manages project planning and task breakdown
- **Git Worktree Manager** (port 8003): Handles Git operations and worktree management
- **Workflow Orchestrator** (port 8004): Coordinates multi-service workflows
- **Verification Feedback** (port 8005): Provides code verification and feedback

### Key Infrastructure
- **PostgreSQL**: Primary database for persistent data
- **Redis**: Used for caching and inter-service communication
- **Consul**: Service discovery and configuration
- **Prometheus/Grafana**: Monitoring and metrics
- **Nginx**: API gateway and load balancing

### Service Communication
Services communicate primarily via HTTP APIs, with Redis used for caching and async messaging. Each service has its own database schema managed via Alembic migrations.

## Development Patterns

### Service Structure
Each service follows a consistent structure:
```
src/service_name/
├── app.py          # FastAPI application setup
├── routes.py       # API route definitions
├── models.py       # Pydantic models and database schemas
├── config.py       # Service-specific configuration
└── service_logic.py # Core business logic
```

### Common Modules
The `src/common/` directory contains shared utilities:
- `settings.py`: Base configuration using pydantic-settings
- `database.py`: SQLite utilities for local persistence
- `logging.py`: Structured logging setup
- `health_check.py`: Health check endpoints
- `metrics.py`: Prometheus metrics integration

### Configuration Management
- Environment variables loaded from `.env` file
- Service-specific settings in `config/` directory (YAML files)
- Base settings class in `src/common/settings.py` using pydantic-settings

### Database Management
- SQLite for local development and testing
- PostgreSQL for production deployment
- Alembic migrations in `database/migrations/`
- Database utilities in `src/common/database.py`

## Testing Strategy

The test suite includes:
- **Unit tests**: Individual component testing in `tests/unit/`
- **Integration tests**: Service interaction testing in `tests/integration/`
- **Performance tests**: Load and scalability testing in `tests/performance/`

Test fixtures and sample data are in `tests/fixtures/`. All tests run via pytest in Docker containers using the dev-tools service.

## Code Standards

- Use `ruff` for linting and `black` for formatting
- All functions require type hints and docstrings
- Avoid global state except where explicitly documented
- MyPy configuration in `mypy.ini` with `ignore_missing_imports = True`

## Monitoring and Observability

Services expose Prometheus metrics and structured logging. Key monitoring endpoints:
- Grafana dashboards: http://localhost:3000 (admin/admin123)
- Prometheus metrics: http://localhost:9090
- Service health checks available via `make status`

## Deployment

The system supports multiple deployment modes:
- **Development**: Docker Compose with override file
- **Production**: Docker Compose with production configuration
- **Kubernetes**: Helm charts in `helm/` directory
- **Container orchestration**: Individual Dockerfiles in `docker/` directory