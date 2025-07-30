"""Fault-Tolerant Execution Patterns for Robust Workflow Management."""

import asyncio
import time
import random
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

from ..common.logging import get_logger
from ..plan_management.models import Task, Plan

logger = get_logger("fault_tolerant_executor")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class RetryStrategy(str, Enum):
    """Retry strategies."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


class FaultType(str, Enum):
    """Types of faults that can occur."""

    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNKNOWN = "unknown"


@dataclass
class ExecutionResult:
    """Result of task execution."""

    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    attempts: int = 1
    fault_type: Optional[FaultType] = None
    recovered: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3


@dataclass
class RetryConfig:
    """Retry configuration."""

    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


@dataclass
class FaultDetectionConfig:
    """Fault detection configuration."""

    timeout_seconds: float = 30.0
    health_check_interval: float = 10.0
    degraded_performance_threshold: float = 5.0
    error_rate_threshold: float = 0.1


class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN")
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise Exception(f"Circuit breaker {self.name} half-open limit reached")
            self.half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if not self.last_failure_time:
            return True

        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.timeout_seconds

    async def _on_success(self):
        """Handle successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker {self.name} moved to CLOSED")
        else:
            self.failure_count = 0

    async def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} moved to OPEN from HALF_OPEN")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} moved to OPEN")

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
        }


