/**
 * Configuration CLI commands - Handle MCP configuration system operations
 * Provides commands for listing agents, commands, and running diagnostics
 */

import chalk from 'chalk';
import ora from 'ora';
import { table } from 'table';
import * as fs from 'fs';
import * as path from 'path';
import { ConfigurationManager } from '../config/configuration-manager';
import { AgentDefinitionLoader } from '../loaders/agent-definition-loader';
import { CommandDefinitionLoader } from '../loaders/command-definition-loader';
import {
  MCPListOptions,
  MCPDoctorOptions,
  ConfigurationValidationResult,
  AgentDefinition,
  CommandDefinition,
} from '../types/configuration';

// Global configuration manager instance
let configManager: ConfigurationManager | null = null;
let agentLoader: AgentDefinitionLoader | null = null;
let commandLoader: CommandDefinitionLoader | null = null;

/**
 * Initialize configuration system
 */
function initializeConfigSystem(): {
  configManager: ConfigurationManager;
  agentLoader: AgentDefinitionLoader;
  commandLoader: CommandDefinitionLoader;
} {
  if (!configManager) {
    configManager = new ConfigurationManager({
      logLevel: 'info',
      enableCaching: true,
      conflictResolution: 'merge',
      validationLevel: 'basic',
    });
    
    agentLoader = new AgentDefinitionLoader(configManager);
    commandLoader = new CommandDefinitionLoader(configManager);
  }
  
  return {
    configManager: configManager!,
    agentLoader: agentLoader!,
    commandLoader: commandLoader!,
  };
}

/**
 * List agents command - mcp list agents
 */
