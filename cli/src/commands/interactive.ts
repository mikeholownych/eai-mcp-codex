import chalk from 'chalk';
import inquirer from 'inquirer';
import ora from 'ora';

// Placeholder clients
class ModelRouterClient {
  async routeRequest(prompt: string): Promise<any> {
    return { response: `Echo: ${prompt}`, model: 'mock-model' };
  }
  async healthCheck() { return Promise.resolve(); }
}

class PlanManagementClient {
  async createPlan(planData: any): Promise<any> {
    return { id: 'plan-123', ...planData };
  }
  async healthCheck() { return Promise.resolve(); }
}

class GitWorktreeClient {
  async listWorktrees(): Promise<any[]> {
    return [{ repository_url: 'https://github.com/test/test', branch: 'main', path: '/tmp/test' }];
  }
  async createWorktree(data: any): Promise<any> {
    return { id: 'wt-123', ...data };
  }
  async healthCheck() { return Promise.resolve(); }
}

class WorkflowOrchestratorClient {
  async listWorkflows(): Promise<any[]> {
    return [{ id: 'wf-123', name: 'Test Workflow', steps: [1, 2] }];
  }
  async executeWorkflow(id: string): Promise<any> {
    return { id: `exec-${id}`, status: 'running' };
  }
  async healthCheck() { return Promise.resolve(); }
}

class VerificationFeedbackClient {
  async submitFeedback(data: any): Promise<any> {
    return { id: 'fb-123', ...data };
  }
  async healthCheck() { return Promise.resolve(); }
}

// Placeholder for AgentClient
class AgentClient {
  async createPlan(task: string): Promise<any> {
    return {
      id: `plan-${Date.now()}`,
      task,
      steps: [
        { id: 'step-1', description: 'Understand the request and context' },
        { id: 'step-2', description: 'Read relevant files' },
        { id: 'step-3', description: 'Generate new code' },
        { id: 'step-4', description: 'Write changes to files' },
        { id: 'step-5', description: 'Run tests to verify changes' }
      ]
    };
  }

  async generateCode(prompt: string): Promise<string> {
    return `// Generated code for: ${prompt}\nconsole.log('Hello, world!');`;
  }

  async refactorCode(filePath: string, prompt: string): Promise<string> {
    return `// Refactored code for: ${filePath} based on: ${prompt}\nconsole.log('Hello, refactored world!');`;
  }
}

export async function interactive() {
  console.log(chalk.blue.bold('🚀 MCP Agent Network - Interactive Mode\n'));
  console.log(chalk.gray('Type "exit" or press Ctrl+C to quit\n'));

  const clients = {
    modelRouter: new ModelRouterClient(),
    planManagement: new PlanManagementClient(),
    gitWorktree: new GitWorktreeClient(),
    workflowOrchestrator: new WorkflowOrchestratorClient(),
    verificationFeedback: new VerificationFeedbackClient(),
    agent: new AgentClient() // Add agent client
  };

  while (true) {
    try {
      const { action } = await inquirer.prompt([
        {
          type: 'list',
          name: 'action',
          message: 'What would you like to do?',
          choices: [
            { name: '🤖 Ask AI Model', value: 'model_query' },
            { name: '📝 Create Development Plan', value: 'create_plan' },
            { name: '🌿 Manage Git Worktree', value: 'git_worktree' },
            { name: '⚡ Run Workflow', value: 'run_workflow' },
            { name: '🔍 Submit Feedback', value: 'submit_feedback' },
            new inquirer.Separator(),
            { name: '🧠 AI Coding Assistant', value: 'ai_coding_assistant' }, // New AI coding option
            new inquirer.Separator(),
            { name: '📊 Check System Status', value: 'system_status' },
            { name: '🚪 Exit', value: 'exit' }
          ]
        }
      ]);

      if (action === 'exit') {
        console.log(chalk.blue('👋 Goodbye!'));
        break;
      }

      switch (action) {
        case 'model_query':
          await handleModelQuery(clients.modelRouter);
          break;
        case 'create_plan':
          await handleCreatePlan(clients.planManagement);
          break;
        case 'git_worktree':
          await handleGitWorktree(clients.gitWorktree);
          break;
        case 'run_workflow':
          await handleRunWorkflow(clients.workflowOrchestrator);
          break;
        case 'submit_feedback':
          await handleSubmitFeedback(clients.verificationFeedback);
          break;
        case 'system_status':
          await handleSystemStatus(clients);
          break;
        case 'ai_coding_assistant':
          await handleAICodingAssistant(clients.agent);
          break;
      }

      console.log(); // Add spacing

    } catch (error: any) {
      if (error.isTtyError || error.name === 'ExitPromptError') {
        console.log(chalk.blue('\n👋 Goodbye!'));
        break;
      }
      console.error(chalk.red(`Error: ${error.message}`));
    }
  }
}

