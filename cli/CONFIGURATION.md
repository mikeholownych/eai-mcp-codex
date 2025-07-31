# MCP Configuration System

A comprehensive configuration system for the MCP Agent Network CLI that supports scoped agent and command definitions via Markdown files with YAML front matter.

## Overview

The MCP Configuration System provides a hierarchical, file-based approach to defining AI agents and commands. It supports three scopes:

- **Default** (`cli/config/default/`): Built-in system configurations
- **Global** (`~/.mcp/`): User-wide configurations  
- **Project** (`./.mcp/`): Project-specific configurations

Configuration resolution follows the priority: **Project > Global > Default**

## Quick Start

### 1. Initialize Configuration

```bash
# Initialize project-level configuration
mcp init

# Initialize global configuration  
mcp init global
```

### 2. List Available Configurations

```bash
# List all agents
mcp list agents

# List all commands
mcp list commands

# List everything with details
mcp list all --detailed
```

### 3. Validate Configuration

```bash
# Run comprehensive diagnostics
mcp doctor

# Verbose diagnostics with warnings
mcp doctor --verbose --include-warnings
```

## Directory Structure

```
~/.mcp/                          # Global configurations
├── enhanced-planner.md          # Agent definition
├── security-reviewer.md         # Another agent
└── commands/                    # Command definitions
    ├── advanced-generate.md
    ├── security-audit.md
    └── deploy.md

./.mcp/                          # Project configurations  
├── project-planner.md           # Project-specific agent
├── custom-agent.md              # Override global agent
└── commands/                    # Project commands
    ├── test.md                  # Override global test command
    └── build.md                 # Project-specific command
```

## Agent Configuration Format

Agent configurations define AI assistants with specific capabilities and behaviors:

```markdown
---
name: enhanced-planner
scope: project
tags: [planner, agent, strategic]
version: 1.2.0
priority: 10
agent_type: planner
capabilities:
  - task-breakdown
  - dependency-analysis
  - strategic-planning
model_preferences:
  - claude-sonnet-4
  - gpt-4o
multi_agent: true
collaboration_mode: consensus
escalation_threshold: 0.8
security_level: medium
author: Your Team
description: Enhanced planner with strategic capabilities
---

# Enhanced Planner Agent

Description of the agent's role and capabilities.

## System Prompt

The system prompt that initializes this agent.

## Instructions

Detailed instructions for the agent's behavior.

## Examples

Example interactions and expected outputs.

## Constraints

- Security requirements
- Operational constraints
- Quality standards
```

### Agent Front Matter Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique agent identifier (required) |
| `agent_type` | enum | planner, developer, security, domain-expert, custom |
| `capabilities` | array | List of agent capabilities |
| `model_preferences` | array | Preferred AI models |
| `multi_agent` | boolean | Supports collaboration |
| `collaboration_mode` | enum | sequential, parallel, consensus |
| `security_level` | enum | low, medium, high, critical |
| `priority` | number | Resolution priority (higher wins) |

## Command Configuration Format

Command configurations define executable operations with validation and lifecycle hooks:

```markdown
---
name: advanced-generate
scope: project
tags: [command, generation, enhanced]
version: 1.3.0
command_type: generation
output_format: code
required_context:
  - file-structure
  - coding-standards
security_level: medium
timeout_ms: 45000
retry_attempts: 2
author: Your Team
description: Advanced code generation with validation
---

# Advanced Generate Command

Enhanced code generation with quality assurance.

## Parameters

- **prompt**: Code generation prompt (string, required)
- **filePath**: Target file path (string, required)  
- **language**: Programming language (string, optional)

## Instructions

Detailed execution instructions for this command.

## Pre-execution Checks

- Validate parameters
- Check permissions
- Verify working directory

## Post-execution Actions

- Validate outputs
- Run security scan
- Log results
```

### Command Front Matter Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique command identifier (required) |
| `command_type` | enum | generation, analysis, refactoring, testing, deployment |
| `output_format` | enum | json, markdown, plain, code |
| `required_context` | array | Required context for execution |
| `timeout_ms` | number | Execution timeout in milliseconds |
| `retry_attempts` | number | Number of retry attempts |

## CLI Commands

### List Commands

```bash
# List agents with filtering and sorting
mcp list agents --scope project --sort-by priority --detailed

# Filter by tags
mcp list agents --filter-tags planner,strategic

# JSON output for scripting
mcp list commands --format json

# List specific scope only
mcp list commands --scope global
```

### Doctor Command

```bash
# Basic health check
mcp doctor

# Comprehensive diagnostics
mcp doctor --verbose --check-all

# JSON output for CI/CD
mcp doctor --output-format json
```

