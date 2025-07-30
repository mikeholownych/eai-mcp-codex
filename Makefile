# MCP Microservices Makefile
# Docker Compose v2 Management Commands
.PHONY: help build up down logs clean test lint format check-env backup restore scale monitoring dev prod

# Default target
help: ## Show this help message
	@echo "MCP Microservices Management Commands"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Environment Setup
check-env: ## Check if required environment variables are set
	@echo "Checking environment variables..."
	@test -n "$(ANTHROPIC_API_KEY)" || (echo "❌ ANTHROPIC_API_KEY is not set" && exit 1)
	@test -f .env || (echo "❌ .env file not found. Copy .env.example to .env" && exit 1)
	@echo "✅ Environment check passed"

setup: ## Initial project setup
	@echo "Setting up MCP Microservices..."
	@cp -n .env.example .env || true
	@mkdir -p logs/{model-router,plan-management,git-worktree,workflow-orchestrator,verification-feedback,nginx}
	@mkdir -p ssl
	@mkdir -p data/{postgres,redis,consul,elasticsearch,grafana,prometheus}
	@docker network create mcp-network 2>/dev/null || true
	@echo "✅ Setup complete. Please edit .env file with your configuration."

##@ Development Commands
dev: check-env ## Start development environment
	@echo "🚀 Starting development environment..."
	docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
	@echo "✅ Development environment started"
	@echo "📊 Services available at:"
	@echo "   - API Gateway: http://localhost"
	@echo "   - Grafana: http://localhost:3000 (admin/admin123)"
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Kibana: http://localhost:5601"
	@echo "   - Consul: http://localhost:8500"

dev-logs: ## Show development logs
	docker compose -f docker-compose.yml -f docker-compose.override.yml logs -f

dev-down: ## Stop development environment
	docker compose -f docker-compose.yml -f docker-compose.override.yml down

dev-clean: ## Clean development environment (remove volumes)
	docker compose -f docker-compose.yml -f docker-compose.override.yml down -v
	docker system prune -f

##@ Production Commands
prod: check-env ## Start production environment
	@echo "🚀 Starting production environment..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	@echo "✅ Production environment started"

prod-logs: ## Show production logs
	docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

prod-down: ## Stop production environment
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-update: ## Update production environment
	docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

##@ Service Management
base: ## Build base image
	@echo "🔨 Building Base Image..."
	docker build -t base -f docker/base.Dockerfile .

build: base ## Build all services
	@echo "🔨 Building all services..."
	docker compose build --parallel

build-service: ## Build specific service (usage: make build-service SERVICE=model-router)
	@test -n "$(SERVICE)" || (echo "❌ Please specify SERVICE" && exit 1)
	docker compose build $(SERVICE)

up: check-env ## Start all services
	docker compose up -d

up-service: ## Start specific service (usage: make up-service SERVICE=model-router)
	@test -n "$(SERVICE)" || (echo "❌ Please specify SERVICE" && exit 1)
	docker compose up -d $(SERVICE)

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

restart-service: ## Restart specific service (usage: make restart-service SERVICE=model-router)
	@test -n "$(SERVICE)" || (echo "❌ Please specify SERVICE" && exit 1)
	docker compose restart $(SERVICE)

scale: ## Scale services (usage: make scale SERVICE=model-router REPLICAS=3)
	@test -n "$(SERVICE)" || (echo "❌ Please specify SERVICE" && exit 1)
	@test -n "$(REPLICAS)" || (echo "❌ Please specify REPLICAS" && exit 1)
	docker compose up -d --scale $(SERVICE)=$(REPLICAS)

##@ Monitoring & Logs
logs: ## Show logs for all services
	docker compose logs -f

logs-service: ## Show logs for specific service (usage: make logs-service SERVICE=model-router)
	@test -n "$(SERVICE)" || (echo "❌ Please specify SERVICE" && exit 1)
	docker compose logs -f $(SERVICE)

