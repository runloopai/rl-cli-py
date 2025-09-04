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
                import subprocess
                subprocess.run([
                    "uv", "run", "rl", "devbox", "shutdown", "--id", devbox_id
                ], capture_output=True, text=True)
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
                "uv", "run", "rl", "devbox", "get", "--id", devbox_id
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
            "uv", "run", "rl", "devbox", "ssh", "--id", devbox_id, "--config-only"
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

    def test_logs_and_exec_async(self):
        """Test logs retrieval and async execution on a devbox."""
        import subprocess
        import json
        
        devbox_id = self.create_test_devbox()
        
        # Trigger logs by running a simple command
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "exec",
            "--id", devbox_id, "--command", "echo 'log-line'"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Fetch logs; should at least return successfully
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "logs", "--id", devbox_id
        ], capture_output=True, text=True)
        assert result.returncode == 0
        # Non-strict assertion: any output produced
        assert result.stdout.strip() != ""
        
        # Start async command
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "exec_async",
            "--id", devbox_id, "--command", "echo 'async'"
        ], capture_output=True, text=True)
        assert result.returncode == 0
        # Extract execution id from JSON
        exec_json = json.loads(result.stdout.split("execution=", 1)[1])
        execution_id = exec_json.get("id")
        assert execution_id
        
        # Query async execution
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "get_async",
            "--id", devbox_id, "--execution_id", execution_id
        ], capture_output=True, text=True)
        assert result.returncode == 0

    def test_devbox_read_write_api(self, temp_dir):
        """Test writing to and reading from a devbox via API wrappers."""
        import subprocess
        import os
        
        devbox_id = self.create_test_devbox()
        remote_path = "/tmp/e2e_api_rw.txt"
        local_input = os.path.join(temp_dir, "input.txt")
        local_output = os.path.join(temp_dir, "output.txt")
        
        with open(local_input, 'w') as f:
            f.write("hello via api")
        
        # Write
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "write",
            "--id", devbox_id, "--input", local_input, "--remote", remote_path
        ], capture_output=True, text=True)
        assert result.returncode == 0
        
        # Read
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "read",
            "--id", devbox_id, "--remote", remote_path, "--output", local_output
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert os.path.exists(local_output)
        with open(local_output, 'r') as f:
            assert f.read() == "hello via api"

    def test_command_execution(self):
        """Test executing commands on a devbox."""
        import subprocess
        import json
        
        devbox_id = self.create_test_devbox()
        
        # Execute a simple command
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "exec",
            "--id", devbox_id, "--command", "echo 'hello from devbox'"
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
            "uv", "run", "rl", "devbox", "suspend", "--id", devbox_id
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        devbox_data = json.loads(result.stdout.split("devbox=", 1)[1])
        assert devbox_data["status"] in ["suspended", "suspending"]
        
        # Wait for suspension to complete
        time.sleep(10)
        
        # Resume devbox  
        result = subprocess.run([
            "uv", "run", "rl", "devbox", "resume", "--id", devbox_id
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