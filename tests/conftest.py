"""Common test fixtures and configuration for RL CLI tests."""

import os
from unittest.mock import AsyncMock, patch
import pytest
from runloop_api_client import AsyncRunloop

@pytest.fixture(autouse=True)
def mock_env():
    """Fixture to set up test environment variables."""
    with patch.dict(os.environ, {
        'RUNLOOP_API_KEY': 'test-api-key',
        'RUNLOOP_ENV': 'dev'
    }, clear=True):
        yield

@pytest.fixture
def mock_runloop_client():
    """Fixture to provide a mocked AsyncRunloop client."""
    with patch('rl_cli.main.runloop_api_client') as mock_client, \
         patch('runloop_api_client._base_client.get_platform', return_value='test-platform'):
        # Create mock response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = AsyncMock(return_value={"data": []})
        mock_response.text = "{}"

        # Create mock HTTP client
        mock_http_client = AsyncMock()
        mock_http_client.send = AsyncMock(return_value=mock_response)

        # Create mock API client
        client = AsyncMock()
        client._client = mock_http_client
        client._platform = 'test-platform'
        client.devboxes = AsyncMock()
        client.blueprints = AsyncMock()
        mock_client.return_value = client
        return client

@pytest.fixture
def temp_cache_dir(tmp_path):
    """Fixture to provide a temporary cache directory."""
    with patch('rl_cli.main.get_cache_dir') as mock_cache_dir:
        cache_dir = tmp_path / '.cache' / 'rl-cli'
        cache_dir.mkdir(parents=True, exist_ok=True)
        mock_cache_dir.return_value = cache_dir
        yield cache_dir
