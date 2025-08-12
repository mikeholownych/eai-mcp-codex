"""Workflow Orchestration business logic implementation."""

import asyncio
import uuid
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

from src.common.logging import get_logger
from src.common.database import (
    DatabaseManager,
    serialize_json_field,
    deserialize_json_field,
    serialize_datetime,
    deserialize_datetime,
)
from .models import (
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStatus,
    StepStatus,
    StepType,
    ExecutionMode,
    WorkflowRequest,
    StepExecutionResult,
)
from .config import settings

logger = get_logger("workflow_orchestrator")


class WorkflowOrchestrator:
    """Core business logic for workflow orchestration."""

    def __init__(self, dsn: str = settings.database_url):
        self.db_manager = DatabaseManager(dsn)
        self.dsn = dsn
        self.service_endpoints = {
            "model_router": "http://localhost:8001",
            "plan_management": "http://localhost:8002",
            "git_worktree": "http://localhost:8003",
            "verification": "http://localhost:8005",  # Corrected port
            "feedback": "http://localhost:8005",  # Corrected port
        }
        # In-memory store for testing mode
        self._testing_mode = os.getenv("TESTING_MODE") == "true"
        self._workflows_mem: Dict[str, Workflow] = {}
        self._steps_mem: Dict[str, List[WorkflowStep]] = {}

    async def initialize_database(self):
        """Initialize database connection and create tables if they don't exist."""
        if self._testing_mode:
            return
        await self.db_manager.connect()
        await self._ensure_database()

    async def shutdown_database(self):
        """Shutdown database connection pool."""
        if self._testing_mode:
            return
        await self.db_manager.disconnect()

    async def _ensure_database(self):
        """Create database and tables if they don't exist."""
        if self._testing_mode:
            return
        script = """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'draft',
                    execution_mode TEXT DEFAULT 'sequential',
                    priority TEXT DEFAULT 'medium',
                    created_by TEXT DEFAULT 'system',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    global_parameters JSONB DEFAULT '{}',
                    success_criteria JSONB DEFAULT '{}',
                    failure_handling JSONB DEFAULT '{}',
                    notifications JSONB DEFAULT '{}',
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS workflow_steps (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    step_type TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    parameters JSONB DEFAULT '{}',
                    expected_output TEXT,
                    timeout_seconds INTEGER DEFAULT 300,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'pending',
                    order_index INTEGER DEFAULT 0,
                    depends_on JSONB DEFAULT '[]',
                    conditions JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    result JSONB DEFAULT '{}',
                    error_message TEXT,
                    metadata JSONB DEFAULT '{}',
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    execution_number INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    triggered_by TEXT DEFAULT 'system',
                    execution_context JSONB DEFAULT '{}',
                    step_results JSONB DEFAULT '{}',
                    total_steps INTEGER DEFAULT 0,
                    completed_steps INTEGER DEFAULT 0,
                    failed_steps INTEGER DEFAULT 0,
                    skipped_steps INTEGER DEFAULT 0,
                    error_message TEXT,
                    metadata JSONB DEFAULT '{}',
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS workflow_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT DEFAULT 'general',
                    template_version TEXT DEFAULT '1.0',
                    author TEXT DEFAULT 'system',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    step_templates JSONB DEFAULT '[]',
                    default_parameters JSONB DEFAULT '{}',
                    required_parameters JSONB DEFAULT '[]',
                    tags JSONB DEFAULT '[]',
                    usage_count INTEGER DEFAULT 0,
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
                CREATE INDEX IF NOT EXISTS idx_steps_workflow ON workflow_steps(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_steps_status ON workflow_steps(status);
                CREATE INDEX IF NOT EXISTS idx_executions_workflow ON workflow_executions(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_templates_category ON workflow_templates(category);
            """
        logger.info(f"Attempting to create tables in {self.dsn}")
        await self.db_manager.execute_script(script)
        logger.info("Database tables ensured.")

    async def create_workflow(
        self, request: WorkflowRequest, created_by: str = "system"
    ) -> Workflow:
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
            metadata=request.metadata,
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
                max_retries=step_data.get("max_retries", 3),
            )
            steps.append(step)

        workflow.steps = steps

        # In testing mode, store in memory and return
        if self._testing_mode:
            self._workflows_mem[workflow.id] = workflow
            self._steps_mem[workflow.id] = steps
            logger.info(f"Created workflow: {workflow.id} - {workflow.name}")
            return workflow

        # Save to database
        query = """
            INSERT INTO workflows (
                id, name, description, status, execution_mode, priority, created_by,
                created_at, updated_at, started_at, completed_at, global_parameters,
                success_criteria, failure_handling, notifications, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
        """
        values = (
            workflow.id,
            workflow.name,
            workflow.description,
            workflow.status.value,
            workflow.execution_mode.value,
            workflow.priority,
            workflow.created_by,
            serialize_datetime(workflow.created_at),
            serialize_datetime(workflow.updated_at),
            serialize_datetime(workflow.started_at),
            serialize_datetime(workflow.completed_at),
            serialize_json_field(workflow.global_parameters),
            serialize_json_field(workflow.success_criteria),
            serialize_json_field(workflow.failure_handling),
            serialize_json_field(workflow.notifications),
            serialize_json_field(workflow.metadata),
        )
        await self.db_manager.execute_update(query, values)

        # Save steps
        for step in steps:
            step_query = """
                INSERT INTO workflow_steps (
                    id, workflow_id, name, description, step_type, service_name, endpoint,
                    parameters, expected_output, timeout_seconds, retry_count, max_retries,
                    status, order_index, depends_on, conditions, created_at, started_at,
                    completed_at, result, error_message, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
            """
            step_values = (
                step.id,
                step.workflow_id,
                step.name,
                step.description,
                step.step_type.value,
                step.service_name,
                step.endpoint,
                serialize_json_field(step.parameters),
                step.expected_output,
                step.timeout_seconds,
                step.retry_count,
                step.max_retries,
                step.status.value,
                step.order,
                serialize_json_field(step.depends_on),
                serialize_json_field(step.conditions),
                serialize_datetime(step.created_at),
                serialize_datetime(step.started_at),
                serialize_datetime(step.completed_at),
                serialize_json_field(step.result),
                step.error_message,
                serialize_json_field(step.metadata),
            )
            await self.db_manager.execute_update(step_query, step_values)

        logger.info(f"Created workflow: {workflow.id} - {workflow.name}")
        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        triggered_by: str = "system",
        context: Dict[str, Any] = None,
    ) -> WorkflowExecution:
        """Execute a workflow asynchronously."""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if (
            workflow.status != WorkflowStatus.DRAFT
            and workflow.status != WorkflowStatus.ACTIVE
        ):
            raise ValueError(
                f"Workflow cannot be executed in status: {workflow.status}"
            )

        # Create execution record
        execution_id = str(uuid.uuid4())
        execution_number = await self._get_next_execution_number(workflow_id)

        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            execution_number=execution_number,
            status=WorkflowStatus.ACTIVE,
            triggered_by=triggered_by,
            execution_context=context or {},
            total_steps=len(workflow.steps),
        )

        # Save initial execution record
        await self._save_execution(execution)

        # Update workflow status
        await self._update_workflow_status(
            workflow_id, WorkflowStatus.ACTIVE, started_at=datetime.utcnow()
        )

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
            await self._update_workflow_status(
                workflow_id, final_status, completed_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()

            await self._update_workflow_status(
                workflow_id, WorkflowStatus.FAILED, completed_at=datetime.utcnow()
            )

        finally:
            await self._save_execution(execution)

        logger.info(
            f"Workflow execution completed: {execution.id} with status {execution.status}"
        )
        return execution

    async def _execute_sequential(
        self, workflow: Workflow, execution: WorkflowExecution
    ):
        """Execute workflow steps sequentially."""
        # Sort steps by order
        sorted_steps = sorted(workflow.steps, key=lambda s: s.order)

        for step in sorted_steps:
            if not self._check_dependencies(step, execution.step_results):
                logger.info(f"Skipping step {step.id} due to unmet dependencies")
                execution.skipped_steps += 1
                continue

            if not self._check_conditions(
                step, execution.step_results, execution.execution_context
            ):
                logger.info(f"Skipping step {step.id} due to unmet conditions")
                execution.skipped_steps += 1
                continue

            result = await self._execute_step(
                step, execution.execution_context, workflow.global_parameters
            )
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
                step
                for step in pending_steps
                if all(dep_id in completed_step_ids for dep_id in step.depends_on)
                and self._check_conditions(
                    step, execution.step_results, execution.execution_context
                )
            ]

            if not ready_steps:
                # No more steps can be executed
                execution.skipped_steps += len(pending_steps)
                break

            # Execute ready steps in parallel
            tasks = [
                self._execute_step(
                    step, execution.execution_context, workflow.global_parameters
                )
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

    async def _execute_conditional(
        self, workflow: Workflow, execution: WorkflowExecution
    ):
        """Execute workflow with conditional logic."""
        # This is similar to sequential but with more complex condition checking
        await self._execute_sequential(workflow, execution)

    async def _execute_step(
        self, step: WorkflowStep, context: Dict[str, Any], global_params: Dict[str, Any]
    ) -> StepExecutionResult:
        """Execute a single workflow step."""
        step_result = StepExecutionResult(
            step_id=step.id, status=StepStatus.RUNNING, started_at=datetime.utcnow()
        )

        # Update step status in database
        await self._update_step_status(
            step.id, StepStatus.RUNNING, started_at=step_result.started_at
        )

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
                if step.endpoint.startswith("/"):
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

            logger.info(
                f"Step {step.id} completed successfully in {execution_time:.2f}ms"
            )

        except Exception as e:
            step_result.status = StepStatus.FAILED
            step_result.completed_at = datetime.utcnow()
            step_result.error_message = str(e)

            logger.error(f"Step {step.id} failed: {e}")

            # Retry logic
            if step.retry_count < step.max_retries:
                logger.info(
                    f"Retrying step {step.id} (attempt {step.retry_count + 1}/{step.max_retries})"
                )
                self._update_step_retry_count(step.id, step.retry_count + 1)
                await asyncio.sleep(2**step.retry_count)  # Exponential backoff
                return await self._execute_step(step, context, global_params)

        # Update step in database
        await self._update_step_status(
            step.id,
            step_result.status,
            completed_at=step_result.completed_at,
            result=step_result.result,
            error_message=step_result.error_message,
        )

        return step_result

    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        if self._testing_mode:
            wf = self._workflows_mem.get(workflow_id)
            if not wf:
                return None
            wf.steps = self._steps_mem.get(workflow_id, [])
            return wf
        query = "SELECT * FROM workflows WHERE id = $1"
        workflow_row = await self.db_manager.execute_query(query, (workflow_id,))

        if not workflow_row:
            return None

        workflow = self._row_to_workflow(workflow_row[0])

        # Get steps
        step_query = (
            "SELECT * FROM workflow_steps WHERE workflow_id = $1 ORDER BY order_index"
        )
        step_rows = await self.db_manager.execute_query(step_query, (workflow_id,))
        workflow.steps = [self._row_to_step(row) for row in step_rows]

        return workflow

    async def list_workflows(
        self, status: Optional[str] = None, created_by: Optional[str] = None
    ) -> List[Workflow]:
        """List workflows with optional filtering."""
        if self._testing_mode:
            workflows = list(self._workflows_mem.values())
            if status:
                workflows = [w for w in workflows if w.status.value == status]
            if created_by:
                workflows = [w for w in workflows if w.created_by == created_by]
            # mimic DB ordering by updated_at desc
            workflows.sort(key=lambda w: w.updated_at, reverse=True)
            return workflows
        query = "SELECT * FROM workflows WHERE 1=1"
        params = []
        param_idx = 1

        if status:
            query += f" AND status = ${param_idx}"
            params.append(status)
            param_idx += 1

        if created_by:
            query += f" AND created_by = ${param_idx}"
            params.append(created_by)
            param_idx += 1

        query += " ORDER BY updated_at DESC"

        rows = await self.db_manager.execute_query(query, tuple(params))
        return [self._row_to_workflow(row) for row in rows]

    async def get_workflow_executions(
        self, workflow_id: str
    ) -> List[WorkflowExecution]:
        """Get all executions for a workflow."""
        query = "SELECT * FROM workflow_executions WHERE workflow_id = $1 ORDER BY execution_number DESC"
        rows = await self.db_manager.execute_query(query, (workflow_id,))
        return [self._row_to_execution(row) for row in rows]

    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow."""
        return await self._update_workflow_status(workflow_id, WorkflowStatus.PAUSED)

    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow."""
        return await self._update_workflow_status(workflow_id, WorkflowStatus.ACTIVE)

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a workflow."""
        return await self._update_workflow_status(workflow_id, WorkflowStatus.CANCELLED)

    def _check_dependencies(
        self, step: WorkflowStep, step_results: Dict[str, Any]
    ) -> bool:
        """Check if step dependencies are satisfied."""
        for dep_id in step.depends_on:
            if dep_id not in step_results:
                return False

            dep_result = step_results[dep_id]
            if dep_result.get("status") != StepStatus.COMPLETED.value:
                return False

        return True

    def _check_conditions(
        self, step: WorkflowStep, step_results: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
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

    async def _get_next_execution_number(self, workflow_id: str) -> int:
        """Get the next execution number for a workflow."""
        query = "SELECT MAX(execution_number) FROM workflow_executions WHERE workflow_id = $1"
        result = await self.db_manager.execute_query(query, (workflow_id,))
        return result[0]["max"] if result and result[0]["max"] is not None else 0

    async def _update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> bool:
        """Update workflow status."""
        updates = {"status": status.value, "updated_at": datetime.utcnow()}

        if started_at:
            updates["started_at"] = started_at
        if completed_at:
            updates["completed_at"] = completed_at

        set_clauses = []
        values = []
        param_idx = 1

        for key, value in updates.items():
            if key in ["created_at", "updated_at", "started_at", "completed_at"]:
                value = serialize_datetime(value)
            set_clauses.append(f"{key} = ${param_idx}")
            values.append(value)
            param_idx += 1

        set_clause = ", ".join(set_clauses)

        query = f"UPDATE workflows SET {set_clause} WHERE id = ${param_idx}"
        values.append(workflow_id)

        rows_affected = await self.db_manager.execute_update(query, tuple(values))
        return rows_affected > 0

    async def _update_step_status(
        self,
        step_id: str,
        status: StepStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ):
        """Update step status."""
        updates = {"status": status.value}

        if started_at:
            updates["started_at"] = started_at
        if completed_at:
            updates["completed_at"] = completed_at
        if result:
            updates["result"] = result
        if error_message:
            updates["error_message"] = error_message

        set_clauses = []
        values = []
        param_idx = 1

        for key, value in updates.items():
            if key in ["started_at", "completed_at"]:
                value = serialize_datetime(value)
            elif key in ["result"]:
                value = serialize_json_field(value)
            set_clauses.append(f"{key} = ${param_idx}")
            values.append(value)
            param_idx += 1

        set_clause = ", ".join(set_clauses)

        query = f"UPDATE workflow_steps SET {set_clause} WHERE id = ${param_idx}"
        values.append(step_id)

        await self.db_manager.execute_update(query, tuple(values))

    async def _update_step_retry_count(self, step_id: str, retry_count: int):
        """Update step retry count."""
        query = "UPDATE workflow_steps SET retry_count = $1 WHERE id = $2"
        await self.db_manager.execute_update(query, (retry_count, step_id))

    async def _save_execution(self, execution: WorkflowExecution):
        """Save workflow execution to database."""
        query = """
            INSERT INTO workflow_executions (
                id, workflow_id, execution_number, status, started_at, completed_at,
                triggered_by, execution_context, step_results, total_steps,
                completed_steps, failed_steps, skipped_steps, error_message, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                completed_at = EXCLUDED.completed_at,
                execution_context = EXCLUDED.execution_context,
                step_results = EXCLUDED.step_results,
                total_steps = EXCLUDED.total_steps,
                completed_steps = EXCLUDED.completed_steps,
                failed_steps = EXCLUDED.failed_steps,
                skipped_steps = EXCLUDED.skipped_steps,
                error_message = EXCLUDED.error_message,
                metadata = EXCLUDED.metadata
        """
        values = (
            execution.id,
            execution.workflow_id,
            execution.execution_number,
            execution.status.value,
            serialize_datetime(execution.started_at),
            serialize_datetime(execution.completed_at),
            execution.triggered_by,
            serialize_json_field(execution.execution_context),
            serialize_json_field(execution.step_results),
            execution.total_steps,
            execution.completed_steps,
            execution.failed_steps,
            execution.skipped_steps,
            execution.error_message,
            serialize_json_field(execution.metadata),
        )
        await self.db_manager.execute_update(query, values)

    def _row_to_workflow(self, row) -> Workflow:
        """Convert database row to Workflow object."""
        return Workflow(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            status=WorkflowStatus(row["status"]),
            execution_mode=ExecutionMode(row["execution_mode"]),
            priority=row["priority"],
            created_by=row["created_by"],
            created_at=deserialize_datetime(row["created_at"]),
            updated_at=deserialize_datetime(row["updated_at"]),
            started_at=deserialize_datetime(row["started_at"]),
            completed_at=deserialize_datetime(row["completed_at"]),
            global_parameters=deserialize_json_field(row["global_parameters"]),
            success_criteria=deserialize_json_field(row["success_criteria"]),
            failure_handling=deserialize_json_field(row["failure_handling"]),
            notifications=deserialize_json_field(row["notifications"]),
            metadata=deserialize_json_field(row["metadata"]),
        )

    def _row_to_step(self, row) -> WorkflowStep:
        """Convert database row to WorkflowStep object."""
        return WorkflowStep(
            id=row["id"],
            workflow_id=row["workflow_id"],
            name=row["name"],
            description=row["description"] or "",
            step_type=StepType(row["step_type"]),
            service_name=row["service_name"],
            endpoint=row["endpoint"],
            parameters=deserialize_json_field(row["parameters"]),
            expected_output=row["expected_output"],
            timeout_seconds=row["timeout_seconds"],
            retry_count=row["retry_count"],
            max_retries=row["max_retries"],
            status=StepStatus(row["status"]),
            order=row["order_index"],
            depends_on=deserialize_json_field(row["depends_on"]),
            conditions=deserialize_json_field(row["conditions"]),
            created_at=deserialize_datetime(row["created_at"]),
            started_at=deserialize_datetime(row["started_at"]),
            completed_at=deserialize_datetime(row["completed_at"]),
            result=deserialize_json_field(row["result"]),
            error_message=row["error_message"],
            metadata=deserialize_json_field(row["metadata"]),
        )

    def _row_to_execution(self, row) -> WorkflowExecution:
        """Convert database row to WorkflowExecution object."""
        return WorkflowExecution(
            id=row["id"],
            workflow_id=row["workflow_id"],
            execution_number=row["execution_number"],
            status=WorkflowStatus(row["status"]),
            started_at=deserialize_datetime(row["started_at"]),
            completed_at=deserialize_datetime(row["completed_at"]),
            triggered_by=row["triggered_by"],
            execution_context=deserialize_json_field(row["execution_context"]),
            step_results=deserialize_json_field(row["step_results"]),
            total_steps=row["total_steps"],
            completed_steps=row["completed_steps"],
            failed_steps=row["failed_steps"],
            skipped_steps=row["skipped_steps"],
            error_message=row["error_message"],
            metadata=deserialize_json_field(row["metadata"]),
        )


# Singleton instance
_orchestrator: Optional[WorkflowOrchestrator] = None


async def get_orchestrator() -> WorkflowOrchestrator:
    """Get singleton WorkflowOrchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = WorkflowOrchestrator()
        await _orchestrator.initialize_database()
    return _orchestrator


# Legacy function for backward compatibility
def start(workflow_id: int) -> Workflow:
    """Kick off a workflow and return its metadata."""
    return Workflow(id=str(workflow_id), name=f"Legacy Workflow {workflow_id}")
