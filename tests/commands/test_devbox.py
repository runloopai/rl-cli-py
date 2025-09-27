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
        args.user = None
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

    # Create mock result object with devboxes property
    mock_result = AsyncMock()
    mock_result.devboxes = [mock_devbox]
    mock_api_client.devboxes.list = AsyncMock(return_value=mock_result)

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
async def test_execute_async_command():
    """Test executing a command asynchronously on a devbox."""
    mock_devbox = MockDevbox()
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.execute_async = AsyncMock(return_value=mock_devbox)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.id = "test-id"
        args.command = "echo hello"
        args.shell_name = None

        await devbox.execute_async(args)

        mock_api_client.devboxes.execute_async.assert_called_once()
        # Starts with 'execution='
        assert mock_print.call_args[0][0].startswith("execution=")

@pytest.mark.asyncio
async def test_get_async_exec():
    """Test retrieving the status of an async execution."""
    mock_execution = MockDevbox(status="finished")
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.executions = AsyncMock()
    mock_api_client.devboxes.executions.retrieve = AsyncMock(return_value=mock_execution)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.id = "test-id"
        args.execution_id = "exec-123"
        args.shell_name = None

        await devbox.get_async_exec(args)

        mock_api_client.devboxes.executions.retrieve.assert_called_once_with(
            execution_id="exec-123",
            devbox_id="test-id",
        )
        assert mock_print.call_args[0][0].startswith("execution=")

@pytest.mark.asyncio
async def test_logs_printing():
    """Test logs printing formatting for different log entry shapes."""
    class LogEntry:
        def __init__(self, timestamp_ms=None, source=None, cmd=None, message=None, exit_code=None):
            self.timestamp_ms = timestamp_ms
            self.source = source
            self.cmd = cmd
            self.message = message
            self.exit_code = exit_code

    mock_logs_response = AsyncMock()
    mock_logs_response.logs = [
        LogEntry(timestamp_ms=1710000000000, source="entrypoint", cmd="echo test"),
        LogEntry(timestamp_ms=1710000000500, message="hello"),
        LogEntry(timestamp_ms=1710000001000, exit_code=0),
    ]

    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.logs = AsyncMock()
    mock_api_client.devboxes.logs.list = AsyncMock(return_value=mock_logs_response)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        args = AsyncMock()
        args.id = "test-id"

        await devbox.logs(args)

        mock_api_client.devboxes.logs.list.assert_called_once_with("test-id")
        printed_lines = [call.args[0] for call in mock_print.call_args_list]
        assert any("-> echo test" in line for line in printed_lines)
        assert any("  hello" in line for line in printed_lines)
        assert any("-> exit_code=0" in line for line in printed_lines)

@pytest.mark.asyncio
async def test_scp_invocation_builds_command():
    """Test scp builds the correct command and executes it."""
    with patch('rl_cli.commands.devbox.get_ssh_key', new=AsyncMock(return_value=("/tmp/key.pem", "key", "host.example"))), \
         patch('rl_cli.commands.devbox.ssh_url', return_value="ssh.runloop.ai:443"), \
         patch('subprocess.run') as mock_run:
        args = AsyncMock()
        args.id = "dbx_123"
        args.src = "./local.txt"
        args.dst = ":/remote.txt"
        args.scp_options = None

        await devbox.scp(args)

        mock_run.assert_called_once()
        cmd = mock_run.call_args.kwargs.get('args') or mock_run.call_args[0][0]
        # Ensure scp is invoked and remote path correctly prefixed
        assert cmd[0] == "scp"
        assert f"user@host.example:/remote.txt" in cmd

