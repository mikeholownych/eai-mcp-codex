#!/bin/bash
# PostgreSQL Monitoring Script for Corruption Detection
# Continuously monitors database health and integrity

set -euo pipefail

# Configuration
POSTGRES_USER=${POSTGRES_USER:-mcp_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-mcp_secure_password}
CHECK_INTERVAL=${POSTGRES_MONITOR_INTERVAL:-300}  # 5 minutes
LOG_FILE="/backups/monitor.log"

# Database list
DATABASES=(
    "mcp_database"
    "plan_management_db"
    "git_worktree_db" 
    "workflow_orchestrator_db"
    "verification_feedback_db"
    "staff_db"
    "grafana_db"
    "auth_db"
)

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if PostgreSQL is responding
check_postgres_health() {
    if ! pg_isready -h localhost -U "$POSTGRES_USER" >/dev/null 2>&1; then
        log "CRITICAL: PostgreSQL is not responding"
        return 1
    fi
    return 0
}

# Check database connections
check_connections() {
    local max_connections=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -U "$POSTGRES_USER" -d mcp_database -t -c "SHOW max_connections;" 2>/dev/null | xargs || echo "0")
    local current_connections=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -U "$POSTGRES_USER" -d mcp_database -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | xargs || echo "0")
    
    if [ "$current_connections" -gt 0 ] && [ "$max_connections" -gt 0 ]; then
        local usage_percent=$(( (current_connections * 100) / max_connections ))
        
        if [ "$usage_percent" -gt 80 ]; then
            log "WARNING: Connection usage at ${usage_percent}% (${current_connections}/${max_connections})"
        elif [ "$usage_percent" -gt 95 ]; then
            log "CRITICAL: Connection usage at ${usage_percent}% (${current_connections}/${max_connections})"
        fi
    fi
}

# Check for corruption indicators
check_corruption_indicators() {
    for db in "${DATABASES[@]}"; do
        # Check for invalid indexes
        local invalid_indexes=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -U "$POSTGRES_USER" -d "$db" -t -c "
            SELECT count(*) 
            FROM pg_class c 
            JOIN pg_index i ON c.oid = i.indexrelid 
            WHERE i.indisvalid = false;" 2>/dev/null | xargs || echo "0")
        
        if [ "$invalid_indexes" -gt 0 ]; then
            log "WARNING: $invalid_indexes invalid indexes found in database $db"
        fi
    done
}

# Generate health report
generate_health_report() {
    local report_file="/backups/health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
PostgreSQL Health Report
========================
Generated: $(date)

Database Sizes:
EOF
    
    for db in "${DATABASES[@]}"; do
        local size=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -U "$POSTGRES_USER" -d "$db" -t -c "SELECT pg_size_pretty(pg_database_size('$db'));" 2>/dev/null | xargs || echo "Unknown")
        echo "$db: $size" >> "$report_file"
    done
    
    log "Health report generated: $report_file"
}

# Main monitoring function
monitor_once() {
    log "Running PostgreSQL health check"
    
    if check_postgres_health; then
        check_connections
        check_corruption_indicators
        generate_health_report
        log "Health check completed successfully"
    else
        log "PostgreSQL health check failed"
        return 1
    fi
}

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

# Run monitoring
monitor_once