/**
 * CommandDefinitionLoader - Specialized loader for command configurations and instructions
 * Handles loading and processing of command-specific Markdown files from commands/ subdirectory
 */

import * as path from 'path';
import { ConfigurationManager } from '../config/configuration-manager';
import { MarkdownParser } from '../utils/markdown-parser';
import {
  MCPConfiguration,
  CommandConfiguration,
  ConfigurationLoadOptions,
  ConfigurationError,
  MCPYamlFrontMatter,
} from '../types/configuration';

export interface CommandLoadOptions extends ConfigurationLoadOptions {
  filterByType?: ('generation' | 'analysis' | 'refactoring' | 'testing' | 'deployment')[];
  filterByOutputFormat?: ('json' | 'markdown' | 'plain' | 'code')[];
  includeParameters?: boolean;
  includeValidation?: boolean;
  includeErrorHandling?: boolean;
  sortBy?: 'name' | 'priority' | 'lastModified' | 'type';
  sortOrder?: 'asc' | 'desc';
}

export interface CommandDefinition extends CommandConfiguration {
  type: 'generation' | 'analysis' | 'refactoring' | 'testing' | 'deployment';
  outputFormat: 'json' | 'markdown' | 'plain' | 'code';
  parameterSchema: {
    [key: string]: {
      type: string;
      required: boolean;
      description: string;
      default?: any;
      validation?: {
        pattern?: string;
        minLength?: number;
        maxLength?: number;
        minimum?: number;
        maximum?: number;
        enum?: any[];
      };
    };
  };
  executionSettings: {
    preExecutionChecks: string[];
    postExecutionActions: string[];
    timeoutMs: number;
    retryAttempts: number;
    requiresConfirmation: boolean;
  };
  errorHandling: {
    retryCount: number;
    fallbackStrategy: 'escalate' | 'skip' | 'prompt' | 'default';
    escalationRules: string[];
    errorMessages: Record<string, string>;
  };
  contextRequirements: {
    requiredContext: string[];
    maxContextSize: number;
    preserveContext: boolean;
  };
  securitySettings: {
    restricted: boolean;
    requiredPermissions: string[];
    securityLevel: 'low' | 'medium' | 'high' | 'critical';
    sandboxed: boolean;
  };
  metadata: {
    author?: string;
    version: string;
    description?: string;
    documentationUrl?: string;
    createdAt?: Date;
    updatedAt?: Date;
    usageCount?: number;
    lastUsed?: Date;
  };
}

export interface CommandExecutionContext {
  command: CommandDefinition;
  parameters: Record<string, any>;
  workingDirectory: string;
  executionEnvironment: 'development' | 'staging' | 'production';
  securityContext: {
    permissions: string[];
    securityLevel: string;
    sandboxed: boolean;
  };
  timeoutMs?: number;
  retryAttempts?: number;
  parentCommand?: string;
  dependentCommands?: string[];
}

export interface CommandValidationResult {
  isValid: boolean;
  errors: Array<{
    parameter: string;
    message: string;
    value?: any;
  }>;
  warnings: Array<{
    parameter: string;
    message: string;
    suggestion?: string;
  }>;
  normalizedParameters: Record<string, any>;
}

export class CommandDefinitionLoader {
  private configManager: ConfigurationManager;
  private markdownParser: MarkdownParser;
  
  constructor(configManager: ConfigurationManager) {
    this.configManager = configManager;
    this.markdownParser = new MarkdownParser({
      strictMode: false,
      validateFrontMatter: true,
      requireFrontMatter: true,
    });
  }

