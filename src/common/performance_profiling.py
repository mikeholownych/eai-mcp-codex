"""
Performance profiling and analysis component for MCP services.
Provides CPU and memory profiling, database query monitoring, external API tracking, and business transaction monitoring.
"""

import logging
import time
import psutil
import tracemalloc
import cProfile
import pstats
import io
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics

from opentelemetry.trace import Status, StatusCode

from src.common.apm import (
    APMOperationType, 
    APMConfig, 
    get_apm
)
from src.common.tracing import get_tracing_config

logger = logging.getLogger(__name__)


class ProfilingType(Enum):
    """Types of profiling available."""
    CPU = "cpu"
    MEMORY = "memory"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    BUSINESS_TRANSACTION = "business_transaction"


@dataclass
class CPUProfile:
    """CPU profiling data."""
    profile_id: str
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    cpu_percent: float
    memory_percent: float
    thread_count: int
    process_id: int
    profile_stats: Dict[str, Any] = field(default_factory=dict)
    top_functions: List[Dict[str, Any]] = field(default_factory=list)
    call_count: int = 0
    total_time: float = 0.0
    cumulative_time: float = 0.0


@dataclass
class MemoryProfile:
    """Memory profiling data."""
    profile_id: str
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_usage_start: float  # MB
    memory_usage_end: float  # MB
    memory_usage_peak: float  # MB
    memory_delta: float  # MB
    memory_traces: List[Dict[str, Any]] = field(default_factory=list)
    top_allocations: List[Dict[str, Any]] = field(default_factory=list)
    allocation_count: int = 0
    allocation_size: float = 0.0  # MB


