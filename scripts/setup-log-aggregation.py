#!/usr/bin/env python3
"""
MCP Log Aggregation and Analysis Pipeline Setup Script
This script initializes and manages the comprehensive log aggregation and analysis pipeline.
"""

import sys
import json
import yaml
import subprocess
import logging
import requests
import time
from pathlib import Path
from typing import Dict
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LogAggregationConfig:
    """Configuration for the log aggregation pipeline."""
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    kibana_host: str = "localhost"
    kibana_port: int = 5601
    fluentd_host: str = "localhost"
    fluentd_port: int = 24224
    prometheus_host: str = "localhost"
    prometheus_port: int = 9090
    grafana_host: str = "localhost"
    grafana_port: int = 3000
    alertmanager_host: str = "localhost"
    alertmanager_port: int = 9093
    environment: str = "development"
    cluster_name: str = "mcp-cluster"
    log_retention_days: int = 365
    backup_enabled: bool = True
    backup_schedule: str = "0 2 * * *"
    monitoring_enabled: bool = True
    alerting_enabled: bool = True
    security_enabled: bool = True
    compliance_enabled: bool = True

class LogAggregationPipeline:
    """Main class for managing the log aggregation and analysis pipeline."""
    
    def __init__(self, config: LogAggregationConfig):
        self.config = config
        self.elasticsearch_url = f"http://{config.elasticsearch_host}:{config.elasticsearch_port}"
        self.kibana_url = f"http://{config.kibana_host}:{config.kibana_port}"
        self.fluentd_url = f"http://{config.fluentd_host}:{config.fluentd_port}"
        self.prometheus_url = f"http://{config.prometheus_host}:{config.prometheus_port}"
        self.grafana_url = f"http://{config.grafana_host}:{config.grafana_port}"
        self.alertmanager_url = f"http://{config.alertmanager_host}:{config.alertmanager_port}"
        
    def wait_for_service(self, url: str, service_name: str, timeout: int = 300) -> bool:
        """Wait for a service to be ready."""
        logger.info(f"Waiting for {service_name} to be ready at {url}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"{service_name} is ready")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            logger.info(f"Waiting for {service_name}...")
            time.sleep(5)
        
        logger.error(f"Timeout waiting for {service_name}")
        return False
    
    def setup_elasticsearch(self) -> bool:
        """Set up Elasticsearch with templates and policies."""
        logger.info("Setting up Elasticsearch...")
        
        if not self.wait_for_service(self.elasticsearch_url, "Elasticsearch"):
            return False
        
        try:
            # Create index template
            template_path = Path("fluentd/templates/mcp-logs-template.json")
            if template_path.exists():
                with open(template_path, 'r') as f:
                    template_data = json.load(f)
                
                template_name = "mcp-logs-template"
                url = f"{self.elasticsearch_url}/_index_template/{template_name}"
                response = requests.put(url, json=template_data)
                if response.status_code == 200:
                    logger.info("Elasticsearch index template created successfully")
                else:
                    logger.error(f"Failed to create index template: {response.text}")
                    return False
            
            # Create ILM policy
            policy_path = Path("fluentd/policies/mcp-logs-policy.json")
            if policy_path.exists():
                with open(policy_path, 'r') as f:
                    policy_data = json.load(f)
                
                policy_name = "mcp-logs-policy"
                url = f"{self.elasticsearch_url}/_ilm/policy/{policy_name}"
                response = requests.put(url, json=policy_data)
                if response.status_code == 200:
                    logger.info("Elasticsearch ILM policy created successfully")
                else:
                    logger.error(f"Failed to create ILM policy: {response.text}")
                    return False
            
            # Create initial index
            index_name = "mcp-logs-000001"
            url = f"{self.elasticsearch_url}/{index_name}"
            response = requests.put(url)
            if response.status_code in [200, 201]:
                logger.info("Initial Elasticsearch index created successfully")
            else:
                logger.error(f"Failed to create initial index: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Elasticsearch: {e}")
            return False
    
    def setup_kibana(self) -> bool:
        """Set up Kibana with dashboards and visualizations."""
        logger.info("Setting up Kibana...")
        
        if not self.wait_for_service(self.kibana_url, "Kibana"):
            return False
        
        try:
            # Create index pattern
            index_pattern = {
                "attributes": {
                    "title": "mcp-logs-*",
                    "timeFieldName": "@timestamp",
                    "fields": "[]"
                }
            }
            
            url = f"{self.kibana_url}/api/saved_objects/index-pattern/mcp-logs"
            headers = {"kbn-xsrf": "true"}
            response = requests.post(url, json=index_pattern, headers=headers)
            if response.status_code == 200:
                logger.info("Kibana index pattern created successfully")
            else:
                logger.error(f"Failed to create index pattern: {response.text}")
                return False
            
            # Import dashboards
            dashboard_dir = Path("monitoring/kibana/dashboards")
            if dashboard_dir.exists():
                for dashboard_file in dashboard_dir.glob("*.json"):
                    with open(dashboard_file, 'r') as f:
                        dashboard_data = json.load(f)
                    
                    url = f"{self.kibana_url}/api/saved_objects/dashboard"
                    response = requests.post(url, json=dashboard_data, headers=headers)
                    if response.status_code == 200:
                        logger.info(f"Dashboard {dashboard_file.name} imported successfully")
                    else:
                        logger.error(f"Failed to import dashboard {dashboard_file.name}: {response.text}")
            
            # Import visualizations
            viz_dir = Path("monitoring/kibana/visualizations")
            if viz_dir.exists():
                for viz_file in viz_dir.glob("*.json"):
                    with open(viz_file, 'r') as f:
                        viz_data = json.load(f)
                    
                    url = f"{self.kibana_url}/api/saved_objects/visualization"
                    response = requests.post(url, json=viz_data, headers=headers)
                    if response.status_code == 200:
                        logger.info(f"Visualization {viz_file.name} imported successfully")
                    else:
                        logger.error(f"Failed to import visualization {viz_file.name}: {response.text}")
            
            # Import searches
            search_dir = Path("monitoring/kibana/searches")
            if search_dir.exists():
                for search_file in search_dir.glob("*.json"):
                    with open(search_file, 'r') as f:
                        search_data = json.load(f)
                    
                    url = f"{self.kibana_url}/api/saved_objects/search"
                    response = requests.post(url, json=search_data, headers=headers)
                    if response.status_code == 200:
                        logger.info(f"Search {search_file.name} imported successfully")
                    else:
                        logger.error(f"Failed to import search {search_file.name}: {response.text}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Kibana: {e}")
            return False
    
    def setup_prometheus(self) -> bool:
        """Set up Prometheus with log-based metrics."""
        logger.info("Setting up Prometheus...")
        
        if not self.wait_for_service(self.prometheus_url, "Prometheus"):
            return False
        
        try:
            # Reload Prometheus configuration
            url = f"{self.prometheus_url}/-/reload"
            response = requests.post(url)
            if response.status_code == 200:
                logger.info("Prometheus configuration reloaded successfully")
            else:
                logger.error(f"Failed to reload Prometheus configuration: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Prometheus: {e}")
            return False
    
    def setup_grafana(self) -> bool:
        """Set up Grafana with data sources and dashboards."""
        logger.info("Setting up Grafana...")
        
        if not self.wait_for_service(self.grafana_url, "Grafana"):
            return False
        
        try:
            # Add Prometheus data source
            prometheus_ds = {
                "name": "Prometheus",
                "type": "prometheus",
                "url": self.prometheus_url,
                "access": "proxy",
                "basicAuth": False,
                "isDefault": True
            }
            
            url = f"{self.grafana_url}/api/datasources"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=prometheus_ds, headers=headers)
            if response.status_code == 200:
                logger.info("Prometheus data source added to Grafana successfully")
            else:
                logger.error(f"Failed to add Prometheus data source: {response.text}")
                return False
            
            # Add Elasticsearch data source
            elasticsearch_ds = {
                "name": "Elasticsearch",
                "type": "elasticsearch",
                "url": self.elasticsearch_url,
                "access": "proxy",
                "basicAuth": False,
                "isDefault": False,
                "database": "mcp-logs-*",
                "timeField": "@timestamp"
            }
            
            response = requests.post(url, json=elasticsearch_ds, headers=headers)
            if response.status_code == 200:
                logger.info("Elasticsearch data source added to Grafana successfully")
            else:
                logger.error(f"Failed to add Elasticsearch data source: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Grafana: {e}")
            return False
    
    def setup_fluentd(self) -> bool:
        """Set up Fluentd configuration."""
        logger.info("Setting up Fluentd...")
        
        try:
            # Check if Fluentd configuration exists
            fluentd_conf = Path("fluentd/conf/fluent.conf")
            if not fluentd_conf.exists():
                logger.error("Fluentd configuration not found")
                return False
            
            logger.info("Fluentd configuration is ready")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Fluentd: {e}")
            return False
    
    def setup_alertmanager(self) -> bool:
        """Set up Alertmanager configuration."""
        logger.info("Setting up Alertmanager...")
        
        if not self.wait_for_service(self.alertmanager_url, "Alertmanager"):
            return False
        
        try:
            # Reload Alertmanager configuration
            url = f"{self.alertmanager_url}/-/reload"
            response = requests.post(url)
            if response.status_code == 200:
                logger.info("Alertmanager configuration reloaded successfully")
            else:
                logger.error(f"Failed to reload Alertmanager configuration: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Alertmanager: {e}")
            return False
    
    def start_services(self) -> bool:
        """Start all log aggregation services using Docker Compose."""
        logger.info("Starting log aggregation services...")
        
        try:
            # Start services
            cmd = ["docker-compose", "-f", "docker-compose.logging.yml", "up", "-d"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Log aggregation services started successfully")
                return True
            else:
                logger.error(f"Failed to start services: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting services: {e}")
            return False
    
    def stop_services(self) -> bool:
        """Stop all log aggregation services."""
        logger.info("Stopping log aggregation services...")
        
        try:
            # Stop services
            cmd = ["docker-compose", "-f", "docker-compose.logging.yml", "down"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Log aggregation services stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop services: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping services: {e}")
            return False
    
    def check_service_health(self) -> Dict[str, bool]:
        """Check the health of all services."""
        logger.info("Checking service health...")
        
        health_status = {}
        
        # Check Elasticsearch
        try:
            response = requests.get(f"{self.elasticsearch_url}/_cluster/health")
            health_status["elasticsearch"] = response.status_code == 200
        except Exception:
            health_status["elasticsearch"] = False
        
        # Check Kibana
        try:
            response = requests.get(f"{self.kibana_url}/api/status")
            health_status["kibana"] = response.status_code == 200
        except Exception:
            health_status["kibana"] = False
        
        # Check Prometheus
        try:
            response = requests.get(f"{self.prometheus_url}/-/healthy")
            health_status["prometheus"] = response.status_code == 200
        except Exception:
            health_status["prometheus"] = False
        
        # Check Grafana
        try:
            response = requests.get(f"{self.grafana_url}/api/health")
            health_status["grafana"] = response.status_code == 200
        except Exception:
            health_status["grafana"] = False
        
        # Check Alertmanager
        try:
            response = requests.get(f"{self.alertmanager_url}/-/healthy")
            health_status["alertmanager"] = response.status_code == 200
        except Exception:
            health_status["alertmanager"] = False
        
        return health_status
    
    def setup_log_shipping(self) -> bool:
        """Set up log shipping from MCP services."""
        logger.info("Setting up log shipping...")
        
        try:
            # Create log shipping configuration
            log_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "handlers": {
                    "fluentd": {
                        "class": "fluent.handler.FluentHandler",
                        "level": "INFO",
                        "tag": "mcp",
                        "host": self.config.fluentd_host,
                        "port": self.config.fluentd_port,
                        "timeout": 3.0
                    }
                },
                "loggers": {
                    "": {
                        "level": "INFO",
                        "handlers": ["fluentd"],
                        "propagate": False
                    }
                }
            }
            
            # Save configuration
            config_path = Path("config/logging-shipper.yml")
            with open(config_path, 'w') as f:
                yaml.dump(log_config, f)
            
            logger.info("Log shipping configuration created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up log shipping: {e}")
            return False
    
    def setup_backup_and_recovery(self) -> bool:
        """Set up log backup and recovery procedures."""
        logger.info("Setting up backup and recovery...")
        
        try:
            # Create backup script
            backup_script = """#!/bin/bash
# MCP Log Backup Script

# Configuration
ELASTICSEARCH_HOST="localhost"
ELASTICSEARCH_PORT="9200"
BACKUP_DIR="/backups/mcp-logs"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Create snapshot repository
curl -X PUT "http://$ELASTICSEARCH_HOST:$ELASTICSEARCH_PORT/_snapshot/mcp_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "'$BACKUP_DIR'",
    "compress": true
  }
}'

# Create snapshot
SNAPSHOT_NAME="mcp_logs_$DATE"
curl -X PUT "http://$ELASTICSEARCH_HOST:$ELASTICSEARCH_PORT/_snapshot/mcp_backup/$SNAPSHOT_NAME?wait_for_completion=true"

# Clean old backups
find $BACKUP_DIR -name "mcp_logs_*" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $SNAPSHOT_NAME"
"""
            
            backup_script_path = Path("scripts/backup-logs.sh")
            with open(backup_script_path, 'w') as f:
                f.write(backup_script)
            
            # Make script executable
            backup_script_path.chmod(0o755)
            
            logger.info("Backup and recovery setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up backup and recovery: {e}")
            return False
    
    def setup_monitoring_and_alerting(self) -> bool:
        """Set up monitoring and alerting for the log pipeline."""
        logger.info("Setting up monitoring and alerting...")
        
        try:
            # Create monitoring configuration
            monitoring_config = {
                "log_level_monitoring": {
                    "enabled": True,
                    "thresholds": {
                        "error_rate": 10,
                        "warning_rate": 50,
                        "critical_rate": 1
                    }
                },
                "performance_monitoring": {
                    "enabled": True,
                    "thresholds": {
                        "response_time_p95": 5.0,
                        "memory_usage_percent": 90,
                        "cpu_usage_percent": 80
                    }
                },
                "security_monitoring": {
                    "enabled": True,
                    "thresholds": {
                        "failed_logins": 5,
                        "unauthorized_access": 3,
                        "security_events": 10
                    }
                },
                "compliance_monitoring": {
                    "enabled": True,
                    "thresholds": {
                        "compliance_violations": 1,
                        "audit_events": 100
                    }
                }
            }
            
            # Save configuration
            config_path = Path("config/log-monitoring.yml")
            with open(config_path, 'w') as f:
                yaml.dump(monitoring_config, f)
            
            logger.info("Monitoring and alerting setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up monitoring and alerting: {e}")
            return False
    
    def setup_security_and_compliance(self) -> bool:
        """Set up security and compliance features."""
        logger.info("Setting up security and compliance...")
        
        try:
            # Create security configuration
            security_config = {
                "log_encryption": {
                    "enabled": True,
                    "algorithm": "AES-256"
                },
                "access_control": {
                    "enabled": True,
                    "roles": {
                        "admin": ["read", "write", "delete"],
                        "analyst": ["read"],
                        "auditor": ["read", "audit"]
                    }
                },
                "compliance": {
                    "enabled": True,
                    "frameworks": ["GDPR", "HIPAA", "SOX", "PCI-DSS"],
                    "retention_policies": {
                        "general": 365,
                        "security": 1825,
                        "audit": 2555
                    }
                },
                "audit_trail": {
                    "enabled": True,
                    "log_all_access": True,
                    "log_data_modification": True
                }
            }
            
            # Save configuration
            config_path = Path("config/log-security.yml")
            with open(config_path, 'w') as f:
                yaml.dump(security_config, f)
            
            logger.info("Security and compliance setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up security and compliance: {e}")
            return False
    
    def initialize_pipeline(self) -> bool:
        """Initialize the complete log aggregation pipeline."""
        logger.info("Initializing log aggregation pipeline...")
        
        # Start services
        if not self.start_services():
            logger.error("Failed to start services")
            return False
        
        # Wait for services to be ready
        time.sleep(30)
        
        # Set up components
        setup_functions = [
            self.setup_elasticsearch,
            self.setup_kibana,
            self.setup_prometheus,
            self.setup_grafana,
            self.setup_fluentd,
            self.setup_alertmanager,
            self.setup_log_shipping,
            self.setup_backup_and_recovery,
            self.setup_monitoring_and_alerting,
            self.setup_security_and_compliance
        ]
        
        for setup_func in setup_functions:
            if not setup_func():
                logger.error(f"Failed to execute {setup_func.__name__}")
                return False
        
        logger.info("Log aggregation pipeline initialized successfully")
        return True
    
    def run_health_check(self) -> bool:
        """Run a health check on the pipeline."""
        logger.info("Running pipeline health check...")
        
        health_status = self.check_service_health()
        
        all_healthy = all(health_status.values())
        
        if all_healthy:
            logger.info("All services are healthy")
        else:
            logger.error("Some services are unhealthy:")
            for service, healthy in health_status.items():
                if not healthy:
                    logger.error(f"  - {service}: unhealthy")
        
        return all_healthy

def main():
    """Main function to run the log aggregation pipeline setup."""
    # Parse command line arguments
    if len(sys.argv) > 1:
        action = sys.argv[1]
    else:
        action = "init"
    
    # Create configuration
    config = LogAggregationConfig()
    
    # Create pipeline instance
    pipeline = LogAggregationPipeline(config)
    
    # Execute action
    if action == "init":
        success = pipeline.initialize_pipeline()
    elif action == "start":
        success = pipeline.start_services()
    elif action == "stop":
        success = pipeline.stop_services()
    elif action == "health":
        success = pipeline.run_health_check()
    else:
        logger.error(f"Unknown action: {action}")
        success = False
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()