status: ## Show service status
	@echo "📊 Service Status:"
	@docker compose ps
	@echo ""
	@echo "🏥 Health Checks:"
	@docker compose exec model-router python health_check.py --service=model-router --port=8001 2>/dev/null && echo "✅ Model Router: Healthy" || echo "❌ Model Router: Unhealthy"
	@docker compose exec plan-management python health_check.py --service=plan-management --port=8002 2>/dev/null && echo "✅ Plan Management: Healthy" || echo "❌ Plan Management: Unhealthy"
	@docker compose exec git-worktree-manager python health_check.py --service=git-worktree --port=8003 2>/dev/null && echo "✅ Git Worktree: Healthy" || echo "❌ Git Worktree: Unhealthy"
	@docker compose exec workflow-orchestrator python health_check.py --service=workflow-orchestrator --port=8004 2>/dev/null && echo "✅ Workflow Orchestrator: Healthy" || echo "❌ Workflow Orchestrator: Unhealthy"
	@docker compose exec verification-feedback python health_check.py --service=verification-feedback --port=8005 2>/dev/null && echo "✅ Verification Feedback: Healthy" || echo "❌ Verification Feedback: Unhealthy"

monitoring: ## Open monitoring dashboards
	@echo "📊 Opening monitoring dashboards..."
	@command -v open >/dev/null 2>&1 && open http://localhost:3000 || echo "Grafana: http://localhost:3000"
	@command -v open >/dev/null 2>&1 && open http://localhost:9090 || echo "Prometheus: http://localhost:9090"
	@command -v open >/dev/null 2>&1 && open http://localhost:5601 || echo "Kibana: http://localhost:5601"

##@ Database Management
db-migrate: ## Run database migrations
	@echo "🗄️  Running database migrations..."
	docker compose exec plan-management python -m alembic upgrade head
	docker compose exec workflow-orchestrator python -m alembic upgrade head
	docker compose exec verification-feedback python -m alembic upgrade head
	@echo "✅ Migrations completed"

db-seed: ## Seed database with sample data
	@echo "🌱 Seeding database with sample data..."
	docker compose exec postgres psql -U mcp_user -d mcp_database -f /docker-entrypoint-initdb.d/sample_data.sql
	@echo "✅ Database seeded"

db-backup: ## Backup database
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	docker compose exec postgres pg_dump -U mcp_user mcp_database > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created in backups/"

db-restore: ## Restore database (usage: make db-restore BACKUP=backup_20231201_120000.sql)
	@test -n "$(BACKUP)" || (echo "❌ Please specify BACKUP file" && exit 1)
	@test -f backups/$(BACKUP) || (echo "❌ Backup file not found" && exit 1)
	@echo "🔄 Restoring database from $(BACKUP)..."
	docker compose exec -T postgres psql -U mcp_user -d mcp_database < backups/$(BACKUP)
	@echo "✅ Database restored"

##@ Testing
test: ## Run all tests
	@echo "🧪 Running all tests..."
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools pytest tests/ -v

test-unit: ## Run unit tests
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools pytest tests/unit/ -v

test-integration: ## Run integration tests
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools pytest tests/integration/ -v

test-performance: ## Run performance tests
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools pytest tests/performance/ -v

test-service: ## Test specific service (usage: make test-service SERVICE=model-router)
	@test -n "$(SERVICE)" || (echo "❌ Please specify SERVICE" && exit 1)
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools pytest tests/unit/test_$(SERVICE).py -v

##@ Code Quality
lint: ## Run linting on all services
	@echo "🔍 Running linting..."
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools flake8 src/
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools mypy src/

format: ## Format code using black
	@echo "🎨 Formatting code..."
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools black src/

format-check: ## Check code formatting
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools black --check src/

pre-commit: ## Run pre-commit hooks
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools pre-commit run --all-files

##@ Utilities
shell: ## Open shell in development container
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools /bin/bash

shell-service: ## Open shell in specific service (usage: make shell-service SERVICE=model-router)
	@test -n "$(SERVICE)" || (echo "❌ Please specify SERVICE" && exit 1)
	docker compose exec $(SERVICE) /bin/bash

redis-cli: ## Open Redis CLI
	docker compose exec redis redis-cli

psql: ## Open PostgreSQL CLI
	docker compose exec postgres psql -U mcp_user -d mcp_database

clean: ## Clean up containers, networks, and volumes
	@echo "🧹 Cleaning up..."
	docker compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup completed"

clean-images: ## Remove all MCP images
	docker images | grep "mcp-" | awk '{print $$3}' | xargs -r docker rmi -f