async function handleModelQuery(client: ModelRouterClient) {
  const { prompt } = await inquirer.prompt([
    {
      type: 'input',
      name: 'prompt',
      message: 'Enter your prompt:',
      validate: (input: string) => input.trim().length > 0
    }
  ]);

  const spinner = ora('Processing request...').start();

  try {
    const result = await client.routeRequest(prompt);
    spinner.succeed('Response received');

    console.log(chalk.green.bold('\n💬 AI Response:'));
    console.log(chalk.white(result.response || result.content));

    if (result.model) {
      console.log(chalk.gray(`\n(Routed to: ${result.model})`));
    }

  } catch (error: any) {
    spinner.fail(`Request failed: ${error.message}`);
  }
}

async function handleCreatePlan(client: PlanManagementClient) {
  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'title',
      message: 'Plan title:',
      validate: (input: string) => input.trim().length > 0
    },
    {
      type: 'input',
      name: 'description',
      message: 'Plan description (optional):'
    },
    {
      type: 'input',
      name: 'tags',
      message: 'Tags (comma-separated, optional):'
    }
  ]);

  const spinner = ora('Creating plan...').start();

  try {
    const planData = {
      title: answers.title,
      description: answers.description,
      tags: answers.tags ? answers.tags.split(',').map((t: string) => t.trim()) : []
    };

    const plan = await client.createPlan(planData);
    spinner.succeed('Plan created successfully');

    console.log(chalk.green.bold('\n✅ Plan Created:'));
    console.log(`ID: ${chalk.cyan(plan.id)}`);
    console.log(`Title: ${chalk.white(plan.title)}`);

  } catch (error: any) {
    spinner.fail(`Failed to create plan: ${error.message}`);
  }
}

async function handleGitWorktree(client: GitWorktreeClient) {
  const { operation } = await inquirer.prompt([
    {
      type: 'list',
      name: 'operation',
      message: 'Git worktree operation:',
      choices: [
        { name: '📋 List worktrees', value: 'list' },
        { name: '🌿 Create worktree', value: 'create' }
      ]
    }
  ]);

  if (operation === 'list') {
    const spinner = ora('Fetching worktrees...').start();

    try {
      const worktrees = await client.listWorktrees();
      spinner.succeed('Worktrees retrieved');

      if (worktrees.length === 0) {
        console.log(chalk.yellow('No worktrees found'));
      } else {
        console.log(chalk.blue.bold('\n🌿 Git Worktrees:'));
        worktrees.forEach((wt: any, index: number) => {
          console.log(`${index + 1}. ${chalk.cyan(wt.repository_url)} (${chalk.yellow(wt.branch)})`);
          console.log(`   Path: ${chalk.gray(wt.path)}`);
        });
      }

    } catch (error: any) {
      spinner.fail(`Failed to fetch worktrees: ${error.message}`);
    }

  } else if (operation === 'create') {
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'repo',
        message: 'Repository URL:',
        validate: (input: string) => input.trim().length > 0
      },
      {
        type: 'input',
        name: 'branch',
        message: 'Branch name:',
        default: 'main'
      }
    ]);

    const spinner = ora('Creating worktree...').start();

    try {
      const worktree = await client.createWorktree(answers);
      spinner.succeed('Worktree created successfully');

      console.log(chalk.green.bold('\n✅ Worktree Created:'));
      console.log(`ID: ${chalk.cyan(worktree.id)}`);
      console.log(`Path: ${chalk.gray(worktree.path)}`);

    } catch (error: any) {
      spinner.fail(`Failed to create worktree: ${error.message}`);
    }
  }
}

async function handleRunWorkflow(client: WorkflowOrchestratorClient) {
  const spinner = ora('Fetching workflows...').start();

  try {
    const workflows = await client.listWorkflows();
    spinner.succeed('Workflows retrieved');

    if (workflows.length === 0) {
      console.log(chalk.yellow('No workflows available. Create one first.'));
      return;
    }

    const { workflowId } = await inquirer.prompt([
      {
        type: 'list',
        name: 'workflowId',
        message: 'Select workflow to execute:',
        choices: workflows.map(wf => ({
          name: `${wf.name} (${wf.steps.length} steps)`,
          value: wf.id
        }))
      }
    ]);

    const executeSpinner = ora('Starting workflow execution...').start();

    try {
      const execution = await client.executeWorkflow(workflowId);
      executeSpinner.succeed('Workflow execution started');

      console.log(chalk.green.bold('\n▶️ Execution Started:'));
      console.log(`Execution ID: ${chalk.cyan(execution.id)}`);
      console.log(`Status: ${chalk.yellow(execution.status)}`);

    } catch (error: any) {
      executeSpinner.fail(`Failed to execute workflow: ${error.message}`);
    }

  } catch (error: any) {
    spinner.fail(`Failed to fetch workflows: ${error.message}`);
  }
}

