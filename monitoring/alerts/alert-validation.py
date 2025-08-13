#!/usr/bin/env python3
"""
Alert Validation and Testing Utilities
Comprehensive tools for validating Prometheus alerting rules and testing alert functionality
"""

import yaml
import requests
import re
import sys
import argparse
import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from prometheus_client import CollectorRegistry, Gauge
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AlertValidator:
    """Validates Prometheus alerting rules for syntax and best practices"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        self.validation_results = []
        
    def validate_rule_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a single alert rule file"""
        try:
            with open(file_path, 'r') as f:
                rules = yaml.safe_load(f)
                
            results = {
                'file': file_path,
                'valid': True,
                'errors': [],
                'warnings': [],
                'rules_count': 0,
                'alerts_count': 0
            }
            
            if not isinstance(rules, dict) or 'groups' not in rules:
                results['valid'] = False
                results['errors'].append("Invalid rule file format: missing 'groups' key")
                return results
                
            for group in rules['groups']:
                if not isinstance(group, dict):
                    results['valid'] = False
                    results['errors'].append(f"Invalid group format in {file_path}")
                    continue
                    
                if 'name' not in group:
                    results['valid'] = False
                    results['errors'].append(f"Group missing 'name' in {file_path}")
                    continue
                    
                if 'rules' not in group:
                    results['valid'] = False
                    results['errors'].append(f"Group '{group['name']}' missing 'rules' in {file_path}")
                    continue
                    
                for rule in group['rules']:
                    results['rules_count'] += 1
                    
                    if 'alert' in rule:
                        results['alerts_count'] += 1
                        results.update(self._validate_alert_rule(rule, group['name'], file_path))
                    elif 'record' in rule:
                        results.update(self._validate_recording_rule(rule, group['name'], file_path))
                    else:
                        results['valid'] = False
                        results['errors'].append(f"Rule missing 'alert' or 'record' in {file_path}")
                        
            return results
            
        except Exception as e:
            logger.error(f"Error validating {file_path}: {str(e)}")
            return {
                'file': file_path,
                'valid': False,
                'errors': [f"Failed to parse file: {str(e)}"],
                'warnings': [],
                'rules_count': 0,
                'alerts_count': 0
            }
    
    def _validate_alert_rule(self, rule: Dict[str, Any], group_name: str, file_path: str) -> Dict[str, Any]:
        """Validate a single alert rule"""
        results = {'errors': [], 'warnings': []}
        
        # Check required fields
        required_fields = ['alert', 'expr']
        for field in required_fields:
            if field not in rule:
                results['valid'] = False
                results['errors'].append(f"Alert rule missing '{field}' in {file_path}")
                
        # Validate expression
        if 'expr' in rule:
            if not self._validate_prometheus_expression(rule['expr']):
                results['warnings'].append(f"Expression may be invalid: {rule['expr']}")
                
        # Validate severity
        if 'labels' in rule and 'severity' in rule['labels']:
            severity = rule['labels']['severity']
            if severity not in ['critical', 'warning', 'info']:
                results['warnings'].append(f"Invalid severity level: {severity}")
        else:
            results['warnings'].append("Alert missing severity label")
            
        # Validate annotations
        if 'annotations' not in rule:
            results['warnings'].append("Alert missing annotations")
        else:
            if 'summary' not in rule['annotations']:
                results['warnings'].append("Alert missing summary annotation")
            if 'description' not in rule['annotations']:
                results['warnings'].append("Alert missing description annotation")
            if 'runbook_url' not in rule['annotations']:
                results['warnings'].append("Alert missing runbook_url annotation")
                
        # Validate duration
        if 'for' in rule:
            try:
                duration_str = rule['for']
                if duration_str.endswith('s'):
                    int(duration_str[:-1])
                elif duration_str.endswith('m'):
                    int(duration_str[:-1])
                elif duration_str.endswith('h'):
                    int(duration_str[:-1])
                elif duration_str.endswith('d'):
                    int(duration_str[:-1])
                else:
                    results['warnings'].append(f"Invalid duration format: {duration_str}")
            except ValueError:
                results['warnings'].append(f"Invalid duration value: {rule['for']}")
                
        return results
    
    def _validate_recording_rule(self, rule: Dict[str, Any], group_name: str, file_path: str) -> Dict[str, Any]:
        """Validate a single recording rule"""
        results = {'errors': [], 'warnings': []}
        
        # Check required fields
        required_fields = ['record', 'expr']
        for field in required_fields:
            if field not in rule:
                results['valid'] = False
                results['errors'].append(f"Recording rule missing '{field}' in {file_path}")
                
        # Validate expression
        if 'expr' in rule:
            if not self._validate_prometheus_expression(rule['expr']):
                results['warnings'].append(f"Expression may be invalid: {rule['expr']}")
                
        return results
    
    def _validate_prometheus_expression(self, expr: str) -> bool:
        """Basic validation of Prometheus expression syntax"""
        try:
            # Check for basic syntax issues
            if not expr or not isinstance(expr, str):
                return False
                
            # Check for balanced parentheses
            if expr.count('(') != expr.count(')'):
                return False
                
            # Check for balanced brackets
            if expr.count('[') != expr.count(']'):
                return False
                
            # Check for balanced braces
            if expr.count('{') != expr.count('}'):
                return False
                
            # Basic pattern matching for common operators
            valid_operators = ['==', '!=', '>', '<', '>=', '<=', '=~', '!~']
            has_operator = any(op in expr for op in valid_operators)
            
            # If it's a comparison, it should have an operator
            if any(char in expr for char in ['>', '<', '=']):
                if not has_operator:
                    return False
                    
            return True
            
        except Exception:
            return False
    
    def validate_all_rules(self, rules_dir: str) -> Dict[str, Any]:
        """Validate all alert rule files in a directory"""
        rules_path = Path(rules_dir)
        if not rules_path.exists():
            logger.error(f"Rules directory does not exist: {rules_dir}")
            return {'valid': False, 'errors': [f"Directory not found: {rules_dir}"]}
            
        all_results = {
            'valid': True,
            'files_validated': 0,
            'total_rules': 0,
            'total_alerts': 0,
            'errors': [],
            'warnings': [],
            'file_results': []
        }
        
        for rule_file in rules_path.glob('**/*.yml'):
            if rule_file.name.startswith('.'):
                continue
                
            result = self.validate_rule_file(str(rule_file))
            all_results['files_validated'] += 1
            all_results['total_rules'] += result['rules_count']
            all_results['total_alerts'] += result['alerts_count']
            all_results['file_results'].append(result)
            
            if not result['valid']:
                all_results['valid'] = False
                
            all_results['errors'].extend(result['errors'])
            all_results['warnings'].extend(result['warnings'])
            
        return all_results

