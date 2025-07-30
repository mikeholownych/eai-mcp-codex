#!/usr/bin/env node

/**
 * CLI Demo Script
 * Demonstrates the MCP Agent Network CLI functionality
 */

const chalk = require('chalk');
const { spawn } = require('child_process');
const path = require('path');

const CLI_PATH = path.join(__dirname, 'bin', 'mcp.js');

console.log(chalk.blue.bold('🚀 MCP Agent Network CLI Demo\n'));

async function runCommand(command, description) {
  console.log(chalk.cyan.bold(`\n📋 ${description}`));
  console.log(chalk.gray(`Running: ${command}\n`));
  
  return new Promise((resolve, reject) => {
    const [cmd, ...args] = command.split(' ');
    const process = spawn(cmd, args, { stdio: 'inherit' });
    
    process.on('close', (code) => {
      if (code === 0) {
        console.log(chalk.green(`✅ Command completed successfully\n`));
        resolve();
      } else {
        console.log(chalk.yellow(`⚠️  Command completed with code ${code}\n`));
        resolve(); // Continue demo even if command fails
      }
    });
    
    process.on('error', (error) => {
      console.log(chalk.red(`❌ Command failed: ${error.message}\n`));
      resolve(); // Continue demo even if command fails
    });
  });
}

async function runDemo() {
  try {
    // 1. Show CLI help
    await runCommand(`node ${CLI_PATH} --help`, 'Display CLI Help');
    
    // 2. Check system status
    await runCommand(`node ${CLI_PATH} status`, 'Check System Status');
    
    // 3. Show detailed health check
    await runCommand(`node ${CLI_PATH} health`, 'Detailed Health Check');
    
    // 4. Try model routing (may fail due to missing AI models)
    await runCommand(`node ${CLI_PATH} model route "This is a test prompt"`, 'Test Model Routing');
    
    // 5. Show interactive mode help
    console.log(chalk.blue.bold('\n🎯 Interactive Mode'));
    console.log(chalk.gray('To start interactive mode, run:'));
    console.log(chalk.white(`node ${CLI_PATH} interactive`));
    console.log(chalk.gray('This provides a user-friendly interface for all CLI operations.\n'));
    
    // 6. Show available commands
    console.log(chalk.blue.bold('📚 Available Commands:'));
    const commands = [
      { cmd: 'status', desc: 'Check service status' },
      { cmd: 'health', desc: 'Detailed health checks' },
      { cmd: 'model route <prompt>', desc: 'Route prompt to AI model' },
      { cmd: 'model models', desc: 'List available models' },
      { cmd: 'plan create <title>', desc: 'Create development plan' },
      { cmd: 'plan list', desc: 'List all plans' },
      { cmd: 'git create <repo> <branch>', desc: 'Create Git worktree' },
      { cmd: 'git list', desc: 'List Git worktrees' },
      { cmd: 'workflow create <name>', desc: 'Create workflow' },
      { cmd: 'workflow execute <id>', desc: 'Execute workflow' },
      { cmd: 'verify submit <type> <title>', desc: 'Submit feedback' },
      { cmd: 'verify list', desc: 'List feedback entries' },
      { cmd: 'interactive', desc: 'Start interactive mode' }
    ];
    
    commands.forEach(({ cmd, desc }) => {
      console.log(`  ${chalk.cyan(cmd.padEnd(30))} ${chalk.gray(desc)}`);
    });
    
    console.log(chalk.green.bold('\n🎉 CLI Demo Completed!'));
    console.log(chalk.blue('The MCP Agent Network CLI is ready for use.'));
    console.log(chalk.gray('Run any of the commands above to interact with the agent network.\n'));
    
  } catch (error) {
    console.error(chalk.red(`Demo failed: ${error.message}`));
    process.exit(1);
  }
}

if (require.main === module) {
  runDemo();
}

module.exports = { runDemo };