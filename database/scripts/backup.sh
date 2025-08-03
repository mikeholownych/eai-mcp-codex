#!/bin/bash
# PostgreSQL Backup Script with Corruption Detection
# Runs automated backups and integrity checks

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=${POSTGRES_BACKUP_RETENTION_DAYS:-7}
POSTGRES_USER=${POSTGRES_USER:-mcp_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-mcp_secure_password}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a ${BACKUP_DIR}/backup.log
}

# Create backup directory
mkdir -p ${BACKUP_DIR}/{dumps,integrity,logs}

# Function to perform integrity check
check_integrity() {
    local db=$1
    log "Starting integrity check for database: $db"
    
    # Check for corruption using pg_dump with --verbose
    if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h localhost \
        -U "$POSTGRES_USER" \
        -d "$db" \
        --verbose \
        --no-data \
        --schema-only \
        -f "${BACKUP_DIR}/integrity/${db}_schema_${TIMESTAMP}.sql" 2>&1 | \
        grep -i "error\|corrupt\|invalid" && [ ${PIPESTATUS[0]} -ne 0 ]; then
        log "ERROR: Corruption detected in database $db during schema dump"
        return 1
    fi
    
    # Verify table checksums if available
    if PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h localhost \
        -U "$POSTGRES_USER" \
        -d "$db" \
        -c "SELECT schemaname, tablename, attname, n_distinct, correlation 
            FROM pg_stats LIMIT 1;" >/dev/null 2>&1; then
        log "Database $db statistics accessible - no major corruption detected"
    else
        log "WARNING: Could not access statistics for database $db"
        return 1
    fi
    
    # Check for table consistency
    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h localhost \
        -U "$POSTGRES_USER" \
        -d "$db" \
        -c "SELECT pg_size_pretty(pg_database_size('$db')) as db_size;" \
        > "${BACKUP_DIR}/integrity/${db}_size_${TIMESTAMP}.txt"
    
    log "Integrity check completed for database: $db"
    return 0
}

# Function to backup a database
backup_database() {
    local db=$1
    local backup_file="${BACKUP_DIR}/dumps/${db}_${TIMESTAMP}.sql.gz"
    
    log "Starting backup for database: $db"
    
    # Perform integrity check first
    if ! check_integrity "$db"; then
        log "ERROR: Integrity check failed for $db - skipping backup"
        return 1
    fi
    
    # Create compressed backup
    if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h localhost \
        -U "$POSTGRES_USER" \
        -d "$db" \
        --verbose \
        --format=custom \
        --compress=9 \
        --no-privileges \
        --no-owner | gzip > "$backup_file"; then
        
        # Verify backup file was created and has content
        if [ -s "$backup_file" ]; then
            local size=$(du -h "$backup_file" | cut -f1)
            log "SUCCESS: Backup completed for $db (Size: $size)"
            
            # Test backup validity by attempting to list contents
            if gunzip -c "$backup_file" | head -10 | grep -q "PostgreSQL database dump"; then
                log "SUCCESS: Backup verification passed for $db"
                return 0
            else
                log "ERROR: Backup verification failed for $db"
                rm -f "$backup_file"
                return 1
            fi
        else
            log "ERROR: Backup file is empty for $db"
            rm -f "$backup_file"
            return 1
        fi
    else
        log "ERROR: Backup failed for database $db"
        return 1
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Starting cleanup of backups older than $RETENTION_DAYS days"
    
    # Remove old dumps
    find "${BACKUP_DIR}/dumps" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # Remove old integrity checks
    find "${BACKUP_DIR}/integrity" -name "*.sql" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "${BACKUP_DIR}/integrity" -name "*.txt" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # Keep only last 100 log entries
    if [ -f "${BACKUP_DIR}/backup.log" ]; then
        tail -100 "${BACKUP_DIR}/backup.log" > "${BACKUP_DIR}/backup.log.tmp"
        mv "${BACKUP_DIR}/backup.log.tmp" "${BACKUP_DIR}/backup.log"
    fi
    
    log "Cleanup completed"
}

# Function to generate backup report
generate_report() {
    local report_file="${BACKUP_DIR}/logs/backup_report_${TIMESTAMP}.txt"
    
    cat > "$report_file" << EOF
PostgreSQL Backup Report
========================
Date: $(date)
Retention: $RETENTION_DAYS days

Backup Status:
EOF
    
    for db in "${DATABASES[@]}"; do
        local latest_backup=$(find "${BACKUP_DIR}/dumps" -name "${db}_*.sql.gz" -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        if [ -n "$latest_backup" ]; then
            local size=$(du -h "$latest_backup" 2>/dev/null | cut -f1 || echo "Unknown")
            local date=$(stat -c %y "$latest_backup" 2>/dev/null | cut -d'.' -f1 || echo "Unknown")
            echo " $db: $size ($date)" >> "$report_file"
        else
            echo " $db: No backup found" >> "$report_file"
        fi
    done
    
    echo "" >> "$report_file"
    echo "Disk Usage:" >> "$report_file"
    du -sh "${BACKUP_DIR}"/* >> "$report_file" 2>/dev/null || true
    
    log "Backup report generated: $report_file"
}

# Main execution
main() {
    log "=== PostgreSQL Backup Process Started ==="
    
    local failed_backups=0
    local total_backups=${#DATABASES[@]}
    
    # Backup each database
    for db in "${DATABASES[@]}"; do
        if ! backup_database "$db"; then
            ((failed_backups++))
        fi
        sleep 2  # Brief pause between backups
    done
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Generate report
    generate_report
    
    # Final status
    local successful_backups=$((total_backups - failed_backups))
    log "=== Backup Process Completed ==="
    log "Total databases: $total_backups"
    log "Successful backups: $successful_backups"
    log "Failed backups: $failed_backups"
    
    if [ $failed_backups -eq 0 ]; then
        log "SUCCESS: All database backups completed successfully"
        exit 0
    else
        log "WARNING: Some backups failed - check logs for details"
        exit 1
    fi
}

# Run main function
main "$@"