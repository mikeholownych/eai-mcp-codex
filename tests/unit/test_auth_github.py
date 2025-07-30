from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.common.auth import AuthManager


@pytest.mark.asyncio
async def test_authenticate_github_oauth_success() -> None:
    auth = AuthManager("secret")

    token_resp = Mock()
    token_resp.json.return_value = {"access_token": "abc"}
    token_resp.raise_for_status.return_value = None

    user_resp = Mock()
    user_resp.json.return_value = {"login": "octocat"}
    user_resp.raise_for_status.return_value = None

    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.return_value = token_resp
    client_mock.get.return_value = user_resp

    with patch("httpx.AsyncClient", return_value=client_mock):
        result = await auth.authenticate_github_oauth(
            code="123",
            client_id="id",
            client_secret="secret",
            redirect_uri="http://localhost/cb",
        )

    assert result.success is True
    assert result.username == "octocat"