@pytest.mark.asyncio
async def test_rsync_invocation_builds_command():
    """Test rsync builds the correct command and executes it."""
    with patch('rl_cli.commands.devbox.get_ssh_key', new=AsyncMock(return_value=("/tmp/key.pem", "key", "host.example"))), \
         patch('rl_cli.commands.devbox.ssh_url', return_value="ssh.runloop.ai:443"), \
         patch('subprocess.run') as mock_run:
        args = AsyncMock()
        args.id = "dbx_123"
        args.src = ":/remote_dir"
        args.dst = "./local_dir"
        args.rsync_options = "-avz"

        await devbox.rsync(args)

        mock_run.assert_called_once()
        cmd = mock_run.call_args.kwargs.get('args') or mock_run.call_args[0][0]
        assert cmd[0] == "rsync"
        # Contains -e with ssh and proxy command
        assert "-e" in cmd
        # Ensure remote arg contains user@host
        assert any(arg.startswith("user@host.example:") for arg in cmd)

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
         patch('rl_cli.commands.devbox.wait_for_ready', new=AsyncMock(return_value=True)):
        
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
async def test_devbox_read_wrapper_calls_read_file():
    """devbox_read should delegate to read_file."""
    with patch('rl_cli.commands.devbox.read_file', new=AsyncMock()) as mock_read:
        args = AsyncMock()
        await devbox.devbox_read(args)
        mock_read.assert_called_once_with(args)

@pytest.mark.asyncio
async def test_devbox_write_wrapper_calls_write_file():
    """devbox_write should delegate to write_file."""
    with patch('rl_cli.commands.devbox.write_file', new=AsyncMock()) as mock_write:
        args = AsyncMock()
        await devbox.devbox_write(args)
        mock_write.assert_called_once_with(args)

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


@pytest.mark.asyncio
async def test_download_file():
    """Test downloading a file from a devbox."""
    mock_result = AsyncMock()
    mock_result.write_to_file = AsyncMock()
    
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.download_file = AsyncMock(return_value=mock_result)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        args = AsyncMock()
        args.id = "test-devbox-id"
        args.file_path = "/remote/file.txt"
        args.output_path = "/local/output.txt"
        
        await devbox.download_file(args)
        
        mock_api_client.devboxes.download_file.assert_called_once_with(
            id="test-devbox-id",
            path="/remote/file.txt"
        )
        mock_result.write_to_file.assert_called_once_with("/local/output.txt")
        mock_print.assert_called_once_with("File downloaded to /local/output.txt")


@pytest.mark.asyncio
async def test_wait_for_ready_success():
    """Test wait_for_ready when devbox becomes ready."""
    mock_devbox = AsyncMock()
    mock_devbox.status = "running"
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.retrieve = AsyncMock(return_value=mock_devbox)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        result = await devbox.wait_for_ready("test-devbox-id", timeout_seconds=10)
        
        assert result is True
        mock_api_client.devboxes.retrieve.assert_called_with("test-devbox-id")
        mock_print.assert_called_with("Devbox test-devbox-id is ready!")


@pytest.mark.asyncio
async def test_wait_for_ready_failure():
    """Test wait_for_ready when devbox fails."""
    mock_devbox = AsyncMock()
    mock_devbox.status = "failure"
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.retrieve = AsyncMock(return_value=mock_devbox)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        result = await devbox.wait_for_ready("test-devbox-id", timeout_seconds=10)
        
        assert result is False
        mock_print.assert_called_with("Devbox test-devbox-id failed to start (status: failure)")


@pytest.mark.asyncio
async def test_wait_for_ready_timeout():
    """Test wait_for_ready timeout."""
    mock_devbox = MockDevbox(status="provisioning")
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.retrieve = AsyncMock(return_value=mock_devbox)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print, \
         patch('asyncio.sleep', new=AsyncMock()):
        
        result = await devbox.wait_for_ready("test-devbox-id", timeout_seconds=0.1, poll_interval_seconds=0.05)
        
        assert result is False
        assert any("Timeout waiting for devbox" in str(call) for call in mock_print.call_args_list)


@pytest.mark.asyncio
async def test_snapshot():
    """Test creating a devbox snapshot."""
    from unittest.mock import Mock
    mock_snapshot = Mock()
    mock_snapshot.model_dump_json.return_value = '{"id": "snap-123"}'
    
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.snapshot_disk_async = AsyncMock(return_value=mock_snapshot)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        args = AsyncMock()
        args.devbox_id = "test-devbox-id"
        
        await devbox.snapshot(args)
        
        mock_api_client.devboxes.snapshot_disk_async.assert_called_once_with("test-devbox-id")
        mock_print.assert_called_once_with('snapshot={"id": "snap-123"}')


