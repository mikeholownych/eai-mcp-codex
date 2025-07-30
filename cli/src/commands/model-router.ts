import chalk from 'chalk';
import { table } from 'table';
import ora from 'ora';

// Placeholder client
class ModelRouterClient {
  async routeRequest(prompt: string, options: any): Promise<any> {
    return {
      response: `Echo: ${prompt}`,
      model: options.model || 'mock-model',
      metadata: { key: 'value' },
      usage: { total_tokens: 123, cost: 0.01 }
    };
  }

  async listModels(): Promise<any[]> {
    return [
      { name: 'model-1', type: 'language', status: 'available', description: 'A powerful language model' },
      { name: 'model-2', type: 'code', status: 'unavailable', description: 'A model for generating code' }
    ];
  }

  async getRoutingRules(): Promise<any[]> {
    return [{ pattern: '/code', model: 'model-2' }];
  }
}

interface RouteOptions {
  model?: string;
  temperature?: string;
}

export async function route(prompt: string, options: RouteOptions) {
  console.log(chalk.blue.bold('🤖 Routing Model Request\n'));

  const client = new ModelRouterClient();
  const spinner = ora('Processing request...').start();

  try {
    const result = await client.routeRequest(prompt, options);
    spinner.succeed('Request processed successfully');

    console.log(chalk.cyan.bold('\n📋 Request Details:'));
    console.log(chalk.gray(`Prompt: ${prompt}`));
    console.log(chalk.gray(`Model: ${result.model || 'auto-selected'}`));
    console.log(chalk.gray(`Temperature: ${options.temperature || '0.7'}`));

    console.log(chalk.green.bold('\n💬 Response:'));
    console.log(chalk.white(result.response || result.content));

    if (result.metadata) {
      console.log(chalk.yellow.bold('\n🔍 Metadata:'));
      console.log(JSON.stringify(result.metadata, null, 2));
    }

    if (result.usage) {
      console.log(chalk.blue.bold('\n📊 Usage:'));
      console.log(`Tokens: ${result.usage.total_tokens || 'N/A'}`);
      console.log(`Cost: $${result.usage.cost || 'N/A'}`);
    }

  } catch (error: any) {
    spinner.fail(`Request failed: ${error.message}`);
    process.exit(1);
  }
}

export async function listModels() {
  console.log(chalk.blue.bold('📋 Available Models\n'));

  const client = new ModelRouterClient();
  const spinner = ora('Fetching models...').start();

  try {
    const models = await client.listModels();
    spinner.succeed('Models retrieved successfully');

    if (!models || models.length === 0) {
      console.log(chalk.yellow('No models available'));
      return;
    }

    const tableData = [
      [chalk.bold('Model'), chalk.bold('Type'), chalk.bold('Status'), chalk.bold('Description')]
    ];

    models.forEach(model => {
      tableData.push([
        chalk.cyan(model.name || model.id),
        model.type || 'N/A',
        model.status === 'available' ? chalk.green('✓ Available') : chalk.red('✗ Unavailable'),
        model.description || 'No description'
      ]);
    });

    console.log(table(tableData, {
      columns: {
        0: { alignment: 'left', width: 15 },
        1: { alignment: 'left', width: 12 },
        2: { alignment: 'center', width: 15 },
        3: { alignment: 'left', width: 40 }
      }
    }));

    // Show routing rules
    try {
      const rules = await client.getRoutingRules();
      if (rules && rules.length > 0) {
        console.log(chalk.yellow.bold('\n🔀 Routing Rules:'));
        rules.forEach((rule, index) => {
          console.log(`${index + 1}. ${chalk.cyan(rule.pattern)} → ${chalk.green(rule.model)}`);
        });
      }
    } catch (ruleError) {
      console.log(chalk.gray('(Routing rules not available)'));
    }

  } catch (error: any) {
    spinner.fail(`Failed to fetch models: ${error.message}`);
    process.exit(1);
  }
}