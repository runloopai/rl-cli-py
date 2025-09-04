"""Tests for devbox commands."""

import json
from unittest.mock import AsyncMock, patch
import pytest
from runloop_api_client import NOT_GIVEN

from rl_cli.commands import devbox
from rl_cli.utils import runloop_api_client

class MockDevbox:
    def __init__(self, **kwargs):
        self.data = {
            "id": "test-id",
            "status": "running",
            "created_at": "2024-01-01T00:00:00Z",
            **kwargs
        }
        self.launch_parameters = AsyncMock()
        self.launch_parameters.user_parameters = AsyncMock()
        self.launch_parameters.user_parameters.username = "test-user"

    def model_dump_json(self, indent=None):
        return json.dumps(self.data, indent=indent)

@pytest.mark.asyncio
async def test_create_devbox():
    """Test creating a devbox."""
    mock_devbox = MockDevbox(status="initializing")
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.create = AsyncMock(return_value=mock_devbox)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.idle_time = None
        args.idle_action = None
        args.architecture = "arm64"
        args.blueprint_id = None
        args.blueprint_name = None
        args.root = True
        args.entrypoint = "echo hello"
        args.env_vars = None
        args.code_mounts = None
        args.snapshot_id = None
        args.resources = "SMALL"
        args.launch_commands = None

        await devbox.create(args)

        mock_api_client.devboxes.create.assert_called_once()
        mock_print.assert_called_once_with(f"create devbox={mock_devbox.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_list_devboxes():
    """Test listing devboxes."""
    mock_devbox = MockDevbox()
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()

    # Create mock paginator
    async def mock_aiter(self):
        yield mock_devbox

    mock_paginator = AsyncMock()
    mock_paginator.__aiter__ = mock_aiter
    mock_api_client.devboxes.list = AsyncMock(return_value=mock_paginator)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.status = None
        args.limit = None

        await devbox.list_devboxes(args)

        mock_api_client.devboxes.list.assert_called_once_with(
            extra_query=None,
            limit=None
        )
        mock_print.assert_called_once_with(f"devbox={mock_devbox.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_get_devbox():
    """Test getting a devbox."""
    mock_devbox = MockDevbox()
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.retrieve = AsyncMock(return_value=mock_devbox)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.id = "test-id"

        await devbox.get(args)

        mock_api_client.devboxes.retrieve.assert_called_once_with("test-id")
        mock_print.assert_called_once_with(f"devbox={mock_devbox.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_execute_command():
    """Test executing a command on a devbox."""
    mock_result = {"output": "test output"}
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.execute_sync = AsyncMock(return_value=mock_result)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.id = "test-id"
        args.command = "echo hello"
        args.shell_name = None

        await devbox.execute(args)

        mock_api_client.devboxes.execute_sync.assert_called_once_with(
            id="test-id",
            command="echo hello",
            shell_name=NOT_GIVEN
        )
        mock_print.assert_called_once_with("exec_result=", mock_result)

@pytest.mark.asyncio
async def test_suspend_devbox():
    """Test suspending a devbox."""
    mock_devbox = MockDevbox(status="suspended")
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.suspend = AsyncMock(return_value=mock_devbox)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.id = "test-id"

        await devbox.suspend(args)

        mock_api_client.devboxes.suspend.assert_called_once_with("test-id")
        mock_print.assert_called_once_with(f"devbox={mock_devbox.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_resume_devbox():
    """Test resuming a devbox."""
    mock_devbox = MockDevbox(status="running")
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.resume = AsyncMock(return_value=mock_devbox)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.id = "test-id"

        await devbox.resume(args)

        mock_api_client.devboxes.resume.assert_called_once_with("test-id")
        mock_print.assert_called_once_with(f"devbox={mock_devbox.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_shutdown_devbox():
    """Test shutting down a devbox."""
    mock_devbox = MockDevbox(status="shutdown")
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.shutdown = AsyncMock(return_value=mock_devbox)

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.id = "test-id"

        await devbox.shutdown(args)

        mock_api_client.devboxes.shutdown.assert_called_once_with("test-id")
        mock_print.assert_called_once_with(f"devbox={mock_devbox.model_dump_json(indent=4)}")

@pytest.mark.asyncio
async def test_get_ssh_key():
    """Test getting SSH key for a devbox."""
    mock_ssh_key_result = AsyncMock()
    mock_ssh_key_result.ssh_private_key = "-----BEGIN PRIVATE KEY-----\ntest-key-content\n-----END PRIVATE KEY-----"
    mock_ssh_key_result.url = "test-host"
    
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.create_ssh_key = AsyncMock(return_value=mock_ssh_key_result)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', create=True) as mock_open, \
         patch('os.chmod') as mock_chmod, \
         patch('os.fsync') as mock_fsync:
        
        result = await devbox.get_ssh_key("test-devbox-id")
        
        assert result is not None
        keyfile_path, username, url = result
        
        assert keyfile_path.endswith("test-devbox-id.pem")
        assert username == "-----BEGIN PRIVATE KEY-----\ntest-key-content\n-----END PRIVATE KEY-----"
        assert url == "test-host"
        
        mock_api_client.devboxes.create_ssh_key.assert_called_once_with("test-devbox-id")
        mock_makedirs.assert_called_once()
        mock_open.assert_called_once()
        mock_chmod.assert_called_once_with(keyfile_path, 0o600)

@pytest.mark.asyncio
async def test_get_ssh_key_failure():
    """Test SSH key creation failure."""
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.create_ssh_key = AsyncMock(return_value=None)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        result = await devbox.get_ssh_key("test-devbox-id")
        
        assert result is None
        mock_print.assert_called_once_with("Failed to create ssh key")

@pytest.mark.asyncio
async def test_ssh_command():
    """Test SSH connection to a devbox."""
    mock_ssh_key_result = AsyncMock()
    mock_ssh_key_result.ssh_private_key = "test-key"
    mock_ssh_key_result.url = "test-host"
    
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.create_ssh_key = AsyncMock(return_value=mock_ssh_key_result)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('os.makedirs'), \
         patch('builtins.open', create=True), \
         patch('os.chmod'), \
         patch('os.fsync'), \
         patch('subprocess.run') as mock_run, \
         patch('rl_cli.commands.devbox.ssh_url', return_value="ssh.runloop.ai:443"), \
         patch('rl_cli.commands.devbox.wait_for_ready', return_value=True):
        
        args = AsyncMock()
        args.id = "test-devbox-id"
        args.no_wait = False
        args.timeout = 180
        args.poll_interval = 3
        args.config_only = False
        
        # Mock devbox retrieval for username
        mock_devbox = AsyncMock()
        mock_devbox.launch_parameters.user_parameters.username = "test-user"
        mock_api_client.devboxes.retrieve = AsyncMock(return_value=mock_devbox)
        
        await devbox.ssh(args)
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "/usr/bin/ssh" in call_args
        assert "test-user@test-host" in " ".join(call_args)

@pytest.mark.asyncio
async def test_tunnel_command():
    """Test creating a tunnel to a devbox."""
    mock_ssh_key_result = AsyncMock()
    mock_ssh_key_result.ssh_private_key = "test-key"
    mock_ssh_key_result.url = "test-host"
    
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.create_ssh_key = AsyncMock(return_value=mock_ssh_key_result)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('os.makedirs'), \
         patch('builtins.open', create=True), \
         patch('os.chmod'), \
         patch('os.fsync'), \
         patch('subprocess.run') as mock_run, \
         patch('signal.signal'), \
         patch('rl_cli.commands.devbox.print') as mock_print, \
         patch('rl_cli.commands.devbox.ssh_url', return_value="ssh.runloop.ai:443"):
        
        args = AsyncMock()
        args.id = "test-devbox-id"
        args.ports = "8080:3000"
        
        await devbox.tunnel(args)
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "/usr/bin/ssh" in call_args
        assert "-L" in call_args
        assert "8080:localhost:3000" in call_args
        mock_print.assert_any_call("Starting tunnel: local port 8080 -> remote port 3000")

@pytest.mark.asyncio
async def test_read_file():
    """Test reading a file from a devbox."""
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.read_file_contents = AsyncMock(return_value="file content")

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('builtins.open', create=True) as mock_open, \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        args = AsyncMock()
        args.id = "test-devbox-id"
        args.remote = "/path/to/remote/file.txt"
        args.output = "/path/to/local/file.txt"
        
        await devbox.read_file(args)
        
        mock_api_client.devboxes.read_file_contents.assert_called_once_with(
            id="test-devbox-id", 
            file_path="/path/to/remote/file.txt"
        )
        mock_open.assert_called_once_with("/path/to/local/file.txt", "w", encoding="utf-8")
        mock_print.assert_called_once_with(
            "Wrote remote file /path/to/remote/file.txt from devbox test-devbox-id to local file /path/to/local/file.txt"
        )

@pytest.mark.asyncio 
async def test_write_file():
    """Test writing a file to a devbox."""
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.write_file_contents = AsyncMock()

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('os.path.exists', return_value=True), \
         patch('builtins.open', create=True) as mock_open, \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        mock_open.return_value.__enter__.return_value.read.return_value = "local file content"
        
        args = AsyncMock()
        args.id = "test-devbox-id"
        args.input = "/path/to/local/file.txt"
        args.remote = "/path/to/remote/file.txt"
        
        await devbox.write_file(args)
        
        mock_api_client.devboxes.write_file_contents.assert_called_once_with(
            id="test-devbox-id",
            file_path="/path/to/remote/file.txt", 
            contents="local file content"
        )
        mock_print.assert_called_once_with(
            "Wrote local file /path/to/local/file.txt to remote file /path/to/remote/file.txt on devbox test-devbox-id"
        )

@pytest.mark.asyncio
async def test_write_file_not_found():
    """Test writing a file that doesn't exist."""
    with patch('os.path.exists', return_value=False):
        args = AsyncMock()
        args.input = "/nonexistent/file.txt"
        
        with pytest.raises(FileNotFoundError, match="Input file /nonexistent/file.txt does not exist"):
            await devbox.write_file(args)

@pytest.mark.asyncio
async def test_upload_file():
    """Test uploading a file to a devbox."""
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.upload_file = AsyncMock()

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('builtins.open', create=True) as mock_open, \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        mock_file = mock_open.return_value.__enter__.return_value
        
        args = AsyncMock()
        args.id = "test-devbox-id"
        args.path = "/remote/path/"
        args.file = "/local/file.txt"
        
        await devbox.upload_file(args)
        
        mock_api_client.devboxes.upload_file.assert_called_once_with(
            id="test-devbox-id",
            path="/remote/path/",
            file=mock_file
        )
        mock_print.assert_called_once_with(
            "Uploaded file /local/file.txt to /remote/path/"
        )