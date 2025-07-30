# Cloudflare Tunnel Setup for MCP Agent Network

This directory contains configuration and scripts for setting up Cloudflare Tunnels to expose the MCP Agent Network frontend and API to the internet securely.

## 🌐 Domain Configuration

- **Frontend**: `new.ethical-ai-insider.com` → `http://localhost:3000` (Next.js)
- **API**: `newapi.ethical-ai-insider.com` → `http://localhost:80` (Nginx Gateway)

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `config.yml` | Main Cloudflare tunnel configuration |
| `setup.sh` | Automated setup script |
| `manage.sh` | Tunnel management script |
| `credentials.json` | Tunnel credentials (generated during setup) |
| `README.md` | This documentation |

## 🚀 Quick Start

### 1. Prerequisites

- Cloudflare account with domain management access
- `cloudflared` CLI tool (will be installed by setup script)
- Running MCP services (nginx on port 80, frontend on port 3000)

### 2. Initial Setup

```bash
# Run the automated setup script
cd /opt/llm-stack/rag-agent/cloudflare-tunnel
./setup.sh
```

The setup script will:
- Install `cloudflared` if not present
- Authenticate with Cloudflare
- Create the tunnel
- Configure DNS records
- Set up systemd service
- Generate credentials

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create mcp-agent-network

# Configure DNS
cloudflared tunnel route dns mcp-agent-network new.ethical-ai-insider.com
cloudflared tunnel route dns mcp-agent-network newapi.ethical-ai-insider.com

# Start tunnel
cloudflared tunnel --config config.yml run
```

## 🛠 Management

Use the management script for common operations:

```bash
# Start tunnel
./manage.sh start

# Stop tunnel
./manage.sh stop

# Restart tunnel
./manage.sh restart

# Check status
./manage.sh status

# View logs
./manage.sh logs

# Test connectivity
./manage.sh test

# Show metrics
./manage.sh metrics
```

## 🐳 Docker Integration

For containerized deployment:

```bash
# Start with tunnel support
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d

# Check tunnel status
docker logs mcp-cloudflare-tunnel
```

## 🔧 Configuration Details

### Ingress Rules

The tunnel uses the following ingress rules (order matters):

1. **Frontend Domain** (`new.ethical-ai-insider.com`)
   - Routes to: `http://localhost:3000`
   - Service: Next.js frontend application
   - Headers: Custom host headers for proper routing

2. **API Domain** (`newapi.ethical-ai-insider.com`)
   - Routes to: `http://localhost:80`
   - Service: Nginx API gateway
   - Headers: API-specific headers

3. **Catch-all**
   - Returns: HTTP 404 for unmatched requests

### Performance Optimizations

- **Protocol**: QUIC for improved performance
- **Keep-alive**: Connection reuse with 30s timeout
- **Retries**: 3 automatic retries on failure
- **Edge IP**: Auto-selection for optimal routing

## 🔐 Security Features

- **TLS Termination**: Handled by Cloudflare
- **DDoS Protection**: Built-in Cloudflare protection
- **Rate Limiting**: Configurable via Cloudflare dashboard
- **Access Control**: Can be configured via Cloudflare Access

## 📊 Monitoring

### Health Checks

The tunnel exposes health endpoints:
- Tunnel health: `http://localhost:9080/ready`
- Frontend health: `https://new.ethical-ai-insider.com`
- API health: `https://newapi.ethical-ai-insider.com/health`

### Metrics

Access tunnel metrics at:
- Local: `http://localhost:9080/metrics`
- Cloudflare Dashboard: Real-time tunnel analytics

### Logs

View logs using:
```bash
# System logs
sudo journalctl -u cloudflared-mcp -f

# Management script
./manage.sh logs

# Docker logs
docker logs mcp-cloudflare-tunnel
```

## 🚨 Troubleshooting

### Common Issues

1. **Tunnel not starting**
   ```bash
   # Check credentials
   ls -la credentials.json
   
   # Verify config
   cloudflared tunnel --config config.yml validate
   ```

2. **DNS not resolving**
   ```bash
   # Check DNS records
   dig new.ethical-ai-insider.com
   dig newapi.ethical-ai-insider.com
   ```

3. **Local services not responding**
   ```bash
   # Check frontend
   curl http://localhost:3000
   
   # Check API gateway
   curl http://localhost/health
   ```

4. **Permission issues**
   ```bash
   # Fix credentials permissions
   chmod 600 credentials.json
   
   # Check service permissions
   sudo systemctl status cloudflared-mcp
   ```

### Debug Commands

```bash
# Test tunnel configuration
cloudflared tunnel --config config.yml validate

# Run tunnel in debug mode
cloudflared tunnel --config config.yml --loglevel debug run

# Check tunnel status
cloudflared tunnel list

# Test local connectivity
curl -v http://localhost:3000
curl -v http://localhost/health
```

## 🔄 Updates and Maintenance

### Updating Configuration

1. Edit `config.yml`
2. Validate: `cloudflared tunnel --config config.yml validate`
3. Apply: `./manage.sh restart`

### Updating Cloudflared

```bash
# Update via package manager
sudo apt update && sudo apt upgrade cloudflared

# Or download latest version
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Backup

Important files to backup:
- `config.yml` - Tunnel configuration
- `credentials.json` - Tunnel credentials
- DNS records in Cloudflare dashboard

## 📞 Support

### Useful Links

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflared CLI Reference](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/)
- [Troubleshooting Guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/troubleshooting/)

### Getting Help

1. Check the management script: `./manage.sh status`
2. Review logs: `./manage.sh logs`
3. Test connectivity: `./manage.sh test`
4. Consult Cloudflare documentation
5. Check GitHub issues for common problems

## 🎯 Next Steps

After successful setup:

1. **Configure Cloudflare Settings**
   - SSL/TLS mode: Full (strict)
   - Security level: Medium/High
   - Enable Bot Fight Mode

2. **Set up Monitoring**
   - Configure uptime monitoring
   - Set up alert notifications
   - Monitor tunnel metrics

3. **Optimize Performance**
   - Enable Cloudflare caching
   - Configure cache rules
   - Set up custom rules for API endpoints

4. **Security Hardening**
   - Configure Cloudflare Access (if needed)
   - Set up rate limiting rules
   - Enable security headers

## ✅ Verification Checklist

- [ ] Tunnel created and running
- [ ] DNS records pointing to tunnel
- [ ] Frontend accessible at `https://new.ethical-ai-insider.com`
- [ ] API accessible at `https://newapi.ethical-ai-insider.com/health`
- [ ] SSL certificates working (A+ rating on SSL Labs)
- [ ] Performance optimized (check GTmetrix/PageSpeed)
- [ ] Monitoring configured
- [ ] Backup procedures in place