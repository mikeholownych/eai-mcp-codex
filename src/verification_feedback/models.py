"""Models for Verification Feedback."""

from pydantic import BaseModel


class Feedback(BaseModel):
    id: int
