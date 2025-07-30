#!/bin/bash

# Cloudflare Tunnel Setup Script for MCP Agent Network
# This script automates the setup of Cloudflare tunnels for frontend and API access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TUNNEL_NAME="mcp-agent-network"
FRONTEND_DOMAIN="new.ethical-ai-insider.com"
API_DOMAIN="newapi.ethical-ai-insider.com"
CONFIG_DIR="/opt/llm-stack/rag-agent/cloudflare-tunnel"
CONFIG_FILE="$CONFIG_DIR/config.yml"
CREDENTIALS_FILE="$CONFIG_DIR/credentials.json"

echo -e "${BLUE}🚀 MCP Agent Network - Cloudflare Tunnel Setup${NC}"
echo "=================================================="

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}❌ cloudflared is not installed${NC}"
    echo -e "${YELLOW}Installing cloudflared...${NC}"
    
    # Install cloudflared based on the OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared-linux-amd64.deb
        rm cloudflared-linux-amd64.deb
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install cloudflared
        else
            echo -e "${RED}❌ Homebrew not found. Please install cloudflared manually${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Unsupported OS. Please install cloudflared manually${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ cloudflared installed successfully${NC}"
fi

# Login to Cloudflare (if not already logged in)
echo -e "${BLUE}🔐 Checking Cloudflare authentication...${NC}"
if ! cloudflared tunnel list &> /dev/null; then
    echo -e "${YELLOW}⚠️ Please authenticate with Cloudflare first:${NC}"
    echo "Run: cloudflared tunnel login"
    echo "This will open a browser for authentication"
    read -p "Press Enter after completing authentication..."
fi

# Create tunnel if it doesn't exist
echo -e "${BLUE}🔧 Creating tunnel '${TUNNEL_NAME}'...${NC}"
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo -e "${YELLOW}⚠️ Tunnel '$TUNNEL_NAME' already exists${NC}"
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
else
    TUNNEL_ID=$(cloudflared tunnel create "$TUNNEL_NAME" | grep -oP 'Created tunnel \K[a-f0-9-]+')
    echo -e "${GREEN}✅ Tunnel created with ID: $TUNNEL_ID${NC}"
fi

# Copy credentials file to our config directory
echo -e "${BLUE}📋 Setting up credentials...${NC}"
CRED_SOURCE="$HOME/.cloudflared/$TUNNEL_ID.json"
if [ -f "$CRED_SOURCE" ]; then
    cp "$CRED_SOURCE" "$CREDENTIALS_FILE"
    chmod 600 "$CREDENTIALS_FILE"
    echo -e "${GREEN}✅ Credentials file copied${NC}"
else
    echo -e "${RED}❌ Credentials file not found at $CRED_SOURCE${NC}"
    exit 1
fi

# Update config file with tunnel ID
echo -e "${BLUE}⚙️ Updating configuration...${NC}"
sed -i "s/tunnel: mcp-agent-network/tunnel: $TUNNEL_ID/" "$CONFIG_FILE"

# Create DNS records
echo -e "${BLUE}🌐 Creating DNS records...${NC}"

# Frontend domain
if cloudflared tunnel route dns "$TUNNEL_ID" "$FRONTEND_DOMAIN"; then
    echo -e "${GREEN}✅ DNS record created for $FRONTEND_DOMAIN${NC}"
else
    echo -e "${YELLOW}⚠️ DNS record for $FRONTEND_DOMAIN may already exist${NC}"
fi

# API domain
if cloudflared tunnel route dns "$TUNNEL_ID" "$API_DOMAIN"; then
    echo -e "${GREEN}✅ DNS record created for $API_DOMAIN${NC}"
else
    echo -e "${YELLOW}⚠️ DNS record for $API_DOMAIN may already exist${NC}"
fi

# Create systemd service for tunnel
echo -e "${BLUE}⚙️ Creating systemd service...${NC}"
sudo tee /etc/systemd/system/cloudflared-mcp.service > /dev/null <<EOF
[Unit]
Description=Cloudflare Tunnel for MCP Agent Network
After=network.target

[Service]
Type=simple
User=nobody
ExecStart=/usr/local/bin/cloudflared tunnel --config $CONFIG_FILE run
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable cloudflared-mcp.service

echo -e "${GREEN}✅ Cloudflare tunnel setup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo "• Tunnel Name: $TUNNEL_NAME"
echo "• Tunnel ID: $TUNNEL_ID"
echo "• Frontend Domain: $FRONTEND_DOMAIN → http://localhost:3000"
echo "• API Domain: $API_DOMAIN → http://localhost:80"
echo "• Config File: $CONFIG_FILE"
echo "• Service: cloudflared-mcp.service"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "1. Start your frontend: cd frontend && npm run dev"
echo "2. Ensure nginx is running: docker compose up nginx -d"
echo "3. Start the tunnel: sudo systemctl start cloudflared-mcp"
echo "4. Check status: sudo systemctl status cloudflared-mcp"
echo ""
echo -e "${BLUE}🔍 Testing:${NC}"
echo "• Frontend: https://$FRONTEND_DOMAIN"
echo "• API Health: https://$API_DOMAIN/health"
echo "• API Status: https://$API_DOMAIN/status"
echo ""
echo -e "${GREEN}🎉 Setup complete! Your MCP Agent Network is now accessible via Cloudflare tunnels.${NC}"