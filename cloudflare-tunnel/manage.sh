#!/bin/bash

# Cloudflare Tunnel Management Script for MCP Agent Network
# Usage: ./manage.sh [start|stop|restart|status|logs|test]

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
SERVICE_NAME="cloudflared-mcp"
CONFIG_DIR="/opt/llm-stack/rag-agent/cloudflare-tunnel"

function print_usage() {
    echo -e "${BLUE}MCP Agent Network - Cloudflare Tunnel Manager${NC}"
    echo "=============================================="
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start    - Start the Cloudflare tunnel"
    echo "  stop     - Stop the Cloudflare tunnel"
    echo "  restart  - Restart the Cloudflare tunnel"
    echo "  status   - Show tunnel status"
    echo "  logs     - Show tunnel logs"
    echo "  test     - Test tunnel connectivity"
    echo "  metrics  - Show tunnel metrics"
    echo "  update   - Update tunnel configuration"
    echo ""
}

function start_tunnel() {
    echo -e "${BLUE}🚀 Starting Cloudflare tunnel...${NC}"
    
    # Check if services are running
    if ! docker compose ps nginx | grep -q "Up"; then
        echo -e "${YELLOW}⚠️ Starting nginx service first...${NC}"
        docker compose up nginx -d
        sleep 5
    fi
    
    # Start the tunnel service
    if sudo systemctl start $SERVICE_NAME; then
        echo -e "${GREEN}✅ Tunnel started successfully${NC}"
        sleep 3
        sudo systemctl status $SERVICE_NAME --no-pager
    else
        echo -e "${RED}❌ Failed to start tunnel${NC}"
        exit 1
    fi
}

function stop_tunnel() {
    echo -e "${BLUE}🛑 Stopping Cloudflare tunnel...${NC}"
    
    if sudo systemctl stop $SERVICE_NAME; then
        echo -e "${GREEN}✅ Tunnel stopped successfully${NC}"
    else
        echo -e "${RED}❌ Failed to stop tunnel${NC}"
        exit 1
    fi
}

function restart_tunnel() {
    echo -e "${BLUE}🔄 Restarting Cloudflare tunnel...${NC}"
    
    if sudo systemctl restart $SERVICE_NAME; then
        echo -e "${GREEN}✅ Tunnel restarted successfully${NC}"
        sleep 3
        sudo systemctl status $SERVICE_NAME --no-pager
    else
        echo -e "${RED}❌ Failed to restart tunnel${NC}"
        exit 1
    fi
}

function show_status() {
    echo -e "${BLUE}📊 Cloudflare Tunnel Status${NC}"
    echo "============================"
    
    # Service status
    echo -e "${BLUE}Service Status:${NC}"
    sudo systemctl status $SERVICE_NAME --no-pager || true
    echo ""
    
    # Check if domains are accessible
    echo -e "${BLUE}Domain Accessibility:${NC}"
    
    # Test frontend domain
    if curl -s -o /dev/null -w "%{http_code}" "https://$FRONTEND_DOMAIN" | grep -q "200\|301\|302"; then
        echo -e "• Frontend ($FRONTEND_DOMAIN): ${GREEN}✅ Accessible${NC}"
    else
        echo -e "• Frontend ($FRONTEND_DOMAIN): ${RED}❌ Not accessible${NC}"
    fi
    
    # Test API domain
    if curl -s -o /dev/null -w "%{http_code}" "https://$API_DOMAIN/health" | grep -q "200"; then
        echo -e "• API ($API_DOMAIN): ${GREEN}✅ Accessible${NC}"
    else
        echo -e "• API ($API_DOMAIN): ${RED}❌ Not accessible${NC}"
    fi
    
    # Show local services
    echo ""
    echo -e "${BLUE}Local Services:${NC}"
    echo "• Frontend (port 3000): $(curl -s http://localhost:3000 >/dev/null 2>&1 && echo -e "${GREEN}✅ Running${NC}" || echo -e "${RED}❌ Not running${NC}")"
    echo "• API Gateway (port 80): $(curl -s http://localhost/health >/dev/null 2>&1 && echo -e "${GREEN}✅ Running${NC}" || echo -e "${RED}❌ Not running${NC}")"
}

function show_logs() {
    echo -e "${BLUE}📋 Cloudflare Tunnel Logs${NC}"
    echo "=========================="
    sudo journalctl -u $SERVICE_NAME -f --no-pager
}

function test_connectivity() {
    echo -e "${BLUE}🧪 Testing Tunnel Connectivity${NC}"
    echo "==============================="
    
    # Test frontend
    echo -e "${BLUE}Testing Frontend Domain...${NC}"
    if response=$(curl -s -w "HTTP Status: %{http_code}\nTime: %{time_total}s\n" "https://$FRONTEND_DOMAIN"); then
        echo -e "${GREEN}✅ Frontend Response:${NC}"
        echo "$response" | head -5
    else
        echo -e "${RED}❌ Frontend test failed${NC}"
    fi
    
    echo ""
    
    # Test API
    echo -e "${BLUE}Testing API Domain...${NC}"
    if response=$(curl -s "https://$API_DOMAIN/health"); then
        echo -e "${GREEN}✅ API Health Response:${NC}"
        echo "$response" | jq . 2>/dev/null || echo "$response"
    else
        echo -e "${RED}❌ API health test failed${NC}"
    fi
    
    echo ""
    
    # Test API status
    echo -e "${BLUE}Testing API Status...${NC}"
    if response=$(curl -s "https://$API_DOMAIN/status"); then
        echo -e "${GREEN}✅ API Status Response:${NC}"
        echo "$response" | jq . 2>/dev/null || echo "$response"
    else
        echo -e "${RED}❌ API status test failed${NC}"
    fi
}

function show_metrics() {
    echo -e "${BLUE}📈 Tunnel Metrics${NC}"
    echo "=================="
    
    if curl -s http://localhost:9080/metrics >/dev/null 2>&1; then
        curl -s http://localhost:9080/metrics
    else
        echo -e "${YELLOW}⚠️ Metrics not available (tunnel may not be running or metrics disabled)${NC}"
    fi
}

function update_config() {
    echo -e "${BLUE}⚙️ Updating Tunnel Configuration${NC}"
    echo "=================================="
    
    # Validate config
    if cloudflared tunnel --config "$CONFIG_DIR/config.yml" validate; then
        echo -e "${GREEN}✅ Configuration is valid${NC}"
        
        # Restart tunnel to apply changes
        echo -e "${BLUE}Restarting tunnel to apply changes...${NC}"
        restart_tunnel
    else
        echo -e "${RED}❌ Configuration validation failed${NC}"
        exit 1
    fi
}

# Main script logic
case ${1:-} in
    start)
        start_tunnel
        ;;
    stop)
        stop_tunnel
        ;;
    restart)
        restart_tunnel
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_connectivity
        ;;
    metrics)
        show_metrics
        ;;
    update)
        update_config
        ;;
    *)
        print_usage
        exit 1
        ;;
esac