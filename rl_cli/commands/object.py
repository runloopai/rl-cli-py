"""Object command group implementation."""
import os
import io
import aiohttp
import mimetypes
from typing import Optional, Literal
from tabulate import tabulate
from ..utils import runloop_api_client

# Map common file extensions to MIME types
CONTENT_TYPE_MAP = {
    # Text files
    '.txt': 'text/plain',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.yaml': 'text/yaml',
    '.yml': 'text/yaml',
    '.csv': 'text/csv',
    '.md': 'text/plain',  # Markdown files as plain text
    
    # Application files
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.pdf': 'application/pdf',
    '.zip': 'application/zip',
    '.gz': 'application/gzip',
    '.tar': 'application/x-tar',
    '.tgz': 'application/x-tar+gzip',
    
    # Images
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
}

def detect_content_type(file_path: str) -> str:
    """Detect content type based on file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: API content type (e.g., 'TEXT_PLAIN', 'APPLICATION_JSON')
    """
    # Get the file extension (lowercase)
    ext = os.path.splitext(file_path)[1].lower()
    
    # Check our custom mapping first
    if ext in CONTENT_TYPE_MAP:
        return CONTENT_TYPE_MAP[ext]
    
    # For unknown types, return application/octet-stream
    return 'application/octet-stream'

async def list_objects(args) -> None:
    """List objects with optional filtering."""
    params = {}
    
    if hasattr(args, "limit"):
        params["limit"] = args.limit
    if hasattr(args, "starting_after"):
        params["starting_after"] = args.starting_after
    if hasattr(args, "name"):
        params["name"] = args.name
    if hasattr(args, "content_type"):
        params["content_type"] = args.content_type
    if hasattr(args, "state"):
        params["state"] = args.state
    if hasattr(args, "search"):
        params["search"] = args.search
    if hasattr(args, "is_public") and args.is_public:
        params["is_public"] = True

    # Use the public endpoint if specified
    if hasattr(args, "public") and args.public:
        objects = await runloop_api_client().objects.list_public(**params)
    else:
        objects = await runloop_api_client().objects.list(**params)

    # Convert objects to a list of dictionaries for tabulate
    table_data = []
    for obj in objects.objects:
        # Format size in human-readable format
        size = "N/A"
        if obj.size_bytes is not None:
            if obj.size_bytes < 1024:
                size = f"{obj.size_bytes} B"
            elif obj.size_bytes < 1024 * 1024:
                size = f"{obj.size_bytes / 1024:.1f} KB"
            else:
                size = f"{obj.size_bytes / (1024 * 1024):.1f} MB"
        
        table_data.append({
            "ID": obj.id,
            "Name": obj.name,
            "Type": obj.content_type,
            "State": obj.state,
            "Size": size
        })
    
    if not table_data:
        print("No objects found.")
        return
    
    # Print the table
    print(tabulate(table_data, headers="keys", tablefmt="grid"))

async def get(args) -> None:
    """Get a specific object."""
    assert args.id is not None
    object = await runloop_api_client().objects.retrieve(args.id)
    print(f"object={object.model_dump_json(indent=4)}")

async def download(args) -> None:
    """Download an object to a local file."""
    assert args.id is not None
    assert args.path is not None

    # Get the download URL
    duration_seconds = args.duration_seconds if hasattr(args, "duration_seconds") else 3600
    download_url_response = await runloop_api_client().objects.generate_download_url(
        args.id, duration_seconds=duration_seconds
    )
    download_url = download_url_response.download_url

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(args.path)), exist_ok=True)

    # Download the file
    async with aiohttp.ClientSession() as session:
        response = await session.get(download_url)
        if response.status != 200:
            raise RuntimeError(f"Failed to download file: HTTP {response.status}")
        
        # Get total size for progress reporting
        total_size = int(response.headers.get('content-length', 0))
        
        # Open file and write chunks
        with open(args.path, 'wb') as f:
            bytes_downloaded = 0
            async for chunk in response.content.iter_chunked(8192):
                f.write(chunk)
                bytes_downloaded += len(chunk)
                if total_size:
                    progress = (bytes_downloaded / total_size) * 100
                    print(f"\rDownloading: {progress:.1f}%", end='', flush=True)
            
            if total_size:
                print()  # New line after progress

    print(f"Downloaded object to {args.path}")

async def upload(args) -> None:
    """Upload a file as an object.
    
    The upload process consists of three steps:
    1. Create object and get upload URL
    2. Upload file content to the provided URL
    3. Mark upload as complete to transition from UPLOADING to READ_ONLY state
    """
    assert args.path is not None
    assert args.name is not None

    # Check if file exists and is accessible
    try:
        file_path = os.path.abspath(args.path)
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as _:
            pass  # Just testing if we can open the file
    except FileNotFoundError:
        raise RuntimeError(f"File not found: {args.path}")
    except PermissionError:
        raise RuntimeError(f"Permission denied accessing file: {args.path}")
    except OSError as e:
        raise RuntimeError(f"Error accessing file: {args.path} - {str(e)}")

    try:
        # Step 1: Create the object (initial state: UPLOADING)
        # Detect content type from file extension if not provided
        content_type = args.content_type if hasattr(args, "content_type") and args.content_type else detect_content_type(args.path)
        print(f"Using content type: {content_type}")
        
        create_response = await runloop_api_client().objects.create(
            name=args.name,
            content_type=content_type
        )
        object_id = create_response.id
        print(f"Created object {object_id} in UPLOADING state")

        # Step 2: Upload the file using the provided upload URL
        upload_url = create_response.upload_url
        async with aiohttp.ClientSession() as session:
            # Open and upload the file with progress tracking
            with open(file_path, 'rb') as f:
                bytes_uploaded = 0
                print(f"Uploading {args.path} ({file_size} bytes)...")

                # Create a progress tracking reader
                class ProgressReader(io.BufferedReader):
                    def __init__(self, file_path, total_size):
                        super().__init__(open(file_path, 'rb'))
                        self.total_size = total_size
                        self.bytes_read = 0

                    def read(self, size=-1):
                        chunk = super().read(size)
                        if chunk:
                            self.bytes_read += len(chunk)
                            progress = (self.bytes_read / self.total_size) * 100
                            print(f"\rProgress: {progress:.1f}%", end='', flush=True)
                        return chunk

                # Create a progress reader (close the original file as we'll reopen it)
                f.close()
                reader = ProgressReader(file_path, file_size)

                try:
                    # Perform the upload (PUT request as required by server)
                    headers = {'Content-Length': str(file_size)}  # Required for some servers
                    async with session.put(upload_url, data=reader, headers=headers) as response:
                        if response.status not in (200, 201, 204):
                            error_text = await response.text()
                            raise RuntimeError(f"Upload failed with status {response.status}: {error_text}")
                    print("\nUpload completed successfully.")
                finally:
                    reader.close()  # Ensure we close the file

        # Step 3: Complete the upload (transition to READ_ONLY state)
        try:
            await runloop_api_client().objects.complete(object_id)
            print(f"Object {object_id} ({args.name}) transitioned to READ_ONLY state")
        except Exception as e:
            print(f"\nWARNING: Failed to complete upload. Object {object_id} remains in UPLOADING state.")
            print("You can try completing it later using: rl objects complete {object_id}")
            raise RuntimeError(f"Failed to complete upload: {str(e)}")

    except aiohttp.ClientError as e:
        raise RuntimeError(f"Network error during upload: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error during upload: {str(e)}")