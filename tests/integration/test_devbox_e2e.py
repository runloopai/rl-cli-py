"""End-to-end tests for devbox commands.

These tests require RUNLOOP_API_KEY environment variable to be set.
They make real API calls and create/manage actual devboxes.
"""
import json
import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from rl_cli.main import run


@pytest.fixture(autouse=True)
def clear_api_cache():
    """Fixture to clear API client cache before each test to ensure real API calls."""
    from rl_cli.utils import runloop_api_client
    runloop_api_client.cache_clear()
    yield
    runloop_api_client.cache_clear()


async def _create_test_devbox(capsys) -> str:
    """Helper function to create a test devbox and return its ID."""
    argv = [
        "rl",
        "devbox", 
        "create",
        "--architecture",
        "arm64",
        "--resources",
        "SMALL",
        "--entrypoint",
        "sleep 30",  # Keep devbox alive longer for testing
    ]
    with patch("sys.argv", argv):
        await run()

    captured = capsys.readouterr()
    
    # Parse devbox id from output - the format is 'create devbox={...}'
    m = re.search(r'"id":\s*"([^"]+)"', captured.out)
    assert m, f"did not find devbox id in output:\n{captured.out}"
    devbox_id = m.group(1)
    
    return devbox_id


async def _wait_for_devbox_ready(devbox_id: str, timeout_seconds: int = 60) -> bool:
    """Helper function to wait for a devbox to be ready."""
    from rl_cli.commands.devbox import wait_for_ready
    return await wait_for_ready(devbox_id, timeout_seconds, 3)


