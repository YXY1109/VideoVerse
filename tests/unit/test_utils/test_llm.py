"""Test LLM client functionality."""
from unittest.mock import MagicMock, patch

from core.utils.llm import _get_openai_client, ask_llm


def test_get_openai_client_singleton():
    """Test LLM client singleton."""

    # Reset singleton cache
    _get_openai_client.cache_clear()

    client1 = _get_openai_client()
    client2 = _get_openai_client()

    assert client1 is client2


@patch("core.utils.llm._get_openai_client")
def test_ask_llm_success(mock_get_client):
    """Test successful LLM call."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "test"}'))]
    mock_client = MagicMock()
    mock_client.chat.completions.create = MagicMock(return_value=mock_response)
    mock_get_client.return_value = mock_client

    result = ask_llm("test prompt", log_title="test")

    assert result == {"result": "test"}
    mock_client.chat.completions.create.assert_called_once()


@patch("core.utils.llm._get_openai_client")
def test_ask_llm_with_cache(mock_get_client, monkeypatch):
    """Test LLM call with cache."""
    # Mock cache
    mock_cache_manager = MagicMock()
    mock_cache_manager.get_llm_cache = MagicMock(return_value={"cached": "result"})
    monkeypatch.setattr("core.utils.llm.cache_manager", mock_cache_manager)

    result = ask_llm("test prompt", log_title="test")

    assert result == {"cached": "result"}
    # Should not call the API when cache hit
    mock_get_client.assert_not_called()
