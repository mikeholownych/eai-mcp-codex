---
name: advanced-generate
scope: project
tags: [command, generation, enhanced]
version: 1.3.0
priority: 5
command_type: generation
output_format: code
required_context:
  - file-structure
  - coding-standards
  - project-dependencies
max_context_size: 6144
security_level: medium
timeout_ms: 45000
retry_attempts: 2
requires_confirmation: false
sandboxed: false
error_messages:
  validation_failed: "Code generation failed validation checks"
  timeout_exceeded: "Generation took too long, consider breaking into smaller tasks"
  security_violation: "Generated code contains potential security issues"
author: MCP Team
description: Advanced code generation command with enhanced validation and quality checks
documentation_url: https://docs.mcp.example.com/commands/advanced-generate
created_at: 2024-01-20T09:00:00Z
updated_at: 2024-03-25T11:15:00Z
usage_count: 127
last_used: 2024-03-25T16:42:00Z
---

# Advanced Generate Command

Generate high-quality, production-ready code with comprehensive validation and quality assurance.

## Parameters

- **prompt**: Detailed description of what to generate (string, required)
  - Must be specific and include functional requirements
  - Should specify programming language and framework
  - Can include architectural constraints and patterns to follow

- **filePath**: Target file path for generated code (string, required)
  - Must use appropriate file extension for the language
  - Path should follow project structure conventions
  - Directory will be created if it doesn't exist

- **language**: Programming language (string, optional, default: inferred from filePath)
  - Supported: typescript, javascript, python, java, go, rust, etc.
  - Influences code style and best practices applied

- **framework**: Framework or library context (string, optional)
  - Examples: react, angular, vue, express, fastapi, spring
  - Affects generated patterns and imports

- **style**: Code style preference (string, optional, default: standard)
  - Options: standard, functional, object-oriented, minimal
  - Determines architectural patterns and code organization

- **includeTests**: Generate accompanying test files (boolean, optional, default: false)
  - Creates unit tests alongside the main code
  - Follows testing conventions for the chosen language/framework

- **includeDocumentation**: Include inline documentation (boolean, optional, default: true)
  - Adds comprehensive JSDoc/docstring comments
  - Includes usage examples and parameter descriptions

## Instructions

This command generates production-quality code by following these principles:

### Code Quality Standards
1. **Clean Code**: Follow naming conventions, SOLID principles, and DRY patterns
2. **Type Safety**: Use strong typing where applicable (TypeScript, typed Python, etc.)
3. **Error Handling**: Include proper error handling and validation
4. **Performance**: Consider performance implications and optimize for common use cases
5. **Security**: Follow security best practices and avoid common vulnerabilities

### Generation Process
1. Analyze the prompt and extract requirements
2. Determine appropriate architectural patterns
3. Generate clean, well-structured code
4. Add comprehensive documentation
5. Include error handling and edge cases
6. Apply language-specific best practices
7. Validate generated code for common issues

### Quality Checks
- Syntax validation for the target language
- Import/dependency verification
- Code style consistency
- Security vulnerability scanning
- Performance anti-pattern detection

## Pre-execution Checks

- Validate parameters and ensure prompt clarity
- Check permissions for target file path
- Verify working directory exists and is writable
- Confirm language/framework compatibility
- Validate project dependencies are available

## Post-execution Actions

- Validate generated code syntax
- Run security scan on generated code
- Check code style compliance
- Log generation metrics and statistics
- Create backup of any overwritten files

## Error Handling

### Retry Strategy
- **Transient Failures**: Retry up to 2 times with exponential backoff
- **Validation Failures**: Attempt to fix common issues automatically
- **Security Issues**: Escalate to security agent for review
- **Syntax Errors**: Re-generate with simplified requirements

### Escalation Rules
- Escalate if generation consistently fails after retries
- Escalate for complex architectural decisions
- Escalate if security vulnerabilities are detected
- Escalate if generated code doesn't meet quality standards

## Examples

### Example 1: React Component Generation
```bash
mcp advanced-generate --prompt "Create a reusable Card component with title, content, and optional actions" --filePath "src/components/Card.tsx" --framework "react" --includeTests true
```

Expected output: A well-structured React component with TypeScript types, proper props interface, and accompanying test file.

### Example 2: Python API Endpoint
```bash
mcp advanced-generate --prompt "Create a FastAPI endpoint for user profile management with CRUD operations" --filePath "src/api/users.py" --framework "fastapi" --includeDocumentation true
```

Expected output: FastAPI router with proper request/response models, error handling, and comprehensive documentation.

### Example 3: Database Model
```bash
mcp advanced-generate --prompt "Create a SQLAlchemy model for a blog post with relationships to users and categories" --filePath "src/models/post.py" --language "python" --style "object-oriented"
```

Expected output: SQLAlchemy model with proper relationships, constraints, and methods.

## Quality Gates

Before code generation is considered complete:
- [ ] Generated code passes syntax validation
- [ ] All imports and dependencies are valid
- [ ] Code follows project's style guidelines
- [ ] Security scan shows no critical vulnerabilities
- [ ] Generated code includes proper error handling
- [ ] Documentation is comprehensive and accurate
- [ ] Test files are generated if requested and are executable

## Integration Notes

This command integrates with:
- **Security Agent**: For vulnerability scanning
- **Style Checker**: For code style validation  
- **Test Runner**: For validating generated tests
- **Documentation Generator**: For API documentation
- **Dependency Manager**: For import validation

## Performance Considerations

- Large file generation may require increased timeout
- Complex architectural patterns may need multiple passes
- Framework-specific generation requires additional context loading
- Test generation doubles the processing time but improves quality