"""Tests for object commands."""

import json
import os
from unittest.mock import AsyncMock, patch, mock_open
import pytest
import aiohttp
from rl_cli.main import run
from rl_cli.utils import runloop_api_client

@pytest.mark.asyncio
async def test_object_list(capsys):
    """Test the object list command."""
    class MockObject:
        def model_dump_json(self, indent=None):
            return json.dumps({
                "id": "test-object-id",
                "name": "test.txt",
                "content_type": "text/plain",
                "state": "READ_ONLY",
                "created_at": "2024-01-01T00:00:00Z"
            }, indent=indent)
    
    mock_object = MockObject()
    
    # Create mock API client
    mock_api_client = AsyncMock()
    mock_api_client._platform = 'test-platform'
    mock_api_client.bearer_token = 'test-api-key'
    
    # Create mock objects
    mock_objects = AsyncMock()
    mock_objects.list = AsyncMock()
    
    # Create mock response
    class MockResponse:
        def __init__(self):
            self.objects = [mock_object]
            self.has_more = False
            self.total_count = 1
            self.remaining_count = 0
        
        def model_dump_json(self, indent=None):
            return json.dumps({
                "objects": [json.loads(obj.model_dump_json()) for obj in self.objects],
                "has_more": self.has_more,
                "total_count": self.total_count,
                "remaining_count": self.remaining_count
            }, indent=indent)
    
    mock_objects.list.return_value = MockResponse()
    mock_api_client.objects = mock_objects
    
    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()
    
    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('sys.argv', ['rl', 'object', 'list']):
        await run()
        
    captured = capsys.readouterr()
    assert "objects=" in captured.out
    output = json.loads(captured.out.split("objects=")[-1].strip())
    assert "objects" in output
    assert len(output["objects"]) == 1
    assert output["objects"][0]["id"] == "test-object-id"

@pytest.mark.asyncio
async def test_object_get(capsys):
    """Test the object get command."""
    class MockObject:
        def model_dump_json(self, indent=None):
            return json.dumps({
                "id": "test-object-id",
                "name": "test.txt",
                "content_type": "text/plain",
                "state": "READ_ONLY",
                "created_at": "2024-01-01T00:00:00Z"
            }, indent=indent)
    
    mock_object = MockObject()
    
    # Create mock API client
    mock_api_client = AsyncMock()
    mock_api_client._platform = 'test-platform'
    mock_api_client.bearer_token = 'test-api-key'
    
    # Create mock objects
    mock_objects = AsyncMock()
    mock_objects.retrieve = AsyncMock(return_value=mock_object)
    mock_api_client.objects = mock_objects
    
    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()
    
    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('sys.argv', ['rl', 'object', 'get', '--id', 'test-object-id']):
        await run()
        
    captured = capsys.readouterr()
    assert "object=" in captured.out
    output = json.loads(captured.out.split("object=")[-1].strip())
    assert output["id"] == "test-object-id"

@pytest.mark.asyncio
async def test_object_download(capsys, tmp_path):
    """Test the object download command."""
    # Create mock download URL response
    class MockDownloadUrlResponse:
        def __init__(self):
            self.download_url = "https://example.com/test.txt"
    
    # Create mock API client
    mock_api_client = AsyncMock()
    mock_api_client._platform = 'test-platform'
    mock_api_client.bearer_token = 'test-api-key'
    
    # Create mock objects client
    mock_objects = AsyncMock()
    mock_objects.generate_download_url = AsyncMock(return_value=MockDownloadUrlResponse())
    mock_api_client.objects = mock_objects
    
    # Create mock aiohttp response
    class MockResponse:
        def __init__(self):
            self.status = 200
            self.headers = {'content-length': '100'}
            self.content = AsyncMock()
            async def mock_iter_chunked(chunk_size):
                yield b'test content'
            self.content.iter_chunked = mock_iter_chunked
    
        async def __aenter__(self):
            return self
    
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    # Create mock aiohttp client session
    class MockClientSession:
        def __init__(self):
            self.response = MockResponse()
            self.get = AsyncMock()
            self.get.return_value = self.response
    
        async def __aenter__(self):
            return self
    
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()
    
    # Create a temporary file path
    test_file = tmp_path / "test.txt"
    
    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('aiohttp.ClientSession', return_value=MockClientSession()), \
         patch('sys.argv', ['rl', 'object', 'download', '--id', 'test-object-id', '--path', str(test_file)]):
        await run()
    
    # Check that the file was created
    assert test_file.exists()
    assert test_file.read_bytes() == b'test content'
    
    # Check output
    captured = capsys.readouterr()
    assert f"Downloaded object to {test_file}" in captured.out

@pytest.mark.asyncio
async def test_object_download_error_handling(capsys):
    """Test error handling in object download command."""
    # Create mock download URL response
    class MockDownloadUrlResponse:
        def __init__(self):
            self.download_url = "https://example.com/test.txt"
    
    # Create mock API client
    mock_api_client = AsyncMock()
    mock_api_client._platform = 'test-platform'
    mock_api_client.bearer_token = 'test-api-key'
    
    # Create mock objects client
    mock_objects = AsyncMock()
    mock_objects.generate_download_url = AsyncMock(return_value=MockDownloadUrlResponse())
    mock_api_client.objects = mock_objects
    
    # Create mock aiohttp response with error
    class MockErrorResponse:
        def __init__(self):
            self.status = 404
    
        async def __aenter__(self):
            return self
    
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    # Create mock aiohttp client session
    class MockClientSession:
        def __init__(self):
            self.response = MockErrorResponse()
            self.get = AsyncMock()
            self.get.return_value = self.response
    
        async def __aenter__(self):
            return self
    
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    # Clear the cache to ensure we get a fresh client
    runloop_api_client.cache_clear()
    
    with patch('rl_cli.utils.AsyncRunloop', return_value=mock_api_client), \
         patch('aiohttp.ClientSession', return_value=MockClientSession()), \
         patch('sys.argv', ['rl', 'object', 'download', '--id', 'test-object-id', '--path', 'test.txt']), \
         pytest.raises(RuntimeError) as exc_info:
        await run()
    
    assert "Failed to download file: HTTP 404" in str(exc_info.value)