"""Consul service discovery utilities."""

import requests
from typing import Optional, Dict, Any, List
from .logging import get_logger

logger = get_logger("consul_client")


class ConsulClient:
    """Consul client for service discovery and configuration."""
    
    def __init__(self, consul_url: str = "http://localhost:8500"):
        self.consul_url = consul_url.rstrip('/')
        
    async def register_service(
        self,
        name: str,
        port: int,
        host: str = "0.0.0.0",
        health_check_path: str = "/health",
        tags: Optional[List[str]] = None,
        meta: Optional[Dict[str, str]] = None
    ) -> bool:
        """Register a service with Consul."""
        try:
            payload = {
                "Name": name,
                "ID": f"{name}-{port}",
                "Address": host,
                "Port": port,
                "Tags": tags or [],
                "Meta": meta or {},
                "Check": {
                    "HTTP": f"http://{host}:{port}{health_check_path}",
                    "Interval": "10s",
                    "Timeout": "5s"
                }
            }
            
            response = requests.put(
                f"{self.consul_url}/v1/agent/service/register",
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Successfully registered service {name} with Consul")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {name}: {e}")
            return False
    
    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service from Consul."""
        try:
            response = requests.put(
                f"{self.consul_url}/v1/agent/service/deregister/{service_id}",
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Successfully deregistered service {service_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deregister service {service_id}: {e}")
            return False
    
    async def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get service information from Consul."""
        try:
            response = requests.get(
                f"{self.consul_url}/v1/catalog/service/{service_name}",
                timeout=5
            )
            response.raise_for_status()
            services = response.json()
            return services[0] if services else None
            
        except Exception as e:
            logger.error(f"Failed to get service {service_name}: {e}")
            return None


def register_service(
    name: str, url: str, consul_url: str = "http://localhost:8500"
) -> None:
    """Register the service with Consul."""
    payload = {
        "Name": name,
        "Address": url,
        "Check": {"HTTP": f"{url}/health", "Interval": "10s"},
    }
    response = requests.put(
        f"{consul_url}/v1/agent/service/register", json=payload, timeout=5
    )
    response.raise_for_status()
