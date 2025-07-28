import pytest
from pydantic import ValidationError
from src.model_router.models import ModelRequest


def test_model_request_validation():
    with pytest.raises(ValidationError):
        ModelRequest()  # type: ignore[arg-type]
