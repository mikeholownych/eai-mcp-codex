import chalk from 'chalk';
import { table } from 'table';
import ora from 'ora';
import inquirer from 'inquirer';

// Placeholder client
class WorkflowOrchestratorClient {
  async createWorkflow(workflowData: any): Promise<any> {
    return { id: 'wf-123', status: 'draft', ...workflowData, created_at: new Date().toISOString() };
  }

  async executeWorkflow(workflowId: string): Promise<any> {
    return { id: `exec-${workflowId}`, status: 'running', start_time: new Date().toISOString() };
  }

  async getWorkflowStatus(workflowId: string): Promise<any> {
    return {
      id: workflowId,
      name: 'Test Workflow',
      status: 'active',
      created_at: new Date().toISOString(),
      last_execution: {
        id: 'exec-123',
        status: 'completed',
        start_time: new Date().toISOString(),
        end_time: new Date().toISOString()
      },
      steps: [
        { name: 'Step 1', type: 'model_request', status: 'completed' },
        { name: 'Step 2', type: 'code_generation', status: 'completed' }
      ]
    };
  }

  async getExecution(executionId: string): Promise<any> {
    // Simulate a workflow that completes in a few steps
    const statuses = ['running', 'running', 'completed'];
    const currentStatus = statuses[Math.floor(Math.random() * statuses.length)];
    return {
      id: executionId,
      status: currentStatus,
      current_step: currentStatus === 'running' ? 'Executing step...' : 'Finished'
    };
  }
}

interface CreateOptions {
  steps?: string;
}

export async function create(name: string, options: CreateOptions) {
  console.log(chalk.blue.bold('⚡ Creating Workflow\n'));

  let steps: any[] = [];

  if (options.steps) {
    try {
      steps = JSON.parse(options.steps);
    } catch (error) {
      console.error(chalk.red('Invalid JSON format for steps'));
      process.exit(1);
    }
  } else {
    // Interactive step creation
    console.log(chalk.yellow('Create workflow steps interactively:'));
    let addMore = true;

    while (addMore) {
      const stepAnswers = await inquirer.prompt([
        {
          type: 'input',
          name: 'name',
          message: 'Step name:',
          validate: (input: string) => input.trim().length > 0
        },
        {
          type: 'list',
          name: 'type',
          message: 'Step type:',
          choices: ['model_request', 'code_generation', 'verification', 'git_operation', 'custom']
        },
        {
          type: 'input',
          name: 'description',
          message: 'Step description:'
        },
        {
          type: 'confirm',
          name: 'addAnother',
          message: 'Add another step?',
          default: false
        }
      ]);

      steps.push({
        name: stepAnswers.name,
        type: stepAnswers.type,
        description: stepAnswers.description,
        config: {}
      });

      addMore = stepAnswers.addAnother;
    }
  }

  const workflowData = {
    name,
    description: `Workflow created via CLI: ${name}`,
    steps
  };

  const client = new WorkflowOrchestratorClient();
  const spinner = ora('Creating workflow...').start();

  try {
    const workflow = await client.createWorkflow(workflowData);
    spinner.succeed('Workflow created successfully');

    console.log(chalk.green.bold('\n✅ Workflow Created:'));
    console.log(`ID: ${chalk.cyan(workflow.id)}`);
    console.log(`Name: ${chalk.white(workflow.name)}`);
    console.log(`Status: ${chalk.yellow(workflow.status)}`);
    console.log(`Steps: ${chalk.blue(workflow.steps.length)}`);

    if (workflow.steps.length > 0) {
      console.log(chalk.yellow.bold('\n📋 Steps:'));
      workflow.steps.forEach((step: any, index: number) => {
        console.log(`${index + 1}. ${chalk.cyan(step.name)} (${step.type})`);
        if (step.description) {
          console.log(`   ${chalk.gray(step.description)}`);
        }
      });
    }

  } catch (error: any) {
    spinner.fail(`Failed to create workflow: ${error.message}`);
    process.exit(1);
  }
}

