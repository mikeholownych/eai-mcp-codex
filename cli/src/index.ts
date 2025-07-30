#!/usr/bin/env node

import { program } from 'commander';
import chalk from 'chalk';

import * as agent from './commands/agent';
import * as modelRouter from './commands/model-router';
import * as planManagement from './commands/plan-management';
import * as gitWorktree from './commands/git-worktree';
import * as workflowOrchestrator from './commands/workflow-orchestrator';
import * as verificationFeedback from './commands/verification-feedback';
import * as system from './commands/system';
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
program
  .command('status')
  .description('Check status of all services')
  .action(system.status);

program
  .command('health')
  .description('Check health of all services')
  .action(system.health);

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

