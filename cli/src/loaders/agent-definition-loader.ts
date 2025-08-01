/**
 * AgentDefinitionLoader - Specialized loader for agent configurations and instructions
 * Handles loading and processing of agent-specific Markdown files
 */

import { ConfigurationManager } from '../config/configuration-manager';
import { MarkdownParser } from '../utils/markdown-parser';
import {
  AgentConfiguration,
  ConfigurationLoadOptions,
  ConfigurationError,
  MCPYamlFrontMatter,
} from '../types/configuration';

export interface AgentLoadOptions extends ConfigurationLoadOptions {
  filterByType?: ('planner' | 'developer' | 'security' | 'domain-expert' | 'custom')[];
  filterByCapabilities?: string[];
  includeSystemPrompts?: boolean;
  includeBehaviorModifiers?: boolean;
  includeExamples?: boolean;
  sortBy?: 'name' | 'priority' | 'lastModified' | 'type';
  sortOrder?: 'asc' | 'desc';
}

export interface AgentDefinition extends AgentConfiguration {
  type: 'planner' | 'developer' | 'security' | 'domain-expert' | 'custom';
  capabilities: string[];
  modelPreferences: string[];
  collaborationSettings: {
    multiAgent: boolean;
    collaborationMode: 'sequential' | 'parallel' | 'consensus';
    escalationThreshold: number;
  };
  securitySettings: {
    restricted: boolean;
    requiredPermissions: string[];
    securityLevel: 'low' | 'medium' | 'high' | 'critical';
  };
  executionSettings: {
    contextRetention: boolean;
    maxContextSize: number;
    autoVerify: boolean;
    validationRules: string[];
    qualityGates: string[];
  };
  metadata: {
    author?: string;
    version: string;
    description?: string;
    documentationUrl?: string;
    createdAt?: Date;
    updatedAt?: Date;
  };
}

export interface AgentExecutionContext {
  agent: AgentDefinition;
  parentTask?: string;
  collaborators?: AgentDefinition[];
  contextData?: Record<string, any>;
  executionEnvironment: 'development' | 'staging' | 'production';
  securityContext?: {
    permissions: string[];
    securityLevel: string;
    restrictedMode: boolean;
  };
  performanceSettings?: {
    temperature: number;
    maxTokens: number;
    timeout: number;
  };
}