export async function execute(workflowId: string) {
  console.log(chalk.blue.bold(`▶️  Executing Workflow: ${workflowId}\n`));

  const client = new WorkflowOrchestratorClient();
  const spinner = ora('Starting workflow execution...').start();

  try {
    const execution = await client.executeWorkflow(workflowId);
    spinner.succeed('Workflow execution started');

    console.log(chalk.green.bold('\n✅ Execution Started:'));
    console.log(`Execution ID: ${chalk.cyan(execution.id)}`);
    console.log(`Status: ${chalk.yellow(execution.status)}`);
    console.log(`Start Time: ${chalk.gray(new Date(execution.start_time).toLocaleString())}`);

    // Poll for status updates
    console.log(chalk.blue('\n📊 Monitoring execution...'));
    await monitorExecution(client, execution.id);

  } catch (error: any) {
    spinner.fail(`Failed to execute workflow: ${error.message}`);
    process.exit(1);
  }
}

export async function status(workflowId: string) {
  console.log(chalk.blue.bold(`📊 Workflow Status: ${workflowId}\n`));

  const client = new WorkflowOrchestratorClient();
  const spinner = ora('Fetching workflow status...').start();

  try {
    const workflow = await client.getWorkflowStatus(workflowId);
    spinner.succeed('Status retrieved successfully');

    console.log(chalk.cyan.bold('Workflow Information:'));
    console.log(`ID: ${chalk.white(workflow.id)}`);
    console.log(`Name: ${chalk.white(workflow.name)}`);
    console.log(`Status: ${getWorkflowStatusColor(workflow.status)}`);
    console.log(`Created: ${chalk.gray(new Date(workflow.created_at).toLocaleString())}`);

    if (workflow.last_execution) {
      console.log(chalk.yellow.bold('\n🔄 Last Execution:'));
      const exec = workflow.last_execution;
      console.log(`Execution ID: ${chalk.cyan(exec.id)}`);
      console.log(`Status: ${getExecutionStatusColor(exec.status)}`);
      console.log(`Started: ${chalk.gray(new Date(exec.start_time).toLocaleString())}`);

      if (exec.end_time) {
        const duration = new Date(exec.end_time).getTime() - new Date(exec.start_time).getTime();
        console.log(`Duration: ${chalk.blue(Math.round(duration / 1000))}s`);
      }
    }

    if (workflow.steps && workflow.steps.length > 0) {
      console.log(chalk.yellow.bold('\n📋 Steps:'));
      workflow.steps.forEach((step: any, index: number) => {
        const status = step.status === 'completed' ? chalk.green('✓') :
                      step.status === 'running' ? chalk.yellow('⏳') :
                      step.status === 'failed' ? chalk.red('✗') :
                      chalk.gray('○');
        console.log(`${index + 1}. ${status} ${step.name} (${step.type})`);
      });
    }

  } catch (error: any) {
    spinner.fail(`Failed to fetch status: ${error.message}`);
    process.exit(1);
  }
}

async function monitorExecution(client: WorkflowOrchestratorClient, executionId: string) {
  const maxAttempts = 60; // 5 minutes with 5-second intervals
  let attempts = 0;

  while (attempts < maxAttempts) {
    try {
      const execution = await client.getExecution(executionId);

      process.stdout.write(`\r${getExecutionStatusColor(execution.status)} - ${execution.current_step || 'Initializing'}...`);

      if (execution.status === 'completed') {
        console.log(chalk.green.bold('\n\n🎉 Workflow completed successfully!'));
        break;
      } else if (execution.status === 'failed') {
        console.log(chalk.red.bold('\n\n❌ Workflow execution failed'));
        if (execution.error) {
          console.log(chalk.red(`Error: ${execution.error}`));
        }
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 5000));
      attempts++;

    } catch (error: any) {
      console.log(chalk.red(`\n\nFailed to monitor execution: ${error.message}`));
      break;
    }
  }

  if (attempts >= maxAttempts) {
    console.log(chalk.yellow('\n\nMonitoring timeout reached. Check status manually.'));
  }
}

function getWorkflowStatusColor(status: string): string {
  switch (status) {
    case 'active': return chalk.green('✓ Active');
    case 'draft': return chalk.yellow('📝 Draft');
    case 'archived': return chalk.gray('📦 Archived');
    default: return chalk.gray(status);
  }
}

function getExecutionStatusColor(status: string): string {
  switch (status) {
    case 'running': return chalk.blue('⏳ Running');
    case 'completed': return chalk.green('✓ Completed');
    case 'failed': return chalk.red('✗ Failed');
    case 'cancelled': return chalk.yellow('⚠ Cancelled');
    default: return chalk.gray(status);
  }
}
