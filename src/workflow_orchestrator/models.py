"""Models for Workflow Orchestrator."""

from pydantic import BaseModel


class Workflow(BaseModel):
    id: int
