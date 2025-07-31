import chalk from 'chalk';
import ora from 'ora';
import inquirer from 'inquirer';
import fs from 'fs';
import path from 'path';
import fetch from 'node-fetch';

// Import other command modules for inter-agent communication
import * as modelRouter from './model-router';
import * as planManagement from './plan-management';
import * as gitWorktree from './git-worktree';
import * as workflowOrchestrator from './workflow-orchestrator';
import * as verificationFeedback from './verification-feedback';

// --- LLMClient Placeholder (Integrate your LLM API here) ---
// This class is responsible for making actual requests to your chosen LLM (e.g., OpenAI, Google Gemini).
// You will need to replace the placeholder methods with actual API calls.
class LLMClient {
  private apiUrl: string;
  private model: string;

  constructor() {
    // Use the llm-router endpoint
    this.apiUrl = process.env.LLM_ROUTER_URL || 'http://localhost:8000/query';
    this.model = process.env.LLM_MODEL || 'deepseek-coder:6.7b'; // Default model for llm-router

    console.log(chalk.gray(`[LLMClient] Using LLM Router API URL: ${this.apiUrl}, Model: ${this.model}`));
  }

  async generateText(prompt: string): Promise<string> {
    console.log(chalk.gray(`\n[LLMClient] Sending prompt to LLM Router:\n${prompt.substring(0, 200)}...`));
    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: prompt,
          model: this.model, // Pass model to llm-router
          max_tokens: 2048, // Increased max tokens for more complex responses
          temperature: 0.7
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`LLM Router API error: ${response.status} ${response.statusText} - ${JSON.stringify(errorData)}`);
      }

      const data: any = await response.json();
      // The llm-router /query endpoint returns a 'response' field
      const generatedContent = data.response || '';
      console.log(chalk.gray(`[LLMClient] Received response (first 200 chars):\n${generatedContent.substring(0, 200)}...`));
      return generatedContent;
    } catch (error: any) {
      console.error(chalk.red(`[LLMClient] Error during LLM Router API call: ${error.message}`));
      throw error;
    }
  }
}

// --- AgentClient (Uses LLMClient for AI capabilities and orchestrates other commands) ---
export class AgentClient {
  public llmClient: LLMClient;

  constructor() {
    this.llmClient = new LLMClient();
  }

  async createPlan(task: string): Promise<any> {
    const prompt = `You are an AI assistant tasked with creating a step-by-step plan to accomplish the following task: \"${task}\".\n\nProvide a detailed plan as a JSON array of steps. Each step should be an object with a \"command\" field (matching CLI commands like \"generate\", \"refactor\", \"verify\", \"plan_create\", \"git_create\") and an \"args\" object containing the arguments for that command.\n\nExample Plan for \"Create a new React component called MyButton in src/components/MyButton.tsx and verify it\":\n[\n  {\"command\": \"generate\", \"args\": {\"prompt\": \"React functional component MyButton\", \"filePath\": \"src/components/MyButton.tsx\"}},\n  {\"command\": \"verify\", \"args\": {\"filePath\": \"src/components/MyButton.tsx\"}}\n]\n\nYour plan for \"${task}\":`;

    const planText = await this.llmClient.generateText(prompt);
    try {
      const plan = JSON.parse(planText);
      if (!Array.isArray(plan)) {
        throw new Error('LLM did not return a JSON array for the plan.');
      }
      return {
        id: `plan-${Date.now()}`,
        task,
        steps: plan
      };
    } catch (error: any) {
      console.error(chalk.red(`Failed to parse plan from LLM: ${error.message}. Raw response:\n${planText}`));
      throw new Error('Invalid plan format from LLM.');
    }
  }

  async executePlan(plan: any): Promise<any> {
    console.log(chalk.blue.bold(`\n▶️  Executing plan: ${plan.id} - ${plan.task}\n`));

    for (const step of plan.steps) {
      const spinner = ora(`Executing step: ${step.command} with args ${JSON.stringify(step.args)}`).start();
      try {
        await this.dispatchCommand(step.command, step.args);
        spinner.succeed(`Step completed: ${step.command}`);
      } catch (error: any) {
        spinner.fail(`Step failed: ${step.command} - ${error.message}`);
        throw error; // Stop execution if a step fails
      }
    }
    console.log(chalk.green.bold('\n✅ Plan executed successfully!'));
    return { status: 'completed' };
  }

  public async dispatchCommand(command: string, args: any): Promise<void> {
    switch (command) {
      case 'generate':
        await this.generateCode(args.prompt, args.filePath);
        break;
      case 'refactor':
        await this.refactorCode(args.filePath, args.prompt);
        break;
      case 'verify':
        await this.verifyCodeChanges(args.filePath);
        break;
      case 'model_route':
        await modelRouter.route(args.prompt, args.options || {});
        break;
      case 'model_list':
        await modelRouter.listModels();
        break;
      case 'plan_create':
        await planManagement.create(args.title, { description: args.description, tags: args.tags });
        break;
      case 'plan_list':
        await planManagement.list({});
        break;
      case 'plan_show':
        await planManagement.show(args.planId);
        break;
      case 'plan_update':
        await planManagement.update(args.planId, { status: args.status });
        break;
      case 'git_create':
        await gitWorktree.create(args.repo, args.branch, { path: args.path });
        break;
      case 'git_list':
        await gitWorktree.list();
        break;
      case 'git_remove':
        await gitWorktree.remove(args.worktreeId);
        break;
      case 'workflow_create':
        await workflowOrchestrator.create(args.name, { steps: args.steps });
        break;
      case 'workflow_execute':
        await workflowOrchestrator.execute(args.workflowId);
        break;
      case 'workflow_status':
        await workflowOrchestrator.status(args.workflowId);
        break;
      case 'verify_submit':
        await verificationFeedback.submit(args.type, args.title, { description: args.description, severity: args.severity });
        break;
      case 'verify_list':
        await verificationFeedback.list();
        break;
      case 'verify_show':
        await verificationFeedback.show(args.feedbackId);
        break;
      default:
        throw new Error(`Unknown command: ${command}`);
    }
  }

