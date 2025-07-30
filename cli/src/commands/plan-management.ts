import chalk from 'chalk';
import { table } from 'table';
import ora from 'ora';
import inquirer from 'inquirer';

// Placeholder client
class PlanManagementClient {
  async createPlan(planData: any): Promise<any> {
    return { id: 'plan-123', status: 'draft', ...planData, created_at: new Date().toISOString() };
  }

  async listPlans(filters: any): Promise<any[]> {
    return [
      { id: 'plan-123', title: 'Implement feature X', status: 'active', created_at: new Date().toISOString(), tasks: [{}, {}] },
      { id: 'plan-456', title: 'Fix bug Y', status: 'completed', created_at: new Date().toISOString(), tasks: [{}] }
    ];
  }

  async getPlan(planId: string): Promise<any> {
    return {
      id: planId,
      title: 'Implement feature X',
      status: 'active',
      created_at: new Date().toISOString(),
      description: 'A detailed description of the plan.',
      tags: ['frontend', 'backend'],
      tasks: [
        { title: 'Design the UI', status: 'completed' },
        { title: 'Develop the API', status: 'in_progress' },
        { title: 'Write tests', status: 'todo' }
      ]
    };
  }

  async updatePlan(planId: string, updates: any): Promise<any> {
    return { id: planId, ...updates };
  }
}

interface CreateOptions {
  description?: string;
  tags?: string;
}

interface ListOptions {
  status?: string;
}

interface UpdateOptions {
  status?: string;
}

export async function create(title: string, options: CreateOptions) {
  console.log(chalk.blue.bold('📝 Creating New Plan\n'));

  const planData = {
    title,
    description: options.description,
    tags: options.tags ? options.tags.split(',').map(t => t.trim()) : []
  };

  const client = new PlanManagementClient();
  const spinner = ora('Creating plan...').start();

  try {
    const plan = await client.createPlan(planData);
    spinner.succeed('Plan created successfully');

    console.log(chalk.green.bold('\n✅ Plan Created:'));
    console.log(`ID: ${chalk.cyan(plan.id)}`);
    console.log(`Title: ${chalk.white(plan.title)}`);
    console.log(`Status: ${chalk.yellow(plan.status)}`);

    if (plan.description) {
      console.log(`Description: ${chalk.gray(plan.description)}`);
    }

    if (plan.tags && plan.tags.length > 0) {
      console.log(`Tags: ${plan.tags.map((t: string) => chalk.blue(t)).join(', ')}`);
    }

  } catch (error: any) {
    spinner.fail(`Failed to create plan: ${error.message}`);
    process.exit(1);
  }
}

export async function list(options: ListOptions) {
  console.log(chalk.blue.bold('📋 Development Plans\n'));

  const client = new PlanManagementClient();
  const spinner = ora('Fetching plans...').start();

  try {
    const filters: any = {};
    if (options.status) filters.status = options.status;

    const plans = await client.listPlans(filters);
    spinner.succeed('Plans retrieved successfully');

    if (!plans || plans.length === 0) {
      console.log(chalk.yellow('No plans found'));
      return;
    }

    const tableData = [
      [chalk.bold('ID'), chalk.bold('Title'), chalk.bold('Status'), chalk.bold('Created'), chalk.bold('Tasks')]
    ];

    plans.forEach(plan => {
      const createdDate = new Date(plan.created_at).toLocaleDateString();
      const taskCount = plan.tasks ? plan.tasks.length : 0;

      tableData.push([
        chalk.cyan(plan.id.substring(0, 8)),
        plan.title.length > 30 ? plan.title.substring(0, 27) + '...' : plan.title,
        getStatusColor(plan.status),
        chalk.gray(createdDate),
        chalk.blue(taskCount.toString())
      ]);
    });

    console.log(table(tableData, {
      columns: {
        0: { alignment: 'left', width: 10 },
        1: { alignment: 'left', width: 35 },
        2: { alignment: 'center', width: 12 },
        3: { alignment: 'left', width: 12 },
        4: { alignment: 'center', width: 8 }
      }
    }));

  } catch (error: any) {
    spinner.fail(`Failed to fetch plans: ${error.message}`);
    process.exit(1);
  }
}

export async function show(planId: string) {
  console.log(chalk.blue.bold(`📖 Plan Details: ${planId}\n`));

  const client = new PlanManagementClient();
  const spinner = ora('Fetching plan details...').start();

  try {
    const plan = await client.getPlan(planId);
    spinner.succeed('Plan details retrieved');

    console.log(chalk.cyan.bold('Plan Information:'));
    console.log(`ID: ${chalk.white(plan.id)}`);
    console.log(`Title: ${chalk.white(plan.title)}`);
    console.log(`Status: ${getStatusColor(plan.status)}`);
    console.log(`Created: ${chalk.gray(new Date(plan.created_at).toLocaleString())}`);

    if (plan.description) {
      console.log(`Description: ${chalk.gray(plan.description)}`);
    }

    if (plan.tags && plan.tags.length > 0) {
      console.log(`Tags: ${plan.tags.map((t: string) => chalk.blue(t)).join(', ')}`);
    }

    if (plan.tasks && plan.tasks.length > 0) {
      console.log(chalk.yellow.bold('\n📋 Tasks:'));
      plan.tasks.forEach((task: any, index: number) => {
        const status = task.status === 'completed' ? chalk.green('✓') :
                      task.status === 'in_progress' ? chalk.yellow('⏳') :
                      chalk.gray('○');
        console.log(`${index + 1}. ${status} ${task.title}`);
        if (task.description) {
          console.log(`   ${chalk.gray(task.description)}`);
        }
      });
    }

  } catch (error: any) {
    spinner.fail(`Failed to fetch plan: ${error.message}`);
    process.exit(1);
  }
}

export async function update(planId: string, options: UpdateOptions) {
  console.log(chalk.blue.bold(`✏️  Updating Plan: ${planId}\n`));

  const client = new PlanManagementClient();

  try {
    const updates: any = {};
    if (options.status) updates.status = options.status;

    if (Object.keys(updates).length === 0) {
      // Interactive update
      const answers = await inquirer.prompt([
        {
          type: 'list',
          name: 'status',
          message: 'Select new status:',
          choices: ['draft', 'active', 'completed', 'cancelled']
        }
      ]);
      updates.status = answers.status;
    }

    const spinner = ora('Updating plan...').start();
    const updatedPlan = await client.updatePlan(planId, updates);
    spinner.succeed('Plan updated successfully');

    console.log(chalk.green.bold('\n✅ Plan Updated:'));
    console.log(`Status: ${getStatusColor(updatedPlan.status)}`);

  } catch (error: any) {
    console.error(chalk.red(`Failed to update plan: ${error.message}`));
    process.exit(1);
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'completed': return chalk.green('✓ Completed');
    case 'active': return chalk.blue('⚡ Active');
    case 'draft': return chalk.yellow('📝 Draft');
    case 'cancelled': return chalk.red('✗ Cancelled');
    default: return chalk.gray(status);
  }
}