# Makefile for Cloudflare Tunnel Management
# MCP Agent Network

.PHONY: help setup start stop restart status logs test verify clean

# Default target
help:
	@echo "🚀 MCP Agent Network - Cloudflare Tunnel Management"
	@echo "=================================================="
	@echo "Available targets:"
	@echo "  setup     - Run initial tunnel setup"
	@echo "  start     - Start the tunnel"
	@echo "  stop      - Stop the tunnel"
	@echo "  restart   - Restart the tunnel"
	@echo "  status    - Show tunnel status"
	@echo "  logs      - Show tunnel logs"
	@echo "  test      - Test tunnel connectivity"
	@echo "  verify    - Run comprehensive verification"
	@echo "  clean     - Clean up tunnel resources"
	@echo ""
	@echo "Quick start: make setup && make start"

# Initial setup
setup:
	@echo "🔧 Running Cloudflare tunnel setup..."
	./setup.sh

# Start tunnel
start:
	@echo "🚀 Starting tunnel..."
	./manage.sh start

# Stop tunnel
stop:
	@echo "🛑 Stopping tunnel..."
	./manage.sh stop

# Restart tunnel
restart:
	@echo "🔄 Restarting tunnel..."
	./manage.sh restart

# Show status
status:
	@echo "📊 Checking tunnel status..."
	./manage.sh status

# Show logs
logs:
	@echo "📋 Showing tunnel logs..."
	./manage.sh logs

# Test connectivity
test:
	@echo "🧪 Testing tunnel connectivity..."
	./manage.sh test

# Run verification
verify:
	@echo "🔍 Running comprehensive verification..."
	./verify.sh

# Clean up
clean:
	@echo "🧹 Cleaning up tunnel resources..."
	@echo "⚠️  This will stop the tunnel and remove configuration"
	@read -p "Are you sure? [y/N]: " confirm && [ "$$confirm" = "y" ] || exit 1
	sudo systemctl stop cloudflared-mcp || true
	sudo systemctl disable cloudflared-mcp || true
	sudo rm -f /etc/systemd/system/cloudflared-mcp.service
	sudo systemctl daemon-reload
	@echo "✅ Cleanup complete"