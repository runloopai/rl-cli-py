"""Common test fixtures and configuration for RL CLI tests."""

import os
from unittest.mock import patch
import pytest

@pytest.fixture(autouse=True)
def mock_env():
    """Fixture to set up test environment variables."""
    with patch.dict(os.environ, {
        'RUNLOOP_API_KEY': 'test-api-key',
        'RUNLOOP_ENV': 'dev'
    }, clear=True):
        yield

@pytest.fixture
def temp_cache_dir(tmp_path):
    """Fixture to provide a temporary cache directory."""
    with patch('rl_cli.utils.get_cache_dir') as mock_cache_dir:
        cache_dir = tmp_path / '.cache' / 'rl-cli'
        cache_dir.mkdir(parents=True, exist_ok=True)
        mock_cache_dir.return_value = cache_dir
        yield cache_dir