"""Workflow Orchestration business logic implementation."""

import asyncio
import sqlite3
import uuid
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.common.logging import get_logger
from .models import (
    Workflow, WorkflowStep, WorkflowExecution, WorkflowStatus, StepStatus,
    StepType, ExecutionMode, WorkflowRequest, StepExecutionResult,
    WorkflowTemplate
)

logger = get_logger("workflow_orchestrator")


class WorkflowOrchestrator:
    """Core business logic for workflow orchestration."""
    
    def __init__(self, db_path: str = "data/workflows.db"):
        self.db_path = db_path
        self.service_endpoints = {
            "model_router": "http://localhost:8001",
            "plan_management": "http://localhost:8002", 
            "git_worktree": "http://localhost:8003",
            "verification": "http://localhost:8004",
            "feedback": "http://localhost:8005"
        }
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'draft',
                    execution_mode TEXT DEFAULT 'sequential',
                    priority TEXT DEFAULT 'medium',
                    created_by TEXT DEFAULT 'system',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    global_parameters TEXT DEFAULT '{}',
                    success_criteria TEXT DEFAULT '{}',
                    failure_handling TEXT DEFAULT '{}',
                    notifications TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS workflow_steps (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    step_type TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    parameters TEXT DEFAULT '{}',
                    expected_output TEXT,
                    timeout_seconds INTEGER DEFAULT 300,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'pending',
                    order_index INTEGER DEFAULT 0,
                    depends_on TEXT DEFAULT '[]',
                    conditions TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT DEFAULT '{}',
                    error_message TEXT,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id)
                );
                
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    execution_number INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    triggered_by TEXT DEFAULT 'system',
                    execution_context TEXT DEFAULT '{}',
                    step_results TEXT DEFAULT '{}',
                    total_steps INTEGER DEFAULT 0,
                    completed_steps INTEGER DEFAULT 0,
                    failed_steps INTEGER DEFAULT 0,
                    skipped_steps INTEGER DEFAULT 0,
                    error_message TEXT,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id)
                );
                
                CREATE TABLE IF NOT EXISTS workflow_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT DEFAULT 'general',
                    template_version TEXT DEFAULT '1.0',
                    author TEXT DEFAULT 'system',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    step_templates TEXT DEFAULT '[]',
                    default_parameters TEXT DEFAULT '{}',
                    required_parameters TEXT DEFAULT '[]',
                    tags TEXT DEFAULT '[]',
                    usage_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
                CREATE INDEX IF NOT EXISTS idx_steps_workflow ON workflow_steps(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_steps_status ON workflow_steps(status);
                CREATE INDEX IF NOT EXISTS idx_executions_workflow ON workflow_executions(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_templates_category ON workflow_templates(category);
            """)
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def create_workflow(self, request: WorkflowRequest, created_by: str = "system") -> Workflow:
        """Create a new workflow."""
        workflow_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        workflow = Workflow(
            id=workflow_id,
            name=request.name,
            description=request.description,
            execution_mode=request.execution_mode,
            priority=request.priority,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            global_parameters=request.global_parameters,
            metadata=request.metadata
        )
        
        # Create workflow steps
        steps = []
        for i, step_data in enumerate(request.steps):
            step = WorkflowStep(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                name=step_data["name"],
                description=step_data.get("description", ""),
                step_type=StepType(step_data["step_type"]),
                service_name=step_data["service_name"],
                endpoint=step_data["endpoint"],
                parameters=step_data.get("parameters", {}),
                order=i,
                depends_on=step_data.get("depends_on", []),
                conditions=step_data.get("conditions", {}),
                timeout_seconds=step_data.get("timeout_seconds", 300),
                max_retries=step_data.get("max_retries", 3)
            )
            steps.append(step)
        
        workflow.steps = steps
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            # Save workflow
            conn.execute("""
                INSERT INTO workflows (
                    id, name, description, execution_mode, priority, created_by,
                    created_at, updated_at, global_parameters, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow.id, workflow.name, workflow.description, workflow.execution_mode.value,
                workflow.priority, workflow.created_by, workflow.created_at.isoformat(),
                workflow.updated_at.isoformat(), str(workflow.global_parameters), str(workflow.metadata)
            ))
            
            # Save steps
            for step in steps:
                conn.execute("""
                    INSERT INTO workflow_steps (
                        id, workflow_id, name, description, step_type, service_name, endpoint,
                        parameters, timeout_seconds, max_retries, order_index, depends_on,
                        conditions, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    step.id, step.workflow_id, step.name, step.description, step.step_type.value,
                    step.service_name, step.endpoint, str(step.parameters), step.timeout_seconds,
                    step.max_retries, step.order, str(step.depends_on), str(step.conditions), str(step.metadata)
                ))
        
        logger.info(f"Created workflow: {workflow.id} - {workflow.name}")
        return workflow
    
    async def execute_workflow(self, workflow_id: str, triggered_by: str = "system", context: Dict[str, Any] = None) -> WorkflowExecution:
        """Execute a workflow asynchronously."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        if workflow.status != WorkflowStatus.DRAFT and workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow cannot be executed in status: {workflow.status}")
        
        # Create execution record
        execution_id = str(uuid.uuid4())
        execution_number = self._get_next_execution_number(workflow_id)
        
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            execution_number=execution_number,
            status=WorkflowStatus.ACTIVE,
            triggered_by=triggered_by,
            execution_context=context or {},
            total_steps=len(workflow.steps)
        )
        
        # Save initial execution record
        self._save_execution(execution)
        
        # Update workflow status
        self._update_workflow_status(workflow_id, WorkflowStatus.ACTIVE, started_at=datetime.utcnow())
        
        try:
            if workflow.execution_mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(workflow, execution)
            elif workflow.execution_mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(workflow, execution)
            elif workflow.execution_mode == ExecutionMode.CONDITIONAL:
                await self._execute_conditional(workflow, execution)
            
            # Determine final status
            final_status = WorkflowStatus.COMPLETED
            if execution.failed_steps > 0:
                final_status = WorkflowStatus.FAILED
            
            execution.status = final_status
            execution.completed_at = datetime.utcnow()
            
            # Update workflow status
            self._update_workflow_status(workflow_id, final_status, completed_at=datetime.utcnow())
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            
            self._update_workflow_status(workflow_id, WorkflowStatus.FAILED, completed_at=datetime.utcnow())
        
        finally:
            self._save_execution(execution)
        
        logger.info(f"Workflow execution completed: {execution.id} with status {execution.status}")
        return execution
    
    async def _execute_sequential(self, workflow: Workflow, execution: WorkflowExecution):
        """Execute workflow steps sequentially."""
        # Sort steps by order
        sorted_steps = sorted(workflow.steps, key=lambda s: s.order)
        
        for step in sorted_steps:
            if not self._check_dependencies(step, execution.step_results):
                logger.info(f"Skipping step {step.id} due to unmet dependencies")
                execution.skipped_steps += 1
                continue
            
            if not self._check_conditions(step, execution.step_results, execution.execution_context):
                logger.info(f"Skipping step {step.id} due to unmet conditions")
                execution.skipped_steps += 1
                continue
            
            result = await self._execute_step(step, execution.execution_context, workflow.global_parameters)
            execution.step_results[step.id] = result.model_dump()
            
            if result.status == StepStatus.COMPLETED:
                execution.completed_steps += 1
            elif result.status == StepStatus.FAILED:
                execution.failed_steps += 1
                
                # Check failure handling
                if workflow.failure_handling.get("stop_on_failure", True):
                    break
    
    async def _execute_parallel(self, workflow: Workflow, execution: WorkflowExecution):
        """Execute workflow steps in parallel where possible."""
        pending_steps = workflow.steps.copy()
        completed_step_ids = set()
        
        while pending_steps:
            # Find steps that can be executed (dependencies met)
            ready_steps = [
                step for step in pending_steps
                if all(dep_id in completed_step_ids for dep_id in step.depends_on)
                and self._check_conditions(step, execution.step_results, execution.execution_context)
            ]
            
            if not ready_steps:
                # No more steps can be executed
                execution.skipped_steps += len(pending_steps)
                break
            
            # Execute ready steps in parallel
            tasks = [
                self._execute_step(step, execution.execution_context, workflow.global_parameters)
                for step in ready_steps
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for step, result in zip(ready_steps, results):
                if isinstance(result, Exception):
                    logger.error(f"Step {step.id} failed with exception: {result}")
                    execution.failed_steps += 1
                else:
                    execution.step_results[step.id] = result.model_dump()
                    if result.status == StepStatus.COMPLETED:
                        execution.completed_steps += 1
                        completed_step_ids.add(step.id)
                    elif result.status == StepStatus.FAILED:
                        execution.failed_steps += 1
                
                pending_steps.remove(step)
    
    async def _execute_conditional(self, workflow: Workflow, execution: WorkflowExecution):
        """Execute workflow with conditional logic."""
        # This is similar to sequential but with more complex condition checking
        await self._execute_sequential(workflow, execution)
    
    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any], global_params: Dict[str, Any]) -> StepExecutionResult:
        """Execute a single workflow step."""
        step_result = StepExecutionResult(
            step_id=step.id,
            status=StepStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        # Update step status in database
        self._update_step_status(step.id, StepStatus.RUNNING, started_at=step_result.started_at)
        
        try:
            # Merge parameters
            merged_params = {**global_params, **step.parameters, **context}
            
            # Make HTTP request to service
            service_url = self.service_endpoints.get(step.service_name)
            if not service_url:
                raise ValueError(f"Unknown service: {step.service_name}")
            
            full_url = f"{service_url}{step.endpoint}"
            
            start_time = datetime.utcnow()
            
            timeout = httpx.Timeout(step.timeout_seconds)
            async with httpx.AsyncClient(timeout=timeout) as client:
                if step.endpoint.startswith('/'):
                    # POST request with parameters as JSON body
                    response = await client.post(full_url, json=merged_params)
                else:
                    # GET request with parameters as query params
                    response = await client.get(full_url, params=merged_params)
                
                response.raise_for_status()
                result_data = response.json()
            
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            step_result.status = StepStatus.COMPLETED
            step_result.completed_at = end_time
            step_result.result = {"response": result_data}
            step_result.execution_time_ms = execution_time
            step_result.output_data = result_data
            
            logger.info(f"Step {step.id} completed successfully in {execution_time:.2f}ms")
            
        except Exception as e:
            step_result.status = StepStatus.FAILED
            step_result.completed_at = datetime.utcnow()
            step_result.error_message = str(e)
            
            logger.error(f"Step {step.id} failed: {e}")
            
            # Retry logic
            if step.retry_count < step.max_retries:
                logger.info(f"Retrying step {step.id} (attempt {step.retry_count + 1}/{step.max_retries})")
                self._update_step_retry_count(step.id, step.retry_count + 1)
                await asyncio.sleep(2 ** step.retry_count)  # Exponential backoff
                return await self._execute_step(step, context, global_params)
        
        # Update step in database
        self._update_step_status(
            step.id, 
            step_result.status, 
            completed_at=step_result.completed_at,
            result=step_result.result,
            error_message=step_result.error_message
        )
        
        return step_result
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get workflow
            cursor = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
            workflow_row = cursor.fetchone()
            
            if not workflow_row:
                return None
            
            # Get steps
            cursor = conn.execute(
                "SELECT * FROM workflow_steps WHERE workflow_id = ? ORDER BY order_index",
                (workflow_id,)
            )
            step_rows = cursor.fetchall()
            
            workflow = self._row_to_workflow(workflow_row)
            workflow.steps = [self._row_to_step(row) for row in step_rows]
            
            return workflow
    
    def list_workflows(self, status: str = None, created_by: str = None) -> List[Workflow]:
        """List workflows with optional filtering."""
        query = "SELECT * FROM workflows WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if created_by:
            query += " AND created_by = ?"
            params.append(created_by)
        
        query += " ORDER BY updated_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_workflow(row) for row in cursor.fetchall()]
    
    def get_workflow_executions(self, workflow_id: str) -> List[WorkflowExecution]:
        """Get all executions for a workflow."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM workflow_executions WHERE workflow_id = ? ORDER BY execution_number DESC",
                (workflow_id,)
            )
            return [self._row_to_execution(row) for row in cursor.fetchall()]
    
    def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow."""
        return self._update_workflow_status(workflow_id, WorkflowStatus.PAUSED)
    
    def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow."""
        return self._update_workflow_status(workflow_id, WorkflowStatus.ACTIVE)
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a workflow."""
        return self._update_workflow_status(workflow_id, WorkflowStatus.CANCELLED)
    
    def _check_dependencies(self, step: WorkflowStep, step_results: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied."""
        for dep_id in step.depends_on:
            if dep_id not in step_results:
                return False
            
            dep_result = step_results[dep_id]
            if dep_result.get("status") != StepStatus.COMPLETED.value:
                return False
        
        return True
    
    def _check_conditions(self, step: WorkflowStep, step_results: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if step conditions are met."""
        if not step.conditions:
            return True
        
        # Simple condition checking - can be extended
        for condition_key, expected_value in step.conditions.items():
            if condition_key in context:
                if context[condition_key] != expected_value:
                    return False
            elif condition_key in step_results:
                # Check in previous step results
                if step_results[condition_key] != expected_value:
                    return False
            else:
                return False
        
        return True
    
    def _get_next_execution_number(self, workflow_id: str) -> int:
        """Get the next execution number for a workflow."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT MAX(execution_number) FROM workflow_executions WHERE workflow_id = ?",
                (workflow_id,)
            )
            result = cursor.fetchone()
            return (result[0] or 0) + 1
    
    def _update_workflow_status(self, workflow_id: str, status: WorkflowStatus, started_at: datetime = None, completed_at: datetime = None) -> bool:
        """Update workflow status."""
        updates = {"status": status.value, "updated_at": datetime.utcnow().isoformat()}
        
        if started_at:
            updates["started_at"] = started_at.isoformat()
        if completed_at:
            updates["completed_at"] = completed_at.isoformat()
        
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values()) + [workflow_id]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"UPDATE workflows SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0
    
    def _update_step_status(self, step_id: str, status: StepStatus, started_at: datetime = None, completed_at: datetime = None, result: Dict[str, Any] = None, error_message: str = None):
        """Update step status."""
        updates = {"status": status.value}
        
        if started_at:
            updates["started_at"] = started_at.isoformat()
        if completed_at:
            updates["completed_at"] = completed_at.isoformat()
        if result:
            updates["result"] = str(result)
        if error_message:
            updates["error_message"] = error_message
        
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values()) + [step_id]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"UPDATE workflow_steps SET {set_clause} WHERE id = ?", values)
    
    def _update_step_retry_count(self, step_id: str, retry_count: int):
        """Update step retry count."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE workflow_steps SET retry_count = ? WHERE id = ?", (retry_count, step_id))
    
    def _save_execution(self, execution: WorkflowExecution):
        """Save workflow execution to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO workflow_executions (
                    id, workflow_id, execution_number, status, started_at, completed_at,
                    triggered_by, execution_context, step_results, total_steps,
                    completed_steps, failed_steps, skipped_steps, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution.id, execution.workflow_id, execution.execution_number, execution.status.value,
                execution.started_at.isoformat(),
                execution.completed_at.isoformat() if execution.completed_at else None,
                execution.triggered_by, str(execution.execution_context), str(execution.step_results),
                execution.total_steps, execution.completed_steps, execution.failed_steps,
                execution.skipped_steps, execution.error_message, str(execution.metadata)
            ))
    
    def _row_to_workflow(self, row) -> Workflow:
        """Convert database row to Workflow object."""
        import json
        
        return Workflow(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            status=WorkflowStatus(row["status"]),
            execution_mode=ExecutionMode(row["execution_mode"]),
            priority=row["priority"],
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            global_parameters=json.loads(row["global_parameters"] or "{}"),
            success_criteria=json.loads(row["success_criteria"] or "{}"),
            failure_handling=json.loads(row["failure_handling"] or "{}"),
            notifications=json.loads(row["notifications"] or "{}"),
            metadata=json.loads(row["metadata"] or "{}")
        )
    
    def _row_to_step(self, row) -> WorkflowStep:
        """Convert database row to WorkflowStep object."""
        import json
        
        return WorkflowStep(
            id=row["id"],
            workflow_id=row["workflow_id"],
            name=row["name"],
            description=row["description"] or "",
            step_type=StepType(row["step_type"]),
            service_name=row["service_name"],
            endpoint=row["endpoint"],
            parameters=json.loads(row["parameters"] or "{}"),
            expected_output=row["expected_output"],
            timeout_seconds=row["timeout_seconds"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            status=StepStatus(row["status"]),
            order=row["order_index"],
            depends_on=json.loads(row["depends_on"] or "[]"),
            conditions=json.loads(row["conditions"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            result=json.loads(row["result"] or "{}"),
            error_message=row["error_message"],
            metadata=json.loads(row["metadata"] or "{}")
        )
    
    def _row_to_execution(self, row) -> WorkflowExecution:
        """Convert database row to WorkflowExecution object."""
        import json
        
        return WorkflowExecution(
            id=row["id"],
            workflow_id=row["workflow_id"],
            execution_number=row["execution_number"],
            status=WorkflowStatus(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            triggered_by=row["triggered_by"],
            execution_context=json.loads(row["execution_context"] or "{}"),
            step_results=json.loads(row["step_results"] or "{}"),
            total_steps=row["total_steps"],
            completed_steps=row["completed_steps"],
            failed_steps=row["failed_steps"],
            skipped_steps=row["skipped_steps"],
            error_message=row["error_message"],
            metadata=json.loads(row["metadata"] or "{}")
        )


# Singleton instance
_orchestrator: Optional[WorkflowOrchestrator] = None


def get_orchestrator() -> WorkflowOrchestrator:
    """Get singleton WorkflowOrchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WorkflowOrchestrator()
    return _orchestrator


# Legacy function for backward compatibility
def start(workflow_id: int) -> Workflow:
    """Kick off a workflow and return its metadata."""
    return Workflow(id=str(workflow_id), name=f"Legacy Workflow {workflow_id}")