async function handleSubmitFeedback(client: VerificationFeedbackClient) {
  const answers = await inquirer.prompt([
    {
      type: 'list',
      name: 'type',
      message: 'Feedback type:',
      choices: ['bug_report', 'feature_request', 'performance_issue', 'security_concern', 'general']
    },
    {
      type: 'input',
      name: 'title',
      message: 'Feedback title:',
      validate: (input: string) => input.trim().length > 0
    },
    {
      type: 'input',
      name: 'description',
      message: 'Description:'
    },
    {
      type: 'list',
      name: 'severity',
      message: 'Severity:',
      choices: ['low', 'medium', 'high', 'critical'],
      default: 'medium'
    }
  ]);

  const spinner = ora('Submitting feedback...').start();

  try {
    const feedback = await client.submitFeedback(answers);
    spinner.succeed('Feedback submitted successfully');

    console.log(chalk.green.bold('\n✅ Feedback Submitted:'));
    console.log(`ID: ${chalk.cyan(feedback.id)}`);
    console.log(`Type: ${chalk.blue(feedback.feedback_type)}`);

  } catch (error: any) {
    spinner.fail(`Failed to submit feedback: ${error.message}`);
  }
}

async function handleSystemStatus(clients: any) {
  console.log(chalk.blue.bold('\n📊 System Status Check\n'));

  const services = [
    { name: 'Model Router', client: clients.modelRouter },
    { name: 'Plan Management', client: clients.planManagement },
    { name: 'Git Worktree', client: clients.gitWorktree },
    { name: 'Workflow Orchestrator', client: clients.workflowOrchestrator },
    { name: 'Verification Feedback', client: clients.verificationFeedback }
  ];

  for (const service of services) {
    const spinner = ora(`Checking ${service.name}...`).start();

    try {
      const startTime = Date.now();
      await service.client.healthCheck();
      const responseTime = Date.now() - startTime;

      spinner.succeed(`${service.name}: ${chalk.green('✓ Healthy')} (${responseTime}ms)`);

    } catch (error: any) {
      spinner.fail(`${service.name}: ${chalk.red('✗ Unhealthy')} - ${error.message}`);
    }
  }
}

async function handleAICodingAssistant(client: AgentClient) {
  const { aiAction } = await inquirer.prompt([
    {
      type: 'list',
      name: 'aiAction',
      message: 'What AI coding task would you like to perform?',
      choices: [
        { name: '📝 Generate a plan', value: 'plan' },
        { name: '💡 Generate code', value: 'generate' },
        { name: '♻️ Refactor code', value: 'refactor' }
      ]
    }
  ]);

  switch (aiAction) {
    case 'plan':
      const { task } = await inquirer.prompt([
        {
          type: 'input',
          name: 'task',
          message: 'Enter the task description:',
          validate: (input: string) => input.trim().length > 0
        }
      ]);
      await client.createPlan(task);
      console.log(chalk.green('Plan generated (check console for details).'));
      break;
    case 'generate':
      const { prompt: generatePrompt } = await inquirer.prompt([
        {
          type: 'input',
          name: 'prompt',
          message: 'Enter the code generation prompt:',
          validate: (input: string) => input.trim().length > 0
        }
      ]);
      const generatedCode = await client.generateCode(generatePrompt);
      console.log(chalk.green.bold('\nGenerated Code:'));
      console.log(chalk.white(generatedCode));
      break;
    case 'refactor':
      const { filePath, prompt: refactorPrompt } = await inquirer.prompt([
        {
          type: 'input',
          name: 'filePath',
          message: 'Enter the file path to refactor:',
          validate: (input: string) => input.trim().length > 0
        },
        {
          type: 'input',
          name: 'prompt',
          message: 'Enter the refactoring prompt:',
          validate: (input: string) => input.trim().length > 0
        }
      ]);
      const refactoredCode = await client.refactorCode(filePath, refactorPrompt);
      console.log(chalk.green.bold('\nRefactored Code:'));
      console.log(chalk.white(refactoredCode));
      break;
  }
}
