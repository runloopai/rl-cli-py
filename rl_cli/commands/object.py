"""Object command group implementation."""
import os
import aiohttp
from typing import Optional
from ..utils import runloop_api_client

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

    print(f"objects={objects.model_dump_json(indent=4)}")

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