@dataclass
class DatabaseQueryProfile:
    """Database query profiling data."""
    query_id: str
    operation_name: str
    query_type: str
    query_text: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    rows_affected: int = 0
    rows_returned: int = 0
    connection_id: str = ""
    database: str = ""
    table: str = ""
    index_used: str = ""
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class ExternalAPIProfile:
    """External API call profiling data."""
    call_id: str
    operation_name: str
    service_name: str
    endpoint: str
    method: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    status_code: int = 0
    request_size: int = 0
    response_size: int = 0
    retry_count: int = 0
    timeout: float = 0.0
    error_message: Optional[str] = None
    response_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class BusinessTransactionProfile:
    """Business transaction profiling data."""
    transaction_id: str
    transaction_name: str
    transaction_type: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    steps: List[Dict[str, Any]] = field(default_factory=list)
    resources_used: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class PerformanceProfiler:
    """Performance profiler for MCP services."""
    
    def __init__(self, config: APMConfig = None):
        """Initialize performance profiler."""
        self.config = config or APMConfig()
        self.apm = get_apm()
        self.tracer = get_tracing_config().get_tracer()
        self.meter = get_tracing_config().get_meter()
        
        # Profiling data storage
        self.cpu_profiles = deque(maxlen=1000)
        self.memory_profiles = deque(maxlen=1000)
        self.database_query_profiles = deque(maxlen=5000)
        self.external_api_profiles = deque(maxlen=5000)
        self.business_transaction_profiles = deque(maxlen=1000)
        
        # Profiling state
        self.is_cpu_profiling = False
        self.is_memory_profiling = False
        self.cpu_profiler = None
        self.memory_profiler = None
        
        # Performance thresholds
        self.slow_query_threshold = 1.0  # seconds
        self.slow_api_threshold = 5.0  # seconds
        self.high_memory_threshold = 100.0  # MB
        self.high_cpu_threshold = 80.0  # percent
        
        # Initialize metrics
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize OpenTelemetry metrics for performance profiling."""
        # Counters
        self.profiling_operations_counter = self.meter.create_counter(
            "performance_profiling_operations_total",
            description="Total number of profiling operations"
        )
        
        self.database_query_counter = self.meter.create_counter(
            "performance_profiling_database_queries_total",
            description="Total number of database queries profiled"
        )
        
        self.external_api_counter = self.meter.create_counter(
            "performance_profiling_external_api_calls_total",
            description="Total number of external API calls profiled"
        )
        
        self.business_transaction_counter = self.meter.create_counter(
            "performance_profiling_business_transactions_total",
            description="Total number of business transactions profiled"
        )
        
        # Histograms
        self.cpu_usage_histogram = self.meter.create_histogram(
            "performance_profiling_cpu_usage_percent",
            description="CPU usage percentage during profiling"
        )
        
        self.memory_usage_histogram = self.meter.create_histogram(
            "performance_profiling_memory_usage_mb",
            description="Memory usage in MB during profiling"
        )
        
        self.query_duration_histogram = self.meter.create_histogram(
            "performance_profiling_query_duration_seconds",
            description="Duration of database queries"
        )
        
        self.api_duration_histogram = self.meter.create_histogram(
            "performance_profiling_api_duration_seconds",
            description="Duration of external API calls"
        )
        
        self.transaction_duration_histogram = self.meter.create_histogram(
            "performance_profiling_transaction_duration_seconds",
            description="Duration of business transactions"
        )
        
        # Gauges
        self.active_profiles_gauge = self.meter.create_up_down_counter(
            "performance_profiling_active_profiles",
            description="Number of currently active profiling sessions"
        )
        
        self.memory_usage_gauge = self.meter.create_up_down_counter(
            "performance_profiling_memory_usage_mb",
            description="Current memory usage in MB"
        )
        
        self.cpu_usage_gauge = self.meter.create_up_down_counter(
            "performance_profiling_cpu_usage_percent",
            description="Current CPU usage percentage"
        )
    
    @contextmanager
    def profile_cpu(self, operation_name: str, enable_stats: bool = True):
        """Context manager for CPU profiling."""
        profile_id = f"cpu_{operation_name}_{int(time.time())}"
        start_time = time.time()
        
        # Get initial system metrics
        process = psutil.Process()
        initial_cpu = process.cpu_percent()
        initial_memory = process.memory_percent()
        initial_threads = process.num_threads()
        
        # Start CPU profiling
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            yield profiler
        finally:
            # Stop CPU profiling
            profiler.disable()
            end_time = time.time()
            duration = end_time - start_time
            
            # Get final system metrics
            final_cpu = process.cpu_percent()
            final_memory = process.memory_percent()
            
            # Process profiling stats
            profile_stats = {}
            top_functions = []
            
            if enable_stats:
                # Get profiling statistics
                stats_stream = io.StringIO()
                stats = pstats.Stats(profiler, stream=stats_stream)
                stats.sort_stats('cumulative')
                stats.print_stats(20)  # Top 20 functions
                
                # Parse stats
                stats_text = stats_stream.getvalue()
                profile_stats = self._parse_profile_stats(stats_text)
                top_functions = self._extract_top_functions(stats)
            
            # Create CPU profile
            cpu_profile = CPUProfile(
                profile_id=profile_id,
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                cpu_percent=final_cpu,
                memory_percent=final_memory,
                thread_count=initial_threads,
                process_id=process.pid,
                profile_stats=profile_stats,
                top_functions=top_functions
            )
            
            self.cpu_profiles.append(cpu_profile)
            
            # Update metrics
            self.profiling_operations_counter.add(1, {
                "profiling_type": "cpu",
                "operation_name": operation_name
            })
            
            self.cpu_usage_histogram.record(final_cpu, {
                "operation_name": operation_name
            })
            
            self.memory_usage_histogram.record(final_memory, {
                "operation_name": operation_name
            })
    
    @contextmanager
    def profile_memory(self, operation_name: str, enable_tracing: bool = True):
        """Context manager for memory profiling."""
        profile_id = f"memory_{operation_name}_{int(time.time())}"
        start_time = time.time()
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Start memory tracing
        if enable_tracing:
            tracemalloc.start()
        
        try:
            yield
        finally:
            # Stop memory tracing
            end_time = time.time()
            duration = end_time - start_time
            
            # Get final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = final_memory - initial_memory
            
            # Get memory traces
            memory_traces = []
            top_allocations = []
            
            if enable_tracing:
                # Get current memory usage and peak
                current, peak = tracemalloc.get_traced_memory()
                
                # Get top memory allocations
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')
                
                for stat in top_stats[:10]:  # Top 10 allocations
                    top_allocations.append({
                        "file": stat.traceback.format()[-1] if stat.traceback.format() else "unknown",
                        "line": stat.traceback.format()[0].split(":")[1] if stat.traceback.format() else "0",
                        "size": stat.size / 1024 / 1024,  # MB
                        "count": stat.count
                    })
                
                tracemalloc.stop()
            
            # Create memory profile
            memory_profile = MemoryProfile(
                profile_id=profile_id,
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                memory_usage_start=initial_memory,
                memory_usage_end=final_memory,
                memory_usage_peak=peak / 1024 / 1024 if enable_tracing else final_memory,
                memory_delta=memory_delta,
                memory_traces=memory_traces,
                top_allocations=top_allocations
            )
            
            self.memory_profiles.append(memory_profile)
            
            # Update metrics
            self.profiling_operations_counter.add(1, {
                "profiling_type": "memory",
                "operation_name": operation_name
            })
            
            self.memory_usage_histogram.record(final_memory, {
                "operation_name": operation_name
            })
            
            self.memory_usage_gauge.add(final_memory, {
                "operation_name": operation_name
            })
    
    @asynccontextmanager
    async def profile_database_query(self, operation_name: str, query_type: str, query_text: str,
                                   database: str = "", table: str = ""):
        """Context manager for database query profiling."""
        query_id = f"db_{operation_name}_{int(time.time())}"
        start_time = time.time()
        success = True
        error_message = None
        rows_affected = 0
        rows_returned = 0
        connection_id = ""
        index_used = ""
        execution_plan = {}
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.DATABASE, {"query_type": query_type}
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Create database query profile
                query_profile = DatabaseQueryProfile(
                    query_id=query_id,
                    operation_name=operation_name,
                    query_type=query_type,
                    query_text=query_text,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    success=success,
                    rows_affected=rows_affected,
                    rows_returned=rows_returned,
                    connection_id=connection_id,
                    database=database,
                    table=table,
                    index_used=index_used,
                    execution_plan=execution_plan,
                    error_message=error_message
                )
                
                self.database_query_profiles.append(query_profile)
                
                # Update metrics
                self.database_query_counter.add(1, {
                    "query_type": query_type,
                    "success": success
                })
                
                self.query_duration_histogram.record(duration, {
                    "query_type": query_type,
                    "database": database
                })
    
    @asynccontextmanager
    async def profile_external_api(self, operation_name: str, service_name: str, endpoint: str,
                                 method: str, timeout: float = 30.0):
        """Context manager for external API call profiling."""
        call_id = f"api_{operation_name}_{int(time.time())}"
        start_time = time.time()
        success = True
        error_message = None
        status_code = 0
        request_size = 0
        response_size = 0
        retry_count = 0
        response_headers = {}
        
        async with self.apm.trace_async_operation(
            operation_name, APMOperationType.EXTERNAL_API, {
                "service_name": service_name,
                "endpoint": endpoint,
                "method": method
            }
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Create external API profile
                api_profile = ExternalAPIProfile(
                    call_id=call_id,
                    operation_name=operation_name,
                    service_name=service_name,
                    endpoint=endpoint,
                    method=method,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    success=success,
                    status_code=status_code,
                    request_size=request_size,
                    response_size=response_size,
                    retry_count=retry_count,
                    timeout=timeout,
                    error_message=error_message,
                    response_headers=response_headers
                )
                
                self.external_api_profiles.append(api_profile)
                
                # Update metrics
                self.external_api_counter.add(1, {
                    "service_name": service_name,
                    "method": method,
                    "success": success
                })
                
                self.api_duration_histogram.record(duration, {
                    "service_name": service_name,
                    "method": method
                })
    
    @asynccontextmanager
    async def profile_business_transaction(self, transaction_name: str, transaction_type: str):
        """Context manager for business transaction profiling."""
        transaction_id = f"tx_{transaction_name}_{int(time.time())}"
        start_time = time.time()
        success = True
        error_message = None
        steps = []
        resources_used = {}
        performance_metrics = {}
        
        async with self.apm.trace_async_operation(
            transaction_name, APMOperationType.BUSINESS_TRANSACTION, {
                "transaction_type": transaction_type
            }
        ) as span:
            try:
                yield span
            except Exception as e:
                success = False
                error_message = str(e)
                span.set_status(Status(StatusCode.ERROR, error_message))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration = end_time - start_time
                
                # Create business transaction profile
                transaction_profile = BusinessTransactionProfile(
                    transaction_id=transaction_id,
                    transaction_name=transaction_name,
                    transaction_type=transaction_type,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    success=success,
                    steps=steps,
                    resources_used=resources_used,
                    performance_metrics=performance_metrics,
                    error_message=error_message
                )
                
                self.business_transaction_profiles.append(transaction_profile)
                
                # Update metrics
                self.business_transaction_counter.add(1, {
                    "transaction_type": transaction_type,
                    "success": success
                })
                
                self.transaction_duration_histogram.record(duration, {
                    "transaction_type": transaction_type
                })
    
    def _parse_profile_stats(self, stats_text: str) -> Dict[str, Any]:
        """Parse cProfile stats text into structured data."""
        lines = stats_text.split('\n')
        stats_data = {}
        
        for line in lines:
            if 'function calls' in line:
                parts = line.split()
                if len(parts) >= 4:
                    stats_data['function_calls'] = int(parts[0])
                    stats_data['primitive_calls'] = int(parts[1])
                    stats_data['total_calls'] = int(parts[2])
                    stats_data['total_time'] = float(parts[4])
        
        return stats_data
    
    def _extract_top_functions(self, stats_text: str) -> List[Dict[str, Any]]:
        """Extract top functions from cProfile stats."""
        lines = stats_text.split('\n')
        top_functions = []
        
        for line in lines:
            if line.strip() and not line.startswith('ncalls') and not line.startswith('function calls'):
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        ncalls = parts[0]
                        tottime = float(parts[1])
                        cumtime = float(parts[3])
                        function_name = ' '.join(parts[5:])
                        
                        top_functions.append({
                            "ncalls": ncalls,
                            "tottime": tottime,
                            "cumtime": cumtime,
                            "function": function_name
                        })
                    except (ValueError, IndexError):
                        continue
        
        return top_functions[:10]  # Return top 10
    
    def get_cpu_profile_summary(self, operation_name: str = None) -> Dict[str, Any]:
        """Get CPU profile summary."""
        profiles = list(self.cpu_profiles)
        if operation_name:
            profiles = [p for p in profiles if p.operation_name == operation_name]
        
        if not profiles:
            return {"message": "No CPU profiles available"}
        
        # Calculate statistics
        durations = [p.duration for p in profiles]
        cpu_usage = [p.cpu_percent for p in profiles]
        memory_usage = [p.memory_percent for p in profiles]
        
        return {
            "total_profiles": len(profiles),
            "average_duration": statistics.mean(durations),
            "max_duration": max(durations),
            "min_duration": min(durations),
            "average_cpu_usage": statistics.mean(cpu_usage),
            "max_cpu_usage": max(cpu_usage),
            "average_memory_usage": statistics.mean(memory_usage),
            "max_memory_usage": max(memory_usage),
            "top_functions": self._get_top_functions_summary(profiles)
        }
    
    def get_memory_profile_summary(self, operation_name: str = None) -> Dict[str, Any]:
        """Get memory profile summary."""
        profiles = list(self.memory_profiles)
        if operation_name:
            profiles = [p for p in profiles if p.operation_name == operation_name]
        
        if not profiles:
            return {"message": "No memory profiles available"}
        
        # Calculate statistics
        durations = [p.duration for p in profiles]
        memory_start = [p.memory_usage_start for p in profiles]
        memory_end = [p.memory_usage_end for p in profiles]
        memory_delta = [p.memory_delta for p in profiles]
        memory_peak = [p.memory_usage_peak for p in profiles]
        
        return {
            "total_profiles": len(profiles),
            "average_duration": statistics.mean(durations),
            "max_duration": max(durations),
            "average_memory_start": statistics.mean(memory_start),
            "average_memory_end": statistics.mean(memory_end),
            "average_memory_delta": statistics.mean(memory_delta),
            "max_memory_peak": max(memory_peak),
            "total_memory_allocated": sum(p.allocation_size for p in profiles),
            "total_allocations": sum(p.allocation_count for p in profiles)
        }
    
    def get_database_query_summary(self, query_type: str = None) -> Dict[str, Any]:
        """Get database query summary."""
        queries = list(self.database_query_profiles)
        if query_type:
            queries = [q for q in queries if q.query_type == query_type]
        
        if not queries:
            return {"message": "No database queries profiled"}
        
        # Calculate statistics
        durations = [q.duration for q in queries]
        successful_queries = [q for q in queries if q.success]
        failed_queries = [q for q in queries if not q.success]
        
        return {
            "total_queries": len(queries),
            "successful_queries": len(successful_queries),
            "failed_queries": len(failed_queries),
            "success_rate": len(successful_queries) / len(queries) if queries else 0,
            "average_duration": statistics.mean(durations),
            "max_duration": max(durations),
            "min_duration": min(durations),
            "slow_queries": len([q for q in queries if q.duration > self.slow_query_threshold]),
            "average_rows_affected": statistics.mean([q.rows_affected for q in queries]),
            "average_rows_returned": statistics.mean([q.rows_returned for q in queries])
        }
    
    def get_external_api_summary(self, service_name: str = None) -> Dict[str, Any]:
        """Get external API summary."""
        calls = list(self.external_api_profiles)
        if service_name:
            calls = [c for c in calls if c.service_name == service_name]
        
        if not calls:
            return {"message": "No external API calls profiled"}
        
        # Calculate statistics
        durations = [c.duration for c in calls]
        successful_calls = [c for c in calls if c.success]
        failed_calls = [c for c in calls if not c.success]
        
        return {
            "total_calls": len(calls),
            "successful_calls": len(successful_calls),
            "failed_calls": len(failed_calls),
            "success_rate": len(successful_calls) / len(calls) if calls else 0,
            "average_duration": statistics.mean(durations),
            "max_duration": max(durations),
            "min_duration": min(durations),
            "slow_calls": len([c for c in calls if c.duration > self.slow_api_threshold]),
            "average_request_size": statistics.mean([c.request_size for c in calls]),
            "average_response_size": statistics.mean([c.response_size for c in calls]),
            "average_retry_count": statistics.mean([c.retry_count for c in calls])
        }
    
    def get_business_transaction_summary(self, transaction_type: str = None) -> Dict[str, Any]:
        """Get business transaction summary."""
        transactions = list(self.business_transaction_profiles)
        if transaction_type:
            transactions = [t for t in transactions if t.transaction_type == transaction_type]
        
        if not transactions:
            return {"message": "No business transactions profiled"}
        
        # Calculate statistics
        durations = [t.duration for t in transactions]
        successful_transactions = [t for t in transactions if t.success]
        failed_transactions = [t for t in transactions if not t.success]
        
        return {
            "total_transactions": len(transactions),
            "successful_transactions": len(successful_transactions),
            "failed_transactions": len(failed_transactions),
            "success_rate": len(successful_transactions) / len(transactions) if transactions else 0,
            "average_duration": statistics.mean(durations),
            "max_duration": max(durations),
            "min_duration": min(durations),
            "average_steps": statistics.mean([len(t.steps) for t in transactions])
        }
    
    def _get_top_functions_summary(self, profiles: List[CPUProfile]) -> List[Dict[str, Any]]:
        """Get summary of top functions across profiles."""
        function_stats = defaultdict(lambda: {"count": 0, "total_time": 0, "max_time": 0})
        
        for profile in profiles:
            for func in profile.top_functions:
                func_name = func["function"]
                function_stats[func_name]["count"] += 1
                function_stats[func_name]["total_time"] += func["cumtime"]
                function_stats[func_name]["max_time"] = max(function_stats[func_name]["max_time"], func["cumtime"])
        
        # Sort by total time
        sorted_functions = sorted(function_stats.items(), key=lambda x: x[1]["total_time"], reverse=True)
        
        return [
            {
                "function": func_name,
                "count": stats["count"],
                "total_time": stats["total_time"],
                "max_time": stats["max_time"],
                "average_time": stats["total_time"] / stats["count"]
            }
            for func_name, stats in sorted_functions[:10]
        ]
    
    def get_performance_insights(self) -> List[Dict[str, Any]]:
        """Get performance insights and recommendations."""
        insights = []
        
        # Analyze CPU profiles
        if self.cpu_profiles:
            recent_cpu = list(self.cpu_profiles)[-100:]  # Last 100 CPU profiles
            
            # Check for high CPU usage
            high_cpu_profiles = [p for p in recent_cpu if p.cpu_percent > self.high_cpu_threshold]
            if len(high_cpu_profiles) > 10:
                insights.append({
                    "type": "high_cpu_usage",
                    "severity": "warning",
                    "message": f"High CPU usage detected in {len(high_cpu_profiles)} recent operations",
                    "recommendation": "Optimize CPU-intensive operations or consider scaling"
                })
            
            # Check for slow operations
            slow_operations = [p for p in recent_cpu if p.duration > 10.0]  # 10 seconds
            if len(slow_operations) > 5:
                insights.append({
                    "type": "slow_operations",
                    "severity": "warning",
                    "message": f"Slow operations detected in {len(slow_operations)} recent CPU profiles",
                    "recommendation": "Review and optimize slow-performing functions"
                })
        
        # Analyze memory profiles
        if self.memory_profiles:
            recent_memory = list(self.memory_profiles)[-100:]  # Last 100 memory profiles
            
            # Check for high memory usage
            high_memory_profiles = [p for p in recent_memory if p.memory_usage_peak > self.high_memory_threshold]
            if len(high_memory_profiles) > 10:
                insights.append({
                    "type": "high_memory_usage",
                    "severity": "warning",
                    "message": f"High memory usage detected in {len(high_memory_profiles)} recent operations",
                    "recommendation": "Optimize memory usage or increase available memory"
                })
            
            # Check for memory leaks
            memory_leak_candidates = [p for p in recent_memory if p.memory_delta > 50.0]  # 50MB increase
            if len(memory_leak_candidates) > 5:
                insights.append({
                    "type": "potential_memory_leak",
                    "severity": "error",
                    "message": f"Potential memory leaks detected in {len(memory_leak_candidates)} recent operations",
                    "recommendation": "Review memory allocation patterns and implement proper cleanup"
                })
        
        # Analyze database queries
        if self.database_query_profiles:
            recent_queries = list(self.database_query_profiles)[-1000:]  # Last 1000 queries
            
            # Check for slow queries
            slow_queries = [q for q in recent_queries if q.duration > self.slow_query_threshold]
            if len(slow_queries) > 50:
                insights.append({
                    "type": "slow_database_queries",
                    "severity": "warning",
                    "message": f"Slow database queries detected ({len(slow_queries)} in last 1000)",
                    "recommendation": "Optimize query performance or add database indexes"
                })
            
            # Check for failed queries
            failed_queries = [q for q in recent_queries if not q.success]
            if len(failed_queries) > 10:
                insights.append({
                    "type": "failed_database_queries",
                    "severity": "error",
                    "message": f"Failed database queries detected ({len(failed_queries)} in last 1000)",
                    "recommendation": "Review database connectivity and query syntax"
                })
        
        # Analyze external API calls
        if self.external_api_profiles:
            recent_apis = list(self.external_api_profiles)[-1000:]  # Last 1000 API calls
            
            # Check for slow API calls
            slow_apis = [a for a in recent_apis if a.duration > self.slow_api_threshold]
            if len(slow_apis) > 20:
                insights.append({
                    "type": "slow_external_apis",
                    "severity": "warning",
                    "message": f"Slow external API calls detected ({len(slow_apis)} in last 1000)",
                    "recommendation": "Optimize API calls or implement caching"
                })
            
            # Check for failed API calls
            failed_apis = [a for a in recent_apis if not a.success]
            if len(failed_apis) > 50:
                insights.append({
                    "type": "failed_external_apis",
                    "severity": "error",
                    "message": f"Failed external API calls detected ({len(failed_apis)} in last 1000)",
                    "recommendation": "Review API connectivity and implement proper error handling"
                })
        
        return insights
    
    def record_query_results(self, query_id: str, rows_affected: int, rows_returned: int,
                           connection_id: str, index_used: str, execution_plan: Dict[str, Any]):
        """Record database query results."""
        for query in self.database_query_profiles:
            if query.query_id == query_id:
                query.rows_affected = rows_affected
                query.rows_returned = rows_returned
                query.connection_id = connection_id
                query.index_used = index_used
                query.execution_plan = execution_plan
                break
    
    def record_api_results(self, call_id: str, status_code: int, request_size: int,
                          response_size: int, retry_count: int, response_headers: Dict[str, str]):
        """Record external API call results."""
        for api_call in self.external_api_profiles:
            if api_call.call_id == call_id:
                api_call.status_code = status_code
                api_call.request_size = request_size
                api_call.response_size = response_size
                api_call.retry_count = retry_count
                api_call.response_headers = response_headers
                break
    
    def record_transaction_step(self, transaction_id: str, step_name: str, step_duration: float,
                              step_success: bool, step_resources: Dict[str, Any]):
        """Record business transaction step."""
        for transaction in self.business_transaction_profiles:
            if transaction.transaction_id == transaction_id:
                transaction.steps.append({
                    "step_name": step_name,
                    "step_duration": step_duration,
                    "step_success": step_success,
                    "step_resources": step_resources
                })
                break
    
    def record_transaction_metrics(self, transaction_id: str, performance_metrics: Dict[str, Any],
                                 resources_used: Dict[str, Any]):
        """Record business transaction metrics."""
        for transaction in self.business_transaction_profiles:
            if transaction.transaction_id == transaction_id:
                transaction.performance_metrics = performance_metrics
                transaction.resources_used = resources_used
                break


# Global instance
performance_profiler = None


def get_performance_profiler() -> PerformanceProfiler:
    """Get the global performance profiler instance."""
    global performance_profiler
    if performance_profiler is None:
        performance_profiler = PerformanceProfiler()
    return performance_profiler


def initialize_performance_profiler(config: APMConfig = None):
    """Initialize the global performance profiler instance."""
    global performance_profiler
    performance_profiler = PerformanceProfiler(config)
    return performance_profiler


# Decorators for performance profiling
def profile_cpu(operation_name: str = None, enable_stats: bool = True):
    """Decorator for CPU profiling."""
    def decorator(func):
        name = operation_name or f"cpu_profile.{func.__name__}"
        
        def sync_wrapper(*args, **kwargs):
            profiler = get_performance_profiler()
            with profiler.profile_cpu(name, enable_stats) as profiler_obj:
                return func(*args, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            profiler = get_performance_profiler()
            with profiler.profile_cpu(name, enable_stats) as profiler_obj:
                return await func(*args, **kwargs)
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return sync_wrapper
    
    return decorator


def profile_memory(operation_name: str = None, enable_tracing: bool = True):
    """Decorator for memory profiling."""
    def decorator(func):
        name = operation_name or f"memory_profile.{func.__name__}"
        
        def sync_wrapper(*args, **kwargs):
            profiler = get_performance_profiler()
            with profiler.profile_memory(name, enable_tracing):
                return func(*args, **kwargs)
        
        async def async_wrapper(*args, **kwargs):
            profiler = get_performance_profiler()
            with profiler.profile_memory(name, enable_tracing):
                return await func(*args, **kwargs)
        
        if hasattr(func, '__call__') and hasattr(func, '__code__') and func.__code__.co_flags & 0x80:
            return async_wrapper
        return sync_wrapper
    
    return decorator


def profile_database_query(operation_name: str = None, query_type: str = "SELECT", 
                          database: str = "", table: str = ""):
    """Decorator for database query profiling."""
    def decorator(func):
        name = operation_name or f"db_query.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            profiler = get_performance_profiler()
            
            # Extract query text from kwargs or args
            query_text = kwargs.get('query', '')
            if not query_text and args:
                query_text = str(args[0])
            
            async with profiler.profile_database_query(name, query_type, query_text, database, table) as span:
                result = await func(*args, **kwargs)
                
                # Record query results
                query_id = span.get_span_context().span_id
                profiler.record_query_results(
                    query_id, 
                    kwargs.get('rows_affected', 0),
                    kwargs.get('rows_returned', 0),
                    kwargs.get('connection_id', ''),
                    kwargs.get('index_used', ''),
                    kwargs.get('execution_plan', {})
                )
                
                return result
        
        return async_wrapper
    
    return decorator


def profile_external_api(operation_name: str = None, service_name: str = "", 
                        method: str = "GET", timeout: float = 30.0):
    """Decorator for external API profiling."""
    def decorator(func):
        name = operation_name or f"api_call.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            profiler = get_performance_profiler()
            
            # Extract endpoint from kwargs or args
            endpoint = kwargs.get('endpoint', '')
            if not endpoint and args:
                endpoint = str(args[0])
            
            async with profiler.profile_external_api(name, service_name, endpoint, method, timeout) as span:
                result = await func(*args, **kwargs)
                
                # Record API results
                call_id = span.get_span_context().span_id
                profiler.record_api_results(
                    call_id,
                    kwargs.get('status_code', 0),
                    kwargs.get('request_size', 0),
                    kwargs.get('response_size', 0),
                    kwargs.get('retry_count', 0),
                    kwargs.get('response_headers', {})
                )
                
                return result
        
        return async_wrapper
    
    return decorator


def profile_business_transaction(transaction_name: str = None, transaction_type: str = "default"):
    """Decorator for business transaction profiling."""
    def decorator(func):
        name = transaction_name or f"transaction.{func.__name__}"
        
        async def async_wrapper(*args, **kwargs):
            profiler = get_performance_profiler()
            
            async with profiler.profile_business_transaction(name, transaction_type) as span:
                result = await func(*args, **kwargs)
                
                # Record transaction metrics
                transaction_id = span.get_span_context().span_id
                profiler.record_transaction_metrics(
                    transaction_id,
                    kwargs.get('performance_metrics', {}),
                    kwargs.get('resources_used', {})
                )
                
                return result
        
        return async_wrapper
    
    return decorator