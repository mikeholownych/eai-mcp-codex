import chalk from 'chalk';
import { table } from 'table';
import ora from 'ora';
import fs from 'fs';

// Placeholder client
class VerificationFeedbackClient {
  async submitFeedback(feedbackData: any): Promise<any> {
    return { id: 'fb-123', status: 'pending', ...feedbackData, created_at: new Date().toISOString() };
  }

  async listFeedback(): Promise<any[]> {
    return [
      { id: 'fb-123', feedback_type: 'bug_report', title: 'UI glitch on login', severity: 'medium', status: 'processed', created_at: new Date().toISOString() },
      { id: 'fb-456', feedback_type: 'feature_request', title: 'Add dark mode', severity: 'low', status: 'pending', created_at: new Date().toISOString() }
    ];
  }

  async getFeedback(feedbackId: string): Promise<any> {
    return {
      id: feedbackId,
      feedback_type: 'bug_report',
      title: 'UI glitch on login',
      severity: 'medium',
      status: 'processed',
      created_at: new Date().toISOString(),
      description: 'When clicking the login button, the page flashes.',
      metadata: { user: 'testuser', browser: 'Chrome' }
    };
  }

  async verifyCode(codeData: any): Promise<any> {
    return {
      overall_score: 85,
      issues: [
        { severity: 'high', message: 'SQL injection vulnerability', line: 42, context: 'executeQuery(query)' },
        { severity: 'low', message: "Unused variable 'x'", line: 15, context: 'let x = 5;' }
      ]
    };
  }
}

interface SubmitOptions {
  description?: string;
  severity?: string;
}

interface VerifyOptions {
  language?: string;
  types?: string;
}

export async function submit(type: string, title: string, options: SubmitOptions) {
  console.log(chalk.blue.bold('📝 Submitting Feedback\n'));

  const feedbackData = {
    type,
    title,
    description: options.description,
    severity: options.severity
  };

  const client = new VerificationFeedbackClient();
  const spinner = ora('Submitting feedback...').start();

  try {
    const feedback = await client.submitFeedback(feedbackData);
    spinner.succeed('Feedback submitted successfully');

    console.log(chalk.green.bold('\n✅ Feedback Submitted:'));
    console.log(`ID: ${chalk.cyan(feedback.id)}`);
    console.log(`Type: ${chalk.white(feedback.feedback_type)}`);
    console.log(`Title: ${chalk.white(feedback.title)}`);
    console.log(`Severity: ${getSeverityColor(feedback.severity)}`);
    console.log(`Status: ${chalk.yellow(feedback.status)}`);

    if (feedback.description) {
      console.log(`Description: ${chalk.gray(feedback.description)}`);
    }

  } catch (error: any) {
    spinner.fail(`Failed to submit feedback: ${error.message}`);
    process.exit(1);
  }
}

export async function list() {
  console.log(chalk.blue.bold('📋 Verification Feedback\n'));

  const client = new VerificationFeedbackClient();
  const spinner = ora('Fetching feedback...').start();

  try {
    const feedback = await client.listFeedback();
    spinner.succeed('Feedback retrieved successfully');

    if (!feedback || feedback.length === 0) {
      console.log(chalk.yellow('No feedback entries found'));
      return;
    }

    const tableData = [
      [chalk.bold('ID'), chalk.bold('Type'), chalk.bold('Title'), chalk.bold('Severity'), chalk.bold('Status'), chalk.bold('Created')]
    ];

    feedback.forEach((item: any) => {
      const createdDate = new Date(item.created_at).toLocaleDateString();

      tableData.push([
        chalk.cyan(item.id.substring(0, 8)),
        chalk.blue(item.feedback_type),
        item.title.length > 25 ? item.title.substring(0, 22) + '...' : item.title,
        getSeverityColor(item.severity),
        getStatusColor(item.status),
        chalk.gray(createdDate)
      ]);
    });

    console.log(table(tableData, {
      columns: {
        0: { alignment: 'left', width: 10 },
        1: { alignment: 'left', width: 12 },
        2: { alignment: 'left', width: 28 },
        3: { alignment: 'center', width: 12 },
        4: { alignment: 'center', width: 10 },
        5: { alignment: 'left', width: 12 }
      }
    }));

  } catch (error: any) {
    spinner.fail(`Failed to fetch feedback: ${error.message}`);
    process.exit(1);
  }
}