export class AgentDefinitionLoader {
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
   * Load all agent definitions from configuration hierarchy
   */
  async loadAgentDefinitions(options: AgentLoadOptions = {}): Promise<AgentDefinition[]> {
    try {
      const hierarchy = await this.configManager.loadConfigurations({
        includeDefault: options.includeDefault ?? true,
        includeGlobal: options.includeGlobal ?? true,
        includeProject: options.includeProject ?? true,
        validateOnLoad: options.validateOnLoad ?? true,
        verbose: options.verbose ?? false,
      });

      const agentConfigs = this.configManager.getAgentConfigurations(hierarchy.resolved);
      let agentDefinitions = agentConfigs.map(config => this.transformToAgentDefinition(config));

      // Apply filters
      agentDefinitions = this.applyFilters(agentDefinitions, options);

      // Sort results
      agentDefinitions = this.sortAgentDefinitions(agentDefinitions, options);

      return agentDefinitions;
    } catch (error) {
      throw new ConfigurationError(
        `Failed to load agent definitions: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        undefined,
        undefined,
        'AGENT_LOAD_ERROR'
      );
    }
  }

  /**
   * Load a specific agent definition by name
   */
  async loadAgentDefinition(
    name: string, 
    options: AgentLoadOptions = {}
  ): Promise<AgentDefinition | null> {
    const agents = await this.loadAgentDefinitions(options);
    return agents.find(agent => agent.frontMatter.name === name) || null;
  }

  /**
   * Load agent definitions by type
   */
  async loadAgentDefinitionsByType(
    type: 'planner' | 'developer' | 'security' | 'domain-expert' | 'custom',
    options: AgentLoadOptions = {}
  ): Promise<AgentDefinition[]> {
    return this.loadAgentDefinitions({
      ...options,
      filterByType: [type],
    });
  }

  /**
   * Load agent definitions by capabilities
   */
  async loadAgentDefinitionsByCapabilities(
    capabilities: string[],
    options: AgentLoadOptions = {}
  ): Promise<AgentDefinition[]> {
    return this.loadAgentDefinitions({
      ...options,
      filterByCapabilities: capabilities,
    });
  }

  /**
   * Create an execution context for an agent
   */
  createExecutionContext(
    agent: AgentDefinition,
    options: {
      parentTask?: string;
      collaborators?: AgentDefinition[];
      contextData?: Record<string, any>;
      executionEnvironment?: 'development' | 'staging' | 'production';
      overrideSettings?: Partial<AgentExecutionContext>;
    } = {}
  ): AgentExecutionContext {
    const context: AgentExecutionContext = {
      agent,
      parentTask: options.parentTask,
      collaborators: options.collaborators || [],
      contextData: options.contextData || {},
      executionEnvironment: options.executionEnvironment || 'development',
      securityContext: {
        permissions: agent.securitySettings.requiredPermissions,
        securityLevel: agent.securitySettings.securityLevel,
        restrictedMode: agent.securitySettings.restricted,
      },
      performanceSettings: {
        temperature: agent.behaviorModifiers?.temperature || 0.7,
        maxTokens: agent.behaviorModifiers?.max_tokens || 2048,
        timeout: 30000, // 30 seconds default
      },
    };

    // Apply any override settings
    if (options.overrideSettings) {
      Object.assign(context, options.overrideSettings);
    }

    return context;
  }

  /**
   * Validate agent definition compatibility for collaboration
   */
  validateCollaborationCompatibility(agents: AgentDefinition[]): {
    compatible: boolean;
    issues: Array<{
      type: 'security' | 'capability' | 'environment' | 'performance';
      message: string;
      agents: string[];
    }>;
  } {
    const issues: Array<{
      type: 'security' | 'capability' | 'environment' | 'performance';
      message: string;
      agents: string[];
    }> = [];

    // Check security compatibility
    const securityLevels = agents.map(a => a.securitySettings.securityLevel);
    const uniqueSecurityLevels = [...new Set(securityLevels)];
    
    if (uniqueSecurityLevels.length > 1) {
      const criticalAgents = agents.filter(a => a.securitySettings.securityLevel === 'critical');
      if (criticalAgents.length > 0) {
        issues.push({
          type: 'security',
          message: 'Critical security level agents cannot collaborate with lower security level agents',
          agents: criticalAgents.map(a => a.frontMatter.name),
        });
      }
    }

    // Check environment compatibility
    const environments = agents.map(a => a.frontMatter.environment || 'all');
    const hasConflictingEnvironments = environments.some((env, index) => {
      return environments.some((otherEnv, otherIndex) => {
        return index !== otherIndex && env !== 'all' && otherEnv !== 'all' && env !== otherEnv;
      });
    });

    if (hasConflictingEnvironments) {
      issues.push({
        type: 'environment',
        message: 'Agents have conflicting environment requirements',
        agents: agents.map(a => a.frontMatter.name),
      });
    }

    // Check capability overlap for meaningful collaboration
    const allCapabilities = agents.flatMap(a => a.capabilities);
    const uniqueCapabilities = [...new Set(allCapabilities)];
    
    if (uniqueCapabilities.length === allCapabilities.length) {
      issues.push({
        type: 'capability',
        message: 'No overlapping capabilities found - collaboration may be ineffective',
        agents: agents.map(a => a.frontMatter.name),
      });
    }

    return {
      compatible: issues.length === 0,
      issues,
    };
  }

  /**
   * Transform configuration to agent definition
   */
  private transformToAgentDefinition(config: AgentConfiguration): AgentDefinition {
    const frontMatter = config.frontMatter;
    
    return {
      ...config,
      type: frontMatter.agent_type || 'custom',
      capabilities: frontMatter.capabilities || [],
      modelPreferences: frontMatter.model_preferences || [],
      collaborationSettings: {
        multiAgent: frontMatter.multi_agent || false,
        collaborationMode: frontMatter.collaboration_mode || 'sequential',
        escalationThreshold: frontMatter.escalation_threshold || 0.7,
      },
      securitySettings: {
        restricted: frontMatter.restricted || false,
        requiredPermissions: frontMatter.required_permissions || [],
        securityLevel: frontMatter.security_level || 'medium',
      },
      executionSettings: {
        contextRetention: frontMatter.context_retention || false,
        maxContextSize: frontMatter.max_context_size || 4096,
        autoVerify: frontMatter.auto_verify || false,
        validationRules: frontMatter.validation_rules || [],
        qualityGates: frontMatter.quality_gates || [],
      },
      metadata: {
        author: frontMatter.author,
        version: frontMatter.version || '1.0.0',
        description: frontMatter.description,
        documentationUrl: frontMatter.documentation_url,
        createdAt: frontMatter.created_at ? new Date(frontMatter.created_at) : undefined,
        updatedAt: frontMatter.updated_at ? new Date(frontMatter.updated_at) : undefined,
      },
    };
  }

  /**
   * Apply filters to agent definitions
   */
  private applyFilters(agents: AgentDefinition[], options: AgentLoadOptions): AgentDefinition[] {
    let filtered = agents;

    // Filter by type
    if (options.filterByType && options.filterByType.length > 0) {
      filtered = filtered.filter(agent => options.filterByType!.includes(agent.type));
    }

    // Filter by capabilities
    if (options.filterByCapabilities && options.filterByCapabilities.length > 0) {
      filtered = filtered.filter(agent => 
        options.filterByCapabilities!.some(capability => 
          agent.capabilities.includes(capability)
        )
      );
    }

    return filtered;
  }

  /**
   * Sort agent definitions
   */
  private sortAgentDefinitions(agents: AgentDefinition[], options: AgentLoadOptions): AgentDefinition[] {
    if (!options.sortBy) {
      return agents;
    }

    const sortOrder = options.sortOrder || 'asc';
    const multiplier = sortOrder === 'asc' ? 1 : -1;

    return agents.sort((a, b) => {
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
   * Generate agent definition template
   */
  static generateAgentTemplate(
    name: string,
    type: 'planner' | 'developer' | 'security' | 'domain-expert' | 'custom',
    options: {
      capabilities?: string[];
      description?: string;
      author?: string;
      securityLevel?: 'low' | 'medium' | 'high' | 'critical';
    } = {}
  ): string {
    const frontMatter: MCPYamlFrontMatter = {
      name,
      scope: 'project',
      tags: [type, 'agent'],
      version: '1.0.0',
      agent_type: type,
      capabilities: options.capabilities || [],
      security_level: options.securityLevel || 'medium',
      multi_agent: true,
      collaboration_mode: 'sequential',
      escalation_threshold: 0.7,
      environment: 'all',
      context_retention: false,
      max_context_size: 4096,
      auto_verify: false,
      author: options.author,
      description: options.description,
      created_at: new Date().toISOString(),
    };

    const content = `# ${name.charAt(0).toUpperCase() + name.slice(1)} Agent

${options.description || `AI agent specialized in ${type} tasks.`}

## Instructions

Provide clear, detailed instructions for this agent's behavior and responsibilities.

## System Prompt

Define the system prompt that will be used to initialize this agent.

## Examples

### Example 1
Input: Example user request
Output: Example agent response
Explanation: Why this response is appropriate

## Constraints

- Follow security best practices
- Validate all inputs
- Provide clear, actionable feedback
- Escalate when uncertain

## Capabilities

${(options.capabilities || []).map(cap => `- ${cap}`).join('\n')}

## Collaboration Guidelines

- Work effectively with other agents
- Share relevant context and findings
- Request assistance when needed
- Contribute to consensus building
`;

    return MarkdownParser.createMarkdownFile(frontMatter, content);
  }

  /**
   * Validate agent definition
   */
  validateAgentDefinition(agent: AgentDefinition): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Required fields
    if (!agent.frontMatter.name) {
      errors.push('Agent must have a name');
    }

    if (!agent.content || agent.content.trim().length === 0) {
      errors.push('Agent must have content/instructions');
    }

    if (!agent.type) {
      errors.push('Agent must have a type');
    }

    // Validate capabilities
    if (agent.capabilities.length === 0) {
      warnings.push('Agent has no defined capabilities');
    }

    // Validate security settings
    if (agent.securitySettings.restricted && agent.securitySettings.requiredPermissions.length === 0) {
      warnings.push('Restricted agent should define required permissions');
    }

    // Validate collaboration settings
    if (agent.collaborationSettings.multiAgent && agent.collaborationSettings.escalationThreshold < 0.1) {
      warnings.push('Multi-agent mode with very low escalation threshold may cause issues');
    }

    // Validate execution settings
    if (agent.executionSettings.maxContextSize < 1024) {
      warnings.push('Very small context size may limit agent effectiveness');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Get agent statistics
   */
  async getAgentStatistics(): Promise<{
    total: number;
    byType: Record<string, number>;
    bySecurityLevel: Record<string, number>;
    bySource: Record<string, number>;
    averageCapabilities: number;
    mostCommonCapabilities: Array<{ capability: string; count: number }>;
  }> {
    const agents = await this.loadAgentDefinitions();
    
    const stats = {
      total: agents.length,
      byType: {} as Record<string, number>,
      bySecurityLevel: {} as Record<string, number>,
      bySource: {} as Record<string, number>,
      averageCapabilities: 0,
      mostCommonCapabilities: [] as Array<{ capability: string; count: number }>,
    };

    // Count by type
    agents.forEach(agent => {
      stats.byType[agent.type] = (stats.byType[agent.type] || 0) + 1;
      stats.bySecurityLevel[agent.securitySettings.securityLevel] = 
        (stats.bySecurityLevel[agent.securitySettings.securityLevel] || 0) + 1;
      stats.bySource[agent.source] = (stats.bySource[agent.source] || 0) + 1;
    });

    // Calculate average capabilities
    const totalCapabilities = agents.reduce((sum, agent) => sum + agent.capabilities.length, 0);
    stats.averageCapabilities = agents.length > 0 ? totalCapabilities / agents.length : 0;

    // Find most common capabilities
    const capabilityCount = new Map<string, number>();
    agents.forEach(agent => {
      agent.capabilities.forEach(capability => {
        capabilityCount.set(capability, (capabilityCount.get(capability) || 0) + 1);
      });
    });

    stats.mostCommonCapabilities = Array.from(capabilityCount.entries())
      .map(([capability, count]) => ({ capability, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    return stats;
  }
}