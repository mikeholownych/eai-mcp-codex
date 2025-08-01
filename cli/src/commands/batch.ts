import fs from 'fs';
import path from 'path';
import chalk from 'chalk';
import yaml from 'yaml';
import { AgentClient } from './agent';

export async function run(file: string, options: { format?: string }) {
  try {
    const resolvedPath = path.resolve(file);
    if (!fs.existsSync(resolvedPath)) {
      console.error(chalk.red(`Batch file not found: ${resolvedPath}`));
      process.exit(1);
    }

    const rawContent = fs.readFileSync(resolvedPath, 'utf8');
    const format = options.format || (file.endsWith('.yaml') || file.endsWith('.yml') ? 'yaml' : 'json');
    const commands: Array<{ command: string; args?: Record<string, any> }> =
      format === 'yaml' ? yaml.parse(rawContent) : JSON.parse(rawContent);

    if (!Array.isArray(commands)) {
      console.error(chalk.red('Batch file must contain an array of commands'));
      process.exit(1);
    }

    const client = new AgentClient();

    for (const step of commands) {
      const name = step.command;
      const args = step.args || {};
      console.log(chalk.blue(`\n▶ Executing: ${name} ${JSON.stringify(args)}`));
      try {
        await client.dispatchCommand(name, args);
      } catch (err: any) {
        console.error(chalk.red(`Command failed: ${err.message}`));
        process.exit(1);
      }
    }

    console.log(chalk.green('\n✅ Batch completed successfully'));
  } catch (error: any) {
    console.error(chalk.red(`Batch execution failed: ${error.message}`));
    process.exit(1);
  }
}
