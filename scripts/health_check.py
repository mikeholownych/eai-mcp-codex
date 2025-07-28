# scripts/health_check.py - Health Check Script
#!/usr/bin/env python3
import argparse
import sys
import requests
import time
import os
import psutil
import redis
import psycopg2
from typing import Dict, Any

def check_http_service(port: int, endpoint: str = "/health") -> Dict[str, Any]:
    """Check HTTP service health"""
    try:
        response = requests.get(f"http://localhost:{port}{endpoint}", timeout=5)
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "response_time": response.elapsed.total_seconds(),
            "status_code": response.status_code
        }
    except requests.RequestException as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def check_database() -> Dict[str, Any]:
    """Check PostgreSQL database health"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "mcp_database"),
            user=os.getenv("POSTGRES_USER", "mcp_user"),
            password=os.getenv("POSTGRES_PASSWORD", "")
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def check_redis() -> Dict[str, Any]:
    """Check Redis health"""
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            socket_connect_timeout=5
        )
        r.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage"""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

def main():
    parser = argparse.ArgumentParser(description="Health check for MCP services")
    parser.add_argument("--service", required=True, help="Service name to check")
    parser.add_argument("--port", type=int, help="Service port")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive health check")
    
    args = parser.parse_args()
    
    health_data = {
        "service": args.service,
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Service-specific health checks
    if args.port:
        health_data["checks"]["http"] = check_http_service(args.port)
    
    if args.comprehensive:
        health_data["checks"]["database"] = check_database()
        health_data["checks"]["redis"] = check_redis()
        health_data["checks"]["system"] = check_system_resources()
    
    # Determine overall health
    overall_healthy = all(
        check.get("status") == "healthy" 
        for check in health_data["checks"].values()
        if "status" in check
    )
    
    health_data["overall_status"] = "healthy" if overall_healthy else "unhealthy"
    
    # Output results
    if args.comprehensive:
        import json
        print(json.dumps(health_data, indent=2))
    else:
        print(health_data["overall_status"])
    
    # Exit with appropriate code
    sys.exit(0 if overall_healthy else 1)

if __name__ == "__main__":
    main()