class RetryHandler:
    """Retry handler with various strategies."""

    def __init__(self, config: RetryConfig):
        self.config = config

    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                if attempt > 1:
                    logger.info(f"Operation succeeded on attempt {attempt}")
                return result
            except Exception as e:
                last_exception = e
                fault_type = self._classify_fault(e)

                if not self._should_retry(fault_type, attempt):
                    logger.error(f"Not retrying after attempt {attempt}: {fault_type}")
                    break

                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt} failed, retrying in {delay:.2f}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)

        raise last_exception

    def _classify_fault(self, exception: Exception) -> FaultType:
        """Classify the type of fault."""
        error_msg = str(exception).lower()

        if any(keyword in error_msg for keyword in ["timeout", "timed out"]):
            return FaultType.TIMEOUT
        elif any(keyword in error_msg for keyword in ["network", "connection", "dns"]):
            return FaultType.NETWORK_ERROR
        elif any(
            keyword in error_msg for keyword in ["rate limit", "too many requests"]
        ):
            return FaultType.RATE_LIMIT
        elif any(
            keyword in error_msg for keyword in ["unavailable", "503", "service down"]
        ):
            return FaultType.SERVICE_UNAVAILABLE
        elif any(
            keyword in error_msg for keyword in ["auth", "unauthorized", "401", "403"]
        ):
            return FaultType.AUTHENTICATION_ERROR
        elif any(
            keyword in error_msg for keyword in ["validation", "invalid", "bad request"]
        ):
            return FaultType.VALIDATION_ERROR
        else:
            return FaultType.UNKNOWN

    def _should_retry(self, fault_type: FaultType, attempt: int) -> bool:
        """Determine if the fault should be retried."""
        # Don't retry validation or authentication errors
        if fault_type in [FaultType.VALIDATION_ERROR, FaultType.AUTHENTICATION_ERROR]:
            return False

        return attempt < self.config.max_attempts

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt."""
        if self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (
                self.config.backoff_multiplier ** (attempt - 1)
            )
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt
        elif self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay
        else:  # IMMEDIATE
            delay = 0.0

        # Apply maximum delay limit
        delay = min(delay, self.config.max_delay)

        # Add jitter to prevent thundering herd
        if self.config.jitter and delay > 0:
            jitter = random.uniform(0.8, 1.2)
            delay *= jitter

        return delay


class GracefulDegradationManager:
    """Manages graceful degradation of services."""

    def __init__(self):
        self.degradation_levels: Dict[str, int] = {}
        self.fallback_strategies: Dict[str, Callable] = {}
        self.health_status: Dict[str, bool] = {}

    def register_fallback(self, service_name: str, fallback_func: Callable):
        """Register a fallback strategy for a service."""
        self.fallback_strategies[service_name] = fallback_func
        logger.info(f"Registered fallback strategy for {service_name}")

    def set_degradation_level(self, service_name: str, level: int):
        """Set degradation level for a service (0=normal, 1-5=degraded)."""
        self.degradation_levels[service_name] = level
        logger.info(f"Set degradation level for {service_name}: {level}")

    async def execute_with_degradation(
        self, service_name: str, primary_func: Callable, *args, **kwargs
    ) -> Any:
        """Execute with graceful degradation support."""
        degradation_level = self.degradation_levels.get(service_name, 0)

        if degradation_level == 0:
            try:
                return await primary_func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Primary function failed for {service_name}: {e}")
                # Auto-degrade on failure
                self.set_degradation_level(service_name, 1)
                return await self._execute_fallback(service_name, *args, **kwargs)
        else:
            logger.info(
                f"Using degraded mode for {service_name} (level {degradation_level})"
            )
            return await self._execute_fallback(service_name, *args, **kwargs)

    async def _execute_fallback(self, service_name: str, *args, **kwargs) -> Any:
        """Execute fallback strategy."""
        if service_name not in self.fallback_strategies:
            raise Exception(f"No fallback strategy registered for {service_name}")

        fallback_func = self.fallback_strategies[service_name]
        return await fallback_func(*args, **kwargs)

    def get_degradation_status(self) -> Dict[str, Any]:
        """Get current degradation status."""
        return {
            "degradation_levels": self.degradation_levels.copy(),
            "registered_fallbacks": list(self.fallback_strategies.keys()),
            "health_status": self.health_status.copy(),
        }


class FaultTolerantExecutor:
    """Main fault-tolerant execution engine."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_handler = RetryHandler(RetryConfig())
        self.degradation_manager = GracefulDegradationManager()
        self.execution_history: List[ExecutionResult] = []
        self.health_checks: Dict[str, Callable] = {}

        # Default configurations
        self.default_circuit_config = CircuitBreakerConfig()
        self.default_retry_config = RetryConfig()
        self.fault_detection_config = FaultDetectionConfig()

        # Statistics
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "recovered_executions": 0,
            "circuit_breaker_trips": 0,
        }

    def get_circuit_breaker(
        self, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if name not in self.circuit_breakers:
            cb_config = config or self.default_circuit_config
            self.circuit_breakers[name] = CircuitBreaker(name, cb_config)
        return self.circuit_breakers[name]

    async def execute_task(
        self,
        task: Task,
        executor_func: Callable,
        circuit_breaker_name: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> ExecutionResult:
        """Execute task with full fault tolerance."""
        start_time = time.time()
        task_id = task.id if hasattr(task, "id") else str(hash(task.description))

        logger.info(f"Executing task {task_id} with fault tolerance")

        try:
            # Use circuit breaker if specified
            if circuit_breaker_name:
                cb = self.get_circuit_breaker(circuit_breaker_name)
                result = await cb.call(
                    self._execute_with_retry, executor_func, task, retry_config
                )
            else:
                result = await self._execute_with_retry(
                    executor_func, task, retry_config
                )

            execution_time = time.time() - start_time

            execution_result = ExecutionResult(
                task_id=task_id,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"circuit_breaker": circuit_breaker_name},
            )

            self.execution_history.append(execution_result)
            self.execution_stats["total_executions"] += 1
            self.execution_stats["successful_executions"] += 1

            return execution_result

        except Exception as e:
            execution_time = time.time() - start_time
            fault_type = self._classify_fault(e)

            execution_result = ExecutionResult(
                task_id=task_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
                fault_type=fault_type,
                metadata={
                    "circuit_breaker": circuit_breaker_name,
                    "traceback": traceback.format_exc(),
                },
            )

            self.execution_history.append(execution_result)
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1

            logger.error(f"Task {task_id} execution failed: {e}")
            return execution_result

    async def _execute_with_retry(
        self,
        executor_func: Callable,
        task: Task,
        retry_config: Optional[RetryConfig] = None,
    ) -> Any:
        """Execute function with retry logic."""
        config = retry_config or self.default_retry_config
        retry_handler = RetryHandler(config)

        return await retry_handler.execute_with_retry(executor_func, task)

    def _classify_fault(self, exception: Exception) -> FaultType:
        """Classify the type of fault."""
        error_msg = str(exception).lower()

        if any(keyword in error_msg for keyword in ["timeout", "timed out"]):
            return FaultType.TIMEOUT
        elif any(keyword in error_msg for keyword in ["network", "connection", "dns"]):
            return FaultType.NETWORK_ERROR
        elif any(
            keyword in error_msg for keyword in ["rate limit", "too many requests"]
        ):
            return FaultType.RATE_LIMIT
        elif any(
            keyword in error_msg for keyword in ["unavailable", "503", "service down"]
        ):
            return FaultType.SERVICE_UNAVAILABLE
        elif any(
            keyword in error_msg for keyword in ["auth", "unauthorized", "401", "403"]
        ):
            return FaultType.AUTHENTICATION_ERROR
        elif any(
            keyword in error_msg for keyword in ["validation", "invalid", "bad request"]
        ):
            return FaultType.VALIDATION_ERROR
        else:
            return FaultType.UNKNOWN

    async def execute_plan_with_fault_tolerance(
        self, plan: Plan, task_executors: Dict[str, Callable]
    ) -> List[ExecutionResult]:
        """Execute entire plan with fault tolerance."""
        logger.info(f"Executing plan {plan.id} with fault tolerance")

        results = []
        failed_tasks = []

        for task in plan.tasks:
            task_type = getattr(task, "task_type", "default")
            executor_func = task_executors.get(task_type)

            if not executor_func:
                logger.error(f"No executor found for task type: {task_type}")
                result = ExecutionResult(
                    task_id=task.id,
                    success=False,
                    error=f"No executor for task type: {task_type}",
                    fault_type=FaultType.VALIDATION_ERROR,
                )
                results.append(result)
                failed_tasks.append(task)
                continue

            result = await self.execute_task(
                task, executor_func, circuit_breaker_name=f"task_{task_type}"
            )

            results.append(result)

            if not result.success:
                failed_tasks.append(task)

                # Implement failure handling strategy
                if await self._should_continue_on_failure(task, result, plan):
                    logger.warning(
                        f"Continuing plan execution despite task {task.id} failure"
                    )
                else:
                    logger.error(
                        f"Stopping plan execution due to critical task {task.id} failure"
                    )
                    break

        # Attempt recovery for failed tasks
        if failed_tasks:
            recovery_results = await self._attempt_task_recovery(
                failed_tasks, task_executors
            )
            results.extend(recovery_results)

        logger.info(
            f"Plan {plan.id} execution completed. Success: {sum(1 for r in results if r.success)}/{len(results)}"
        )
        return results

    async def _should_continue_on_failure(
        self, task: Task, result: ExecutionResult, plan: Plan
    ) -> bool:
        """Determine if execution should continue after task failure."""
        # Check if task is marked as critical
        if hasattr(task, "critical") and task.critical:
            return False

        # Check fault type
        if result.fault_type in [
            FaultType.VALIDATION_ERROR,
            FaultType.AUTHENTICATION_ERROR,
        ]:
            return False

        # Check failure rate
        recent_failures = [r for r in self.execution_history[-10:] if not r.success]
        if len(recent_failures) > 5:  # More than 50% failure rate in recent executions
            return False

        return True

    async def _attempt_task_recovery(
        self, failed_tasks: List[Task], task_executors: Dict[str, Callable]
    ) -> List[ExecutionResult]:
        """Attempt to recover failed tasks."""
        logger.info(f"Attempting recovery for {len(failed_tasks)} failed tasks")

        recovery_results = []

        for task in failed_tasks:
            try:
                # Wait before retry
                await asyncio.sleep(5.0)

                # Use more aggressive retry config for recovery
                recovery_config = RetryConfig(
                    max_attempts=5,
                    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                    base_delay=2.0,
                    max_delay=30.0,
                )

                task_type = getattr(task, "task_type", "default")
                executor_func = task_executors.get(task_type)

                if executor_func:
                    result = await self.execute_task(
                        task, executor_func, retry_config=recovery_config
                    )

                    if result.success:
                        result.recovered = True
                        self.execution_stats["recovered_executions"] += 1
                        logger.info(f"Successfully recovered task {task.id}")

                    recovery_results.append(result)

            except Exception as e:
                logger.error(f"Recovery failed for task {task.id}: {e}")

        return recovery_results

    def register_health_check(self, service_name: str, health_check_func: Callable):
        """Register health check for a service."""
        self.health_checks[service_name] = health_check_func
        logger.info(f"Registered health check for {service_name}")

    async def perform_health_checks(self) -> Dict[str, bool]:
        """Perform health checks on all registered services."""
        health_results = {}

        for service_name, health_check_func in self.health_checks.items():
            try:
                is_healthy = await health_check_func()
                health_results[service_name] = is_healthy

                if not is_healthy:
                    logger.warning(f"Health check failed for {service_name}")
                    # Auto-degrade service
                    self.degradation_manager.set_degradation_level(service_name, 1)

            except Exception as e:
                logger.error(f"Health check error for {service_name}: {e}")
                health_results[service_name] = False
                self.degradation_manager.set_degradation_level(service_name, 2)

        return health_results

    async def start_health_monitoring(self):
        """Start continuous health monitoring."""
        logger.info("Starting continuous health monitoring")

        while True:
            try:
                await self.perform_health_checks()
                await asyncio.sleep(self.fault_detection_config.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)  # Longer delay on error

    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get comprehensive execution statistics."""
        total = self.execution_stats["total_executions"]
        success_rate = (
            (self.execution_stats["successful_executions"] / total * 100)
            if total > 0
            else 0
        )
        recovery_rate = (
            self.execution_stats["recovered_executions"]
            / max(self.execution_stats["failed_executions"], 1)
            * 100
        )

        # Fault type distribution
        fault_distribution = {}
        for result in self.execution_history:
            if result.fault_type:
                fault_distribution[result.fault_type.value] = (
                    fault_distribution.get(result.fault_type.value, 0) + 1
                )

        # Circuit breaker states
        circuit_states = {
            name: cb.get_state() for name, cb in self.circuit_breakers.items()
        }

        return {
            "execution_stats": self.execution_stats.copy(),
            "success_rate": round(success_rate, 2),
            "recovery_rate": round(recovery_rate, 2),
            "fault_distribution": fault_distribution,
            "circuit_breakers": circuit_states,
            "degradation_status": self.degradation_manager.get_degradation_status(),
            "total_circuit_breakers": len(self.circuit_breakers),
            "recent_executions": len(
                [
                    r
                    for r in self.execution_history
                    if datetime.utcnow()
                    - datetime.fromisoformat(
                        r.metadata.get("timestamp", "2024-01-01T00:00:00")
                    )
                    < timedelta(hours=1)
                ]
            ),
        }

    @asynccontextmanager
    async def fault_tolerant_context(self, service_name: str):
        """Context manager for fault-tolerant operations."""
        circuit_breaker = self.get_circuit_breaker(service_name)

        try:
            if circuit_breaker.state == CircuitState.OPEN:
                raise Exception(f"Service {service_name} circuit breaker is OPEN")

            yield circuit_breaker

        except Exception as e:
            logger.error(f"Fault in service {service_name}: {e}")
            await circuit_breaker._on_failure()
            raise
        else:
            await circuit_breaker._on_success()


# Example usage and default fallback strategies
async def default_model_fallback(*args, **kwargs) -> str:
    """Default fallback for model routing failures."""
    return "Service temporarily unavailable. Please try again later."


async def default_database_fallback(*args, **kwargs) -> Dict[str, Any]:
    """Default fallback for database failures."""
    return {"status": "degraded", "message": "Using cached data"}


async def default_health_check() -> bool:
    """Default health check implementation."""
    return True


# Initialize global fault-tolerant executor
fault_tolerant_executor = FaultTolerantExecutor()

# Register default fallback strategies
fault_tolerant_executor.degradation_manager.register_fallback(
    "model_router", default_model_fallback
)
fault_tolerant_executor.degradation_manager.register_fallback(
    "database", default_database_fallback
)
fault_tolerant_executor.register_health_check("default", default_health_check)