class AlertTester:
    """Tests alert functionality by simulating metrics and checking alert states"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        self.test_results = []
        
    def test_alert_expression(self, alert_name: str, expression: str, 
                            test_values: Dict[str, float]) -> Dict[str, Any]:
        """Test an alert expression with simulated values"""
        try:
            # Create test metrics
            registry = CollectorRegistry()
            
            # Create test metrics based on the expression
            for metric_name, value in test_values.items():
                gauge = Gauge(metric_name, f"Test metric for {metric_name}", registry=registry)
                gauge.set(value)
                
            # Query Prometheus with the test expression
            query_url = f"{self.prometheus_url}/api/v1/query"
            params = {
                'query': expression,
                'time': int(time.time())
            }
            
            response = requests.get(query_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'alert_name': alert_name,
                'expression': expression,
                'test_values': test_values,
                'should_fire': self._should_alert_fire(result),
                'result': result,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error testing alert {alert_name}: {str(e)}")
            return {
                'alert_name': alert_name,
                'expression': expression,
                'test_values': test_values,
                'success': False,
                'error': str(e)
            }
    
    def _should_alert_fire(self, query_result: Dict[str, Any]) -> bool:
        """Determine if an alert should fire based on query result"""
        try:
            if query_result['status'] != 'success':
                return False
                
            data = query_result['data']
            if not data.get('result'):
                return False
                
            for result in data['result']:
                value = result.get('value')
                if value and len(value) > 1:
                    # Convert string value to float
                    try:
                        float_value = float(value[1])
                        if float_value > 0:
                            return True
                    except (ValueError, IndexError):
                        continue
                        
            return False
            
        except Exception:
            return False
    
    def test_all_alerts(self, rules_dir: str) -> Dict[str, Any]:
        """Test all alerts in rule files"""
        validator = AlertValidator(self.prometheus_url)
        all_results = validator.validate_all_rules(rules_dir)
        
        test_results = {
            'alerts_tested': 0,
            'alerts_passed': 0,
            'alerts_failed': 0,
            'test_results': []
        }
        
        for file_result in all_results['file_results']:
            with open(file_result['file'], 'r') as f:
                rules = yaml.safe_load(f)
                
            for group in rules.get('groups', []):
                for rule in group.get('rules', []):
                    if 'alert' in rule:
                        test_result = self._test_single_alert(rule)
                        test_results['alerts_tested'] += 1
                        
                        if test_result['success']:
                            test_results['alerts_passed'] += 1
                        else:
                            test_results['alerts_failed'] += 1
                            
                        test_results['test_results'].append(test_result)
                        
        return test_results
    
    def _test_single_alert(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single alert rule"""
        alert_name = rule['alert']
        expression = rule['expr']
        
        # Generate test values based on the alert type
        test_values = self._generate_test_values(alert_name, expression)
        
        return self.test_alert_expression(alert_name, expression, test_values)
    
    def _generate_test_values(self, alert_name: str, expression: str) -> Dict[str, float]:
        """Generate test values for an alert based on its name and expression"""
        test_values = {}
        
        # Extract metric names from expression
        metric_names = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)', expression)
        
        # Generate test values based on alert name patterns
        if 'error' in alert_name.lower() or 'fail' in alert_name.lower():
            # For error alerts, generate values that should trigger the alert
            for metric in metric_names:
                if 'rate' in metric.lower():
                    test_values[metric] = 0.1  # 10% error rate
                elif 'count' in metric.lower():
                    test_values[metric] = 10.0  # 10 errors
                else:
                    test_values[metric] = 1.0   # Generic error condition
        elif 'high' in alert_name.lower() or 'critical' in alert_name.lower():
            # For high/critical alerts, generate high values
            for metric in metric_names:
                if 'cpu' in metric.lower():
                    test_values[metric] = 90.0  # 90% CPU usage
                elif 'memory' in metric.lower():
                    test_values[metric] = 85.0  # 85% memory usage
                elif 'latency' in metric.lower():
                    test_values[metric] = 5.0   # 5 seconds latency
                else:
                    test_values[metric] = 100.0 # Generic high value
        else:
            # For other alerts, generate moderate values
            for metric in metric_names:
                test_values[metric] = 50.0  # 50% generic value
                
        return test_values

