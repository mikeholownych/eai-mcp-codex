#!/bin/bash

# Cloudflare Tunnel Verification Script
# This script verifies that the tunnel setup is working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_DOMAIN="new.ethical-ai-insider.com"
API_DOMAIN="newapi.ethical-ai-insider.com"

echo -e "${BLUE}🔍 MCP Agent Network - Tunnel Verification${NC}"
echo "=============================================="

# Function to check HTTP status
check_url() {
    local url="$1"
    local expected_status="$2"
    local description="$3"
    
    echo -n "Testing $description... "
    
    if status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null); then
        if [[ "$status" == "$expected_status"* ]]; then
            echo -e "${GREEN}✅ $status${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️ $status (expected $expected_status)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Failed to connect${NC}"
        return 1
    fi
}

# Function to check DNS resolution
check_dns() {
    local domain="$1"
    echo -n "DNS resolution for $domain... "
    
    if dig +short "$domain" | grep -q .; then
        echo -e "${GREEN}✅ Resolved${NC}"
        return 0
    else
        echo -e "${RED}❌ Not resolved${NC}"
        return 1
    fi
}

# Function to check SSL certificate
check_ssl() {
    local domain="$1"
    echo -n "SSL certificate for $domain... "
    
    if openssl s_client -connect "$domain:443" -servername "$domain" </dev/null 2>/dev/null | openssl x509 -noout -dates >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Valid${NC}"
        return 0
    else
        echo -e "${RED}❌ Invalid or missing${NC}"
        return 1
    fi
}

# Start verification
echo -e "${BLUE}🔍 Starting verification checks...${NC}"
echo ""

# DNS Checks
echo -e "${BLUE}📡 DNS Resolution Tests${NC}"
echo "------------------------"
check_dns "$FRONTEND_DOMAIN"
check_dns "$API_DOMAIN"
echo ""

# SSL Certificate Checks
echo -e "${BLUE}🔒 SSL Certificate Tests${NC}"
echo "-------------------------"
check_ssl "$FRONTEND_DOMAIN"
check_ssl "$API_DOMAIN"
echo ""

# HTTP Connectivity Tests
echo -e "${BLUE}🌐 HTTP Connectivity Tests${NC}"
echo "----------------------------"
check_url "https://$FRONTEND_DOMAIN" "200" "Frontend Home Page"
check_url "https://$API_DOMAIN/health" "200" "API Health Endpoint"
check_url "https://$API_DOMAIN/status" "200" "API Status Endpoint"
echo ""

# Performance Tests
echo -e "${BLUE}⚡ Performance Tests${NC}"
echo "---------------------"
echo -n "Frontend response time... "
frontend_time=$(curl -s -w "%{time_total}" -o /dev/null "https://$FRONTEND_DOMAIN" 2>/dev/null || echo "0")
if (( $(echo "$frontend_time > 0" | bc -l) )); then
    if (( $(echo "$frontend_time < 2.0" | bc -l) )); then
        echo -e "${GREEN}✅ ${frontend_time}s${NC}"
    else
        echo -e "${YELLOW}⚠️ ${frontend_time}s (slow)${NC}"
    fi
else
    echo -e "${RED}❌ Failed${NC}"
fi

echo -n "API response time... "
api_time=$(curl -s -w "%{time_total}" -o /dev/null "https://$API_DOMAIN/health" 2>/dev/null || echo "0")
if (( $(echo "$api_time > 0" | bc -l) )); then
    if (( $(echo "$api_time < 1.0" | bc -l) )); then
        echo -e "${GREEN}✅ ${api_time}s${NC}"
    else
        echo -e "${YELLOW}⚠️ ${api_time}s (slow)${NC}"
    fi
else
    echo -e "${RED}❌ Failed${NC}"
fi
echo ""

# Local Service Tests
echo -e "${BLUE}🏠 Local Service Tests${NC}"
echo "-----------------------"
echo -n "Frontend local service (port 3000)... "
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
fi

echo -n "API Gateway local service (port 80)... "
if curl -s http://localhost/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
fi

echo -n "Nginx service status... "
if docker compose ps nginx | grep -q "Up"; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
fi
echo ""

# Tunnel Service Tests
echo -e "${BLUE}🚇 Tunnel Service Tests${NC}"
echo "------------------------"
echo -n "Cloudflare tunnel service... "
if sudo systemctl is-active --quiet cloudflared-mcp 2>/dev/null; then
    echo -e "${GREEN}✅ Active${NC}"
else
    echo -e "${RED}❌ Inactive${NC}"
fi

echo -n "Tunnel metrics endpoint... "
if curl -s http://localhost:9080/ready >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Available${NC}"
else
    echo -e "${YELLOW}⚠️ Not available${NC}"
fi
echo ""

# API Endpoint Tests
echo -e "${BLUE}🔌 API Endpoint Tests${NC}"
echo "----------------------"
endpoints=(
    "/health:API Health"
    "/status:API Status"
    "/api/model:Model Router"
    "/api/plans:Plan Management"
    "/api/git:Git Worktree"
    "/api/workflows:Workflow Orchestrator"
    "/api/feedback:Verification Feedback"
)

for endpoint_info in "${endpoints[@]}"; do
    IFS=':' read -r endpoint description <<< "$endpoint_info"
    check_url "https://$API_DOMAIN$endpoint" "200" "$description"
done
echo ""

# Security Tests
echo -e "${BLUE}🛡️ Security Tests${NC}"
echo "------------------"
echo -n "HTTPS redirect... "
if curl -s -I "http://$FRONTEND_DOMAIN" | grep -q "301\|302"; then
    echo -e "${GREEN}✅ Enabled${NC}"
else
    echo -e "${YELLOW}⚠️ Not configured${NC}"
fi

echo -n "Security headers... "
headers=$(curl -s -I "https://$FRONTEND_DOMAIN" | grep -i "strict-transport-security\|x-frame-options\|x-content-type-options")
if [[ -n "$headers" ]]; then
    echo -e "${GREEN}✅ Present${NC}"
else
    echo -e "${YELLOW}⚠️ Missing${NC}"
fi
echo ""

# Final Summary
echo -e "${BLUE}📋 Verification Summary${NC}"
echo "========================"
echo "✅ Domains configured:"
echo "  • Frontend: https://$FRONTEND_DOMAIN"
echo "  • API: https://$API_DOMAIN"
echo ""
echo "🔗 Test URLs:"
echo "  • Frontend: https://$FRONTEND_DOMAIN"
echo "  • API Health: https://$API_DOMAIN/health"
echo "  • API Status: https://$API_DOMAIN/status"
echo ""
echo -e "${GREEN}🎉 Verification complete!${NC}"

# Additional recommendations
echo ""
echo -e "${BLUE}💡 Recommendations:${NC}"
echo "• Test the full user flow through the frontend"
echo "• Configure monitoring alerts"
echo "• Set up Cloudflare security rules"
echo "• Enable caching for static assets"
echo "• Monitor tunnel metrics regularly"