## Configuration Resolution

The system resolves configurations using a hierarchical approach:

1. **Load all scopes**: Default → Global → Project
2. **Merge by name**: Configurations with the same name are merged
3. **Apply priority**: Higher priority values override lower ones
4. **Resolve conflicts**: Based on `conflictResolution` strategy

### Conflict Resolution Strategies

- **merge** (default): Merge configurations, project takes precedence
- **override**: Project completely overrides global/default
- **strict**: Throw error on conflicts

### Example Resolution

```yaml
# Global: ~/.mcp/planner.md
name: planner
priority: 5
capabilities: [planning, analysis]

# Project: ./.mcp/planner.md  
name: planner
priority: 10
capabilities: [planning, security-review]
security_level: high

# Resolved Result:
name: planner
priority: 10                    # Project wins (higher priority)
capabilities: [planning, analysis, security-review]  # Merged
security_level: high            # Project only
```

## Integration with Agent Execution

The configuration system is fully integrated with agent execution:

### Enhanced Planning

```typescript
// Agent execution now uses configured planner agents
const client = new AgentClient();
const plan = await client.createPlan("Build user authentication", "enhanced-planner");
```

### Configuration-Aware Commands

```typescript
// Commands automatically load their configurations
await client.dispatchCommand("advanced-generate", {
  prompt: "React user profile component",
  filePath: "src/components/UserProfile.tsx"
});
```

### Validation and Context

- Parameters are validated against command schemas
- Pre/post execution hooks are automatically run
- Security levels are enforced based on configuration
- Context requirements are checked before execution

## Advanced Features

### Configuration Inheritance

```yaml
# Base agent
name: base-developer
agent_type: developer
capabilities: [coding, testing]

# Specialized agent
name: react-developer  
extends: base-developer
capabilities: [coding, testing, react, typescript]
```

### Environment-Specific Configs

```yaml
# Development environment
environment: development
security_level: low
auto_verify: false

# Production environment  
environment: production
security_level: high
auto_verify: true
```

### Multi-Agent Collaboration

```yaml
name: security-reviewer
multi_agent: true
collaboration_mode: consensus
escalation_threshold: 0.7
required_permissions: [security-scan, code-review]
```

## Best Practices

### 1. Naming Conventions
- Use kebab-case for configuration names
- Include purpose in name: `security-code-reviewer`
- Version your configurations: `v1.2.0`

### 2. Documentation
- Always include comprehensive descriptions
- Provide examples for complex configurations
- Document any special requirements or constraints

### 3. Security
- Set appropriate security levels
- Define required permissions explicitly
- Use sandboxing for untrusted operations

### 4. Testing
- Validate configurations with `mcp doctor`
- Test agent behaviors with example scenarios
- Version control your configurations

### 5. Organization
- Group related agents by domain
- Use consistent tagging schemes
- Keep project configs focused and minimal

## Troubleshooting

### Common Issues

**Configuration not found:**
```bash
# Check configuration paths
mcp doctor --verbose

# List available configurations
mcp list all
```

**Validation errors:**
```bash
# Run diagnostics
mcp doctor --include-warnings

# Check specific file
mcp doctor --check-all
```

**Command execution fails:**
```bash
# Verify command configuration
mcp list commands --detailed --filter-tags your-command

# Check parameter schema
mcp doctor --verbose
```

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
# Set debug environment
export MCP_LOG_LEVEL=debug

# Run with verbose output
mcp list agents --verbose
mcp doctor --verbose
```

## API Reference

For programmatic access to the configuration system:

```typescript
import { ConfigurationManager } from './config/configuration-manager';
import { AgentDefinitionLoader } from './loaders/agent-definition-loader';

const configManager = new ConfigurationManager();
const agentLoader = new AgentDefinitionLoader(configManager);

// Load all agents
const agents = await agentLoader.loadAgentDefinitions();

// Load specific agent
const planner = await agentLoader.loadAgentDefinition('enhanced-planner');

// Validate configurations
const validation = await configManager.doctor();
```

## Contributing

When contributing new configurations:

1. Follow the established naming conventions
2. Include comprehensive documentation
3. Add appropriate tags and metadata
4. Test with `mcp doctor` before submitting
5. Update this documentation if adding new features

## Migration Guide

### From Hardcoded to Configuration-Based

1. Create configuration files for existing agents/commands
2. Test with `mcp doctor` to ensure validity
3. Update any hardcoded references to use configuration names
4. Remove deprecated hardcoded implementations

### Version Updates

When updating configuration versions:
1. Increment version number in front matter
2. Update `updated_at` timestamp
3. Document changes in configuration content
4. Test backward compatibility where possible