class AlertHealthChecker:
    """Checks the health of the alerting system"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        
    def check_prometheus_health(self) -> Dict[str, Any]:
        """Check Prometheus health"""
        try:
            response = requests.get(f"{self.prometheus_url}/-/healthy")
            response.raise_for_status()
            
            return {
                'component': 'prometheus',
                'healthy': True,
                'status': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                'component': 'prometheus',
                'healthy': False,
                'error': str(e)
            }
    
    def check_alertmanager_health(self, alertmanager_url: str = "http://localhost:9093") -> Dict[str, Any]:
        """Check Alertmanager health"""
        try:
            response = requests.get(f"{alertmanager_url}/-/healthy")
            response.raise_for_status()
            
            return {
                'component': 'alertmanager',
                'healthy': True,
                'status': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                'component': 'alertmanager',
                'healthy': False,
                'error': str(e)
            }
    
    def check_alert_rules_health(self) -> Dict[str, Any]:
        """Check alert rules health"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/rules")
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'success':
                return {
                    'component': 'alert_rules',
                    'healthy': False,
                    'error': 'Failed to get rules'
                }
                
            rules = data['data'].get('groups', [])
            total_rules = 0
            unhealthy_rules = 0
            
            for group in rules:
                for rule in group['rules']:
                    total_rules += 1
                    if rule.get('health') != 'ok':
                        unhealthy_rules += 1
                        
            return {
                'component': 'alert_rules',
                'healthy': unhealthy_rules == 0,
                'total_rules': total_rules,
                'unhealthy_rules': unhealthy_rules,
                'health_percentage': ((total_rules - unhealthy_rules) / total_rules) * 100 if total_rules > 0 else 100
            }
            
        except Exception as e:
            return {
                'component': 'alert_rules',
                'healthy': False,
                'error': str(e)
            }
    
    def check_active_alerts(self) -> Dict[str, Any]:
        """Check currently active alerts"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/alerts")
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'success':
                return {
                    'component': 'active_alerts',
                    'healthy': False,
                    'error': 'Failed to get alerts'
                }
                
            alerts = data['data'].get('alerts', [])
            active_alerts = [alert for alert in alerts if alert.get('state') == 'firing']
            
            return {
                'component': 'active_alerts',
                'healthy': True,
                'total_alerts': len(alerts),
                'active_alerts': len(active_alerts),
                'active_alerts_list': active_alerts
            }
            
        except Exception as e:
            return {
                'component': 'active_alerts',
                'healthy': False,
                'error': str(e)
            }
    
    def run_full_health_check(self, alertmanager_url: str = "http://localhost:9093") -> Dict[str, Any]:
        """Run a full health check of the alerting system"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_healthy': True,
            'checks': []
        }
        
        checks = [
            self.check_prometheus_health(),
            self.check_alertmanager_health(alertmanager_url),
            self.check_alert_rules_health(),
            self.check_active_alerts()
        ]
        
        for check in checks:
            results['checks'].append(check)
            if not check['healthy']:
                results['overall_healthy'] = False
                
        return results

