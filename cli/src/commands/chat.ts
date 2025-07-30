import chalk from 'chalk';
import inquirer from 'inquirer';
import ora from 'ora';
import { AgentClient } from './agent';

export async function chat() {
  console.log(chalk.blue.bold('💬 MCP Agent Network - Chat Mode\n'));
  console.log(chalk.gray('Type "exit" or "quit" to end the chat.\n'));

  const agentClient = new AgentClient();

  while (true) {
    try {
      const { userInput } = await inquirer.prompt([
        {
          type: 'input',
          name: 'userInput',
          message: chalk.green('You:'),
        },
      ]);

      const trimmedInput = userInput.trim();

      if (trimmedInput.toLowerCase() === 'exit' || trimmedInput.toLowerCase() === 'quit') {
        console.log(chalk.blue('\n👋 Goodbye!'));
        break;
      }

      const spinner = ora('Agent: Thinking...').start();

      const llmPrompt = `Analyze the following user input and determine the intended command and its arguments. Respond with a JSON object in the format: { "command": "<command_name>", "args": { "<arg_name>": "<arg_value>" } }. If no specific command is identified, use "unknown".

Available commands and their expected arguments:
- plan <task>: Generate a plan for a task. (e.g., {"command": "plan", "args": {"task": "Create a new React component"}})
- execute <planId>: Execute a plan. (e.g., {"command": "execute", "args": {"planId": "plan-123"}})
- generate <prompt> <filePath>: Generate code. (e.g., {"command": "generate", "args": {"prompt": "a login form", "filePath": "src/LoginForm.js"}})
- refactor <filePath> <prompt>: Refactor code. (e.g., {"command": "refactor", "args": {"filePath": "src/App.js", "prompt": "simplify the rendering logic"}})
- verify <filePath>: Verify code. (e.g., {"command": "verify", "args": {"filePath": "src/test.js"}})
- status: Check system status. (e.g., {"command": "status"})
- health: Check system health. (e.g., {"command": "health"})
- model route <prompt>: Route a prompt to a model. (e.g., {"command": "model_route", "args": {"prompt": "What is the capital of France?"}})
- model list: List available models. (e.g., {"command": "model_list"})
- plan create <title>: Create a new plan. (e.g., {"command": "plan_create", "args": {"title": "Build a new feature"}})
- plan list: List all plans. (e.g., {"command": "plan_list"})
- plan show <planId>: Show plan details. (e.g., {"command": "plan_show", "args": {"planId": "plan-123"}})
- plan update <planId> <status>: Update a plan. (e.g., {"command": "plan_update", "args": {"planId": "plan-123", "status": "completed"}})
- git create <repo> <branch> [path]: Create a git worktree. (e.g., {"command": "git_create", "args": {"repo": "my-repo", "branch": "dev", "path": "."}})
- git list: List git worktrees. (e.g., {"command": "git_list"})
- git remove <worktreeId>: Remove a git worktree. (e.g., {"command": "git_remove", "args": {"worktreeId": "wt-123"}})
- workflow create <name> [steps]: Create a workflow. (e.g., {"command": "workflow_create", "args": {"name": "deploy-app", "steps": "[{ \"name\": \"build\" }]"}})
- workflow execute <workflowId>: Execute a workflow. (e.g., {"command": "workflow_execute", "args": {"workflowId": "wf-123"}})
- workflow status <workflowId>: Check workflow status. (e.g., {"command": "workflow_status", "args": {"workflowId": "wf-123"}})
- verify submit <type> <title> [description] [severity]: Submit feedback. (e.g., {"command": "verify_submit", "args": {"type": "bug_report", "title": "UI bug"}})
- verify list: List feedback. (e.g., {"command": "verify_list"})
- verify show <feedbackId>: Show feedback details. (e.g., {"command": "verify_show", "args": {"feedbackId": "fb-123"}})

User input: ${trimmedInput}

JSON Response:`;

      let llmResponse;
      try {
        llmResponse = await agentClient.llmClient.generateText(llmPrompt);
        spinner.succeed('Agent: Understood.');
      } catch (llmError: any) {
        spinner.fail(`Agent: Failed to communicate with LLM: ${llmError.message}`);
        console.log(chalk.red('Agent: I\'m having trouble understanding right now. Please try again.'));
        continue;
      }

      let parsedCommand;
      try {
        parsedCommand = JSON.parse(llmResponse);
      } catch (parseError) {
        console.log(chalk.red('Agent: I received an unparseable response from the AI. Please try rephrasing.'));
        continue;
      }

      const { command, args } = parsedCommand;

      // Dispatch the command through the AgentClient's dispatchCommand method
      try {
        await agentClient.dispatchCommand(command, args);
      } catch (dispatchError: any) {
        console.error(chalk.red(`Agent: Error executing command: ${dispatchError.message}`));
      }

    } catch (error: any) {
      if (error.isTtyError || error.name === 'ExitPromptError') {
        console.log(chalk.blue('\n👋 Goodbye!'));
        break;
      }
      console.error(chalk.red(`Agent: An unexpected error occurred: ${error.message}`));
    }
  }
}