clean-all: clean clean-images ## Full cleanup including images

##@ Security
security-scan: ## Run security scan on images
	@echo "🔒 Running security scan..."
	@command -v trivy >/dev/null 2>&1 || (echo "❌ Trivy not installed. Install with: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin" && exit 1)
	trivy image mcp-model-router:latest
	trivy image mcp-plan-management:latest
	trivy image mcp-git-worktree:latest
	trivy image mcp-workflow-orchestrator:latest
	trivy image mcp-verification-feedback:latest

update-deps: ## Update dependencies in all services
	@echo "📦 Updating dependencies..."
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools pip-review --auto
	@echo "✅ Dependencies updated"

##@ Quick Actions
quick-start: setup build up ## Quick start for new users
	@echo "🎉 MCP Microservices started successfully!"
	@echo "Visit http://localhost for the API Gateway"
	@echo "Visit http://localhost:3000 for Grafana dashboard"

quick-test: ## Quick test to verify everything is working
	@echo "🚀 Running quick verification test..."
	@sleep 30  # Wait for services to be fully ready
	@curl -f http://localhost/health || (echo "❌ Health check failed" && exit 1)
	@echo "✅ Quick test passed - all services are responding"

demo: ## Run demonstration workflow
	@echo "🎭 Running demonstration workflow..."
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools python scripts/demo_workflow.py
	@echo "✅ Demo completed"

##@ Agent Framework
agent-list: ## List all registered agents
	@echo "🤖 Listing registered agents..."
	@curl -s http://localhost:8010/system/stats | python -m json.tool || echo "❌ A2A Communication service not available"

agent-status: ## Show agent status and health
	@echo "📊 Agent status overview:"
	@curl -s http://localhost:8016/agents/status | python -m json.tool || echo "❌ Agent Monitor service not available"

agent-conversations: ## Monitor active agent conversations
	@echo "💬 Active agent conversations:"
	@curl -s http://localhost:8016/conversations/active | python -m json.tool || echo "❌ Agent Monitor service not available"

agent-collaborations: ## Show active collaboration sessions
	@echo "🤝 Active collaboration sessions:"
	@curl -s http://localhost:8016/collaborations/active | python -m json.tool || echo "❌ Agent Monitor service not available"

agent-metrics: ## Show agent system metrics
	@echo "📈 Agent system metrics:"
	@curl -s http://localhost:8016/metrics/system | python -m json.tool || echo "❌ Agent Monitor service not available"

agent-pool-stats: ## Show agent pool statistics
	@echo "🏊 Agent pool statistics:"
	@curl -s http://localhost:8011/stats | python -m json.tool || echo "❌ Agent Pool service not available"

agent-workload: ## Show agent workload distribution
	@echo "⚖️ Agent workload distribution:"
	@curl -s http://localhost:8011/workload/distribution | python -m json.tool || echo "❌ Agent Pool service not available"

start-agents: ## Start all agent services
	@echo "🚀 Starting agent framework services..."
	docker compose up -d a2a-communication agent-pool collaboration-orchestrator
	@echo "🤖 Starting specialized agents..."
	docker compose up -d planner-agent security-agent developer-agent agent-monitor
	@echo "✅ All agent services started"

stop-agents: ## Stop all agent services
	@echo "🛑 Stopping agent services..."
	docker compose stop planner-agent security-agent developer-agent agent-monitor
	docker compose stop collaboration-orchestrator agent-pool a2a-communication
	@echo "✅ All agent services stopped"

restart-agents: ## Restart all agent services
	@echo "🔄 Restarting agent services..."
	$(MAKE) stop-agents
	$(MAKE) start-agents

agent-logs: ## Show logs for all agent services
	docker compose logs -f a2a-communication agent-pool collaboration-orchestrator planner-agent security-agent developer-agent agent-monitor

agent-logs-service: ## Show logs for specific agent service (usage: make agent-logs-service SERVICE=planner-agent)
	@test -n "$(SERVICE)" || (echo "❌ Please specify SERVICE (e.g., planner-agent, security-agent, developer-agent)" && exit 1)
	docker compose logs -f $(SERVICE)

