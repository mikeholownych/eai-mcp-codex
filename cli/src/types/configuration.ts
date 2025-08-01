/**
 * Comprehensive type definitions for MCP Configuration System
 * Supports both ~/.mcp/ (global) and ./.mcp/ (project) scoped configurations
 */

export interface MCPYamlFrontMatter {
  name: string;
  scope?: 'global' | 'project' | 'default';
  tags?: string[];
  version?: string;
  priority?: number;
  extends?: string; // Reference to parent configuration
  overrides?: string[]; // List of configurations this overrides
  dependencies?: string[]; // Required configurations
  
  // Agent-specific metadata
  agent_type?: 'planner' | 'developer' | 'security' | 'domain-expert' | 'custom';
  capabilities?: string[];
  model_preferences?: string[];
  
  // Command-specific metadata
  command_type?: 'generation' | 'analysis' | 'refactoring' | 'testing' | 'deployment';
  required_context?: string[];
  output_format?: 'json' | 'markdown' | 'plain' | 'code';
  
  // Security and access control
  restricted?: boolean;
  required_permissions?: string[];
  security_level?: 'low' | 'medium' | 'high' | 'critical';
  
  // Collaboration settings
  multi_agent?: boolean;
  collaboration_mode?: 'sequential' | 'parallel' | 'consensus';
  escalation_threshold?: number;
  
  // Environment and context
  environment?: 'development' | 'staging' | 'production' | 'all';
  context_retention?: boolean;
  max_context_size?: number;
  
  // Validation and quality
  validation_rules?: string[];
  quality_gates?: string[];
  auto_verify?: boolean;
  
  // Metadata
  author?: string;
  created_at?: string;
  updated_at?: string;
  description?: string;
  documentation_url?: string;
}

export interface MCPConfiguration {
  frontMatter: MCPYamlFrontMatter;
  content: string;
  filePath: string;
  source: 'default' | 'global' | 'project';
  lastModified: Date;
  checksum?: string;
}

export interface AgentDefinition extends MCPConfiguration {
  instructions: string;
  systemPrompt?: string;
  examples?: Array<{
    input: string;
    output: string;
    explanation?: string;
  }>;
  constraints?: string[];
  behaviorModifiers?: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
  };
  type: string; // e.g., 'planner', 'developer'
  capabilities: string[];
  securitySettings: { securityLevel: string };
  collaborationSettings: { multiAgent: boolean };
  metadata: { version: string; usageCount?: number; };
}

export interface CommandDefinition extends MCPConfiguration {
  instructions: string;
  parameters?: {
    [key: string]: {
      type: string;
      required: boolean;
      description: string;
      default?: any;
      validation?: string;
    };
  };
  preExecutionChecks?: string[];
  postExecutionActions?: string[];
  errorHandling?: {
    retryCount?: number;
    fallbackStrategy?: string;
    escalationRules?: string[];
  };
  type: string; // e.g., 'generation', 'analysis'
  outputFormat: string;
  parameterSchema: { [key: string]: any }; // Detailed schema for parameters
  executionSettings: { preExecutionChecks: string[]; postExecutionActions: string[] };
  securitySettings: { securityLevel: string };
  contextRequirements: { requiredContext: string[] };
  metadata: { version: string; usageCount?: number; };
}

export interface AgentDefinition extends MCPConfiguration {
  instructions: string;
  systemPrompt?: string;
  examples?: Array<{
    input: string;
    output: string;
    explanation?: string;
  }>;
  constraints?: string[];
  behaviorModifiers?: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    presence_penalty?: number;
    frequency_penalty?: number;
  };
  type: string; // e.g., 'planner', 'developer'
  capabilities: string[];
  securitySettings: { securityLevel: string };
  collaborationSettings: { multiAgent: boolean };
  metadata: { version: string; usageCount?: number; };
}

export interface CommandDefinition extends MCPConfiguration {
  instructions: string;
  parameters?: {
    [key: string]: {
      type: string;
      required: boolean;
      description: string;
      default?: any;
      validation?: string;
    };
  };
  preExecutionChecks?: string[];
  postExecutionActions?: string[];
  errorHandling?: {
    retryCount?: number;
    fallbackStrategy?: string;
    escalationRules?: string[];
  };
  type: string; // e.g., 'generation', 'analysis'
  outputFormat: string;
  parameterSchema: { [key: string]: any }; // Detailed schema for parameters
  executionSettings: { preExecutionChecks: string[]; postExecutionActions: string[] };
  securitySettings: { securityLevel: string };
  contextRequirements: { requiredContext: string[] };
  metadata: { version: string; usageCount?: number; };
}

export interface AgentExecutionContext {
  agent: AgentDefinition;
  parameters: any;
  securityContext: {
    permissions: string[];
  };
  workingDirectory: string;
  executionEnvironment: string;
}

export interface CommandExecutionContext {
  command: CommandDefinition;
  parameters: any;
  securityContext: {
    permissions: string[];
  };
  workingDirectory: string;
  executionEnvironment: string;
  [key: string]: any; // Allow for additional properties
}