def main():
    parser = argparse.ArgumentParser(description='Alert Validation and Testing Utilities')
    parser.add_argument('--prometheus-url', default='http://localhost:9090', 
                       help='Prometheus URL')
    parser.add_argument('--alertmanager-url', default='http://localhost:9093',
                       help='Alertmanager URL')
    parser.add_argument('--rules-dir', default='./monitoring/alerts',
                       help='Directory containing alert rules')
    parser.add_argument('--action', choices=['validate', 'test', 'health-check', 'all'],
                       default='all', help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action in ['validate', 'all']:
        print("=== Validating Alert Rules ===")
        validator = AlertValidator(args.prometheus_url)
        results = validator.validate_all_rules(args.rules_dir)
        
        print(f"Files validated: {results['files_validated']}")
        print(f"Total rules: {results['total_rules']}")
        print(f"Total alerts: {results['total_alerts']}")
        print(f"Valid: {results['valid']}")
        
        if results['errors']:
            print("Errors:")
            for error in results['errors']:
                print(f"  - {error}")
                
        if results['warnings']:
            print("Warnings:")
            for warning in results['warnings']:
                print(f"  - {warning}")
    
    if args.action in ['test', 'all']:
        print("\n=== Testing Alert Rules ===")
        tester = AlertTester(args.prometheus_url)
        results = tester.test_all_alerts(args.rules_dir)
        
        print(f"Alerts tested: {results['alerts_tested']}")
        print(f"Alerts passed: {results['alerts_passed']}")
        print(f"Alerts failed: {results['alerts_failed']}")
        
        if results['alerts_failed'] > 0:
            print("Failed alerts:")
            for result in results['test_results']:
                if not result['success']:
                    print(f"  - {result['alert_name']}: {result.get('error', 'Unknown error')}")
    
    if args.action in ['health-check', 'all']:
        print("\n=== Health Check ===")
        health_checker = AlertHealthChecker(args.prometheus_url)
        results = health_checker.run_full_health_check(args.alertmanager_url)
        
        print(f"Overall healthy: {results['overall_healthy']}")
        print(f"Timestamp: {results['timestamp']}")
        
        for check in results['checks']:
            print(f"\n{check['component']}:")
            print(f"  Healthy: {check['healthy']}")
            if 'error' in check:
                print(f"  Error: {check['error']}")
            if 'total_rules' in check:
                print(f"  Total rules: {check['total_rules']}")
                print(f"  Unhealthy rules: {check['unhealthy_rules']}")
                print(f"  Health percentage: {check['health_percentage']:.1f}%")
            if 'active_alerts' in check:
                print(f"  Active alerts: {check['active_alerts']}")
    
    # Exit with appropriate code
    if args.action == 'all':
        # For 'all' action, exit with error if any check failed
        validator = AlertValidator(args.prometheus_url)
        validation_results = validator.validate_all_rules(args.rules_dir)
        
        tester = AlertTester(args.prometheus_url)
        test_results = tester.test_all_alerts(args.rules_dir)
        
        health_checker = AlertHealthChecker(args.prometheus_url)
        health_results = health_checker.run_full_health_check(args.alertmanager_url)
        
        if not validation_results['valid'] or test_results['alerts_failed'] > 0 or not health_results['overall_healthy']:
            sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main()