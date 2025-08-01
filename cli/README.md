# MCP Agent Network CLI

A powerful command-line interface for interacting with the MCP (Model Communication Protocol) Agent Network - a microservices-based AI agent system.

## Features

- 🤖 **Model Router**: Route prompts to appropriate AI models with intelligent routing
- 📝 **Plan Management**: Create and manage development plans and tasks
- 🌿 **Git Worktree**: Manage Git worktrees for isolated development
- ⚡ **Workflow Orchestrator**: Create and execute complex workflows
- 🔍 **Verification Feedback**: Submit feedback and verify code quality
- 🎯 **Interactive Mode**: User-friendly interactive interface
- 📊 **System Status**: Monitor service health and performance

## Installation

### Prerequisites

- Node.js 16.0.0 or higher
- MCP Agent Network services running (see main project README)

### Install Dependencies

```bash
cd cli
npm install
```

### Make CLI Globally Available

```bash
npm link
```

Or run directly:

```bash
chmod +x bin/mcp.js
```

## Quick Start

### Check System Status

```bash
mcp status
mcp health
```

### Interactive Mode

```bash
mcp interactive
# or
mcp i
```

### Model Router

```bash
# Ask AI a question
mcp model route "Explain microservices architecture"

# Force specific model
mcp model route "Write a Python function" --model sonnet

# List available models
mcp models
```

### Plan Management

```bash
# Create a new plan
mcp plan create "Build user authentication" --description "Implement JWT-based auth system"

# List all plans
mcp plan list

# Show plan details
mcp plan show <plan-id>

# Update plan status
mcp plan update <plan-id> --status active
```

### Git Worktree Management

```bash
# Create worktree
mcp git create https://github.com/user/repo.git feature-branch

# List worktrees
mcp git list

# Remove worktree
mcp git remove <worktree-id>
```

### Workflow Orchestration

```bash
# Create workflow
mcp workflow create "Deploy Application" --steps '[{"name":"build","type":"code_generation"},{"name":"test","type":"verification"}]'

# Execute workflow
mcp workflow execute <workflow-id>

# Check workflow status
mcp workflow status <workflow-id>
```

### Verification & Feedback

```bash
# Submit feedback
mcp verify submit bug_report "API endpoint returning 500" --severity high --description "User login endpoint fails intermittently"

# List feedback
mcp verify list

# Verify code file
mcp verify code src/auth.py --language python --types syntax,security,quality
```

## Configuration

The CLI reads configuration from:

1. Environment variables
2. `.env` file in the project root
3. Command-line options

### Environment Variables

```bash
# Service endpoints
MODEL_ROUTER_URL=http://localhost:8001
PLAN_MANAGEMENT_URL=http://localhost:8002
GIT_WORKTREE_URL=http://localhost:8003
WORKFLOW_ORCHESTRATOR_URL=http://localhost:8004
VERIFICATION_FEEDBACK_URL=http://localhost:8005

# Debug mode
DEBUG=true
```

## Command Reference

### Global Options

- `--host <host>`: API host (default: localhost)
- `--verbose`: Verbose output
- `--json`: Output in JSON format

### System Commands

- `mcp status`: Check service status
- `mcp health`: Detailed health check

### Model Router Commands

- `mcp model route <prompt>`: Route prompt to AI model
  - `--model <model>`: Force specific model
  - `--temperature <temp>`: Model temperature (default: 0.7)
- `mcp model models`: List available models

### Plan Management Commands

- `mcp plan create <title>`: Create new plan
  - `--description <desc>`: Plan description
  - `--tags <tags>`: Comma-separated tags
- `mcp plan list`: List all plans
  - `--status <status>`: Filter by status
- `mcp plan show <planId>`: Show plan details
- `mcp plan update <planId>`: Update plan
  - `--status <status>`: Update status

### Git Worktree Commands

- `mcp git create <repo> <branch>`: Create worktree
  - `--path <path>`: Custom worktree path
- `mcp git list`: List all worktrees
- `mcp git remove <worktreeId>`: Remove worktree

### Workflow Orchestrator Commands

- `mcp workflow create <name>`: Create workflow
  - `--steps <steps>`: Workflow steps JSON
- `mcp workflow execute <workflowId>`: Execute workflow
- `mcp workflow status <workflowId>`: Check workflow status

### Verification Feedback Commands

- `mcp verify submit <type> <title>`: Submit feedback
  - `--description <desc>`: Feedback description
  - `--severity <severity>`: Severity level (low|medium|high|critical)
- `mcp verify list`: List feedback entries

### Batch Execution Command

- `mcp batch <file>`: Run a sequence of commands from a JSON or YAML file
  - `--format <format>`: Specify `json` or `yaml` explicitly

## Development  

### Project Structure

```
cli/
├── bin/mcp.js              # CLI entry point
├── commands/               # Command handlers
│   ├── system.js
│   ├── model-router.js
│   ├── plan-management.js
│   ├── git-worktree.js
│   ├── workflow-orchestrator.js
│   ├── verification-feedback.js
│   └── interactive.js
├── lib/                    # Utilities and clients
│   ├── clients/            # Service clients
│   ├── http-client.js      # HTTP client utility
│   └── utils.js            # Helper functions
├── config/                 # Configuration
└── package.json
```

### Adding New Commands

1. Create command handler in `commands/`
2. Create service client in `lib/clients/`
3. Register command in `bin/mcp.js`
4. Update README

### Error Handling

The CLI includes comprehensive error handling:

- Network timeouts and retries
- Service unavailability detection
- Input validation
- Graceful error messages

## Troubleshooting

### Service Connection Issues

```bash
# Check if services are running
mcp status

# Test individual service health
curl http://localhost:8001/health
```

### Permission Issues

```bash
# Make CLI executable
chmod +x bin/mcp.js

# Install globally
sudo npm link
```

### Environment Configuration

```bash
# Copy example environment file
cp ../.env.example ../.env

# Edit configuration
nano ../.env
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-command`
3. Make changes and test: `npm test`
4. Submit pull request

## License

MIT License - see LICENSE file for details.