@pytest.mark.asyncio
async def test_get_snapshot_status():
    """Test getting snapshot status."""
    from unittest.mock import Mock
    mock_status = Mock()
    mock_status.model_dump_json.return_value = '{"status": "completed"}'
    
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.disk_snapshots = AsyncMock()
    mock_api_client.devboxes.disk_snapshots.query_status = AsyncMock(return_value=mock_status)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        args = AsyncMock()
        args.snapshot_id = "snap-123"
        
        await devbox.get_snapshot_status(args)
        
        mock_api_client.devboxes.disk_snapshots.query_status.assert_called_once_with("snap-123")
        mock_print.assert_called_once_with('snapshot_status={"status": "completed"}')


@pytest.mark.asyncio
async def test_list_snapshots():
    """Test listing snapshots."""
    from unittest.mock import Mock
    mock_snapshots = Mock()
    mock_snapshots.model_dump_json.return_value = '{"snapshots": []}'
    
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.list_disk_snapshots = AsyncMock(return_value=mock_snapshots)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('rl_cli.commands.devbox.print') as mock_print:
        
        args = AsyncMock()
        
        await devbox.list_snapshots(args)
        
        mock_api_client.devboxes.list_disk_snapshots.assert_called_once()
        mock_print.assert_called_once_with('snapshots={"snapshots": []}')


@pytest.mark.asyncio
async def test_parse_code_mounts():
    """Test _parse_code_mounts function."""
    # Test with None
    result = devbox._parse_code_mounts(None)
    assert result is None
    
    # Test with valid JSON
    json_str = '{"repo_url": "https://github.com/test/repo", "path": "/app"}'
    result = devbox._parse_code_mounts(json_str)
    assert result is not None
    # Can't easily test the exact structure without importing CodeMountParameters


@pytest.mark.asyncio 
async def test_ssh_with_no_wait():
    """Test SSH command with --no-wait flag."""
    mock_ssh_key_result = AsyncMock()
    mock_ssh_key_result.ssh_private_key = "test-key"
    mock_ssh_key_result.url = "test-host"
    
    mock_devbox = AsyncMock()
    mock_devbox.launch_parameters.user_parameters.username = "test-user"
    
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.create_ssh_key = AsyncMock(return_value=mock_ssh_key_result)
    mock_api_client.devboxes.retrieve = AsyncMock(return_value=mock_devbox)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('os.makedirs'), \
         patch('builtins.open', create=True), \
         patch('os.chmod'), \
         patch('os.fsync'), \
         patch('subprocess.run') as mock_run, \
         patch('rl_cli.commands.devbox.ssh_url', return_value="ssh.runloop.ai:443"):
        
        args = AsyncMock()
        args.id = "test-devbox-id"
        args.no_wait = True
        args.config_only = False
        
        await devbox.ssh(args)
        
        # Should not call wait_for_ready
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_ssh_config_only_with_no_wait():
    """Test SSH config-only generation with --no-wait."""
    mock_ssh_key_result = AsyncMock()
    mock_ssh_key_result.ssh_private_key = "test-key"
    mock_ssh_key_result.url = "test-host"
    
    mock_devbox = AsyncMock()
    mock_devbox.launch_parameters.user_parameters.username = "test-user"
    
    mock_api_client = AsyncMock()
    mock_api_client.devboxes = AsyncMock()
    mock_api_client.devboxes.create_ssh_key = AsyncMock(return_value=mock_ssh_key_result)
    mock_api_client.devboxes.retrieve = AsyncMock(return_value=mock_devbox)

    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('os.makedirs'), \
         patch('builtins.open', create=True), \
         patch('os.chmod'), \
         patch('os.fsync'), \
         patch('rl_cli.commands.devbox.print') as mock_print, \
         patch('rl_cli.commands.devbox.ssh_url', return_value="ssh.runloop.ai:443"):
        
        args = AsyncMock()
        args.id = "test-devbox-id"
        args.no_wait = True
        args.config_only = True
        
        await devbox.ssh(args)
        
        # Should print SSH config
        config_output = mock_print.call_args[0][0]
        assert "Host test-devbox-id" in config_output
        assert "User test-user" in config_output
        assert "Hostname test-host" in config_output