import { Command } from 'commander';
import * as path from 'path';
import * as os from 'os';
import * as child_process from 'child_process';
import * as fs from 'fs';
import chalk from 'chalk';

const configDirectoryName = '.mcp';

export const memoryCommand = new Command('memory')
  .description('Manage MCP memory files');

memoryCommand
  .command('edit [scope]')
  .description('Edit global or project memory file')
  .option('-e, --editor <editor>', 'Specify editor to use (e.g., code, nano, vim)')
  .action(async (scope, options) => {
    let memoryFilePath: string;

    if (scope === 'global') {
      memoryFilePath = path.join(os.homedir(), configDirectoryName, 'MEMORY.md');
    } else if (scope === 'project' || !scope) {
      memoryFilePath = path.join(process.cwd(), configDirectoryName, 'MEMORY.md');
    } else {
      console.error(chalk.red(`Invalid scope: ${scope}. Use 'global' or 'project'.`));
      process.exit(1);
    }

    if (!fs.existsSync(path.dirname(memoryFilePath))) {
      console.warn(chalk.yellow(`Memory directory does not exist: ${path.dirname(memoryFilePath)}. Creating it.`));
      fs.mkdirSync(path.dirname(memoryFilePath), { recursive: true });
    }

    if (!fs.existsSync(memoryFilePath)) {
      console.warn(chalk.yellow(`Memory file does not exist: ${memoryFilePath}. Creating it.`));
      fs.writeFileSync(memoryFilePath, '# MCP Memory\n\n');
    }

    const editors = options.editor ? [options.editor] : ['code', 'nano', 'vim', 'vi'];
    let editorFound = false;

    for (const editor of editors) {
      try {
        console.log(chalk.blue(`Attempting to open ${memoryFilePath} with ${editor}...`));
        child_process.spawnSync(editor, [memoryFilePath], { stdio: 'inherit' });
        editorFound = true;
        break;
      } catch (error) {
        // Editor not found or command failed, try next one
      }
    }

    if (!editorFound) {
      console.error(chalk.red('No suitable editor found. Please install one or specify with --editor option.'));
      console.error(chalk.red(`You can manually edit the file at: ${memoryFilePath}`));
      process.exit(1);
    }
  });
