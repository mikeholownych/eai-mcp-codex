/**
 * ConfigurationManager - Core class for managing MCP configuration system
 * Handles detection, loading, and resolution of .mcp/ directories and configurations
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { EventEmitter } from 'events';
import { MarkdownParser } from '../utils/markdown-parser';
import {
  MCPConfiguration,
  AgentConfiguration,
  CommandConfiguration,
  ConfigurationHierarchy,
  ConfigurationSource,
  ConfigurationResolutionContext,
  ConfigurationValidationResult,
  ConfigurationLoadOptions,
  ConfigurationManagerOptions,
  ConfigurationCache,
  ConfigurationWatcher,
  ConfigurationMetrics,
  ConfigurationEvent,
  ConfigurationEventListener,
  ConfigurationError,
  ConfigurationValidationError,
  ConfigurationConflictError,
  MCPYamlFrontMatter,
} from '../types/configuration';

export class ConfigurationManager extends EventEmitter {
  private options: Required<ConfigurationManagerOptions>;
  private markdownParser: MarkdownParser;
  private cache: ConfigurationCache;
  private watcher: ConfigurationWatcher;
  private metrics: ConfigurationMetrics;
  private resolutionContext: ConfigurationResolutionContext;
  
  constructor(options: ConfigurationManagerOptions = {}) {
    super();
    
    this.options = {
      defaultConfigPath: options.defaultConfigPath || path.join(__dirname, '../../config/default'),
      configDirectoryName: options.configDirectoryName || '.mcp',
      commandsSubdirectory: options.commandsSubdirectory || 'commands',
      supportedFileExtensions: options.supportedFileExtensions || ['.md', '.markdown'],
      enableCaching: options.enableCaching ?? true,
      watchForChanges: options.watchForChanges ?? false,
      conflictResolution: options.conflictResolution || 'merge',
      validationLevel: options.validationLevel || 'basic',
      logLevel: options.logLevel || 'info',
    };
    
    this.markdownParser = new MarkdownParser({
      strictMode: this.options.validationLevel === 'strict',
      validateFrontMatter: this.options.validationLevel !== 'none',
      requireFrontMatter: true,
    });
    
    this.cache = {
      configurations: new Map(),
      lastUpdated: new Map(),
      checksums: new Map(),
      dependencyGraph: new Map(),
      resolutionCache: new Map(),
    };
    
    this.watcher = {
      isWatching: false,
      watchedPaths: [],
      callbacks: [],
      debounceMs: 500,
    };
    
    this.metrics = {
      loadTime: 0,
      cacheHitRate: 0,
      totalConfigurations: 0,
      resolutionConflicts: 0,
      validationErrors: 0,
      lastReloadTime: new Date(),
      memoryUsage: 0,
    };
    
    this.resolutionContext = this.createResolutionContext();
    
    // Initialize default configurations if they don't exist
    this.initializeDefaults().catch(error => {
      this.log('warn', `Failed to initialize default configurations: ${error.message}`);
    });
  }

  /**
   * Create resolution context for configuration hierarchy
   */
  private createResolutionContext(): ConfigurationResolutionContext {
    const workingDirectory = process.cwd();
    const homeDirectory = os.homedir();
    const defaultConfigPath = this.options.defaultConfigPath;
    
    return {
      workingDirectory,
      homeDirectory,
      defaultConfigPath,
      sources: [
        {
          type: 'default',
          path: defaultConfigPath,
          exists: fs.existsSync(defaultConfigPath),
          readable: this.isDirectoryReadable(defaultConfigPath),
        },
        {
          type: 'global',
          path: path.join(homeDirectory, this.options.configDirectoryName),
          exists: fs.existsSync(path.join(homeDirectory, this.options.configDirectoryName)),
          readable: this.isDirectoryReadable(path.join(homeDirectory, this.options.configDirectoryName)),
        },
        {
          type: 'project',
          path: path.join(workingDirectory, this.options.configDirectoryName),
          exists: fs.existsSync(path.join(workingDirectory, this.options.configDirectoryName)),
          readable: this.isDirectoryReadable(path.join(workingDirectory, this.options.configDirectoryName)),
        },
      ],
      resolutionOrder: ['default', 'global', 'project'],
      conflictResolution: this.options.conflictResolution,
    };
  }

  /**
   * Load all configurations with hierarchy resolution
   */
  async loadConfigurations(options: ConfigurationLoadOptions = {}): Promise<ConfigurationHierarchy> {
    const startTime = Date.now();
    
    try {
      const loadOptions = {
        includeDefault: options.includeDefault ?? true,
        includeGlobal: options.includeGlobal ?? true,
        includeProject: options.includeProject ?? true,
        validateOnLoad: options.validateOnLoad ?? true,
        watchForChanges: options.watchForChanges ?? this.options.watchForChanges,
        cacheDuration: options.cacheDuration ?? 300000, // 5 minutes
        strictMode: options.strictMode ?? false,
        verbose: options.verbose ?? false,
      };

      const hierarchy: ConfigurationHierarchy = {
        default: [],
        global: [],
        project: [],
        resolved: [],
      };

      // Load configurations from each source
      for (const source of this.resolutionContext.sources) {
        if (!this.shouldLoadSource(source.type, loadOptions)) {
          continue;
        }

        if (!source.exists || !source.readable) {
          if (loadOptions.verbose) {
            this.log('info', `Skipping ${source.type} source: ${source.path} (not accessible)`);
          }
          continue;
        }

        try {
          const configurations = await this.loadConfigurationsFromSource(source, loadOptions);
          hierarchy[source.type] = configurations;
          
          if (loadOptions.verbose) {
            this.log('info', `Loaded ${configurations.length} configurations from ${source.type} source`);
          }
        } catch (error) {
          this.log('error', `Failed to load configurations from ${source.type} source: ${error instanceof Error ? error.message : String(error)}`);
          
          if (loadOptions.strictMode) {
            throw error;
          }
        }
      }

      // Resolve configuration hierarchy
      hierarchy.resolved = this.resolveConfigurationHierarchy(hierarchy, loadOptions);

      // Validate resolved configurations
      if (loadOptions.validateOnLoad) {
        const validationResult = await this.validateConfigurations(hierarchy.resolved);
        if (!validationResult.isValid && loadOptions.strictMode) {
          throw new ConfigurationValidationError(
            'Configuration validation failed',
            validationResult.errors
              .filter(e => e.severity !== 'info')
              .map(e => ({
                rule: e.code || 'unknown',
                severity: e.severity as 'error' | 'warning',
                description: e.message,
              }))
          );
        }
      }

      // Setup file watching if requested
      if (loadOptions.watchForChanges) {
        this.setupWatcher();
      }

      // Update metrics
      this.updateMetrics(hierarchy.resolved, Date.now() - startTime);

      // Emit loaded event
      this.emit('loaded', {
        type: 'loaded',
        timestamp: new Date(),
        source: { type: 'project', path: 'multiple', exists: true, readable: true },
        metadata: { configurationsLoaded: hierarchy.resolved.length },
      } as ConfigurationEvent);

      return hierarchy;
    } catch (error) {
      const configError = error instanceof ConfigurationError ? error : new ConfigurationError(
        `Failed to load configurations: ${error instanceof Error ? error.message : String(error)}`,
        undefined,
        undefined,
        undefined,
        'LOAD_ERROR'
      );

      this.emit('error', {
        type: 'error',
        timestamp: new Date(),
        source: { type: 'project', path: 'multiple', exists: true, readable: true },
        error: configError,
      } as ConfigurationEvent);

      throw configError;
    }
  }

  /**
   * Load configurations from a specific source
   */
  private async loadConfigurationsFromSource(
    source: ConfigurationSource,
    options: ConfigurationLoadOptions
  ): Promise<MCPConfiguration[]> {
    const configurations: MCPConfiguration[] = [];
    
    try {
      // Load root level configurations
      const rootConfigs = await this.loadConfigurationsFromDirectory(
        source.path,
        source.type,
        false // Don't recurse for root level
      );
      configurations.push(...rootConfigs);

      // Load command configurations from commands subdirectory
      const commandsPath = path.join(source.path, this.options.commandsSubdirectory);
      if (fs.existsSync(commandsPath) && this.isDirectoryReadable(commandsPath)) {
        const commandConfigs = await this.loadConfigurationsFromDirectory(
          commandsPath,
          source.type,
          true // Recurse for commands
        );
        configurations.push(...commandConfigs);
      }

      return configurations;
    } catch (error) {
      throw new ConfigurationError(
        `Failed to load configurations from ${source.type} source: ${error instanceof Error ? error.message : String(error)}`,
        source.path,
        undefined,
        undefined,
        'SOURCE_LOAD_ERROR'
      );
    }
  }

  /**
   * Load configurations from a directory
   */
  private async loadConfigurationsFromDirectory(
    directoryPath: string,
    sourceType: 'default' | 'global' | 'project',
    recursive: boolean = false
  ): Promise<MCPConfiguration[]> {
    const configurations: MCPConfiguration[] = [];
    
    try {
      const entries = await fs.promises.readdir(directoryPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(directoryPath, entry.name);
        
        if (entry.isFile() && this.isSupportedFile(entry.name)) {
          try {
            const config = await this.loadSingleConfiguration(fullPath, sourceType);
            if (config) {
              configurations.push(config);
            }
          } catch (error) {
            this.log('warn', `Failed to load configuration file ${fullPath}: ${error instanceof Error ? error.message : String(error)}`);
          }
        } else if (entry.isDirectory() && recursive) {
          const subConfigs = await this.loadConfigurationsFromDirectory(fullPath, sourceType, recursive);
          configurations.push(...subConfigs);
        }
      }
    } catch (error) {
      throw new ConfigurationError(
        `Failed to read directory: ${error instanceof Error ? error.message : String(error)}`,
        directoryPath,
        undefined,
        undefined,
        'DIRECTORY_READ_ERROR'
      );
    }

    return configurations;
  }

  /**
   * Load a single configuration file
   */
  private async loadSingleConfiguration(
    filePath: string,
    sourceType: 'default' | 'global' | 'project'
  ): Promise<MCPConfiguration | null> {
    try {
      // Check cache first
      if (this.options.enableCaching) {
        const cached = this.getCachedConfiguration(filePath);
        if (cached) {
          return cached;
        }
      }

      const parsed = await this.markdownParser.parseFile(filePath);
      
      if (!parsed.hasValidFrontMatter || !parsed.frontMatter) {
        this.log('warn', `Configuration file has invalid or missing front matter: ${filePath}`);
        return null;
      }

      const config: MCPConfiguration = {
        frontMatter: parsed.frontMatter,
        content: parsed.content,
        filePath,
        source: sourceType,
        lastModified: parsed.fileStats.mtime,
        checksum: this.calculateChecksum(parsed.content + JSON.stringify(parsed.frontMatter)),
      };

      // Cache the configuration
      if (this.options.enableCaching) {
        this.cacheConfiguration(config);
      }

      return config;
    } catch (error) {
      throw new ConfigurationError(
        `Failed to load configuration: ${error instanceof Error ? error.message : String(error)}`,
        filePath,
        undefined,
        undefined,
        'CONFIG_LOAD_ERROR'
      );
    }
  }

  /**
   * Resolve configuration hierarchy with conflict resolution
   */
  private resolveConfigurationHierarchy(
    hierarchy: ConfigurationHierarchy,
    options: ConfigurationLoadOptions
  ): MCPConfiguration[] {
    const resolved: MCPConfiguration[] = [];
    const nameMap = new Map<string, MCPConfiguration[]>();
    
    // Group configurations by name across all sources
    for (const sourceType of this.resolutionContext.resolutionOrder) {
      for (const config of hierarchy[sourceType]) {
        const name = config.frontMatter.name;
        if (!nameMap.has(name)) {
          nameMap.set(name, []);
        }
        nameMap.get(name)!.push(config);
      }
    }

    // Resolve conflicts for each configuration name
    for (const [name, configs] of nameMap) {
      try {
        const resolvedConfig = this.resolveConfigurationConflict(configs, options);
        if (resolvedConfig) {
          resolved.push(resolvedConfig);
        }
      } catch (error) {
        this.log('error', `Failed to resolve configuration conflict for ${name}: ${error instanceof Error ? error.message : String(error)}`);
        
        if (options.strictMode) {
          throw error;
        }
      }
    }

    return resolved;
  }

  /**
   * Resolve conflicts between configurations with the same name
   */
  private resolveConfigurationConflict(
    configs: MCPConfiguration[],
    options: ConfigurationLoadOptions
  ): MCPConfiguration | null {
    if (configs.length === 1) {
      return configs[0];
    }

    // Sort by resolution order (project > global > default)
    const sortedConfigs = configs.sort((a, b) => {
      const orderA = this.resolutionContext.resolutionOrder.indexOf(a.source);
      const orderB = this.resolutionContext.resolutionOrder.indexOf(b.source);
      return orderB - orderA; // Reverse order for higher priority first
    });

    switch (this.options.conflictResolution) {
      case 'override':
        // Take the highest priority configuration
        return sortedConfigs[0];
        
      case 'merge':
        // Merge configurations with higher priority taking precedence
        return this.mergeConfigurations(sortedConfigs);
        
      case 'strict':
        // Throw error on conflicts
        throw new ConfigurationConflictError(
          `Configuration conflict detected for ${configs[0].frontMatter.name}`,
          [{
            name: configs[0].frontMatter.name,
            sources: configs.map(c => c.source),
            conflictType: 'name',
          }],
          configs[0].filePath
        );
        
      default:
        return sortedConfigs[0];
    }
  }

  /**
   * Merge multiple configurations with priority-based resolution
   */
  private mergeConfigurations(configs: MCPConfiguration[]): MCPConfiguration {
    if (configs.length === 0) {
      throw new Error('Cannot merge empty configuration array');
    }
    
    if (configs.length === 1) {
      return configs[0];
    }

    // Start with the lowest priority (base) config
    const baseConfig = configs[configs.length - 1];
    const result: MCPConfiguration = JSON.parse(JSON.stringify(baseConfig));

    // Apply higher priority configurations
    for (let i = configs.length - 2; i >= 0; i--) {
      const config = configs[i];
      
      // Merge front matter
      result.frontMatter = this.mergeFrontMatter(result.frontMatter, config.frontMatter);
      
      // Override content if not empty
      if (config.content.trim()) {
        result.content = config.content;
      }
      
      // Update metadata
      result.source = config.source; // Take the highest priority source
      result.filePath = config.filePath;
      result.lastModified = config.lastModified;
      result.checksum = config.checksum;
    }

    return result;
  }

  /**
   * Merge front matter objects with priority-based resolution
   */
  private mergeFrontMatter(
    base: MCPYamlFrontMatter,
    override: MCPYamlFrontMatter
  ): MCPYamlFrontMatter {
    const result: MCPYamlFrontMatter = { ...base };

    // Override scalar values
    const scalarFields = ['name', 'scope', 'version', 'priority', 'extends', 'agent_type', 
                         'command_type', 'output_format', 'restricted', 'security_level',
                         'multi_agent', 'collaboration_mode', 'escalation_threshold',
                         'environment', 'context_retention', 'max_context_size',
                         'auto_verify', 'author', 'created_at', 'updated_at', 
                         'description', 'documentation_url'];
    
    for (const field of scalarFields) {
      if (override[field as keyof MCPYamlFrontMatter] !== undefined) {
        (result as any)[field] = (override as any)[field];
      }
    }

    // Merge array values
    const arrayFields = ['tags', 'overrides', 'dependencies', 'capabilities', 
                        'model_preferences', 'required_context', 'required_permissions',
                        'validation_rules', 'quality_gates'];
    
    for (const field of arrayFields) {
      const baseArray = (base as any)[field] || [];
      const overrideArray = (override as any)[field] || [];
      
      if (overrideArray.length > 0) {
        // Merge arrays and remove duplicates
        (result as any)[field] = [...new Set([...baseArray, ...overrideArray])];
      }
    }

    return result;
  }

  /**
   * Validate configurations
   */
  async validateConfigurations(configs: MCPConfiguration[]): Promise<ConfigurationValidationResult> {
    const errors: ConfigurationValidationResult['errors'] = [];
    const warnings: ConfigurationValidationResult['warnings'] = [];
    const statistics = {
      totalConfigurations: configs.length,
      agentConfigurations: 0,
      commandConfigurations: 0,
      overrides: 0,
      conflicts: 0,
    };

    for (const config of configs) {
      try {
        // Basic validation
        this.validateSingleConfiguration(config);
        
        // Type-specific validation
        if (config.frontMatter.agent_type) {
          statistics.agentConfigurations++;
        }
        
        if (config.frontMatter.command_type) {
          statistics.commandConfigurations++;
        }
        
        if (config.frontMatter.overrides && config.frontMatter.overrides.length > 0) {
          statistics.overrides++;
        }
        
      } catch (error) {
        if (error instanceof ConfigurationError) {
          errors.push({
            file: config.filePath,
            line: error.line,
            column: error.column,
            severity: 'error',
            message: error.message,
            code: error.code,
          });
        } else {
          errors.push({
            file: config.filePath,
            severity: 'error',
            message: error instanceof Error ? error.message : String(error),
          });
        }
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      statistics,
    };
  }

  /**
   * Validate a single configuration
   */
  private validateSingleConfiguration(config: MCPConfiguration): void {
    const { frontMatter, content } = config;
    
    // Required fields
    if (!frontMatter.name) {
      throw new ConfigurationError('Configuration must have a name', config.filePath);
    }
    
    // Content validation
    if (!content || content.trim().length === 0) {
      throw new ConfigurationError('Configuration must have content', config.filePath);
    }
    
    // Dependency validation
    if (frontMatter.dependencies && frontMatter.dependencies.length > 0) {
      // Check for circular dependencies (simplified check)
      if (frontMatter.dependencies.includes(frontMatter.name)) {
        throw new ConfigurationError(
          `Configuration cannot depend on itself: ${frontMatter.name}`,
          config.filePath
        );
      }
    }
    
    // Override validation
    if (frontMatter.overrides && frontMatter.overrides.length > 0) {
      if (frontMatter.overrides.includes(frontMatter.name)) {
        throw new ConfigurationError(
          `Configuration cannot override itself: ${frontMatter.name}`,
          config.filePath
        );
      }
    }
  }

  /**
   * Get agent configurations
   */
  getAgentConfigurations(configs: MCPConfiguration[]): AgentConfiguration[] {
    return configs
      .filter(config => config.frontMatter.agent_type || this.isAgentConfiguration(config))
      .map(config => this.transformToAgentConfiguration(config));
  }

  /**
   * Get command configurations
   */
  getCommandConfigurations(configs: MCPConfiguration[]): CommandConfiguration[] {
    return configs
      .filter(config => config.frontMatter.command_type || this.isCommandConfiguration(config))
      .map(config => this.transformToCommandConfiguration(config));
  }

  /**
   * Helper methods
   */
  private shouldLoadSource(
    sourceType: 'default' | 'global' | 'project',
    options: ConfigurationLoadOptions
  ): boolean {
    switch (sourceType) {
      case 'default': return options.includeDefault!;
      case 'global': return options.includeGlobal!;
      case 'project': return options.includeProject!;
      default: return false;
    }
  }

  private isDirectoryReadable(dirPath: string): boolean {
    try {
      fs.accessSync(dirPath, fs.constants.R_OK);
      return true;
    } catch {
      return false;
    }
  }

  private isSupportedFile(filename: string): boolean {
    const ext = path.extname(filename).toLowerCase();
    return this.options.supportedFileExtensions.includes(ext);
  }

  private isAgentConfiguration(config: MCPConfiguration): boolean {
    // Check if configuration is in commands subdirectory
    const isInCommands = config.filePath.includes(this.options.commandsSubdirectory);
    return !isInCommands || !!config.frontMatter.agent_type;
  }

  private isCommandConfiguration(config: MCPConfiguration): boolean {
    // Check if configuration is in commands subdirectory
    const isInCommands = config.filePath.includes(this.options.commandsSubdirectory);
    return isInCommands || !!config.frontMatter.command_type;
  }

  private transformToAgentConfiguration(config: MCPConfiguration): AgentConfiguration {
    return {
      ...config,
      instructions: config.content,
      systemPrompt: this.extractSystemPrompt(config.content),
      examples: this.extractExamples(config.content),
      constraints: this.extractConstraints(config.content),
      behaviorModifiers: this.extractBehaviorModifiers(config.frontMatter),
    };
  }

  private transformToCommandConfiguration(config: MCPConfiguration): CommandConfiguration {
    return {
      ...config,
      instructions: config.content,
      parameters: this.extractParameters(config.content),
      preExecutionChecks: this.extractPreExecutionChecks(config.content),
      postExecutionActions: this.extractPostExecutionActions(config.content),
      errorHandling: this.extractErrorHandling(config.frontMatter),
    };
  }

  private extractSystemPrompt(content: string): string | undefined {
    const match = content.match(/## System Prompt\s*\n([\s\S]*?)(?=\n##|\n---|\n```|$)/i);
    return match ? match[1].trim() : undefined;
  }

  private extractExamples(content: string): Array<{ input: string; output: string; explanation?: string }> {
    const examples: Array<{ input: string; output: string; explanation?: string }> = [];
    const exampleRegex = /## Examples?\s*\n([\s\S]*?)(?=\n##|\n---|\n```|$)/i;
    const match = content.match(exampleRegex);
    
    if (match) {
      const exampleContent = match[1];
      // Simple parsing - could be enhanced
      const inputOutputRegex = /Input:\s*(.*?)\s*Output:\s*(.*?)(?=Input:|$)/gs;
      let exampleMatch;
      
      while ((exampleMatch = inputOutputRegex.exec(exampleContent)) !== null) {
        examples.push({
          input: exampleMatch[1].trim(),
          output: exampleMatch[2].trim(),
        });
      }
    }
    
    return examples;
  }

  private extractConstraints(content: string): string[] {
    const constraints: string[] = [];
    const constraintsRegex = /## Constraints?\s*\n([\s\S]*?)(?=\n##|\n---|\n```|$)/i;
    const match = content.match(constraintsRegex);
    
    if (match) {
      const constraintContent = match[1];
      const lines = constraintContent.split('\n')
        .map(line => line.trim())
        .filter(line => line.startsWith('-') || line.startsWith('*'))
        .map(line => line.substring(1).trim());
      
      constraints.push(...lines);
    }
    
    return constraints;
  }

  private extractBehaviorModifiers(frontMatter: MCPYamlFrontMatter): any {
    return {
      temperature: (frontMatter as any).temperature,
      max_tokens: (frontMatter as any).max_tokens,
      top_p: (frontMatter as any).top_p,
      presence_penalty: (frontMatter as any).presence_penalty,
      frequency_penalty: (frontMatter as any).frequency_penalty,
    };
  }

  private extractParameters(content: string): any {
    // Extract parameter definitions from content
    const params: any = {};
    const paramRegex = /## Parameters?\s*\n([\s\S]*?)(?=\n##|\n---|\n```|$)/i;
    const match = content.match(paramRegex);
    
    if (match) {
      // Simple parsing - could be enhanced with more sophisticated parsing
      const paramContent = match[1];
      const lines = paramContent.split('\n').filter(line => line.trim());
      
      for (const line of lines) {
        if (line.includes(':')) {
          const [name, description] = line.split(':').map(s => s.trim());
          params[name.replace(/^-\s*/, '')] = {
            type: 'string',
            required: !line.includes('(optional)'),
            description: description,
          };
        }
      }
    }
    
    return params;
  }

  private extractPreExecutionChecks(content: string): string[] {
    return this.extractListSection(content, 'Pre-execution Checks?');
  }

  private extractPostExecutionActions(content: string): string[] {
    return this.extractListSection(content, 'Post-execution Actions?');
  }

  private extractListSection(content: string, sectionName: string): string[] {
    const items: string[] = [];
    const regex = new RegExp(`## ${sectionName}\\s*\\n([\\s\\S]*?)(?=\\n##|\\n---|\\n\`\`\`|$)`, 'i');
    const match = content.match(regex);
    
    if (match) {
      const sectionContent = match[1];
      const lines = sectionContent.split('\n')
        .map(line => line.trim())
        .filter(line => line.startsWith('-') || line.startsWith('*'))
        .map(line => line.substring(1).trim());
      
      items.push(...lines);
    }
    
    return items;
  }

  private extractErrorHandling(frontMatter: MCPYamlFrontMatter): any {
    return {
      retryCount: (frontMatter as any).retry_count || 3,
      fallbackStrategy: (frontMatter as any).fallback_strategy || 'escalate',
      escalationRules: (frontMatter as any).escalation_rules || [],
    };
  }

  private getCachedConfiguration(filePath: string): MCPConfiguration | null {
    if (!this.cache.configurations.has(filePath)) {
      return null;
    }
    
    const cached = this.cache.configurations.get(filePath)!;
    const lastUpdated = this.cache.lastUpdated.get(filePath);
    
    if (!lastUpdated) {
      return null;
    }
    
    // Check if file has been modified
    try {
      const stats = fs.statSync(filePath);
      if (stats.mtime > lastUpdated) {
        // File modified, invalidate cache
        this.cache.configurations.delete(filePath);
        this.cache.lastUpdated.delete(filePath);
        this.cache.checksums.delete(filePath);
        return null;
      }
    } catch {
      // File might not exist anymore
      this.cache.configurations.delete(filePath);
      this.cache.lastUpdated.delete(filePath);
      this.cache.checksums.delete(filePath);
      return null;
    }
    
    return cached;
  }

  private cacheConfiguration(config: MCPConfiguration): void {
    this.cache.configurations.set(config.filePath, config);
    this.cache.lastUpdated.set(config.filePath, new Date());
    if (config.checksum) {
      this.cache.checksums.set(config.filePath, config.checksum);
    }
  }

  private calculateChecksum(content: string): string {
    // Simple checksum calculation - could use crypto for better hashing
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(16);
  }

  private setupWatcher(): void {
    if (this.watcher.isWatching) {
      return;
    }
    
    this.watcher.isWatching = true;
    
    // Watch all configuration sources
    for (const source of this.resolutionContext.sources) {
      if (source.exists && source.readable) {
        this.watcher.watchedPaths.push(source.path);
        // Implementation would use fs.watch or a file watcher library
        // For now, this is a placeholder
      }
    }
  }

  private updateMetrics(configs: MCPConfiguration[], loadTime: number): void {
    this.metrics.loadTime = loadTime;
    this.metrics.totalConfigurations = configs.length;
    this.metrics.lastReloadTime = new Date();
    this.metrics.memoryUsage = process.memoryUsage().heapUsed;
  }

  private log(level: 'debug' | 'info' | 'warn' | 'error', message: string): void {
    const levels = ['debug', 'info', 'warn', 'error'];
    const currentLevelIndex = levels.indexOf(this.options.logLevel);
    const messageLevel = levels.indexOf(level);
    
    if (messageLevel >= currentLevelIndex) {
      console[level === 'debug' ? 'log' : level](`[ConfigurationManager] ${message}`);
    }
  }

  /**
   * Initialize default configurations if they don't exist
   */
  private async initializeDefaults(): Promise<void> {
    const defaultPath = this.options.defaultConfigPath;
    
    if (!fs.existsSync(defaultPath)) {
      await fs.promises.mkdir(defaultPath, { recursive: true });
      
      // Create default agent configuration
      const defaultAgentConfig = MarkdownParser.createMarkdownFile(
        {
          name: 'default-agent',
          scope: 'default',
          tags: ['default', 'agent'],
          version: '1.0.0',
          agent_type: 'developer',
          capabilities: ['code-generation', 'refactoring', 'analysis'],
          description: 'Default agent configuration',
        },
        '# Default Agent\n\nThis is the default agent configuration.\n\n## Instructions\n\nProvide helpful coding assistance while following best practices.\n\n## Constraints\n\n- Always validate input\n- Follow security best practices\n- Write clean, maintainable code'
      );
      
      await fs.promises.writeFile(
        path.join(defaultPath, 'default-agent.md'),
        defaultAgentConfig
      );
      
      // Create commands directory and default command
      const commandsPath = path.join(defaultPath, this.options.commandsSubdirectory);
      await fs.promises.mkdir(commandsPath, { recursive: true });
      
      const defaultCommandConfig = MarkdownParser.createMarkdownFile(
        {
          name: 'generate',
          scope: 'default',
          tags: ['default', 'command', 'generation'],
          version: '1.0.0',
          command_type: 'generation',
          output_format: 'code',
          description: 'Default code generation command',
        },
        '# Generate Command\n\nGenerate code based on user requirements.\n\n## Parameters\n\n- prompt: Description of what to generate (required)\n- filePath: Target file path (required)\n- language: Programming language (optional)\n\n## Instructions\n\nGenerate clean, well-documented code that follows best practices for the target language.'
      );
      
      await fs.promises.writeFile(
        path.join(commandsPath, 'generate.md'),
        defaultCommandConfig
      );
    }
  }

  /**
   * Public API methods
   */
  
  async reload(): Promise<ConfigurationHierarchy> {
    this.cache.configurations.clear();
    this.cache.lastUpdated.clear();
    this.cache.checksums.clear();
    this.cache.resolutionCache.clear();
    
    return this.loadConfigurations();
  }

  getMetrics(): ConfigurationMetrics {
    return { ...this.metrics };
  }

  async doctor(): Promise<ConfigurationValidationResult> {
    const hierarchy = await this.loadConfigurations({ validateOnLoad: false });
    return this.validateConfigurations(hierarchy.resolved);
  }

  addEventListener(listener: ConfigurationEventListener): void {
    this.on('loaded', listener);
    this.on('error', listener);
    this.on('reloaded', listener);
  }

  removeEventListener(listener: ConfigurationEventListener): void {
    this.off('loaded', listener);
    this.off('error', listener);
    this.off('reloaded', listener);
  }
}