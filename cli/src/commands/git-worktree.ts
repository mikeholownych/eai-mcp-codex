import chalk from 'chalk';
import { table } from 'table';
import ora from 'ora';
import { GitWorktreeClient, WorktreeData } from '../clients/git-worktree';

interface WorktreeOptions {
  path?: string;
}

export async function create(repo: string, branch: string, options: WorktreeOptions) {
  console.log(chalk.blue.bold('🌿 Creating Git Worktree\n'));

  const worktreeData: WorktreeData = {
    repo,
    branch,
    path: options.path
  };

  const client = new GitWorktreeClient();
  const spinner = ora('Creating worktree...').start();

  try {
    const worktree = await client.createWorktree(worktreeData);
    spinner.succeed('Worktree created successfully');

    console.log(chalk.green.bold('\n✅ Worktree Created:'));
    console.log(`ID: ${chalk.cyan(worktree.id)}`);
    console.log(`Repository: ${chalk.white(worktree.repository_url)}`);
    console.log(`Branch: ${chalk.yellow(worktree.branch)}`);
    console.log(`Path: ${chalk.gray(worktree.path)}`);
    console.log(`Status: ${chalk.blue(worktree.status)}`);

  } catch (error: any) {
    spinner.fail(`Failed to create worktree: ${error.message}`);
    process.exit(1);
  }
}

export async function list() {
  console.log(chalk.blue.bold('🌿 Git Worktrees\n'));

  const client = new GitWorktreeClient();
  const spinner = ora('Fetching worktrees...').start();

  try {
    const worktrees = await client.listWorktrees();
    spinner.succeed('Worktrees retrieved successfully');

    if (!worktrees || worktrees.length === 0) {
      console.log(chalk.yellow('No worktrees found'));
      return;
    }

    const tableData = [
      [chalk.bold('ID'), chalk.bold('Repository'), chalk.bold('Branch'), chalk.bold('Status'), chalk.bold('Path')]
    ];

    worktrees.forEach(worktree => {
      const repoName = worktree.repository_url.split('/').pop().replace('.git', '');

      tableData.push([
        chalk.cyan(worktree.id.substring(0, 8)),
        repoName.length > 20 ? repoName.substring(0, 17) + '...' : repoName,
        chalk.yellow(worktree.branch),
        getWorktreeStatusColor(worktree.status),
        chalk.gray(worktree.path.length > 25 ? '...' + worktree.path.slice(-22) : worktree.path)
      ]);
    });

    console.log(table(tableData, {
      columns: {
        0: { alignment: 'left', width: 10 },
        1: { alignment: 'left', width: 22 },
        2: { alignment: 'left', width: 15 },
        3: { alignment: 'center', width: 12 },
        4: { alignment: 'left', width: 28 }
      }
    }));

  } catch (error: any) {
    spinner.fail(`Failed to fetch worktrees: ${error.message}`);
    process.exit(1);
  }
}

export async function remove(worktreeId: string) {
  console.log(chalk.blue.bold(`🗑️  Removing Worktree: ${worktreeId}\n`));

  const client = new GitWorktreeClient();
  const spinner = ora('Removing worktree...').start();

  try {
    await client.removeWorktree(worktreeId);
    spinner.succeed('Worktree removed successfully');

    console.log(chalk.green.bold('\n✅ Worktree Removed'));

  } catch (error: any) {
    spinner.fail(`Failed to remove worktree: ${error.message}`);
    process.exit(1);
  }
}

export async function status(worktreeId: string) {
  console.log(chalk.blue.bold(`📊 Worktree Status: ${worktreeId}\n`));

  const client = new GitWorktreeClient();
  const spinner = ora('Fetching worktree status...').start();

  try {
    const status = await client.getWorktreeStatus(worktreeId);
    spinner.succeed('Status retrieved successfully');

    console.log(chalk.cyan.bold('Worktree Information:'));
    console.log(`ID: ${chalk.white(status.id)}`);
    console.log(`Repository: ${chalk.white(status.repository_url)}`);
    console.log(`Branch: ${chalk.yellow(status.branch)}`);
    console.log(`Status: ${getWorktreeStatusColor(status.status)}`);
    console.log(`Path: ${chalk.gray(status.path)}`);

    if (status.git_status) {
      console.log(chalk.blue.bold('\n📋 Git Status:'));
      if (status.git_status.modified && status.git_status.modified.length > 0) {
        console.log(chalk.yellow('Modified files:'));
        status.git_status.modified.forEach((file: string) => {
          console.log(`  ${chalk.yellow('M')} ${file}`);
        });
      }

      if (status.git_status.untracked && status.git_status.untracked.length > 0) {
        console.log(chalk.red('Untracked files:'));
        status.git_status.untracked.forEach((file: string) => {
          console.log(`  ${chalk.red('??')} ${file}`);
        });
      }

      if (status.git_status.staged && status.git_status.staged.length > 0) {
        console.log(chalk.green('Staged files:'));
        status.git_status.staged.forEach((file: string) => {
          console.log(`  ${chalk.green('A')} ${file}`);
        });
      }
    }

  } catch (error: any) {
    spinner.fail(`Failed to fetch status: ${error.message}`);
    process.exit(1);
  }
}

function getWorktreeStatusColor(status: string): string {
  switch (status) {
    case 'active': return chalk.green('✓ Active');
    case 'syncing': return chalk.yellow('⏳ Syncing');
    case 'error': return chalk.red('✗ Error');
    case 'clean': return chalk.blue('🧹 Clean');
    default: return chalk.gray(status);
  }
}