export async function show(feedbackId: string) {
  console.log(chalk.blue.bold(`📖 Feedback Details: ${feedbackId}\n`));

  const client = new VerificationFeedbackClient();
  const spinner = ora('Fetching feedback details...').start();

  try {
    const feedback = await client.getFeedback(feedbackId);
    spinner.succeed('Feedback details retrieved');

    console.log(chalk.cyan.bold('Feedback Information:'));
    console.log(`ID: ${chalk.white(feedback.id)}`);
    console.log(`Type: ${chalk.blue(feedback.feedback_type)}`);
    console.log(`Title: ${chalk.white(feedback.title)}`);
    console.log(`Severity: ${getSeverityColor(feedback.severity)}`);
    console.log(`Status: ${getStatusColor(feedback.status)}`);
    console.log(`Created: ${chalk.gray(new Date(feedback.created_at).toLocaleString())}`);

    if (feedback.description) {
      console.log(`\nDescription:`);
      console.log(chalk.gray(feedback.description));
    }

    if (feedback.metadata && Object.keys(feedback.metadata).length > 0) {
      console.log(chalk.yellow.bold('\n🔍 Metadata:'));
      Object.entries(feedback.metadata).forEach(([key, value]) => {
        console.log(`${key}: ${chalk.white(value as string)}`);
      });
    }

  } catch (error: any) {
    spinner.fail(`Failed to fetch feedback: ${error.message}`);
    process.exit(1);
  }
}

export async function verify(codeFile: string, options: VerifyOptions) {
  console.log(chalk.blue.bold('🔍 Code Verification\n'));

  if (!fs.existsSync(codeFile)) {
    console.error(chalk.red(`File not found: ${codeFile}`));
    process.exit(1);
  }

  const code = fs.readFileSync(codeFile, 'utf8');
  const language = options.language || detectLanguage(codeFile);

  const codeData = {
    code,
    language,
    types: options.types ? options.types.split(',') : ['syntax', 'security', 'quality']
  };

  const client = new VerificationFeedbackClient();
  const spinner = ora('Verifying code...').start();

  try {
    const result = await client.verifyCode(codeData);
    spinner.succeed('Code verification completed');

    console.log(chalk.green.bold('\n✅ Verification Results:'));
    console.log(`File: ${chalk.white(codeFile)}`);
    console.log(`Language: ${chalk.blue(language)}`);
    console.log(`Overall Score: ${getScoreColor(result.overall_score)}`);

    if (result.issues && result.issues.length > 0) {
      console.log(chalk.yellow.bold('\n⚠️ Issues Found:'));
      result.issues.forEach((issue: any, index: number) => {
        const severity = getSeverityColor(issue.severity);
        console.log(`${index + 1}. ${severity} ${issue.message}`);
        if (issue.line) {
          console.log(`   Line ${issue.line}: ${chalk.gray(issue.context)}`);
        }
      });
    } else {
      console.log(chalk.green('\n✨ No issues found!'));
    }

  } catch (error: any) {
    spinner.fail(`Code verification failed: ${error.message}`);
    process.exit(1);
  }
}

function detectLanguage(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  const langMap: { [key: string]: string } = {
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    'java': 'java',
    'cpp': 'cpp',
    'c': 'c',
    'go': 'go',
    'rs': 'rust',
    'php': 'php',
    'rb': 'ruby'
  };
  return langMap[ext] || 'text';
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical': return chalk.red.bold('🚨 Critical');
    case 'high': return chalk.red('🔴 High');
    case 'medium': return chalk.yellow('🟡 Medium');
    case 'low': return chalk.blue('🔵 Low');
    default: return chalk.gray(severity);
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'pending': return chalk.yellow('⏳ Pending');
    case 'processed': return chalk.green('✓ Processed');
    case 'closed': return chalk.gray('📁 Closed');
    default: return chalk.gray(status);
  }
}

function getScoreColor(score: number): string {
  if (score >= 90) return chalk.green.bold(`${score}% ✨`);
  if (score >= 70) return chalk.blue(`${score}% 👍`);
  if (score >= 50) return chalk.yellow(`${score}% ⚠️`);
  return chalk.red(`${score}% ❌`);
}