export async function listAgents(options: MCPListOptions = {}) {
  const spinner = ora('Loading agent configurations...').start();
  
  try {
    const { agentLoader } = initializeConfigSystem();
    
    const agents = await agentLoader.loadAgentDefinitions({
      verbose: options.detailed,
      includeDefault: options.scope !== 'project' && options.scope !== 'global',
      includeGlobal: options.scope !== 'project' && options.scope !== 'default',
      includeProject: options.scope !== 'global' && options.scope !== 'default',
    });

    spinner.succeed(`Found ${agents.length} agent configuration${agents.length !== 1 ? 's' : ''}`);

    if (agents.length === 0) {
      console.log(chalk.yellow('\n🤖 No agent configurations found.'));
      console.log(chalk.gray('   Try creating an agent configuration in ./.mcp/ or ~/.mcp/'));
      return;
    }

    // Apply additional filters
    let filteredAgents = agents;
    
    if (options.filterTags && options.filterTags.length > 0) {
      filteredAgents = filteredAgents.filter(agent =>
        options.filterTags!.some(tag => agent.frontMatter.tags?.includes(tag))
      );
    }

    // Sort agents
    if (options.sortBy) {
      filteredAgents = sortAgents(filteredAgents, options.sortBy, options.sortOrder || 'asc');
    }

    // Output format
    switch (options.format) {
      case 'json':
        console.log(JSON.stringify(filteredAgents, null, 2));
        break;
        
      case 'yaml':
        const yaml = await import('yaml');
        console.log(yaml.stringify(filteredAgents));
        break;
        
      case 'table':
      default:
        displayAgentsTable(filteredAgents, options);
        break;
    }

    // Show additional details if requested
    if (options.detailed) {
      console.log(chalk.blue.bold('\n📊 Agent Statistics:'));
      const stats = await agentLoader.getAgentStatistics();
      displayAgentStatistics(stats);
    }

  } catch (error) {
    spinner.fail(`Failed to load agent configurations: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

/**
 * List commands command - mcp list commands
 */
export async function listCommands(options: MCPListOptions = {}) {
  const spinner = ora('Loading command configurations...').start();
  
  try {
    const { commandLoader } = initializeConfigSystem();
    
    const commands = await commandLoader.loadCommandDefinitions({
      verbose: options.detailed,
      includeDefault: options.scope !== 'project' && options.scope !== 'global',
      includeGlobal: options.scope !== 'project' && options.scope !== 'default',
      includeProject: options.scope !== 'global' && options.scope !== 'default',
    });

    spinner.succeed(`Found ${commands.length} command configuration${commands.length !== 1 ? 's' : ''}`);

    if (commands.length === 0) {
      console.log(chalk.yellow('\n⚡ No command configurations found.'));
      console.log(chalk.gray('   Try creating command configurations in ./.mcp/commands/ or ~/.mcp/commands/'));
      return;
    }

    // Apply additional filters
    let filteredCommands = commands;
    
    if (options.filterTags && options.filterTags.length > 0) {
      filteredCommands = filteredCommands.filter(command =>
        options.filterTags!.some(tag => command.frontMatter.tags?.includes(tag))
      );
    }

    // Sort commands
    if (options.sortBy) {
      filteredCommands = sortCommands(filteredCommands, options.sortBy, options.sortOrder || 'asc');
    }

    // Output format
    switch (options.format) {
      case 'json':
        console.log(JSON.stringify(filteredCommands, null, 2));
        break;
        
      case 'yaml':
        const yaml = await import('yaml');
        console.log(yaml.stringify(filteredCommands));
        break;
        
      case 'table':
      default:
        displayCommandsTable(filteredCommands, options);
        break;
    }

    // Show additional details if requested
    if (options.detailed) {
      console.log(chalk.blue.bold('\n📊 Command Statistics:'));
      const stats = await commandLoader.getCommandStatistics();
      displayCommandStatistics(stats);
    }

  } catch (error) {
    spinner.fail(`Failed to load command configurations: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

/**
 * List all configurations command - mcp list
 */
export async function listAll(options: MCPListOptions = {}) {
  console.log(chalk.blue.bold('🤖 MCP Configuration Overview\n'));
  
  // List agents
  console.log(chalk.cyan.bold('Agents:'));
  await listAgents({ ...options, format: 'table' });
  
  console.log('\n');
  
  // List commands
  console.log(chalk.cyan.bold('Commands:'));
  await listCommands({ ...options, format: 'table' });
}

/**
 * Doctor command - mcp doctor
 */
export async function doctor(options: MCPDoctorOptions = {}) {
  console.log(chalk.blue.bold('🔧 MCP Configuration Doctor\n'));
  
  const spinner = ora('Running configuration diagnostics...').start();
  
  try {
    const { configManager } = initializeConfigSystem();
    
    // Run comprehensive validation
    const validationResult = await configManager.doctor();
    
    spinner.succeed('Configuration diagnostics completed');
    
    // Display results
    displayDoctorResults(validationResult, options);
    
    // Show metrics
    if (options.verbose) {
      console.log(chalk.blue.bold('\n📊 System Metrics:'));
      const metrics = configManager.getMetrics();
      displaySystemMetrics(metrics);
    }
    
    // Check for common issues
    await runAdditionalChecks(options);
    
    // Exit with appropriate code
    if (!validationResult.isValid) {
      process.exit(1);
    }

  } catch (error) {
    spinner.fail(`Configuration diagnostics failed: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

/**
 * Initialize configuration directories - mcp init
 */
export async function initializeConfiguration(scope: 'global' | 'project' = 'project') {
  const spinner = ora(`Initializing ${scope} MCP configuration...`).start();
  
  try {
    const configDir = scope === 'global' 
      ? path.join(require('os').homedir(), '.mcp')
      : path.join(process.cwd(), '.mcp');
      
    const commandsDir = path.join(configDir, 'commands');
    
    // Create directories
    await fs.promises.mkdir(configDir, { recursive: true });
    await fs.promises.mkdir(commandsDir, { recursive: true });
    
    // Create example agent configuration
    const exampleAgent = AgentDefinitionLoader.generateAgentTemplate(
      'example-agent',
      'developer',
      {
        capabilities: ['code-generation', 'refactoring', 'analysis'],
        description: 'Example developer agent for code assistance',
        author: 'MCP CLI',
        securityLevel: 'medium',
      }
    );
    
    await fs.promises.writeFile(
      path.join(configDir, 'example-agent.md'),
      exampleAgent
    );
    
    // Create example command configuration
    const exampleCommand = CommandDefinitionLoader.generateCommandTemplate(
      'example-generate',
      'generation',
      {
        description: 'Example code generation command',
        parameters: [
          { name: 'prompt', type: 'string', required: true, description: 'Code generation prompt' },
          { name: 'filePath', type: 'string', required: true, description: 'Target file path' },
          { name: 'language', type: 'string', required: false, description: 'Programming language' },
        ],
        outputFormat: 'code',
        author: 'MCP CLI',
        securityLevel: 'medium',
      }
    );
    
    await fs.promises.writeFile(
      path.join(commandsDir, 'example-generate.md'),
      exampleCommand
    );
    
    spinner.succeed(`MCP configuration initialized in ${configDir}`);
    
    console.log(chalk.green.bold('\n✅ Configuration initialized successfully!'));
    console.log(chalk.gray(`\n   Configuration directory: ${configDir}`));
    console.log(chalk.gray(`   Commands directory: ${commandsDir}`));
    console.log(chalk.gray('\n   Example files created:'));
    console.log(chalk.gray(`   - ${path.join(configDir, 'example-agent.md')}`));
    console.log(chalk.gray(`   - ${path.join(commandsDir, 'example-generate.md')}`));
    console.log(chalk.yellow('\n💡 Next steps:'));
    console.log(chalk.yellow('   1. Edit the example configurations to match your needs'));
    console.log(chalk.yellow('   2. Run "mcp doctor" to validate your configurations'));
    console.log(chalk.yellow('   3. Use "mcp list agents" and "mcp list commands" to see your configurations'));

  } catch (error) {
    spinner.fail(`Failed to initialize configuration: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

/**
 * Helper functions
 */

function displayAgentsTable(agents: AgentDefinition[], options: MCPListOptions) {
  const headers = ['Name', 'Type', 'Capabilities', 'Source', 'Version'];
  
  if (options.detailed) {
    headers.push('Security', 'Multi-Agent', 'Last Modified');
  }
  
  const rows = agents.map(agent => {
    const row = [
      chalk.cyan(agent.frontMatter.name),
      agent.type,
      agent.capabilities.slice(0, 3).join(', ') + (agent.capabilities.length > 3 ? '...' : ''),
      getSourceColor(agent.source),
      agent.metadata.version,
    ];
    
    if (options.detailed) {
      row.push(
        agent.securitySettings.securityLevel,
        agent.collaborationSettings.multiAgent ? '✓' : '✗',
        agent.lastModified.toLocaleDateString()
      );
    }
    
    return row;
  });
  
  console.log(table([headers, ...rows], {
    border: {
      topBody: `─`,
      topJoin: `┬`,
      topLeft: `┌`,
      topRight: `┐`,
      bottomBody: `─`,
      bottomJoin: `┴`,
      bottomLeft: `└`,
      bottomRight: `┘`,
      bodyLeft: `│`,
      bodyRight: `│`,
      bodyJoin: `│`,
      joinBody: `─`,
      joinLeft: `├`,
      joinRight: `┤`,
      joinJoin: `┼`
    }
  }));
}

function displayCommandsTable(commands: CommandDefinition[], options: MCPListOptions) {
  const headers = ['Name', 'Type', 'Output Format', 'Parameters', 'Source', 'Version'];
  
  if (options.detailed) {
    headers.push('Security', 'Usage', 'Last Modified');
  }
  
  const rows = commands.map(command => {
    const paramCount = Object.keys(command.parameterSchema).length;
    const row = [
      chalk.cyan(command.frontMatter.name),
      command.type,
      command.outputFormat,
      `${paramCount} param${paramCount !== 1 ? 's' : ''}`,
      getSourceColor(command.source),
      command.metadata.version,
    ];
    
    if (options.detailed) {
      row.push(
        command.securitySettings.securityLevel,
        (command.metadata.usageCount || 0).toString(),
        command.lastModified.toLocaleDateString()
      );
    }
    
    return row;
  });
  
  console.log(table([headers, ...rows], {
    border: {
      topBody: `─`,
      topJoin: `┬`,
      topLeft: `┌`,
      topRight: `┐`,
      bottomBody: `─`,
      bottomJoin: `┴`,
      bottomLeft: `└`,
      bottomRight: `┘`,
      bodyLeft: `│`,
      bodyRight: `│`,
      bodyJoin: `│`,
      joinBody: `─`,
      joinLeft: `├`,
      joinRight: `┤`,
      joinJoin: `┼`
    }
  }));
}

function displayAgentStatistics(stats: any) {
  console.log(`   Total agents: ${chalk.cyan(stats.total)}`);
  console.log(`   By type: ${Object.entries(stats.byType).map(([type, count]) => `${type}(${count})`).join(', ')}`);
  console.log(`   By security level: ${Object.entries(stats.bySecurityLevel).map(([level, count]) => `${level}(${count})`).join(', ')}`);
  console.log(`   Average capabilities: ${chalk.cyan(stats.averageCapabilities.toFixed(1))}`);
  
  if (stats.mostCommonCapabilities.length > 0) {
    console.log(`   Top capabilities: ${stats.mostCommonCapabilities.slice(0, 5).map((cap: any) => `${cap.capability}(${cap.count})`).join(', ')}`);
  }
}

function displayCommandStatistics(stats: any) {
  console.log(`   Total commands: ${chalk.cyan(stats.total)}`);
  console.log(`   By type: ${Object.entries(stats.byType).map(([type, count]) => `${type}(${count})`).join(', ')}`);
  console.log(`   By output format: ${Object.entries(stats.byOutputFormat).map(([format, count]) => `${format}(${count})`).join(', ')}`);
  console.log(`   Average parameters: ${chalk.cyan(stats.averageParameters.toFixed(1))}`);
  console.log(`   Total usage: ${chalk.cyan(stats.totalUsage)}`);
  
  if (stats.mostCommonParameters.length > 0) {
    console.log(`   Common parameters: ${stats.mostCommonParameters.slice(0, 5).map((param: any) => `${param.parameter}(${param.count})`).join(', ')}`);
  }
}

function displayDoctorResults(result: ConfigurationValidationResult, options: MCPDoctorOptions) {
  // Summary
  const status = result.isValid ? chalk.green('✅ HEALTHY') : chalk.red('❌ ISSUES FOUND');
  console.log(`\nOverall Status: ${status}\n`);
  
  // Statistics
  console.log(chalk.blue.bold('📊 Configuration Statistics:'));
  console.log(`   Total configurations: ${chalk.cyan(result.statistics.totalConfigurations)}`);
  console.log(`   Agent configurations: ${chalk.cyan(result.statistics.agentConfigurations)}`);
  console.log(`   Command configurations: ${chalk.cyan(result.statistics.commandConfigurations)}`);
  console.log(`   Overrides: ${chalk.cyan(result.statistics.overrides)}`);
  console.log(`   Conflicts: ${chalk.cyan(result.statistics.conflicts)}`);
  
  // Errors
  if (result.errors.length > 0) {
    console.log(chalk.red.bold('\n❌ Errors:'));
    result.errors.forEach((error, index) => {
      console.log(chalk.red(`   ${index + 1}. ${error.file}${error.line ? `:${error.line}` : ''}`));
      console.log(chalk.red(`      ${error.message}`));
      if (error.code) {
        console.log(chalk.gray(`      Code: ${error.code}`));
      }
    });
  }
  
  // Warnings
  if (result.warnings.length > 0 && (options.includeWarnings || options.verbose)) {
    console.log(chalk.yellow.bold('\n⚠️  Warnings:'));
    result.warnings.forEach((warning, index) => {
      console.log(chalk.yellow(`   ${index + 1}. ${warning.file}${warning.line ? `:${warning.line}` : ''}`));
      console.log(chalk.yellow(`      ${warning.message}`));
    });
  }
  
  // JSON output if requested
  if (options.outputFormat === 'json') {
    console.log('\n' + JSON.stringify(result, null, 2));
  }
}

function displaySystemMetrics(metrics: any) {
  console.log(`   Load time: ${chalk.cyan(metrics.loadTime + 'ms')}`);
  console.log(`   Cache hit rate: ${chalk.cyan((metrics.cacheHitRate * 100).toFixed(1) + '%')}`);
  console.log(`   Memory usage: ${chalk.cyan((metrics.memoryUsage / 1024 / 1024).toFixed(1) + 'MB')}`);
  console.log(`   Last reload: ${chalk.cyan(metrics.lastReloadTime.toLocaleString())}`);
  console.log(`   Resolution conflicts: ${chalk.cyan(metrics.resolutionConflicts)}`);
  console.log(`   Validation errors: ${chalk.cyan(metrics.validationErrors)}`);
}

async function runAdditionalChecks(options: MCPDoctorOptions) {
  console.log(chalk.blue.bold('\n🔍 Additional Checks:'));
  
  // Check for .mcp directories
  const projectMcpPath = path.join(process.cwd(), '.mcp');
  const globalMcpPath = path.join(require('os').homedir(), '.mcp');
  
  const projectExists = fs.existsSync(projectMcpPath);
  const globalExists = fs.existsSync(globalMcpPath);
  
  console.log(`   Project .mcp directory: ${projectExists ? chalk.green('✓ Found') : chalk.gray('✗ Not found')}`);
  console.log(`   Global .mcp directory: ${globalExists ? chalk.green('✓ Found') : chalk.gray('✗ Not found')}`);
  
  if (!projectExists && !globalExists) {
    console.log(chalk.yellow('\n💡 Recommendation: Run "mcp init" to create configuration directories'));
  }
  
  // Check for commands subdirectory
  if (projectExists) {
    const projectCommandsPath = path.join(projectMcpPath, 'commands');
    const projectCommandsExists = fs.existsSync(projectCommandsPath);
    console.log(`   Project commands directory: ${projectCommandsExists ? chalk.green('✓ Found') : chalk.gray('✗ Not found')}`);
  }
  
  if (globalExists) {
    const globalCommandsPath = path.join(globalMcpPath, 'commands');
    const globalCommandsExists = fs.existsSync(globalCommandsPath);
    console.log(`   Global commands directory: ${globalCommandsExists ? chalk.green('✓ Found') : chalk.gray('✗ Not found')}`);
  }
}

function getSourceColor(source: string): string {
  switch (source) {
    case 'default': return chalk.blue('default');
    case 'global': return chalk.cyan('global');
    case 'project': return chalk.green('project');
    default: return chalk.gray(source);
  }
}

function sortAgents(agents: AgentDefinition[], sortBy: string, sortOrder: 'asc' | 'desc') {
  const multiplier = sortOrder === 'asc' ? 1 : -1;
  
  return agents.sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return multiplier * a.frontMatter.name.localeCompare(b.frontMatter.name);
      case 'type':
        return multiplier * a.type.localeCompare(b.type);
      case 'lastModified':
        return multiplier * (a.lastModified.getTime() - b.lastModified.getTime());
      case 'priority':
        const aPriority = a.frontMatter.priority || 0;
        const bPriority = b.frontMatter.priority || 0;
        return multiplier * (aPriority - bPriority);
      default:
        return 0;
    }
  });
}

function sortCommands(commands: CommandDefinition[], sortBy: string, sortOrder: 'asc' | 'desc') {
  const multiplier = sortOrder === 'asc' ? 1 : -1;
  
  return commands.sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return multiplier * a.frontMatter.name.localeCompare(b.frontMatter.name);
      case 'type':
        return multiplier * a.type.localeCompare(b.type);
      case 'lastModified':
        return multiplier * (a.lastModified.getTime() - b.lastModified.getTime());
      case 'priority':
        const aPriority = a.frontMatter.priority || 0;
        const bPriority = b.frontMatter.priority || 0;
        return multiplier * (aPriority - bPriority);
      default:
        return 0;
    }
  });
}