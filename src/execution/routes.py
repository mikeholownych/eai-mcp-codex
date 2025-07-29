"""API routes for fault-tolerant execution management."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from .fault_tolerant_executor import (
    fault_tolerant_executor, 
    CircuitBreakerConfig, 
    RetryConfig, 
    FaultDetectionConfig,
    RetryStrategy,
    ExecutionResult
)
from ..common.logging import get_logger
from ..plan_management.models import Plan, Task

router = APIRouter(prefix="/execution", tags=["fault-tolerant-execution"])
logger = get_logger("execution_routes")


class ExecutionRequest(BaseModel):
    """Request model for task execution."""
    task_id: str
    task_description: str
    task_type: str = "default"
    circuit_breaker_name: Optional[str] = None
    retry_config: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


class PlanExecutionRequest(BaseModel):
    """Request model for plan execution."""
    plan_id: str
    plan_title: str
    tasks: List[Dict[str, Any]]
    task_executors: Dict[str, str] = {}  # task_type -> executor_name mapping


class CircuitBreakerRequest(BaseModel):
    """Request model for circuit breaker configuration."""
    name: str
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3


class HealthCheckRequest(BaseModel):
    """Request model for health check registration."""
    service_name: str
    endpoint_url: Optional[str] = None
    check_interval: float = 10.0


@router.post("/execute/task", response_model=Dict[str, Any])
async def execute_task_with_fault_tolerance(request: ExecutionRequest) -> Dict[str, Any]:
    """Execute a single task with fault tolerance."""
    try:
        # Create task object
        task = Task(
            id=request.task_id,
            description=request.task_description,
            task_type=request.task_type
        )
        
        # Mock executor function for demonstration
        async def mock_executor(task: Task) -> str:
            """Mock task executor."""
            import random
            import asyncio
            
            # Simulate varying execution times
            await asyncio.sleep(random.uniform(0.1, 2.0))
            
            # Simulate occasional failures
            if random.random() < 0.1:  # 10% failure rate
                raise Exception("Simulated task execution failure")
            
            return f"Task {task.id} completed successfully"
        
        # Parse retry config if provided
        retry_config = None
        if request.retry_config:
            retry_config = RetryConfig(
                max_attempts=request.retry_config.get('max_attempts', 3),
                strategy=RetryStrategy(request.retry_config.get('strategy', 'exponential_backoff')),
                base_delay=request.retry_config.get('base_delay', 1.0),
                max_delay=request.retry_config.get('max_delay', 60.0)
            )
        
        # Execute task
        result = await fault_tolerant_executor.execute_task(
            task=task,
            executor_func=mock_executor,
            circuit_breaker_name=request.circuit_breaker_name,
            retry_config=retry_config
        )
        
        return {
            "execution_result": {
                "task_id": result.task_id,
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "attempts": result.attempts,
                "fault_type": result.fault_type.value if result.fault_type else None,
                "recovered": result.recovered,
                "metadata": result.metadata
            },
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@router.post("/execute/plan", response_model=Dict[str, Any])
async def execute_plan_with_fault_tolerance(request: PlanExecutionRequest) -> Dict[str, Any]:
    """Execute an entire plan with fault tolerance."""
    try:
        # Create plan object
        tasks = []
        for task_data in request.tasks:
            task = Task(
                id=task_data.get('id', str(len(tasks))),
                description=task_data.get('description', ''),
                task_type=task_data.get('task_type', 'default')
            )
            tasks.append(task)
        
        plan = Plan(
            id=request.plan_id,
            title=request.plan_title,
            tasks=tasks
        )
        
        # Mock task executors
        task_executors = {
            'default': lambda task: f"Executed {task.description}",
            'analysis': lambda task: f"Analyzed {task.description}",
            'implementation': lambda task: f"Implemented {task.description}",
            'testing': lambda task: f"Tested {task.description}"
        }
        
        # Execute plan
        results = await fault_tolerant_executor.execute_plan_with_fault_tolerance(
            plan=plan,
            task_executors=task_executors
        )
        
        # Convert results to serializable format
        execution_results = []
        for result in results:
            execution_results.append({
                "task_id": result.task_id,
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "attempts": result.attempts,
                "fault_type": result.fault_type.value if result.fault_type else None,
                "recovered": result.recovered,
                "metadata": result.metadata
            })
        
        success_count = sum(1 for r in results if r.success)
        
        return {
            "plan_id": request.plan_id,
            "execution_results": execution_results,
            "summary": {
                "total_tasks": len(results),
                "successful_tasks": success_count,
                "failed_tasks": len(results) - success_count,
                "recovered_tasks": sum(1 for r in results if r.recovered),
                "success_rate": round((success_count / len(results)) * 100, 2) if results else 0
            },
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Plan execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Plan execution failed: {str(e)}")


@router.post("/circuit-breaker/configure")
async def configure_circuit_breaker(request: CircuitBreakerRequest) -> Dict[str, Any]:
    """Configure a circuit breaker."""
    try:
        config = CircuitBreakerConfig(
            failure_threshold=request.failure_threshold,
            success_threshold=request.success_threshold,
            timeout_seconds=request.timeout_seconds,
            half_open_max_calls=request.half_open_max_calls
        )
        
        # Create or update circuit breaker
        circuit_breaker = fault_tolerant_executor.get_circuit_breaker(request.name, config)
        
        return {
            "circuit_breaker_name": request.name,
            "configuration": {
                "failure_threshold": config.failure_threshold,
                "success_threshold": config.success_threshold,
                "timeout_seconds": config.timeout_seconds,
                "half_open_max_calls": config.half_open_max_calls
            },
            "current_state": circuit_breaker.get_state(),
            "status": "configured"
        }
        
    except Exception as e:
        logger.error(f"Circuit breaker configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")


@router.get("/circuit-breaker/{name}/state", response_model=Dict[str, Any])
async def get_circuit_breaker_state(name: str) -> Dict[str, Any]:
    """Get current state of a circuit breaker."""
    try:
        if name not in fault_tolerant_executor.circuit_breakers:
            raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")
        
        circuit_breaker = fault_tolerant_executor.circuit_breakers[name]
        state = circuit_breaker.get_state()
        
        return {
            "circuit_breaker": state,
            "status": "retrieved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get circuit breaker state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get state: {str(e)}")


@router.post("/circuit-breaker/{name}/reset")
async def reset_circuit_breaker(name: str) -> Dict[str, Any]:
    """Reset a circuit breaker to closed state."""
    try:
        if name not in fault_tolerant_executor.circuit_breakers:
            raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")
        
        circuit_breaker = fault_tolerant_executor.circuit_breakers[name]
        circuit_breaker.state = CircuitState.CLOSED
        circuit_breaker.failure_count = 0
        circuit_breaker.success_count = 0
        circuit_breaker.last_failure_time = None
        
        logger.info(f"Reset circuit breaker {name}")
        
        return {
            "circuit_breaker_name": name,
            "new_state": circuit_breaker.get_state(),
            "status": "reset"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.get("/health-checks", response_model=Dict[str, Any])
async def perform_health_checks() -> Dict[str, Any]:
    """Perform health checks on all registered services."""
    try:
        health_results = await fault_tolerant_executor.perform_health_checks()
        
        healthy_services = sum(1 for status in health_results.values() if status)
        total_services = len(health_results)
        
        return {
            "health_results": health_results,
            "summary": {
                "healthy_services": healthy_services,
                "total_services": total_services,
                "overall_health": "healthy" if healthy_services == total_services else "degraded"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Health checks failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health checks failed: {str(e)}")


@router.post("/health-check/register")
async def register_health_check(request: HealthCheckRequest) -> Dict[str, Any]:
    """Register a health check for a service."""
    try:
        # Create a simple HTTP-based health check
        async def http_health_check() -> bool:
            if request.endpoint_url:
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(request.endpoint_url, timeout=5) as response:
                            return response.status == 200
                except:
                    return False
            return True  # Default to healthy if no endpoint specified
        
        fault_tolerant_executor.register_health_check(request.service_name, http_health_check)
        
        return {
            "service_name": request.service_name,
            "endpoint_url": request.endpoint_url,
            "check_interval": request.check_interval,
            "status": "registered"
        }
        
    except Exception as e:
        logger.error(f"Health check registration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.get("/statistics", response_model=Dict[str, Any])
async def get_execution_statistics() -> Dict[str, Any]:
    """Get comprehensive execution statistics."""
    try:
        stats = fault_tolerant_executor.get_execution_statistics()
        return {
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "retrieved"
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")


@router.post("/degradation/set")
async def set_service_degradation_level(service_name: str, level: int) -> Dict[str, Any]:
    """Set degradation level for a service."""
    try:
        if level < 0 or level > 5:
            raise HTTPException(status_code=400, detail="Degradation level must be between 0 and 5")
        
        fault_tolerant_executor.degradation_manager.set_degradation_level(service_name, level)
        
        return {
            "service_name": service_name,
            "degradation_level": level,
            "status": "set"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set degradation level: {e}")
        raise HTTPException(status_code=500, detail=f"Degradation setting failed: {str(e)}")


@router.get("/degradation/status", response_model=Dict[str, Any])
async def get_degradation_status() -> Dict[str, Any]:
    """Get current degradation status of all services."""
    try:
        status = fault_tolerant_executor.degradation_manager.get_degradation_status()
        return {
            "degradation_status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "retrieved"
        }
        
    except Exception as e:
        logger.error(f"Failed to get degradation status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.post("/monitoring/start")
async def start_health_monitoring(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start continuous health monitoring."""
    try:
        background_tasks.add_task(fault_tolerant_executor.start_health_monitoring)
        
        return {
            "monitoring": "started",
            "check_interval": fault_tolerant_executor.fault_detection_config.health_check_interval,
            "status": "initiated"
        }
        
    except Exception as e:
        logger.error(f"Failed to start health monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Monitoring start failed: {str(e)}")


@router.get("/execution/history", response_model=Dict[str, Any])
async def get_execution_history(limit: int = 100) -> Dict[str, Any]:
    """Get recent execution history."""
    try:
        history = fault_tolerant_executor.execution_history[-limit:]
        
        # Convert to serializable format
        execution_history = []
        for result in history:
            execution_history.append({
                "task_id": result.task_id,
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "attempts": result.attempts,
                "fault_type": result.fault_type.value if result.fault_type else None,
                "recovered": result.recovered,
                "metadata": result.metadata
            })
        
        return {
            "execution_history": execution_history,
            "total_records": len(execution_history),
            "limit_applied": limit,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "retrieved"
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution history: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


# Import fix for CircuitState
from .fault_tolerant_executor import CircuitState