"""Tests for blueprint commands."""

import json
from unittest.mock import AsyncMock, patch, mock_open
import pytest

from rl_cli.commands import blueprint
from rl_cli.utils import runloop_api_client

class MockBlueprint:
    def __init__(self, **kwargs):
        self.data = {
            "id": "test-blueprint",
            "name": "test",
            "status": "active",
            **kwargs
        }

    def model_dump_json(self, indent=None):
        return json.dumps(self.data, indent=indent)

@pytest.mark.asyncio
async def test_create_blueprint():
    """Test creating a blueprint."""
    mock_blueprint = MockBlueprint()
    mock_api_client = AsyncMock()
    mock_api_client.blueprints = AsyncMock()
    mock_api_client.blueprints.create = AsyncMock(return_value=mock_blueprint)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.blueprint.print') as mock_print:
        args = AsyncMock()
        args.name = "test"
        args.dockerfile = "FROM ubuntu:latest"
        args.dockerfile_path = None
        args.resources = "SMALL"
        args.available_ports = None
        args.architecture = "arm64"
        args.root = True

        await blueprint.create(args)

        mock_api_client.blueprints.create.assert_called_once()
        mock_print.assert_called_once_with(f"created blueprint={mock_blueprint.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_create_blueprint_from_file():
    """Test creating a blueprint from a Dockerfile."""
    mock_blueprint = MockBlueprint()
    mock_api_client = AsyncMock()
    mock_api_client.blueprints = AsyncMock()
    mock_api_client.blueprints.create = AsyncMock(return_value=mock_blueprint)

    dockerfile_contents = "FROM ubuntu:latest"

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.blueprint.print') as mock_print, \
         patch('builtins.open', mock_open(read_data=dockerfile_contents)):
        args = AsyncMock()
        args.name = "test"
        args.dockerfile = None
        args.dockerfile_path = "Dockerfile"
        args.resources = "SMALL"
        args.available_ports = None
        args.architecture = "arm64"
        args.root = True

        await blueprint.create(args)

        mock_api_client.blueprints.create.assert_called_once()
        mock_print.assert_called_once_with(f"created blueprint={mock_blueprint.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_list_blueprints():
    """Test listing blueprints."""
    mock_blueprint = MockBlueprint()
    mock_api_client = AsyncMock()
    mock_api_client.blueprints = AsyncMock()

    class MockResponse:
        blueprints = [mock_blueprint]

    mock_api_client.blueprints.list = AsyncMock(return_value=MockResponse())

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.blueprint.print') as mock_print:
        args = AsyncMock()
        args.name = None

        await blueprint.list_blueprints(args)

        mock_api_client.blueprints.list.assert_called_once_with(name=None)
        mock_print.assert_called_once_with(f"blueprints={mock_blueprint.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_list_blueprints_with_name():
    """Test listing blueprints with a name filter."""
    mock_blueprint = MockBlueprint()
    mock_api_client = AsyncMock()
    mock_api_client.blueprints = AsyncMock()

    class MockResponse:
        blueprints = [mock_blueprint]

    mock_api_client.blueprints.list = AsyncMock(return_value=MockResponse())

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.blueprint.print') as mock_print:
        args = AsyncMock()
        args.name = "test"

        await blueprint.list_blueprints(args)

        mock_api_client.blueprints.list.assert_called_once_with(name="test")
        mock_print.assert_called_once_with(f"blueprints={mock_blueprint.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_list_blueprints_empty():
    """Test listing blueprints when none exist."""
    mock_api_client = AsyncMock()
    mock_api_client.blueprints = AsyncMock()

    class MockResponse:
        blueprints = []

    mock_api_client.blueprints.list = AsyncMock(return_value=MockResponse())

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.blueprint.print') as mock_print:
        args = AsyncMock()
        args.name = None

        await blueprint.list_blueprints(args)

        mock_api_client.blueprints.list.assert_called_once_with(name=None)
        mock_print.assert_not_called()

@pytest.mark.asyncio
async def test_preview_blueprint():
    """Test previewing a blueprint."""
    mock_blueprint = MockBlueprint()
    mock_api_client = AsyncMock()
    mock_api_client.blueprints = AsyncMock()
    mock_api_client.blueprints.preview = AsyncMock(return_value=mock_blueprint)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.blueprint.print') as mock_print:
        args = AsyncMock()
        args.name = "test"
        args.dockerfile = "FROM ubuntu:latest"
        args.system_setup_commands = ["apt-get update"]

        await blueprint.preview(args)

        mock_api_client.blueprints.preview.assert_called_once_with(
            name="test",
            system_setup_commands=["apt-get update"],
            dockerfile="FROM ubuntu:latest"
        )
        mock_print.assert_called_once_with(f"preview blueprint={mock_blueprint.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_get_blueprint():
    """Test getting a specific blueprint."""
    mock_blueprint = MockBlueprint()
    mock_api_client = AsyncMock()
    mock_api_client.blueprints = AsyncMock()
    mock_api_client.blueprints.retrieve = AsyncMock(return_value=mock_blueprint)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.blueprint.print') as mock_print:
        args = AsyncMock()
        args.id = "test-blueprint-id"

        await blueprint.get(args)

        mock_api_client.blueprints.retrieve.assert_called_once_with("test-blueprint-id")
        mock_print.assert_called_once_with(f"blueprint={mock_blueprint.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_blueprint_logs():
    """Test getting blueprint build logs."""
    class MockLog:
        def __init__(self, timestamp_ms, level, message):
            self.timestamp_ms = timestamp_ms
            self.level = level
            self.message = message

    class MockLogsResponse:
        def __init__(self):
            self.logs = [
                MockLog("1234567890", "INFO", "Building image"),
                MockLog("1234567891", "INFO", "Build completed")
            ]

    mock_logs_response = MockLogsResponse()
    mock_api_client = AsyncMock()
    mock_api_client.blueprints = AsyncMock()
    mock_api_client.blueprints.logs = AsyncMock(return_value=mock_logs_response)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.blueprint.print') as mock_print:
        args = AsyncMock()
        args.id = "test-blueprint-id"

        await blueprint.logs(args)

        mock_api_client.blueprints.logs.assert_called_once_with("test-blueprint-id")
        assert mock_print.call_count == 2
        mock_print.assert_any_call("1234567890 INFO Building image")
        mock_print.assert_any_call("1234567891 INFO Build completed")

@pytest.mark.asyncio
async def test_blueprint_logs_empty():
    """Test getting blueprint logs when none exist."""
    class MockLogsResponse:
        def __init__(self):
            self.logs = []

    mock_logs_response = MockLogsResponse()
    mock_api_client = AsyncMock()
    mock_api_client.blueprints = AsyncMock()
    mock_api_client.blueprints.logs = AsyncMock(return_value=mock_logs_response)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.blueprint.print') as mock_print:
        args = AsyncMock()
        args.id = "test-blueprint-id"

        await blueprint.logs(args)

        mock_api_client.blueprints.logs.assert_called_once_with("test-blueprint-id")
        mock_print.assert_not_called()