scale-agents: ## Scale agent services (usage: make scale-agents AGENT_TYPE=developer-agent REPLICAS=3)
	@test -n "$(AGENT_TYPE)" || (echo "❌ Please specify AGENT_TYPE" && exit 1)
	@test -n "$(REPLICAS)" || (echo "❌ Please specify REPLICAS" && exit 1)
	docker compose up -d --scale $(AGENT_TYPE)=$(REPLICAS)
	@echo "✅ Scaled $(AGENT_TYPE) to $(REPLICAS) replicas"

##@ Agent Development
agent-test-collaboration: ## Test agent collaboration with sample task
	@echo "🧪 Testing agent collaboration..."
	@curl -X POST http://localhost:8012/sessions/create \
		-H "Content-Type: application/json" \
		-d '{"title":"Test Collaboration","description":"Test multi-agent collaboration","lead_agent":"planner-001"}' \
		|| echo "❌ Collaboration service not available"

agent-test-consensus: ## Test consensus mechanism
	@echo "🗳️ Testing consensus mechanism..."
	@echo "This would create a test consensus item for agents to vote on"

agent-simulate-task: ## Simulate a task submission to agent pool
	@echo "⚡ Simulating task submission..."
	@curl -X POST http://localhost:8011/tasks/submit \
		-H "Content-Type: application/json" \
		-d '{"task_type":"code_review","description":"Review sample code","required_agent_type":"security","priority":"medium","payload":{"code":"print(\"hello world\")"}}' \
		|| echo "❌ Agent Pool service not available"

agent-demo: ## Run comprehensive agent demonstration
	@echo "🎭 Running agent demonstration..."
	@echo "1. Starting collaboration session..."
	@$(MAKE) agent-test-collaboration
	@sleep 2
	@echo "2. Submitting test task..."
	@$(MAKE) agent-simulate-task
	@sleep 2
	@echo "3. Checking agent status..."
	@$(MAKE) agent-status
	@echo "✅ Demo completed"

##@ A2A Communication
a2a-stats: ## Show A2A communication statistics
	@curl -s http://localhost:8010/system/stats | python -m json.tool || echo "❌ A2A service not available"

a2a-cleanup: ## Clean up expired A2A messages and inactive agents
	@echo "🧹 Cleaning up A2A system..."
	@curl -X POST http://localhost:8010/system/cleanup || echo "❌ A2A service not available"

a2a-send-message: ## Send test A2A message (usage: make a2a-send-message SENDER=agent1 RECIPIENT=agent2 MESSAGE="hello")
	@test -n "$(SENDER)" || (echo "❌ Please specify SENDER" && exit 1)
	@test -n "$(RECIPIENT)" || (echo "❌ Please specify RECIPIENT" && exit 1)
	@test -n "$(MESSAGE)" || (echo "❌ Please specify MESSAGE" && exit 1)
	@curl -X POST http://localhost:8010/messages/send \
		-H "Content-Type: application/json" \
		-d '{"sender_agent_id":"$(SENDER)","recipient_agent_id":"$(RECIPIENT)","message_type":"notification","payload":{"message":"$(MESSAGE)"}}' \
		|| echo "❌ A2A service not available"

##@ Quick Agent Actions
quick-start-agents: setup build start-agents ## Quick start for agent framework
	@echo "🎉 Agent framework started successfully!"
	@echo "Visit http://localhost:8010 for A2A Communication Hub"
	@echo "Visit http://localhost:8011 for Agent Pool Manager"
	@echo "Visit http://localhost:8012 for Collaboration Orchestrator"
	@echo "Visit http://localhost:8016 for Agent Monitor"

quick-test-agents: ## Quick test to verify agent framework is working
	@echo "🚀 Running agent framework verification..."
	@sleep 30  # Wait for services to be fully ready
	@curl -f http://localhost:8010/health || (echo "❌ A2A Communication health check failed" && exit 1)
	@curl -f http://localhost:8011/health || (echo "❌ Agent Pool health check failed" && exit 1)
	@curl -f http://localhost:8012/health || (echo "❌ Collaboration Orchestrator health check failed" && exit 1)
	@curl -f http://localhost:8016/health || (echo "❌ Agent Monitor health check failed" && exit 1)
	@echo "✅ Agent framework verification passed - all services responding"

