#!/usr/bin/env node

import { program } from 'commander';
import chalk from 'chalk';

import * as agent from './commands/agent';
import * as modelRouter from './commands/model-router';
import * as planManagement from './commands/plan-management';
import * as gitWorktree from './commands/git-worktree';
import * as workflowOrchestrator from './commands/workflow-orchestrator';
import * as verificationFeedback from './commands/verification-feedback';
import * as configuration from './commands/configuration';
import { interactive } from './commands/interactive';
import { chat } from './commands/chat';

const packageJson = require('../package.json');

program
  .name('mcp')
  .description(chalk.blue('MCP Agent Network CLI - Interface with microservice-based AI agents'))
  .version(packageJson.version);

// Global options
program
  .option('-h, --host <host>', 'API host', 'localhost')
  .option('-v, --verbose', 'verbose output')
  .option('--json', 'output in JSON format');

// System commands

// Model Router commands
const modelCmd = program
  .command('model')
  .description('Interact with Model Router service');

modelCmd
  .command('route <prompt>')
  .description('Route a prompt to appropriate model')
  .option('-m, --model <model>', 'force specific model')
  .option('-t, --temperature <temp>', 'model temperature', '0.7')
  .action(modelRouter.route);

modelCmd
  .command('models')
  .description('List available models')
  .action(modelRouter.listModels);

// Plan Management commands
const planCmd = program
  .command('plan')
  .description('Manage development plans');

planCmd
  .command('create <title>')
  .description('Create a new plan')
  .option('-d, --description <desc>', 'plan description')
  .option('-t, --tags <tags>', 'comma-separated tags')
  .action(planManagement.create);

planCmd
  .command('list')
  .description('List all plans')
  .option('-s, --status <status>', 'filter by status')
  .action(planManagement.list);

planCmd
  .command('show <planId>')
  .description('Show plan details')
  .action(planManagement.show);

planCmd
  .command('update <planId>')
  .description('Update a plan')
  .option('-s, --status <status>', 'update status')
  .action(planManagement.update);

// Git Worktree commands
const gitCmd = program
  .command('git')
  .description('Manage Git worktrees');

gitCmd
  .command('create <repo> <branch>')
  .description('Create a new worktree')
  .option('-p, --path <path>', 'worktree path')
  .action(gitWorktree.create);

gitCmd
  .command('list')
  .description('List all worktrees')
  .action(gitWorktree.list);

gitCmd
  .command('remove <worktreeId>')
  .description('Remove a worktree')
  .action(gitWorktree.remove);

// Workflow Orchestrator commands
const workflowCmd = program
  .command('workflow')
  .description('Manage workflows');

workflowCmd
  .command('create <name>')
  .description('Create a new workflow')
  .option('-s, --steps <steps>', 'workflow steps JSON')
  .action(workflowOrchestrator.create);

workflowCmd
  .command('execute <workflowId>')
  .description('Execute a workflow')
  .action(workflowOrchestrator.execute);

workflowCmd
  .command('status <workflowId>')
  .description('Check workflow status')
  .action(workflowOrchestrator.status);

// Verification Feedback commands
const verifyCmd = program
  .command('verify')
  .description('Verification and feedback operations');

verifyCmd
  .command('submit <type> <title>')
  .description('Submit feedback')
  .option('-d, --description <desc>', 'feedback description')
  .option('-s, --severity <severity>', 'severity level', 'medium')
  .action(verificationFeedback.submit);

verifyCmd
  .command('list')
  .description('List feedback entries')
  .action(verificationFeedback.list);

// Interactive mode
program
  .command('interactive')
  .alias('i')
  .description('Start interactive mode')
  .action(interactive);

program
  .command('chat')
  .description('Start chat mode with AI assistant')
  .action(chat);

// Configuration commands
const listCmd = program
  .command('list')
  .description('List MCP configurations');

listCmd
  .command('agents')
  .description('List available agent configurations')
  .option('--scope <scope>', 'Configuration scope (default|global|project|all)', 'all')
  .option('--format <format>', 'Output format (table|json|yaml)', 'table')
  .option('--detailed', 'Show detailed information')
  .option('--filter-tags <tags>', 'Filter by tags (comma-separated)')
  .option('--sort-by <field>', 'Sort by field (name|type|priority|lastModified)')
  .option('--sort-order <order>', 'Sort order (asc|desc)', 'asc')
  .action(configuration.listAgents);

listCmd
  .command('commands')
  .description('List available command configurations')
  .option('--scope <scope>', 'Configuration scope (default|global|project|all)', 'all')
  .option('--format <format>', 'Output format (table|json|yaml)', 'table')
  .option('--detailed', 'Show detailed information')
  .option('--filter-tags <tags>', 'Filter by tags (comma-separated)')
  .option('--sort-by <field>', 'Sort by field (name|type|priority|lastModified)')
  .option('--sort-order <order>', 'Sort order (asc|desc)', 'asc')
  .action(configuration.listCommands);

listCmd
  .command('all')
  .description('List all configurations (agents and commands)')
  .option('--scope <scope>', 'Configuration scope (default|global|project|all)', 'all')
  .option('--format <format>', 'Output format (table|json|yaml)', 'table')
  .option('--detailed', 'Show detailed information')
  .option('--filter-tags <tags>', 'Filter by tags (comma-separated)')
  .option('--sort-by <field>', 'Sort by field (name|type|priority|lastModified)')
  .option('--sort-order <order>', 'Sort order (asc|desc)', 'asc')
  .action(configuration.listAll);

// Make 'list' without subcommand show all configurations
listCmd.action(() => {
  configuration.listAll();
});

// Doctor command
program
  .command('doctor')
  .description('Run configuration diagnostics and validation')
  .option('--check-all', 'Check all aspects of configuration')
  .option('--fix-issues', 'Attempt to fix found issues')
  .option('--verbose', 'Show detailed diagnostic information')
  .option('--output-format <format>', 'Output format (text|json)', 'text')
  .option('--include-warnings', 'Include warnings in output')
  .action(configuration.doctor);

// Init command
program
  .command('init [scope]')
  .description('Initialize MCP configuration directories and example files')
  .option('--scope <scope>', 'Configuration scope (global|project)', 'project')
  .action((scope, options) => {
    const targetScope = scope || options.scope || 'project';
    configuration.initializeConfiguration(targetScope as 'global' | 'project');
  });

// Error handling
program.on('command:*', () => {
  console.error(chalk.red(`Invalid command: ${program.args.join(' ')}`));
  console.log(chalk.yellow('See --help for a list of available commands.'));
  process.exit(1);
});

// Agent commands
const agentCmd = program
  .command('agent')
  .description('AI coding assistant');

agentCmd
  .command('plan <task>')
  .description('Generate a plan to accomplish a task')
  .action(agent.plan);

agentCmd
  .command('execute <planId>')
  .description('Execute a previously generated plan')
  .action(agent.execute);

agentCmd
  .command('generate <prompt> <filePath>')
  .description('Generate code based on a prompt')
  .action(agent.generate);

agentCmd
  .command('refactor <file_path> <prompt>')
  .description('Refactor a specific file based on a prompt')
  .action(agent.refactor);

agentCmd
  .command('verify <file_path>')
  .description('Run tests and linting on a specified file')
  .action(agent.verify);

program.parse();