export interface ConfigurationHierarchy {
  default: MCPConfiguration[];
  global: MCPConfiguration[];
  project: MCPConfiguration[];
  resolved: MCPConfiguration[];
  settings: { [key: string]: any };
  memory: string;
}

export interface ConfigurationSource {
  type: 'default' | 'global' | 'project';
  path: string;
  exists: boolean;
  readable: boolean;
  lastScanned?: Date;
}

export interface ConfigurationResolutionContext {
  workingDirectory: string;
  homeDirectory: string;
  defaultConfigPath: string;
  sources: ConfigurationSource[];
  resolutionOrder: ('default' | 'global' | 'project')[];
  conflictResolution: 'merge' | 'override' | 'strict';
}

export interface ConfigurationValidationResult {
  isValid: boolean;
  errors: Array<{
    file: string;
    line?: number;
    column?: number;
    severity: 'error' | 'warning' | 'info';
    message: string;
    code?: string;
  }>;
  warnings: Array<{
    file: string;
    line?: number;
    column?: number;
    message: string;
    suggestion?: string;
  }>;
  statistics: {
    totalConfigurations: number;
    agentConfigurations: number;
    commandConfigurations: number;
    overrides: number;
    conflicts: number;
  };
}

export interface ConfigurationLoadOptions {
  includeDefault?: boolean;
  includeGlobal?: boolean;
  includeProject?: boolean;
  validateOnLoad?: boolean;
  watchForChanges?: boolean;
  cacheDuration?: number;
  strictMode?: boolean;
  verbose?: boolean;
}

export interface ConfigurationManagerOptions {
  defaultConfigPath?: string;
  configDirectoryName?: string;
  commandsSubdirectory?: string;
  supportedFileExtensions?: string[];
  enableCaching?: boolean;
  watchForChanges?: boolean;
  conflictResolution?: 'merge' | 'override' | 'strict';
  validationLevel?: 'none' | 'basic' | 'strict';
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
}

export interface ConfigurationCache {
  configurations: Map<string, MCPConfiguration>;
  lastUpdated: Map<string, Date>;
  checksums: Map<string, string>;
  dependencyGraph: Map<string, string[]>;
  resolutionCache: Map<string, MCPConfiguration[]>;
}

export interface ConfigurationWatcher {
  isWatching: boolean;
  watchedPaths: string[];
  callbacks: Array<(event: 'added' | 'changed' | 'removed', filePath: string) => void>;
  debounceMs: number;
}

export interface ConfigurationMetrics {
  loadTime: number;
  cacheHitRate: number;
  totalConfigurations: number;
  resolutionConflicts: number;
  validationErrors: number;
  lastReloadTime: Date;
  memoryUsage: number;
}

// CLI-specific types
export interface MCPListOptions {
  type?: 'agents' | 'commands' | 'all';
  scope?: 'default' | 'global' | 'project' | 'all';
  format?: 'table' | 'json' | 'yaml';
  detailed?: boolean;
  includeContent?: boolean;
  filterTags?: string[];
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface MCPDoctorOptions {
  checkAll?: boolean;
  fixIssues?: boolean;
  verbose?: boolean;
  outputFormat?: 'text' | 'json';
  includeWarnings?: boolean;
}

export interface ConfigurationDiff {
  added: MCPConfiguration[];
  modified: MCPConfiguration[];
  removed: MCPConfiguration[];
  conflicts: Array<{
    path: string;
    configurations: MCPConfiguration[];
    resolution: MCPConfiguration;
    reason: string;
  }>;
}

// Error types
export class ConfigurationError extends Error {
  constructor(
    message: string,
    public filePath?: string,
    public line?: number,
    public column?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ConfigurationError';
  }
}

export class ConfigurationValidationError extends ConfigurationError {
  constructor(
    message: string,
    public violations: Array<{
      rule: string;
      severity: 'error' | 'warning';
      description: string;
    }>,
    filePath?: string,
    line?: number,
    column?: number
  ) {
    super(message, filePath, line, column, 'VALIDATION_ERROR');
    this.name = 'ConfigurationValidationError';
  }
}

export class ConfigurationConflictError extends ConfigurationError {
  constructor(
    message: string,
    public conflicts: Array<{
      name: string;
      sources: string[];
      conflictType: 'name' | 'priority' | 'override';
    }>,
    filePath?: string
  ) {
    super(message, filePath, undefined, undefined, 'CONFIGURATION_CONFLICT');
    this.name = 'ConfigurationConflictError';
  }
}

// Event types for configuration system
export interface ConfigurationEvent {
  type: 'loaded' | 'reloaded' | 'added' | 'modified' | 'removed' | 'error';
  timestamp: Date;
  source: ConfigurationSource;
  configuration?: MCPConfiguration;
  error?: ConfigurationError;
  metadata?: Record<string, any>;
}

export type ConfigurationEventListener = (event: ConfigurationEvent) => void;

// Re-export specialized types from loaders
export type { AgentDefinition, AgentExecutionContext } from '../loaders/agent-definition-loader';
export type { CommandDefinition, CommandExecutionContext } from '../loaders/command-definition-loader';