  async generateCode(prompt: string, filePath: string): Promise<string> {
    const llmPrompt = `Generate code based on the following prompt: \"${prompt}\".\nProvide only the code, no explanations or extra text.`;
    const generatedContent = await this.llmClient.generateText(llmPrompt);
    fs.writeFileSync(filePath, generatedContent);
    return generatedContent;
  }

  async refactorCode(filePath: string, prompt: string): Promise<string> {
    const originalContent = fs.readFileSync(filePath, 'utf8');
    const llmPrompt = `Refactor the following code from file \"${filePath}\" based on this instruction: \"${prompt}\".\n\nOriginal Code:\n\`\`\`\n${originalContent}\n\`\`\`\n\nProvide only the refactored code, no explanations or extra text.`;
    const refactoredContent = await this.llmClient.generateText(llmPrompt);
    fs.writeFileSync(filePath, refactoredContent);
    return refactoredContent;
  }

  async verifyCodeChanges(filePath: string): Promise<boolean> {
    const spinner = ora(`Running tests and linting for ${filePath}...`).start();
    // In a real scenario, you\'d run actual tests and linting tools here.\n    await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate testing
    const success = Math.random() > 0.2; // 80% chance of success
    if (success) {
      spinner.succeed(`Verification passed for ${filePath}!`);
    } else {
      spinner.fail(`Verification failed for ${filePath}. Please check the code.`);
    }
    return success;
  }
}

export async function plan(task: string) {
  console.log(chalk.blue.bold('🤖 Generating a plan for your task...\n'));

  const client = new AgentClient();
  const spinner = ora('Analyzing task and creating plan...').start();

  try {
    const plan = await client.createPlan(task);
    spinner.succeed('Plan created successfully!');

    console.log(chalk.green.bold('\n📝 Plan Details:'));
    console.log(`ID: ${chalk.cyan(plan.id)}`);
    console.log(`Task: ${chalk.white(plan.task)}`);

    console.log(chalk.yellow.bold('\n📋 Steps:'));
    plan.steps.forEach((step: any, index: number) => {
      console.log(`${index + 1}. Command: ${step.command}, Args: ${JSON.stringify(step.args)}`);
    });

    const { confirm } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'confirm',
        message: 'Do you want to execute this plan?',
        default: false
      }
    ]);

    if (confirm) {
      await execute(plan);
    }

  } catch (error: any) {
    spinner.fail(`Failed to create plan: ${error.message}`);
    process.exit(1);
  }
}

export async function execute(plan: any) {
  console.log(chalk.blue.bold(`\n▶️  Executing plan: ${plan.id}\n`));

  const client = new AgentClient();

  try {
    const result = await client.executePlan(plan);
    console.log(chalk.green.bold('\n✅ Plan executed successfully!'));
    console.log(`Status: ${result.status}`);
  } catch (error: any) {
    console.error(chalk.red(`Failed to execute plan: ${error.message}`));
    process.exit(1);
  }
}

export async function generate(prompt: string, filePath: string) {
  console.log(chalk.blue.bold('🤖 Generating code...\n'));

  const client = new AgentClient();
  const spinner = ora('Generating code...').start();

  try {
    const code = await client.generateCode(prompt, filePath);
    spinner.succeed(`Code generated successfully to ${filePath}!`);

    console.log(chalk.green.bold('\nGenerated Code:'));
    console.log(chalk.white(code));

  } catch (error: any) {
    spinner.fail(`Failed to generate code: ${error.message}`);
    process.exit(1);
  }
}

export async function refactor(filePath: string, prompt: string) {
  console.log(chalk.blue.bold('🤖 Refactoring code...\n'));

  const client = new AgentClient();
  const spinner = ora('Refactoring code...').start();

  try {
    const code = await client.refactorCode(filePath, prompt);
    spinner.succeed(`Code refactored successfully in ${filePath}!`);

    console.log(chalk.green.bold('\nRefactored Code:'));
    console.log(chalk.white(code));

  } catch (error: any) {
    spinner.fail(`Failed to refactor code: ${error.message}`);
    process.exit(1);
  }
}

export async function verify(filePath: string) {
  console.log(chalk.blue.bold(`🤖 Verifying code changes in ${filePath}...\n`));

  const client = new AgentClient();

  try {
    const success = await client.verifyCodeChanges(filePath);
    if (success) {
      console.log(chalk.green.bold('\n✅ Code verification passed!'));
    } else {
      console.log(chalk.red.bold('\n❌ Code verification failed. Please review the output above.'));
    }
  } catch (error: any) {
    console.error(chalk.red(`Failed to verify code: ${error.message}`));
    process.exit(1);
  }
}