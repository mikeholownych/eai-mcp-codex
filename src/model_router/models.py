"""Data models for Model Router."""

from pydantic import BaseModel


class ModelRequest(BaseModel):
    text: str


class ModelResponse(BaseModel):
    result: str
