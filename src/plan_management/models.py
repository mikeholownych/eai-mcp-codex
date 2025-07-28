"""Data models for Plan Management."""

from pydantic import BaseModel


class Plan(BaseModel):
    id: int
    name: str
