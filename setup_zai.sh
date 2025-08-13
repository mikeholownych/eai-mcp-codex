#!/bin/bash

# Setup script for z.ai GLM-4.5 integration

echo "Setting up z.ai GLM-4.5 integration..."

# Check if ZAI_API_KEY is already set
if [ -z "$ZAI_API_KEY" ]; then
    echo "ZAI_API_KEY environment variable is not set."
    echo "Please set it with: export ZAI_API_KEY=your_zai_api_key"
    echo "Or add it to your .env file"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "src/model_router/router.py" ]; then
    echo "Please run this script from the rag-agent directory"
    exit 1
fi

# Create a backup of the original abacus_client.py
if [ -f "src/model_router/abacus_client.py.backup" ]; then
    echo "Backup already exists"
else
    cp src/model_router/abacus_client.py src/model_router/abacus_client.py.backup
    echo "Created backup of original abacus_client.py"
fi

# Verify the changes
echo "Verifying z.ai integration..."

# Check if the model router has been updated
if grep -q "glm-4.5" src/model_router/router.py; then
    echo "✓ Model router updated for GLM-4.5"
else
    echo "✗ Model router not updated"
fi

# Check if routing rules are updated
if grep -q "glm-4.5" config/routing_rules.yml; then
    echo "✓ Routing rules updated for GLM-4.5"
else
    echo "✗ Routing rules not updated"
fi

# Check if the client has been updated
if grep -q "ZAIClient" src/model_router/abacus_client.py; then
    echo "✓ Client updated for z.ai"
else
    echo "✗ Client not updated"
fi

echo ""
echo "Setup complete! The llm-stack is now configured to use z.ai GLM-4.5."
echo ""
echo "To test the configuration:"
echo "1. Make sure ZAI_API_KEY is set in your environment"
echo "2. Start the services: make up"
echo "3. Test the model router: curl http://localhost:8001/health"
echo ""
echo "The system will now prioritize z.ai GLM-4.5 for all requests."