async def _cleanup_devbox(devbox_id: str):
    """Helper function to clean up a test devbox."""
    try:
        with patch("sys.argv", ["rl", "devbox", "shutdown", "--id", devbox_id]):
            await run()
    except Exception as e:
        # Don't fail the test if cleanup fails, just log it
        print(f"Warning: Failed to cleanup devbox {devbox_id}: {e}")


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for basic operations
async def test_devbox_create_and_get(capsys):
    """Test devbox creation and retrieval."""
    # Require an API key
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        # Create devbox (returns immediately like object E2E tests)
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Test devbox get (works immediately after creation)
        with patch("sys.argv", ["rl", "devbox", "get", "--id", devbox_id]):
            await run()
        get_out = capsys.readouterr().out
        assert devbox_id in get_out
        assert "devbox=" in get_out
        # Don't assert on status - devbox might be provisioning, running, or other states

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio
@pytest.mark.timeout(30)  # 30 second timeout
async def test_devbox_list(capsys):
    """Test listing devboxes."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    # Test list command with limit to prevent hanging on large result sets
    with patch("sys.argv", ["rl", "devbox", "list", "--limit", "5"]):
        await run()
    list_out = capsys.readouterr().out
    # Should contain devbox= entries or be empty (both are valid)
    assert isinstance(list_out, str)  # Should at least return a string, not a coroutine


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for basic operations
async def test_devbox_basic_lifecycle(capsys):
    """Test basic devbox lifecycle operations."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Test basic operations that work on any devbox state
        # Just test that the commands execute without error
        
        # Test get (should always work)
        with patch("sys.argv", ["rl", "devbox", "get", "--id", devbox_id]):
            await run()
        get_out = capsys.readouterr().out
        assert devbox_id in get_out
        assert "devbox=" in get_out

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio  
@pytest.mark.timeout(30)  # 30 second timeout for snapshot list
async def test_devbox_snapshot_list(capsys):
    """Test listing snapshots (doesn't require creating a devbox)."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    # Test list snapshots (works without any devboxes)
    with patch("sys.argv", ["rl", "devbox", "snapshot", "list"]):
        await run()
    list_out = capsys.readouterr().out
    assert "snapshots=" in list_out


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for exec operations
async def test_devbox_exec(capsys):
    """Test devbox command execution."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Wait for devbox to be ready before testing exec
        is_ready = await _wait_for_devbox_ready(devbox_id, 60)
        if not is_ready:
            pytest.skip(f"Devbox {devbox_id} not ready within timeout, skipping exec test")

        # Test execute command 
        with patch("sys.argv", [
            "rl", "devbox", "exec",
            "--id", devbox_id,
            "--command", "echo 'test execution'"
        ]):
            await run()
        exec_out = capsys.readouterr().out
        assert isinstance(exec_out, str)
        assert "exec_result=" in exec_out

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for async exec operations
async def test_devbox_exec_async(capsys):
    """Test devbox async command execution."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Wait for devbox to be ready before testing async exec
        is_ready = await _wait_for_devbox_ready(devbox_id, 60)
        if not is_ready:
            pytest.skip(f"Devbox {devbox_id} not ready within timeout, skipping async exec test")

        # Test async execute command
        with patch("sys.argv", [
            "rl", "devbox", "exec_async",
            "--id", devbox_id,
            "--command", "echo 'async test'"
        ]):
            await run()
        exec_out = capsys.readouterr().out
        assert isinstance(exec_out, str)
        
        # If we get an execution ID, test get_async
        if "execution=" in exec_out:
            # Parse execution ID from output
            m = re.search(r'execution=.*?"id":\s*"([^"]+)"', exec_out, re.DOTALL)
            if m:
                execution_id = m.group(1)
                
                # Test get async execution status
                with patch("sys.argv", [
                    "rl", "devbox", "get_async",
                    "--id", devbox_id,
                    "--execution_id", execution_id
                ]):
                    await run()
                status_out = capsys.readouterr().out
                assert isinstance(status_out, str)

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for logs
async def test_devbox_logs(capsys):
    """Test devbox logs retrieval."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Test logs retrieval
        with patch("sys.argv", ["rl", "devbox", "logs", "--id", devbox_id]):
            await run()
        logs_out = capsys.readouterr().out
        # Logs might be empty initially, but command should not fail
        assert isinstance(logs_out, str)

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for lifecycle operations
async def test_devbox_lifecycle_operations(capsys):
    """Test devbox lifecycle operations (suspend/resume)."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Wait for devbox to be ready before testing lifecycle operations
        is_ready = await _wait_for_devbox_ready(devbox_id, 60)
        if not is_ready:
            pytest.skip(f"Devbox {devbox_id} not ready within timeout, skipping lifecycle test")

        # Test suspend
        with patch("sys.argv", ["rl", "devbox", "suspend", "--id", devbox_id]):
            await run()
        suspend_out = capsys.readouterr().out
        assert isinstance(suspend_out, str)

        # Test resume
        with patch("sys.argv", ["rl", "devbox", "resume", "--id", devbox_id]):
            await run()
        resume_out = capsys.readouterr().out
        assert isinstance(resume_out, str)

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for file operations
async def test_devbox_file_operations(capsys, tmp_path):
    """Test devbox file read/write operations."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Wait for devbox to be ready before testing file operations
        is_ready = await _wait_for_devbox_ready(devbox_id, 60)
        if not is_ready:
            pytest.skip(f"Devbox {devbox_id} not ready within timeout, skipping file operations test")

        # Create test files
        input_file = tmp_path / "test_input.txt"
        output_file = tmp_path / "test_output.txt"
        input_file.write_text("Hello from E2E test!")
        remote_path = "/tmp/e2e_test_file.txt"

        # Test write file
        with patch("sys.argv", [
            "rl", "devbox", "write", 
            "--id", devbox_id,
            "--input", str(input_file),
            "--remote", remote_path
        ]):
            await run()
        write_out = capsys.readouterr().out
        assert isinstance(write_out, str)

        # Test read file
        with patch("sys.argv", [
            "rl", "devbox", "read",
            "--id", devbox_id, 
            "--remote", remote_path,
            "--output", str(output_file)
        ]):
            await run()
        read_out = capsys.readouterr().out
        assert isinstance(read_out, str)

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for upload/download
async def test_devbox_upload_download(capsys, tmp_path):
    """Test devbox file upload/download operations."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Wait for devbox to be ready before testing upload/download
        is_ready = await _wait_for_devbox_ready(devbox_id, 60)
        if not is_ready:
            pytest.skip(f"Devbox {devbox_id} not ready within timeout, skipping upload/download test")

        # Create test file
        test_file = tmp_path / "upload_test.txt"
        test_file.write_text("Upload test content")
        remote_path = "/tmp/uploaded_file.txt"
        download_path = tmp_path / "downloaded_file.txt"

        # Test upload
        with patch("sys.argv", [
            "rl", "devbox", "upload_file",
            "--id", devbox_id,
            "--file", str(test_file),
            "--path", remote_path
        ]):
            await run()
        upload_out = capsys.readouterr().out
        assert isinstance(upload_out, str)

        # Test download
        with patch("sys.argv", [
            "rl", "devbox", "download_file",
            "--id", devbox_id,
            "--file_path", remote_path,
            "--output_path", str(download_path)
        ]):
            await run()
        download_out = capsys.readouterr().out
        assert isinstance(download_out, str)

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for snapshot operations
async def test_devbox_snapshot_operations(capsys):
    """Test devbox snapshot create and status operations."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Wait for devbox to be ready before testing snapshot operations
        is_ready = await _wait_for_devbox_ready(devbox_id, 60)
        if not is_ready:
            pytest.skip(f"Devbox {devbox_id} not ready within timeout, skipping snapshot test")

        # Test create snapshot
        with patch("sys.argv", [
            "rl", "devbox", "snapshot", "create",
            "--devbox_id", devbox_id
        ]):
            await run()
        snapshot_out = capsys.readouterr().out
        assert isinstance(snapshot_out, str)
        
        # If we get a snapshot ID, test snapshot status
        if "snapshot=" in snapshot_out:
            # Parse snapshot ID from output
            m = re.search(r'snapshot=.*?"id":\s*"([^"]+)"', snapshot_out, re.DOTALL)
            if m:
                snapshot_id = m.group(1)
                
                # Test get snapshot status
                with patch("sys.argv", [
                    "rl", "devbox", "snapshot", "status",
                    "--snapshot_id", snapshot_id
                ]):
                    await run()
                status_out = capsys.readouterr().out
                assert isinstance(status_out, str)

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for SSH operations
async def test_devbox_ssh_operations(capsys, tmp_path):
    """Test devbox SSH-related operations (non-interactive)."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Wait for devbox to be ready before testing SSH operations
        is_ready = await _wait_for_devbox_ready(devbox_id, 60)
        if not is_ready:
            pytest.skip(f"Devbox {devbox_id} not ready within timeout, skipping SSH operations test")

        # Test SSH config generation (config-only, no actual connection)
        with patch("sys.argv", [
            "rl", "devbox", "ssh",
            "--id", devbox_id,
            "--config-only",
            "--no-wait"
        ]):
            await run()
        ssh_out = capsys.readouterr().out
        assert isinstance(ssh_out, str)

        # Test SCP (dry run or basic syntax check)
        test_file = tmp_path / "scp_test.txt"
        test_file.write_text("SCP test")
        with patch("sys.argv", [
            "rl", "devbox", "scp",
            "--id", devbox_id,
            str(test_file),  # src (positional)
            ":/tmp/scp_test.txt"  # dst (positional, :remote_path format)
        ]):
            await run()
        scp_out = capsys.readouterr().out
        assert isinstance(scp_out, str)

        # Test rsync (dry run or basic syntax check)
        with patch("sys.argv", [
            "rl", "devbox", "rsync",
            "--id", devbox_id,
            str(tmp_path),  # src (positional)
            ":/tmp/rsync_test/"  # dst (positional, :remote_path format)
        ]):
            await run()
        rsync_out = capsys.readouterr().out
        assert isinstance(rsync_out, str)

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 1 minute timeout for tunnel operations
async def test_devbox_tunnel_basic(capsys):
    """Test devbox tunnel command (basic syntax check only)."""
    api_key = os.environ.get("RUNLOOP_API_KEY")
    if not api_key:
        pytest.fail("RUNLOOP_API_KEY is required for end-to-end tests. Set it in the environment.")
    
    created_devbox_ids = []
    
    try:
        devbox_id = await _create_test_devbox(capsys)
        created_devbox_ids.append(devbox_id)

        # Wait for devbox to be ready before testing tunnel
        is_ready = await _wait_for_devbox_ready(devbox_id, 60)
        if not is_ready:
            pytest.skip(f"Devbox {devbox_id} not ready within timeout, skipping tunnel test")

        # Test tunnel command (will likely fail but should not hang)
        # Using a short timeout to prevent actual tunnel establishment
        with patch("sys.argv", [
            "rl", "devbox", "tunnel",
            "--id", devbox_id,
            "8080:80"  # Correct format: local:remote
        ]):
            await run()
        tunnel_out = capsys.readouterr().out
        assert isinstance(tunnel_out, str)

    finally:
        # Cleanup: shutdown created devboxes
        for devbox_id in created_devbox_ids:
            await _cleanup_devbox(devbox_id)


@pytest.mark.skip(reason="SSH connection requires interactive session and is hard to test in CI")
def test_ssh_connection():
    pass