  /**
   * Load all command definitions from configuration hierarchy
   */
  async loadCommandDefinitions(options: CommandLoadOptions = {}): Promise<CommandDefinition[]> {
    try {
      const hierarchy = await this.configManager.loadConfigurations({
        includeDefault: options.includeDefault ?? true,
        includeGlobal: options.includeGlobal ?? true,
        includeProject: options.includeProject ?? true,
        validateOnLoad: options.validateOnLoad ?? true,
        verbose: options.verbose ?? false,
      });

      const commandConfigs = this.configManager.getCommandConfigurations(hierarchy.resolved);
      let commandDefinitions = commandConfigs.map(config => this.transformToCommandDefinition(config));

      // Apply filters
      commandDefinitions = this.applyFilters(commandDefinitions, options);

      // Sort results
      commandDefinitions = this.sortCommandDefinitions(commandDefinitions, options);

      return commandDefinitions;
    } catch (error) {
      throw new ConfigurationError(
        `Failed to load command definitions: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        undefined,
        undefined,
        'COMMAND_LOAD_ERROR'
      );
    }
  }

  /**
   * Load a specific command definition by name
   */
  async loadCommandDefinition(
    name: string, 
    options: CommandLoadOptions = {}
  ): Promise<CommandDefinition | null> {
    const commands = await this.loadCommandDefinitions(options);
    return commands.find(command => command.frontMatter.name === name) || null;
  }

  /**
   * Load command definitions by type
   */
  async loadCommandDefinitionsByType(
    type: 'generation' | 'analysis' | 'refactoring' | 'testing' | 'deployment',
    options: CommandLoadOptions = {}
  ): Promise<CommandDefinition[]> {
    return this.loadCommandDefinitions({
      ...options,
      filterByType: [type],
    });
  }

  /**
   * Create execution context for a command
   */
  createExecutionContext(
    command: CommandDefinition,
    parameters: Record<string, any>,
    options: {
      workingDirectory?: string;
      executionEnvironment?: 'development' | 'staging' | 'production';
      timeoutMs?: number;
      retryAttempts?: number;
      parentCommand?: string;
      dependentCommands?: string[];
    } = {}
  ): CommandExecutionContext {
    return {
      command,
      parameters,
      workingDirectory: options.workingDirectory || process.cwd(),
      executionEnvironment: options.executionEnvironment || 'development',
      securityContext: {
        permissions: command.securitySettings.requiredPermissions,
        securityLevel: command.securitySettings.securityLevel,
        sandboxed: command.securitySettings.sandboxed,
      },
      timeoutMs: options.timeoutMs || command.executionSettings.timeoutMs,
      retryAttempts: options.retryAttempts || command.executionSettings.retryAttempts,
      parentCommand: options.parentCommand,
      dependentCommands: options.dependentCommands || [],
    };
  }

  /**
   * Validate command parameters against schema
   */
  validateCommandParameters(
    command: CommandDefinition,
    parameters: Record<string, any>
  ): CommandValidationResult {
    const errors: Array<{ parameter: string; message: string; value?: any }> = [];
    const warnings: Array<{ parameter: string; message: string; suggestion?: string }> = [];
    const normalizedParameters: Record<string, any> = {};

    for (const [paramName, paramSchema] of Object.entries(command.parameterSchema)) {
      const value = parameters[paramName];
      
      // Check required parameters
      if (paramSchema.required && (value === undefined || value === null)) {
        errors.push({
          parameter: paramName,
          message: `Parameter '${paramName}' is required`,
        });
        continue;
      }

      // Use default value if not provided
      if (value === undefined && paramSchema.default !== undefined) {
        normalizedParameters[paramName] = paramSchema.default;
        continue;
      }

      // Skip validation if value is not provided and not required
      if (value === undefined) {
        continue;
      }

      // Type validation
      const typeValidation = this.validateParameterType(paramName, value, paramSchema.type);
      if (!typeValidation.isValid) {
        errors.push({
          parameter: paramName,
          message: typeValidation.message,
          value,
        });
        continue;
      }

      let normalizedValue = typeValidation.normalizedValue;

      // Additional validation rules
      if (paramSchema.validation) {
        const validationResults = this.validateParameterConstraints(
          paramName,
          normalizedValue,
          paramSchema.validation
        );
        
        errors.push(...validationResults.errors);
        warnings.push(...validationResults.warnings);
        
        if (validationResults.errors.length === 0) {
          normalizedValue = validationResults.normalizedValue;
        }
      }

      normalizedParameters[paramName] = normalizedValue;
    }

    // Check for unknown parameters
    for (const paramName of Object.keys(parameters)) {
      if (!command.parameterSchema[paramName]) {
        warnings.push({
          parameter: paramName,
          message: `Unknown parameter '${paramName}' will be ignored`,
          suggestion: `Available parameters: ${Object.keys(command.parameterSchema).join(', ')}`,
        });
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      normalizedParameters,
    };
  }

  /**
   * Generate command execution plan
   */
  generateExecutionPlan(
    commands: CommandDefinition[],
    parameters: Record<string, Record<string, any>>
  ): {
    executionOrder: string[];
    dependencies: Record<string, string[]>;
    validationResults: Record<string, CommandValidationResult>;
    estimatedDuration: number;
    securityRequirements: {
      maxSecurityLevel: string;
      requiredPermissions: string[];
      sandboxedCommands: string[];
    };
  } {
    const executionOrder: string[] = [];
    const dependencies: Record<string, string[]> = {};
    const validationResults: Record<string, CommandValidationResult> = {};
    let estimatedDuration = 0;
    
    const securityRequirements = {
      maxSecurityLevel: 'low',
      requiredPermissions: [] as string[],
      sandboxedCommands: [] as string[],
    };

    // Validate parameters for each command
    for (const command of commands) {
      const commandParams = parameters[command.frontMatter.name] || {};
      validationResults[command.frontMatter.name] = this.validateCommandParameters(
        command,
        commandParams
      );
      
      // Update security requirements
      const securityLevels = ['low', 'medium', 'high', 'critical'];
      const currentMaxIndex = securityLevels.indexOf(securityRequirements.maxSecurityLevel);
      const commandSecurityIndex = securityLevels.indexOf(command.securitySettings.securityLevel);
      
      if (commandSecurityIndex > currentMaxIndex) {
        securityRequirements.maxSecurityLevel = command.securitySettings.securityLevel;
      }
      
      securityRequirements.requiredPermissions.push(
        ...command.securitySettings.requiredPermissions
      );
      
      if (command.securitySettings.sandboxed) {
        securityRequirements.sandboxedCommands.push(command.frontMatter.name);
      }
      
      // Add to estimated duration
      estimatedDuration += command.executionSettings.timeoutMs;
    }

    // Remove duplicate permissions
    securityRequirements.requiredPermissions = [
      ...new Set(securityRequirements.requiredPermissions)
    ];

    // Build dependency graph and execution order
    // For now, use simple sequential order - could be enhanced with dependency analysis
    executionOrder.push(...commands.map(cmd => cmd.frontMatter.name));

    return {
      executionOrder,
      dependencies,
      validationResults,
      estimatedDuration,
      securityRequirements,
    };
  }

  /**
   * Transform configuration to command definition
   */
  private transformToCommandDefinition(config: CommandConfiguration): CommandDefinition {
    const frontMatter = config.frontMatter;
    
    return {
      ...config,
      type: frontMatter.command_type || 'generation',
      outputFormat: frontMatter.output_format || 'markdown',
      parameterSchema: this.parseParameterSchema(config.parameters || {}),
      executionSettings: {
        preExecutionChecks: config.preExecutionChecks || [],
        postExecutionActions: config.postExecutionActions || [],
        timeoutMs: (frontMatter as any).timeout_ms || 30000,
        retryAttempts: (frontMatter as any).retry_attempts || 3,
        requiresConfirmation: (frontMatter as any).requires_confirmation || false,
      },
      errorHandling: {
        retryCount: config.errorHandling?.retryCount || 3,
        fallbackStrategy: config.errorHandling?.fallbackStrategy as any || 'escalate',
        escalationRules: config.errorHandling?.escalationRules || [],
        errorMessages: (frontMatter as any).error_messages || {},
      },
      contextRequirements: {
        requiredContext: frontMatter.required_context || [],
        maxContextSize: frontMatter.max_context_size || 4096,
        preserveContext: (frontMatter as any).preserve_context || false,
      },
      securitySettings: {
        restricted: frontMatter.restricted || false,
        requiredPermissions: frontMatter.required_permissions || [],
        securityLevel: frontMatter.security_level || 'medium',
        sandboxed: (frontMatter as any).sandboxed || false,
      },
      metadata: {
        author: frontMatter.author,
        version: frontMatter.version || '1.0.0',
        description: frontMatter.description,
        documentationUrl: frontMatter.documentation_url,
        createdAt: frontMatter.created_at ? new Date(frontMatter.created_at) : undefined,
        updatedAt: frontMatter.updated_at ? new Date(frontMatter.updated_at) : undefined,
        usageCount: (frontMatter as any).usage_count || 0,
        lastUsed: (frontMatter as any).last_used ? new Date((frontMatter as any).last_used) : undefined,
      },
    };
  }

  /**
   * Parse parameter schema from configuration
   */
  private parseParameterSchema(parameters: any): CommandDefinition['parameterSchema'] {
    const schema: CommandDefinition['parameterSchema'] = {};
    
    for (const [name, config] of Object.entries(parameters)) {
      const paramConfig = config as any;
      schema[name] = {
        type: paramConfig.type || 'string',
        required: paramConfig.required || false,
        description: paramConfig.description || '',
        default: paramConfig.default,
        validation: paramConfig.validation || {},
      };
    }
    
    return schema;
  }

  /**
   * Apply filters to command definitions
   */
  private applyFilters(commands: CommandDefinition[], options: CommandLoadOptions): CommandDefinition[] {
    let filtered = commands;

    // Filter by type
    if (options.filterByType && options.filterByType.length > 0) {
      filtered = filtered.filter(command => options.filterByType!.includes(command.type));
    }

    // Filter by output format
    if (options.filterByOutputFormat && options.filterByOutputFormat.length > 0) {
      filtered = filtered.filter(command => options.filterByOutputFormat!.includes(command.outputFormat));
    }

    return filtered;
  }

  /**
   * Sort command definitions
   */
  private sortCommandDefinitions(commands: CommandDefinition[], options: CommandLoadOptions): CommandDefinition[] {
    if (!options.sortBy) {
      return commands;
    }

    const sortOrder = options.sortOrder || 'asc';
    const multiplier = sortOrder === 'asc' ? 1 : -1;

    return commands.sort((a, b) => {
      switch (options.sortBy) {
        case 'name':
          return multiplier * a.frontMatter.name.localeCompare(b.frontMatter.name);
          
        case 'priority':
          const aPriority = a.frontMatter.priority || 0;
          const bPriority = b.frontMatter.priority || 0;
          return multiplier * (aPriority - bPriority);
          
        case 'lastModified':
          return multiplier * (a.lastModified.getTime() - b.lastModified.getTime());
          
        case 'type':
          return multiplier * a.type.localeCompare(b.type);
          
        default:
          return 0;
      }
    });
  }

  /**
   * Validate parameter type
   */
  private validateParameterType(
    paramName: string,
    value: any,
    expectedType: string
  ): { isValid: boolean; message: string; normalizedValue: any } {
    const normalizedValue = value;
    
    switch (expectedType.toLowerCase()) {
      case 'string':
        if (typeof value !== 'string') {
          normalizedValue = String(value);
        }
        break;
        
      case 'number':
        const numValue = Number(value);
        if (isNaN(numValue)) {
          return {
            isValid: false,
            message: `Parameter '${paramName}' must be a number`,
            normalizedValue: value,
          };
        }
        normalizedValue = numValue;
        break;
        
      case 'boolean':
        if (typeof value === 'string') {
          normalizedValue = value.toLowerCase() === 'true';
        } else if (typeof value !== 'boolean') {
          normalizedValue = Boolean(value);
        }
        break;
        
      case 'array':
        if (!Array.isArray(value)) {
          if (typeof value === 'string') {
            try {
              normalizedValue = JSON.parse(value);
              if (!Array.isArray(normalizedValue)) {
                throw new Error('Not an array');
              }
            } catch {
              // Try comma-separated values
              normalizedValue = value.split(',').map(v => v.trim());
            }
          } else {
            return {
              isValid: false,
              message: `Parameter '${paramName}' must be an array`,
              normalizedValue: value,
            };
          }
        }
        break;
        
      case 'object':
        if (typeof value !== 'object' || value === null || Array.isArray(value)) {
          if (typeof value === 'string') {
            try {
              normalizedValue = JSON.parse(value);
            } catch {
              return {
                isValid: false,
                message: `Parameter '${paramName}' must be a valid JSON object`,
                normalizedValue: value,
              };
            }
          } else {
            return {
              isValid: false,
              message: `Parameter '${paramName}' must be an object`,
              normalizedValue: value,
            };
          }
        }
        break;
        
      default:
        // Unknown type, accept as-is
        break;
    }

    return {
      isValid: true,
      message: '',
      normalizedValue,
    };
  }

  /**
   * Validate parameter constraints
   */
  private validateParameterConstraints(
    paramName: string,
    value: any,
    validation: any
  ): {
    errors: Array<{ parameter: string; message: string; value?: any }>;
    warnings: Array<{ parameter: string; message: string; suggestion?: string }>;
    normalizedValue: any;
  } {
    const errors: Array<{ parameter: string; message: string; value?: any }> = [];
    const warnings: Array<{ parameter: string; message: string; suggestion?: string }> = [];
    const normalizedValue = value;

    // Pattern validation for strings
    if (validation.pattern && typeof value === 'string') {
      const regex = new RegExp(validation.pattern);
      if (!regex.test(value)) {
        errors.push({
          parameter: paramName,
          message: `Parameter '${paramName}' does not match required pattern: ${validation.pattern}`,
          value,
        });
      }
    }

    // Length validation for strings and arrays
    if (typeof value === 'string' || Array.isArray(value)) {
      if (validation.minLength !== undefined && value.length < validation.minLength) {
        errors.push({
          parameter: paramName,
          message: `Parameter '${paramName}' must have at least ${validation.minLength} ${typeof value === 'string' ? 'characters' : 'items'}`,
          value,
        });
      }
      
      if (validation.maxLength !== undefined && value.length > validation.maxLength) {
        errors.push({
          parameter: paramName,
          message: `Parameter '${paramName}' must have at most ${validation.maxLength} ${typeof value === 'string' ? 'characters' : 'items'}`,
          value,
        });
      }
    }

    // Numeric range validation
    if (typeof value === 'number') {
      if (validation.minimum !== undefined && value < validation.minimum) {
        errors.push({
          parameter: paramName,
          message: `Parameter '${paramName}' must be at least ${validation.minimum}`,
          value,
        });
      }
      
      if (validation.maximum !== undefined && value > validation.maximum) {
        errors.push({
          parameter: paramName,
          message: `Parameter '${paramName}' must be at most ${validation.maximum}`,
          value,
        });
      }
    }

    // Enum validation
    if (validation.enum && Array.isArray(validation.enum)) {
      if (!validation.enum.includes(value)) {
        errors.push({
          parameter: paramName,
          message: `Parameter '${paramName}' must be one of: ${validation.enum.join(', ')}`,
          value,
        });
      }
    }

    return {
      errors,
      warnings,
      normalizedValue,
    };
  }

  /**
   * Generate command definition template
   */
  static generateCommandTemplate(
    name: string,
    type: 'generation' | 'analysis' | 'refactoring' | 'testing' | 'deployment',
    options: {
      description?: string;
      parameters?: Array<{ name: string; type: string; required: boolean; description: string }>;
      outputFormat?: 'json' | 'markdown' | 'plain' | 'code';
      author?: string;
      securityLevel?: 'low' | 'medium' | 'high' | 'critical';
    } = {}
  ): string {
    const frontMatter: MCPYamlFrontMatter = {
      name,
      scope: 'project',
      tags: [type, 'command'],
      version: '1.0.0',
      command_type: type,
      output_format: options.outputFormat || 'markdown',
      security_level: options.securityLevel || 'medium',
      required_context: [],
      author: options.author,
      description: options.description,
      created_at: new Date().toISOString(),
    };

    const parametersList = (options.parameters || [])
      .map(p => `- ${p.name}: ${p.description} (${p.type}${p.required ? ', required' : ', optional'})`)
      .join('\n');

    const content = `# ${name.charAt(0).toUpperCase() + name.slice(1)} Command

${options.description || `Command for ${type} operations.`}

## Parameters

${parametersList || '- No parameters defined'}

## Instructions

Provide detailed instructions for executing this command.

## Pre-execution Checks

- Validate all parameters
- Check required permissions
- Verify working directory

## Post-execution Actions

- Validate outputs
- Clean up temporary files
- Log execution results

## Error Handling

- Retry on transient failures
- Escalate on critical errors
- Provide clear error messages

## Examples

### Example 1
\`\`\`bash
mcp ${name} --param1 value1 --param2 value2
\`\`\`

Expected output: Description of expected results
`;

    return MarkdownParser.createMarkdownFile(frontMatter, content);
  }

  /**
   * Get command statistics
   */
  async getCommandStatistics(): Promise<{
    total: number;
    byType: Record<string, number>;
    byOutputFormat: Record<string, number>;
    bySecurityLevel: Record<string, number>;
    bySource: Record<string, number>;
    averageParameters: number;
    mostCommonParameters: Array<{ parameter: string; count: number }>;
    totalUsage: number;
  }> {
    const commands = await this.loadCommandDefinitions();
    
    const stats = {
      total: commands.length,
      byType: {} as Record<string, number>,
      byOutputFormat: {} as Record<string, number>,
      bySecurityLevel: {} as Record<string, number>,
      bySource: {} as Record<string, number>,
      averageParameters: 0,
      mostCommonParameters: [] as Array<{ parameter: string; count: number }>,
      totalUsage: 0,
    };

    // Count by various attributes
    commands.forEach(command => {
      stats.byType[command.type] = (stats.byType[command.type] || 0) + 1;
      stats.byOutputFormat[command.outputFormat] = (stats.byOutputFormat[command.outputFormat] || 0) + 1;
      stats.bySecurityLevel[command.securitySettings.securityLevel] = 
        (stats.bySecurityLevel[command.securitySettings.securityLevel] || 0) + 1;
      stats.bySource[command.source] = (stats.bySource[command.source] || 0) + 1;
      stats.totalUsage += command.metadata.usageCount || 0;
    });

    // Calculate average parameters
    const totalParameters = commands.reduce((sum, command) => 
      sum + Object.keys(command.parameterSchema).length, 0);
    stats.averageParameters = commands.length > 0 ? totalParameters / commands.length : 0;

    // Find most common parameters
    const parameterCount = new Map<string, number>();
    commands.forEach(command => {
      Object.keys(command.parameterSchema).forEach(parameter => {
        parameterCount.set(parameter, (parameterCount.get(parameter) || 0) + 1);
      });
    });

    stats.mostCommonParameters = Array.from(parameterCount.entries())
      .map(([parameter, count]) => ({ parameter, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    return stats;
  }
}