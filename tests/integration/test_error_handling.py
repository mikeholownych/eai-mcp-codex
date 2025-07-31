import pytest
from pydantic import ValidationError
from src.model_router.models import ModelRequest

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


def test_model_request_validation():
    with pytest.raises(ValidationError):
        ModelRequest()  # type: ignore[arg-type]
