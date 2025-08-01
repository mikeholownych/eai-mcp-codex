/**
 * MarkdownParser - Utility for parsing Markdown files with YAML front matter
 * Supports the MCP configuration system's requirements for agent and command definitions
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import { MCPYamlFrontMatter, ConfigurationError } from '../types/configuration';

export interface ParsedMarkdown {
  frontMatter: MCPYamlFrontMatter | null;
  content: string;
  rawFrontMatter: string;
  hasValidFrontMatter: boolean;
  filePath: string;
  fileStats: fs.Stats;
}

export interface MarkdownParseOptions {
  strictMode?: boolean;
  validateFrontMatter?: boolean;
  preserveWhitespace?: boolean;
  encoding?: BufferEncoding;
  maxFileSize?: number;
  requireFrontMatter?: boolean;
}

export class MarkdownParser {
  private options: Required<MarkdownParseOptions>;
  
  constructor(options: MarkdownParseOptions = {}) {
    this.options = {
      strictMode: options.strictMode ?? false,
      validateFrontMatter: options.validateFrontMatter ?? true,
      preserveWhitespace: options.preserveWhitespace ?? false,
      encoding: options.encoding ?? 'utf8',
      maxFileSize: options.maxFileSize ?? 10 * 1024 * 1024, // 10MB
      requireFrontMatter: options.requireFrontMatter ?? false,
    };
  }

  /**
   * Parse a markdown file from disk
   */
  async parseFile(filePath: string): Promise<ParsedMarkdown> {
    try {
      // Check if file exists and is readable
      const absolutePath = path.resolve(filePath);
      const fileStats = await fs.promises.stat(absolutePath);
      
      if (!fileStats.isFile()) {
        throw new ConfigurationError(
          `Path is not a file: ${absolutePath}`,
          absolutePath,
          undefined,
          undefined,
          'NOT_A_FILE'
        );
      }

      if (fileStats.size > this.options.maxFileSize) {
        throw new ConfigurationError(
          `File too large: ${fileStats.size} bytes (max: ${this.options.maxFileSize})`,
          absolutePath,
          undefined,
          undefined,
          'FILE_TOO_LARGE'
        );
      }

      // Read file content
      const content = await fs.promises.readFile(absolutePath, this.options.encoding);
      
      return this.parseContent(content, absolutePath, fileStats);
    } catch (error) {
      if (error instanceof ConfigurationError) {
        throw error;
      }
      
      throw new ConfigurationError(
        `Failed to read file: ${error instanceof Error ? error.message : String(error)}`,
        filePath,
        undefined,
        undefined,
        'FILE_READ_ERROR'
      );
    }
  }

  /**
   * Parse markdown content directly
   */
  parseContent(content: string, filePath?: string, fileStats?: fs.Stats): ParsedMarkdown {
    try {
      const result = this.extractFrontMatter(content);
      
      let frontMatter: MCPYamlFrontMatter | null = null;
      let hasValidFrontMatter = false;

      if (result.frontMatter) {
        try {
          const parsed = yaml.parse(result.frontMatter);
          
          if (this.options.validateFrontMatter) {
            frontMatter = this.validateAndTransformFrontMatter(parsed, filePath);
            hasValidFrontMatter = true;
          } else {
            frontMatter = parsed as MCPYamlFrontMatter;
            hasValidFrontMatter = true;
          }
        } catch (yamlError) {
          if (this.options.strictMode || this.options.requireFrontMatter) {
            throw new ConfigurationError(
              `Invalid YAML front matter: ${yamlError instanceof Error ? yamlError.message : String(yamlError)}`,
              filePath,
              undefined,
              undefined,
              'INVALID_YAML'
            );
          }
          // In non-strict mode, continue with null front matter
          hasValidFrontMatter = false;
        }
      } else if (this.options.requireFrontMatter) {
        throw new ConfigurationError(
          'YAML front matter is required but not found',
          filePath,
          undefined,
          undefined,
          'MISSING_FRONT_MATTER'
        );
      }

      const processedContent = this.options.preserveWhitespace 
        ? result.content 
        : result.content.trim();

      return {
        frontMatter,
        content: processedContent,
        rawFrontMatter: result.frontMatter || '',
        hasValidFrontMatter,
        filePath: filePath || '<unknown>',
        fileStats: fileStats || ({} as fs.Stats),
      };
    } catch (error) {
      if (error instanceof ConfigurationError) {
        throw error;
      }
      
      throw new ConfigurationError(
        `Failed to parse markdown content: ${error instanceof Error ? error.message : String(error)}`,
        filePath,
        undefined,
        undefined,
        'PARSE_ERROR'
      );
    }
  }

  /**
   * Extract YAML front matter from markdown content
   */
  private extractFrontMatter(content: string): { frontMatter: string | null; content: string } {
    const frontMatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;
    const match = content.match(frontMatterRegex);
    
    if (match) {
      return {
        frontMatter: match[1],
        content: match[2],
      };
    }
    
    return {
      frontMatter: null,
      content: content,
    };
  }

  /**
   * Validate and transform front matter to ensure it conforms to MCPYamlFrontMatter
   */
  private validateAndTransformFrontMatter(
    parsed: any, 
    filePath?: string
  ): MCPYamlFrontMatter {
    const errors: string[] = [];
    
    // Required fields validation
    if (!parsed.name || typeof parsed.name !== 'string') {
      errors.push('Front matter must include a "name" field of type string');
    }
    
    // Optional field type validation
    if (parsed.scope && !['global', 'project', 'default'].includes(parsed.scope)) {
      errors.push('Front matter "scope" must be one of: global, project, default');
    }
    
    if (parsed.tags && !Array.isArray(parsed.tags)) {
      errors.push('Front matter "tags" must be an array');
    }
    
    if (parsed.version && typeof parsed.version !== 'string') {
      errors.push('Front matter "version" must be a string');
    }
    
    if (parsed.priority && (typeof parsed.priority !== 'number' || parsed.priority < 0)) {
      errors.push('Front matter "priority" must be a non-negative number');
    }

    // Agent-specific validation
    if (parsed.agent_type && !['planner', 'developer', 'security', 'domain-expert', 'custom'].includes(parsed.agent_type)) {
      errors.push('Front matter "agent_type" must be one of: planner, developer, security, domain-expert, custom');
    }
    
    if (parsed.capabilities && !Array.isArray(parsed.capabilities)) {
      errors.push('Front matter "capabilities" must be an array');
    }
    
    if (parsed.model_preferences && !Array.isArray(parsed.model_preferences)) {
      errors.push('Front matter "model_preferences" must be an array');
    }

    // Command-specific validation
    if (parsed.command_type && !['generation', 'analysis', 'refactoring', 'testing', 'deployment'].includes(parsed.command_type)) {
      errors.push('Front matter "command_type" must be one of: generation, analysis, refactoring, testing, deployment');
    }
    
    if (parsed.required_context && !Array.isArray(parsed.required_context)) {
      errors.push('Front matter "required_context" must be an array');
    }
    
    if (parsed.output_format && !['json', 'markdown', 'plain', 'code'].includes(parsed.output_format)) {
      errors.push('Front matter "output_format" must be one of: json, markdown, plain, code');
    }

    // Security validation
    if (parsed.restricted && typeof parsed.restricted !== 'boolean') {
      errors.push('Front matter "restricted" must be a boolean');
    }
    
    if (parsed.required_permissions && !Array.isArray(parsed.required_permissions)) {
      errors.push('Front matter "required_permissions" must be an array');
    }
    
    if (parsed.security_level && !['low', 'medium', 'high', 'critical'].includes(parsed.security_level)) {
      errors.push('Front matter "security_level" must be one of: low, medium, high, critical');
    }

    // Collaboration validation
    if (parsed.multi_agent && typeof parsed.multi_agent !== 'boolean') {
      errors.push('Front matter "multi_agent" must be a boolean');
    }
    
    if (parsed.collaboration_mode && !['sequential', 'parallel', 'consensus'].includes(parsed.collaboration_mode)) {
      errors.push('Front matter "collaboration_mode" must be one of: sequential, parallel, consensus');
    }
    
    if (parsed.escalation_threshold && (typeof parsed.escalation_threshold !== 'number' || parsed.escalation_threshold < 0 || parsed.escalation_threshold > 1)) {
      errors.push('Front matter "escalation_threshold" must be a number between 0 and 1');
    }

    // Environment validation
    if (parsed.environment && !['development', 'staging', 'production', 'all'].includes(parsed.environment)) {
      errors.push('Front matter "environment" must be one of: development, staging, production, all');
    }

    // Array field validation
    const arrayFields = ['extends', 'overrides', 'dependencies', 'validation_rules', 'quality_gates'];
    arrayFields.forEach(field => {
      if (parsed[field] && !Array.isArray(parsed[field])) {
        errors.push(`Front matter "${field}" must be an array`);
      }
    });

    // Date validation
    if (parsed.created_at && !this.isValidISODate(parsed.created_at)) {
      errors.push('Front matter "created_at" must be a valid ISO date string');
    }
    
    if (parsed.updated_at && !this.isValidISODate(parsed.updated_at)) {
      errors.push('Front matter "updated_at" must be a valid ISO date string');
    }

    // Throw errors if validation fails in strict mode
    if (errors.length > 0 && this.options.strictMode) {
      throw new ConfigurationError(
        `Front matter validation failed:\n${errors.map(e => `  - ${e}`).join('\n')}`,
        filePath,
        undefined,
        undefined,
        'FRONT_MATTER_VALIDATION_ERROR'
      );
    }

    // Return validated and transformed front matter
    return {
      name: parsed.name,
      scope: parsed.scope || 'project',
      tags: parsed.tags || [],
      version: parsed.version || '1.0.0',
      priority: parsed.priority || 0,
      extends: parsed.extends,
      overrides: parsed.overrides || [],
      dependencies: parsed.dependencies || [],
      
      // Agent-specific
      agent_type: parsed.agent_type,
      capabilities: parsed.capabilities || [],
      model_preferences: parsed.model_preferences || [],
      
      // Command-specific
      command_type: parsed.command_type,
      required_context: parsed.required_context || [],
      output_format: parsed.output_format || 'markdown',
      
      // Security
      restricted: parsed.restricted || false,
      required_permissions: parsed.required_permissions || [],
      security_level: parsed.security_level || 'medium',
      
      // Collaboration
      multi_agent: parsed.multi_agent || false,
      collaboration_mode: parsed.collaboration_mode || 'sequential',
      escalation_threshold: parsed.escalation_threshold || 0.7,
      
      // Environment
      environment: parsed.environment || 'all',
      context_retention: parsed.context_retention || false,
      max_context_size: parsed.max_context_size || 4096,
      
      // Validation
      validation_rules: parsed.validation_rules || [],
      quality_gates: parsed.quality_gates || [],
      auto_verify: parsed.auto_verify || false,
      
      // Metadata
      author: parsed.author,
      created_at: parsed.created_at,
      updated_at: parsed.updated_at,
      description: parsed.description,
      documentation_url: parsed.documentation_url,
    };
  }

  /**
   * Validate if a string is a valid ISO date
   */
  private isValidISODate(dateString: string): boolean {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date.getTime()) && date.toISOString() === dateString;
  }

  /**
   * Generate YAML front matter from MCPYamlFrontMatter object
   */
  static generateFrontMatter(frontMatter: MCPYamlFrontMatter): string {
    const cleanedFrontMatter = Object.fromEntries(
      Object.entries(frontMatter).filter(([_, value]) => value !== undefined && value !== null)
    );
    
    const yamlContent = yaml.stringify(cleanedFrontMatter, {
      indent: 2,
      lineWidth: 80,
      minContentWidth: 20,
    });
    
    return `---\n${yamlContent}---\n`;
  }

  /**
   * Create a complete markdown file with front matter and content
   */
  static createMarkdownFile(frontMatter: MCPYamlFrontMatter, content: string): string {
    const frontMatterSection = MarkdownParser.generateFrontMatter(frontMatter);
    return `${frontMatterSection}\n${content}`;
  }

  /**
   * Validate multiple markdown files in a directory
   */
  async validateDirectory(
    directoryPath: string, 
    options: { recursive?: boolean; filePattern?: RegExp } = {}
  ): Promise<Array<{ filePath: string; isValid: boolean; errors: string[] }>> {
    const results: Array<{ filePath: string; isValid: boolean; errors: string[] }> = [];
    const { recursive = false, filePattern = /\.md$/ } = options;

    try {
      const entries = await fs.promises.readdir(directoryPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(directoryPath, entry.name);
        
        if (entry.isFile() && filePattern.test(entry.name)) {
          try {
            await this.parseFile(fullPath);
            results.push({ filePath: fullPath, isValid: true, errors: [] });
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            results.push({ filePath: fullPath, isValid: false, errors: [errorMessage] });
          }
        } else if (entry.isDirectory() && recursive) {
          const subResults = await this.validateDirectory(fullPath, options);
          results.push(...subResults);
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

    return results;
  }
}