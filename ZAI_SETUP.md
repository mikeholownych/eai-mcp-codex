# z.ai GLM-4.5 Integration Guide

This guide explains how to set up and use z.ai GLM-4.5 with the MCP Codex llm-stack.

## Overview

The system has been configured to use z.ai GLM-4.5 as the primary model for all requests, with fallback to Claude and local models when needed.

## Prerequisites

1. **z.ai API Key**: You need a valid z.ai API key
2. **Environment Setup**: The llm-stack must be properly installed

## Setup Instructions

### 1. Set Environment Variable

```bash
export ZAI_API_KEY=your_zai_api_key_here
```

Or add to your `.env` file:
```
ZAI_API_KEY=your_zai_api_key_here
```

### 2. Run Setup Script

```bash
cd /opt/Tmux-Orchestrator/llm-stack/rag-agent
./setup_zai.sh
```

### 3. Start Services

```bash
make up
```

## Configuration Changes Made

### Model Router Updates
- **Default Model**: Changed from `gpt-4o-mini` to `glm-4.5`
- **Primary Provider**: z.ai GLM-4.5 is now the preferred model
- **Fallback Hierarchy**: z.ai → Claude → Local LLM

### Client Integration
- **Client Class**: `AbacusAIClient` → `ZAIClient`
- **API Endpoint**: Uses `https://api.z.ai/v1/chat/completions`
- **Model Mapping**: GLM-4.5 added as primary model

### Routing Rules
- **All Tasks**: Default to `glm-4.5`
- **Coding Tasks**: Use `glm-4.5`
- **Complex Tasks**: Use `glm-4.5`
- **Simple Tasks**: Use `glm-4.5`

## API Usage

The z.ai client uses the OpenAI-compatible API format:

```python
# Example usage
response = await client.post(
    "https://api.z.ai/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": "glm-4.5",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4000,
    },
)
```

## Testing the Integration

### 1. Health Check
```bash
curl http://localhost:8001/health
```

### 2. Model Router Test
```bash
curl -X POST http://localhost:8001/route \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!"}'
```

### 3. Direct Model Test
```bash
curl -X POST http://localhost:8001/test \
  -H "Content-Type: application/json" \
  -d '{"text": "Write a Python function to calculate factorial"}'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ZAI_API_KEY` | Your z.ai API key | Required |
| `USE_ZAI` | Enable/disable z.ai | `true` |
| `PREFER_LOCAL_MODELS` | Use local models only | `false` |

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   ZAI_API_KEY not found. z.ai client will not be available.
   ```
   **Solution**: Set the `ZAI_API_KEY` environment variable

2. **Model Not Available**
   ```
   Model glm-4.5 not available
   ```
   **Solution**: Verify your z.ai API key has access to GLM-4.5

3. **Connection Timeout**
   ```
   Error calling z.ai API: timeout
   ```
   **Solution**: Check internet connection and z.ai service status

### Debug Commands

```bash
# Check model router status
make logs-service SERVICE=model-router

# Test routing directly
curl http://localhost:8001/stats

# Check environment variables
env | grep ZAI
```

## Performance Considerations

- **Response Time**: z.ai GLM-4.5 provides fast responses
- **Token Limits**: Supports up to 4000 tokens by default
- **Rate Limits**: Respect z.ai's rate limiting policies
- **Cost**: GLM-4.5 is cost-effective for most use cases

## Rollback

If you need to revert to the previous configuration:

```bash
# Restore backup
cp src/model_router/abacus_client.py.backup src/model_router/abacus_client.py

# Revert routing rules
git checkout config/routing_rules.yml

# Restart services
make down && make up
```

## Monitoring

The system provides comprehensive monitoring:

- **Grafana Dashboard**: http://localhost:3000
- **Prometheus Metrics**: http://localhost:9090
- **Model Router Stats**: http://localhost:8001/stats

## Security

- **API Key Security**: Never commit API keys to version control
- **HTTPS Only**: All API calls use HTTPS
- **Token Validation**: Responses are validated for proper format
- **Error Handling**: Graceful fallback to alternative models

## Support

For issues with z.ai integration:
1. Check z.ai service status
2. Verify API key and permissions
3. Review logs in `logs/model-router/`
4. Check system health with `make status`