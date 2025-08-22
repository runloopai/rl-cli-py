"""Tests for object commands."""

import json
import os
import tempfile
from unittest.mock import AsyncMock, patch, mock_open
import pytest
from rl_cli.main import run
from rl_cli.utils import runloop_api_client

class MockObject:
    def __init__(self, id="test-obj-id", name="test.txt", content_type="text/plain", state="READ_ONLY", size_bytes=1024):
        self.id = id
        self.name = name
        self.content_type = content_type
        self.state = state
        self.size_bytes = size_bytes
        self.upload_url = "https://example.com/upload"

    def model_dump_json(self, indent=None):
        return json.dumps({
            "id": self.id,
            "name": self.name,
            "content_type": self.content_type,
            "state": self.state,
            "size_bytes": self.size_bytes,
            "upload_url": self.upload_url
        }, indent=indent)

@pytest.mark.asyncio
async def test_object_upload_success(capsys):
    """Test successful object upload."""
    # Create mock objects
    mock_object = MockObject()
    mock_response = AsyncMock()
    mock_response.status = 200

    # Create mock API client
    mock_api_client = AsyncMock()
    mock_api_client._platform = 'test-platform'
    mock_api_client.bearer_token = 'test-api-key'

    # Create mock objects resource
    mock_objects = AsyncMock()
    mock_objects.create = AsyncMock(return_value=mock_object)
    mock_objects.complete = AsyncMock(return_value=mock_object)
    mock_api_client.objects = mock_objects

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write("test content")
        temp_path = temp_file.name

    try:
        # Clear the cache to ensure we get a fresh client
        runloop_api_client.cache_clear()

        # Mock aiohttp ClientSession
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = AsyncMock()
        mock_session.__aenter__.return_value.put = AsyncMock(return_value=mock_response)

        with patch('aiohttp.ClientSession', return_value=mock_session), \
             patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
             patch('sys.argv', ['rl', 'object', 'upload', '--path', temp_path, '--name', 'test.txt']), \
             patch.dict('os.environ', {'RUNLOOP_API_KEY': 'test-api-key', 'RUNLOOP_ENV': 'dev'}):
            await run()

        # Check output
        captured = capsys.readouterr()
        assert "Created object test-obj-id in UPLOADING state" in captured.out
        assert "Upload completed successfully" in captured.out
        assert "transitioned to READ_ONLY state" in captured.out

        # Verify API calls
        mock_objects.create.assert_called_once()
        mock_objects.complete.assert_called_once_with("test-obj-id")

    finally:
        # Clean up temporary file
        os.unlink(temp_path)

@pytest.mark.asyncio
async def test_object_upload_file_not_found(capsys):
    """Test object upload with non-existent file."""
    # Create mock API client
    mock_api_client = AsyncMock()
    mock_api_client._platform = 'test-platform'
    mock_api_client.bearer_token = 'test-api-key'

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('sys.argv', ['rl', 'object', 'upload', '--path', '/nonexistent/file.txt', '--name', 'test.txt']), \
         patch.dict('os.environ', {'RUNLOOP_API_KEY': 'test-api-key', 'RUNLOOP_ENV': 'dev'}), \
         pytest.raises(RuntimeError) as exc_info:
        await run()

    assert "File not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_object_upload_content_type_detection(capsys):
    """Test content type detection during upload."""
    # Create mock objects
    mock_object = MockObject()
    mock_response = AsyncMock()
    mock_response.status = 200

    # Create mock API client
    mock_api_client = AsyncMock()
    mock_api_client._platform = 'test-platform'
    mock_api_client.bearer_token = 'test-api-key'

    # Create mock objects resource
    mock_objects = AsyncMock()
    mock_objects.create = AsyncMock(return_value=mock_object)
    mock_objects.complete = AsyncMock(return_value=mock_object)
    mock_api_client.objects = mock_objects

    # Test different file extensions
    test_cases = [
        ('test.json', 'application/json'),
        ('test.txt', 'text/plain'),
        ('test.md', 'text/plain'),
        ('test.png', 'image/png'),
        ('test.unknown', 'application/octet-stream'),
    ]

    for filename, expected_type in test_cases:
        # Clear the cache to ensure we get a fresh client
        runloop_api_client.cache_clear()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = temp_file.name

        try:
            # Mock aiohttp ClientSession
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = AsyncMock()
            mock_session.__aenter__.return_value.put = AsyncMock(return_value=mock_response)

            # Rename the temp file to have the correct extension
            new_path = temp_path + filename
            os.rename(temp_path, new_path)

            with patch('aiohttp.ClientSession', return_value=mock_session), \
                 patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
                 patch('sys.argv', ['rl', 'object', 'upload', '--path', new_path, '--name', filename]), \
                 patch.dict('os.environ', {'RUNLOOP_API_KEY': 'test-api-key', 'RUNLOOP_ENV': 'dev'}):
                await run()

            # Verify content type
            mock_objects.create.assert_called_with(name=filename, content_type=expected_type)
            mock_objects.create.reset_mock()

            # Clean up the renamed file
            os.unlink(new_path)

        except:
            # Clean up files in case of error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(new_path):
                os.unlink(new_path)
            raise

@pytest.mark.asyncio
async def test_object_delete_success(capsys):
    """Test successful object deletion."""
    # Create mock object
    mock_object = MockObject()

    # Create mock API client
    mock_api_client = AsyncMock()
    mock_api_client._platform = 'test-platform'
    mock_api_client.bearer_token = 'test-api-key'

    # Create mock objects resource
    mock_objects = AsyncMock()
    mock_objects.delete = AsyncMock(return_value=mock_object)
    mock_api_client.objects = mock_objects

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('sys.argv', ['rl', 'object', 'delete', '--id', 'test-obj-id']), \
         patch.dict('os.environ', {'RUNLOOP_API_KEY': 'test-api-key', 'RUNLOOP_ENV': 'dev'}):
        await run()

    # Check output
    captured = capsys.readouterr()
    assert "Successfully deleted object test-obj-id" in captured.out
    assert "Deleted object details" in captured.out

    # Verify API call
    mock_objects.delete.assert_called_once_with("test-obj-id")

@pytest.mark.asyncio
async def test_object_delete_not_found(capsys):
    """Test object deletion with non-existent ID."""
    # Create mock API client
    mock_api_client = AsyncMock()
    mock_api_client._platform = 'test-platform'
    mock_api_client.bearer_token = 'test-api-key'

    # Create mock objects resource with error
    mock_objects = AsyncMock()
    mock_objects.delete = AsyncMock(side_effect=Exception("Object not found"))
    mock_api_client.objects = mock_objects

    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()

    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('sys.argv', ['rl', 'object', 'delete', '--id', 'nonexistent-id']), \
         patch.dict('os.environ', {'RUNLOOP_API_KEY': 'test-api-key', 'RUNLOOP_ENV': 'dev'}), \
         pytest.raises(RuntimeError) as exc_info:
        await run()

    assert "Failed to delete object" in str(exc_info.value)
    assert "Object not found" in str(exc_info.value)