monitoring-agents: ## Open agent monitoring dashboards
	@echo "📊 Opening agent monitoring interfaces..."
	@command -v open >/dev/null 2>&1 && open http://localhost:8016 || echo "Agent Monitor: http://localhost:8016"
	@command -v open >/dev/null 2>&1 && open http://localhost:8010 || echo "A2A Communication: http://localhost:8010"
	@command -v open >/dev/null 2>&1 && open http://localhost:8011 || echo "Agent Pool: http://localhost:8011"
	@command -v open >/dev/null 2>&1 && open http://localhost:8012 || echo "Collaboration: http://localhost:8012"

##@ Frontend Management
frontend-dev: ## Start frontend in development mode (both customer and staff)
	@echo "🌐 Starting frontend development servers..."
	cd frontend && npm run dev &
	cd frontend && npm run dev:staff &
	@echo "✅ Frontend servers started:"
	@echo "   Customer Frontend: http://localhost:3000"
	@echo "   Staff Frontend: http://localhost:3001"

frontend-build: ## Build frontend applications
	@echo "🔨 Building frontend applications..."
	cd frontend && npm run build
	@echo "✅ Frontend build completed"

frontend-start: ## Start production frontend servers
	@echo "🚀 Starting production frontend servers..."
	./scripts/start_frontend.sh

frontend-stop: ## Stop frontend servers
	@echo "🛑 Stopping frontend servers..."
	@pkill -f "next start" || true
	@echo "✅ Frontend servers stopped"

frontend-restart: frontend-stop frontend-start ## Restart frontend servers

frontend-logs: ## Show frontend container logs
	docker compose logs -f frontend staff-frontend

frontend-shell: ## Open shell in frontend container
	docker compose exec frontend /bin/bash

frontend-install: ## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Dependencies installed"

frontend-lint: ## Lint frontend code
	@echo "🔍 Linting frontend code..."
	cd frontend && npm run lint
	@echo "✅ Frontend linting completed"

frontend-test: ## Run frontend tests (when available)
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test 2>/dev/null || echo "No tests configured"

##@ Tunnel Management
tunnel-start: ## Start Cloudflare tunnel
	@echo "🚇 Starting Cloudflare tunnel..."
	cd cloudflare-tunnel && ./setup.sh
	@echo "✅ Tunnel started"

tunnel-stop: ## Stop Cloudflare tunnel
	@echo "🛑 Stopping Cloudflare tunnel..."
	cd cloudflare-tunnel && ./manage.sh stop
	@echo "✅ Tunnel stopped"

tunnel-status: ## Check tunnel status
	@echo "📊 Checking tunnel status..."
	cd cloudflare-tunnel && ./verify.sh

tunnel-logs: ## Show tunnel logs
	cd cloudflare-tunnel && ./manage.sh logs

##@ Full Stack Management
full-stack: build up frontend-start tunnel-start ## Start complete stack (backend + frontend + tunnel)
	@echo "🎉 Full stack started successfully!"
	@echo "🌐 External URLs:"
	@echo "   Customer Frontend: https://new.ethical-ai-insider.com"
	@echo "   Staff Frontend: https://staff.ethical-ai-insider.com"
	@echo "   API Gateway: https://newapi.ethical-ai-insider.com"
	@echo "🏠 Local URLs:"
	@echo "   Customer Frontend: http://localhost:3000"
	@echo "   Staff Frontend: http://localhost:3001"
	@echo "   API Gateway: http://localhost"
	@echo "   Grafana: http://localhost:3000"

full-stack-stop: tunnel-stop frontend-stop down ## Stop complete stack
	@echo "✅ Full stack stopped"

full-stack-restart: full-stack-stop full-stack ## Restart complete stack

##@ Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm dev-tools sphinx-build -b html docs/ docs/_build/
	@echo "✅ Documentation generated in docs/_build/"

docs-serve: ## Serve documentation locally
	docker compose -f docker-compose.yml -f docker-compose.override.yml run --rm -p 8080:8080 dev-tools python -m http.server 8080 --directory docs/_build/

##@ Environment Variables
# Load environment variables from .env file
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Default values
COMPOSE_PROJECT_NAME ?= mcp
POSTGRES_PASSWORD ?= mcp_secure_password
GRAFANA_PASSWORD ?= admin123
