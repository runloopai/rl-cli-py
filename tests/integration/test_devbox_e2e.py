"""End-to-end tests for devbox commands.

These tests require RUNLOOP_API_KEY environment variable to be set.
They make real API calls and create/manage actual devboxes.
"""
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from rl_cli.main import run


pytestmark = pytest.mark.skipif(
    not os.environ.get("RUNLOOP_API_KEY"),
    reason="RUNLOOP_API_KEY environment variable not set"
)


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content for devbox file operations")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_path:
        yield temp_path


class TestDevboxE2E:
    """End-to-end tests for devbox functionality."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for each test method."""
        self.created_devboxes = []
        
        yield
        
        # Cleanup any devboxes created during tests
        for devbox_id in self.created_devboxes:
            try:
                # Try to shutdown the devbox
                run(["devbox", "shutdown", devbox_id])
            except Exception as e:
                print(f"Failed to cleanup devbox {devbox_id}: {e}")

    def create_test_devbox(self, timeout=300):
        """Create a test devbox and wait for it to be ready."""
        import subprocess
        import json
        
        # Create devbox
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "create",
            "--architecture", "arm64",
            "--resources", "SMALL",
            "--entrypoint", "echo 'ready'"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            pytest.fail(f"Failed to create devbox: {result.stderr}")
        
        # Extract devbox ID from output
        output = result.stdout
        devbox_data = json.loads(output.split("create devbox=", 1)[1])
        devbox_id = devbox_data["id"]
        self.created_devboxes.append(devbox_id)
        
        # Wait for devbox to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = subprocess.run([
                "uv", "run", "rl", "devbox", "get", devbox_id
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                devbox_data = json.loads(result.stdout.split("devbox=", 1)[1])
                if devbox_data["status"] == "running":
                    return devbox_id
                elif devbox_data["status"] == "failure":
                    pytest.fail(f"Devbox {devbox_id} failed to start")
            
            time.sleep(5)
        
        pytest.fail(f"Devbox {devbox_id} did not become ready within {timeout} seconds")

    def test_ssh_key_creation(self):
        """Test SSH key creation for a devbox."""
        import subprocess
        import os
        
        devbox_id = self.create_test_devbox()
        
        # Test SSH key creation by attempting to get SSH config
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "ssh", devbox_id, "--config-only"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert f"Host {devbox_id}" in result.stdout
        assert "IdentityFile" in result.stdout
        assert "ProxyCommand" in result.stdout
        
        # Verify SSH key file was created
        key_path = os.path.expanduser(f"~/.runloop/ssh_keys/{devbox_id}.pem")
        assert os.path.exists(key_path)
        
        # Verify key file permissions
        stat = os.stat(key_path)
        assert oct(stat.st_mode)[-3:] == "600"

    def test_file_write_and_read(self, temp_file, temp_dir):
        """Test writing a file to devbox and reading it back."""
        import subprocess
        
        devbox_id = self.create_test_devbox()
        
        remote_path = "/tmp/test_file.txt"
        local_output = os.path.join(temp_dir, "downloaded_file.txt")
        
        # Write file to devbox
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "write-file",
            devbox_id, "--input", temp_file, "--remote", remote_path
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert f"Wrote local file {temp_file} to remote file {remote_path}" in result.stdout
        
        # Read file back from devbox
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "read-file", 
            devbox_id, "--remote", remote_path, "--output", local_output
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert f"Wrote remote file {remote_path} from devbox {devbox_id}" in result.stdout
        
        # Verify file contents match
        with open(temp_file, 'r') as f1, open(local_output, 'r') as f2:
            assert f1.read() == f2.read()

    def test_file_upload(self, temp_file):
        """Test uploading a file to devbox."""
        import subprocess
        
        devbox_id = self.create_test_devbox()
        
        remote_path = "/tmp/"
        
        # Upload file to devbox
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "upload-file",
            devbox_id, "--path", remote_path, "--file", temp_file
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert f"Uploaded file {temp_file} to {remote_path}" in result.stdout

    def test_command_execution(self):
        """Test executing commands on a devbox."""
        import subprocess
        import json
        
        devbox_id = self.create_test_devbox()
        
        # Execute a simple command
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "execute",
            devbox_id, "--command", "echo 'hello from devbox'"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        # The output should contain the execution result
        assert "hello from devbox" in result.stdout

    def test_devbox_lifecycle(self):
        """Test devbox suspend/resume lifecycle."""
        import subprocess
        import json
        
        devbox_id = self.create_test_devbox()
        
        # Suspend devbox
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "suspend", devbox_id
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        devbox_data = json.loads(result.stdout.split("devbox=", 1)[1])
        assert devbox_data["status"] in ["suspended", "suspending"]
        
        # Wait for suspension to complete
        time.sleep(10)
        
        # Resume devbox  
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "resume", devbox_id
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        devbox_data = json.loads(result.stdout.split("devbox=", 1)[1])
        assert devbox_data["status"] in ["running", "resuming"]

    @pytest.mark.skip(reason="SSH tunneling requires interactive session and is hard to test in CI")
    def test_ssh_tunnel(self):
        """Test SSH tunnel creation (skipped in CI due to interactive nature)."""
        # This would require more complex setup to test properly
        # as tunnels are interactive and require signal handling
        pass

    @pytest.mark.skip(reason="SSH connection requires interactive session and is hard to test in CI") 
    def test_ssh_connection(self):
        """Test SSH connection (skipped in CI due to interactive nature)."""
        # This would require more complex setup to test properly
        # as SSH is interactive
        pass