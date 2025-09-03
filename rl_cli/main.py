"""Main entry point for rl-cli."""
import argparse
import asyncio
import os
import sys

from . import __version__
from .utils import (
    get_latest_version,
    update_check_cache,
    should_check_for_updates,
    _parse_env_arg,
    _parse_code_mounts,
)
from .commands import devbox, blueprint, invocation, object

def check_for_updates():
    """Check for available updates."""
    if not should_check_for_updates():
        return
    
    latest_version = get_latest_version()
    if latest_version is None:
        update_check_cache()
        return
    
    current_version = __version__
    if latest_version != current_version:
        print(f"Update available: rl-cli {latest_version} (current: {current_version})", file=sys.stderr)
        print("Run 'uv tool upgrade rl-cli' to update", file=sys.stderr)
    
    update_check_cache()

async def update_check_command(args) -> None:
    """Command to manually check for updates."""
    latest_version = get_latest_version()
    if latest_version is None:
        print("Unable to check for updates")
        return
    
    current_version = __version__
    if latest_version != current_version:
        print(f"Update available: rl-cli {latest_version} (current: {current_version})")
        print("Run 'uv tool upgrade rl-cli' to update")
    else:
        print(f"rl-cli is up to date (version {current_version})")
    
    update_check_cache()

def setup_devbox_parser(subparsers):
    """Setup the devbox command parser."""
    parser = subparsers.add_parser("devbox", help="Manage devboxes")
    subparsers = parser.add_subparsers(dest="subcommand")

    # Create
    create_parser = subparsers.add_parser("create", help="Create a devbox")
    create_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.create(args)))
    create_parser.add_argument(
        "--launch_commands",
        help="Devbox initialization commands",
        action="append",
    )
    create_parser.add_argument("--entrypoint", type=str, help="Devbox entrypoint")
    create_parser.add_argument("--blueprint_id", type=str, help="Blueprint to use")
    create_parser.add_argument("--blueprint_name", type=str, help="Blueprint to use")
    create_parser.add_argument("--snapshot_id", type=str, help="Snapshot to use")
    create_parser.add_argument(
        "--env_vars",
        help="Environment variables (key=value)",
        type=_parse_env_arg,
        action="append",
    )
    create_parser.add_argument(
        "--code_mounts",
        help='Code mount dictionary',
        type=_parse_code_mounts,
        action="append",
    )
    create_parser.add_argument(
        "--idle_time",
        type=int,
        help="Idle time in seconds",
    )
    create_parser.add_argument(
        "--idle_action",
        type=str,
        choices=["shutdown", "suspend"],
        help="Action on idle",
    )
    create_parser.add_argument(
        "--resources",
        type=str,
        help="Resource size",
        choices=["X_SMALL", "SMALL", "MEDIUM", "LARGE", "X_LARGE", "XX_LARGE"],
    )
    create_parser.add_argument(
        "--architecture",
        type=str,
        help="Architecture (default: arm64)",
        choices=["arm64", "x86_64"],
    )
    create_parser.add_argument(
        "--root",
        action="store_true",
        help="Run as root",
    )

    # List
    list_parser = subparsers.add_parser("list", help="List devboxes")
    list_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.list_devboxes(args)))
    list_parser.add_argument(
        "--status",
        type=str,
        help="Filter by status",
        choices=[
            "initializing",
            "running",
            "suspending",
            "suspended",
            "resuming",
            "failure",
            "shutdown",
        ],
    )
    list_parser.add_argument(
        "--limit",
        type=int,
        help="Max results",
        default=20,
    )

    # Get
    get_parser = subparsers.add_parser("get", help="Get devbox")
    get_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.get(args)))
    get_parser.add_argument("--id", required=True, help="Devbox ID")

    # Execute
    execute_parser = subparsers.add_parser("execute", help="Execute command on devbox")
    execute_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.execute(args)))
    execute_parser.add_argument("--id", required=True, help="Devbox ID")
    execute_parser.add_argument("--command", required=True, help="Command to execute")
    execute_parser.add_argument("--shell_name", help="Shell name")

    # Execute async
    execute_async_parser = subparsers.add_parser("execute-async", help="Execute command asynchronously")
    execute_async_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.execute_async(args)))
    execute_async_parser.add_argument("--id", required=True, help="Devbox ID")
    execute_async_parser.add_argument("--command", required=True, help="Command to execute")
    execute_async_parser.add_argument("--shell_name", help="Shell name")

    # Get async execution
    get_async_exec_parser = subparsers.add_parser("get-async-exec", help="Get async execution status")
    get_async_exec_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.get_async_exec(args)))
    get_async_exec_parser.add_argument("--id", required=True, help="Devbox ID")
    get_async_exec_parser.add_argument("--execution_id", required=True, help="Execution ID")
    get_async_exec_parser.add_argument("--shell_name", help="Shell name")

    # Logs
    logs_parser = subparsers.add_parser("logs", help="Get devbox logs")
    logs_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.logs(args)))
    logs_parser.add_argument("--id", required=True, help="Devbox ID")

    # Suspend
    suspend_parser = subparsers.add_parser("suspend", help="Suspend devbox")
    suspend_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.suspend(args)))
    suspend_parser.add_argument("--id", required=True, help="Devbox ID")

    # Resume
    resume_parser = subparsers.add_parser("resume", help="Resume devbox")
    resume_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.resume(args)))
    resume_parser.add_argument("--id", required=True, help="Devbox ID")

    # Shutdown
    shutdown_parser = subparsers.add_parser("shutdown", help="Shutdown devbox")
    shutdown_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.shutdown(args)))
    shutdown_parser.add_argument("--id", required=True, help="Devbox ID")

    # SSH
    ssh_parser = subparsers.add_parser("ssh", help="SSH into devbox")
    ssh_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.ssh(args)))
    ssh_parser.add_argument("--id", required=True, help="Devbox ID")
    ssh_parser.add_argument("--no-wait", action="store_true", help="Don't wait for devbox to be ready")
    ssh_parser.add_argument("--timeout", type=int, default=180, help="Timeout in seconds")
    ssh_parser.add_argument("--poll-interval", type=int, default=3, help="Poll interval in seconds")
    ssh_parser.add_argument("--config-only", action="store_true", help="Print SSH config only")

    # SCP
    scp_parser = subparsers.add_parser("scp", help="SCP files to/from devbox")
    scp_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.scp(args)))
    scp_parser.add_argument("--id", required=True, help="Devbox ID")
    scp_parser.add_argument("--src", required=True, help="Source path")
    scp_parser.add_argument("--dst", required=True, help="Destination path")
    scp_parser.add_argument("--scp-options", help="Additional SCP options")

    # Rsync
    rsync_parser = subparsers.add_parser("rsync", help="Rsync files to/from devbox")
    rsync_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.rsync(args)))
    rsync_parser.add_argument("--id", required=True, help="Devbox ID")
    rsync_parser.add_argument("--src", required=True, help="Source path")
    rsync_parser.add_argument("--dst", required=True, help="Destination path")
    rsync_parser.add_argument("--rsync-options", help="Additional rsync options")

    # Tunnel
    tunnel_parser = subparsers.add_parser("tunnel", help="Create SSH tunnel to devbox")
    tunnel_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.tunnel(args)))
    tunnel_parser.add_argument("--id", required=True, help="Devbox ID")
    tunnel_parser.add_argument("--ports", required=True, help="Port mapping (local:remote)")

    # File operations
    read_file_parser = subparsers.add_parser("read-file", help="Read file from devbox")
    read_file_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.read_file(args)))
    read_file_parser.add_argument("--id", required=True, help="Devbox ID")
    read_file_parser.add_argument("--remote", required=True, help="Remote file path")
    read_file_parser.add_argument("--output", required=True, help="Local output file")

    write_file_parser = subparsers.add_parser("write-file", help="Write file to devbox")
    write_file_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.write_file(args)))
    write_file_parser.add_argument("--id", required=True, help="Devbox ID")
    write_file_parser.add_argument("--input", required=True, help="Local input file")
    write_file_parser.add_argument("--remote", required=True, help="Remote file path")

    upload_file_parser = subparsers.add_parser("upload-file", help="Upload file to devbox")
    upload_file_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.upload_file(args)))
    upload_file_parser.add_argument("--id", required=True, help="Devbox ID")
    upload_file_parser.add_argument("--file", required=True, help="File to upload")
    upload_file_parser.add_argument("--path", required=True, help="Remote path")

    download_file_parser = subparsers.add_parser("download-file", help="Download file from devbox")
    download_file_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.download_file(args)))
    download_file_parser.add_argument("--id", required=True, help="Devbox ID")
    download_file_parser.add_argument("--file-path", required=True, help="Remote file path")
    download_file_parser.add_argument("--output-path", required=True, help="Local output path")

    # Snapshot operations
    snapshot_parser = subparsers.add_parser("snapshot", help="Create devbox snapshot")
    snapshot_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.snapshot(args)))
    snapshot_parser.add_argument("--devbox-id", required=True, help="Devbox ID")

    get_snapshot_status_parser = subparsers.add_parser("get-snapshot-status", help="Get snapshot status")
    get_snapshot_status_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.get_snapshot_status(args)))
    get_snapshot_status_parser.add_argument("--snapshot-id", required=True, help="Snapshot ID")

    list_snapshots_parser = subparsers.add_parser("list-snapshots", help="List snapshots")
    list_snapshots_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.list_snapshots(args)))

def setup_blueprint_parser(subparsers):
    """Setup the blueprint command parser."""
    parser = subparsers.add_parser("blueprint", help="Manage blueprints")
    subparsers = parser.add_subparsers(dest="subcommand")

    # List
    list_parser = subparsers.add_parser("list", help="List blueprints")
    list_parser.add_argument(
        "--name", help="Blueprint name.", type=str, required=False
    )
    list_parser.set_defaults(func=lambda args: asyncio.create_task(blueprint.list_blueprints(args)))

    # Create
    create_parser = subparsers.add_parser("create", help="Create blueprint")
    create_parser.set_defaults(func=lambda args: asyncio.create_task(blueprint.create(args)))
    create_parser.add_argument("--name", required=True, help="Blueprint name")
    create_parser.add_argument(
        "--system_setup_commands",
        help="System setup commands",
        action="append",
    )
    create_parser.add_argument("--dockerfile", help="Dockerfile contents")
    create_parser.add_argument("--dockerfile_path", help="Dockerfile path")
    create_parser.add_argument(
        "--resources",
        type=str,
        help="Resource size",
        choices=["X_SMALL", "SMALL", "MEDIUM", "LARGE", "X_LARGE", "XX_LARGE"],
    )
    create_parser.add_argument(
        "--available_ports",
        type=int,
        nargs="+",
        help="Available ports",
    )
    create_parser.add_argument(
        "--architecture",
        type=str,
        help="Architecture (default: arm64)",
        choices=["arm64", "x86_64"],
    )
    create_parser.add_argument(
        "--root",
        action="store_true",
        help="Run as root",
    )

    # ... Add other blueprint subcommands similarly ...

def setup_invocation_parser(subparsers):
    """Setup the invocation command parser."""
    parser = subparsers.add_parser("invocation", help="Manage invocations")
    subparsers = parser.add_subparsers(dest="subcommand")

    # Get
    get_parser = subparsers.add_parser("get", help="Get invocation")
    get_parser.set_defaults(func=lambda args: asyncio.create_task(invocation.get(args)))
    get_parser.add_argument("--id", required=True, help="Invocation ID")

    # ... Add other invocation subcommands similarly ...

def setup_object_parser(subparsers):
    """Setup the object command parser."""
    parser = subparsers.add_parser("object", help="Manage objects")
    subparsers = parser.add_subparsers(dest="subcommand")

    # List
    list_parser = subparsers.add_parser("list", help="List objects")
    list_parser.set_defaults(func=lambda args: asyncio.create_task(object.list_objects(args)))
    list_parser.add_argument(
        "--limit",
        type=int,
        help="Max results",
        default=20,
    )
    list_parser.add_argument(
        "--starting_after",
        type=str,
        help="Starting point for pagination",
    )
    list_parser.add_argument(
        "--name",
        type=str,
        help="Filter by name (partial match supported)",
    )
    list_parser.add_argument(
        "--content_type",
        type=str,
        help="Filter by content type",
    )
    list_parser.add_argument(
        "--state",
        type=str,
        help="Filter by state (UPLOADING, READ_ONLY, DELETED)",
        choices=["UPLOADING", "READ_ONLY", "DELETED"],
    )
    list_parser.add_argument(
        "--search",
        type=str,
        help="Search by object ID or name",
    )
    list_parser.add_argument(
        "--public",
        action="store_true",
        help="List public objects only",
    )

    # Get
    get_parser = subparsers.add_parser("get", help="Get object")
    get_parser.set_defaults(func=lambda args: asyncio.create_task(object.get(args)))
    get_parser.add_argument("--id", required=True, help="Object ID")

    # Download
    download_parser = subparsers.add_parser("download", help="Download object to local file")
    download_parser.set_defaults(func=lambda args: asyncio.create_task(object.download(args)))
    download_parser.add_argument("--id", required=True, help="Object ID")
    download_parser.add_argument("--path", required=True, help="Local path to save the file")
    download_parser.add_argument("--extract", action="store_true", help="Extract downloaded archive after download (supports .zip, .tar.gz, .tgz, .zst, .tar.zst)")
    download_parser.add_argument(
        "--duration_seconds",
        type=int,
        help="Duration in seconds for the presigned URL validity (default: 3600)",
        default=3600,
    )

    # Upload
    upload_parser = subparsers.add_parser("upload", help="Upload a file as an object")
    upload_parser.set_defaults(func=lambda args: asyncio.create_task(object.upload(args)))
    upload_parser.add_argument("--path", required=True, help="Path to the file to upload")
    upload_parser.add_argument("--name", required=True, help="Name for the object")
    upload_parser.add_argument(
        "--content_type",
        help="Content type: unspecified|text|binary|gzip|tar|tgz (auto-detected if omitted)",
        choices=["unspecified", "text", "binary", "gzip", "tar", "tgz"],
    )

    # Delete
    delete_parser = subparsers.add_parser("delete", help="Delete an object (irreversible)")
    delete_parser.set_defaults(func=lambda args: asyncio.create_task(object.delete(args)))
    delete_parser.add_argument("--id", required=True, help="Object ID to delete")

async def run():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Perform various devbox operations.")
    parser.add_argument("--version", action="version", version=f"rl-cli {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Setup command parsers
    setup_devbox_parser(subparsers)
    setup_blueprint_parser(subparsers)
    setup_invocation_parser(subparsers)
    setup_object_parser(subparsers)

    # Hidden update check command
    update_check_parser = subparsers.add_parser("_update_check", add_help=False)
    update_check_parser.set_defaults(
        func=lambda args: asyncio.create_task(update_check_command(args))
    )

    args = parser.parse_args()
    if hasattr(args, "func"):
        if not os.getenv("RUNLOOP_API_KEY"):
            raise RuntimeError("API key not found, RUNLOOP_API_KEY must be set")

        # Print environment message unless it's SSH config-only
        should_suppress_env_message = (
            args.command == "devbox"
            and hasattr(args, "subcommand")
            and args.subcommand == "ssh"
            and hasattr(args, "config_only")
            and args.config_only
        )

        if not should_suppress_env_message:
            env = os.getenv("RUNLOOP_ENV")
            if env and env.lower() == "dev":
                print("Using dev environment", file=sys.stderr)
            else:
                print("Using prod environment", file=sys.stderr)

        # Check for updates in background
        try:
            check_for_updates()
        except Exception:
            pass  # Silently ignore update check failures

        await args.func(args)
    else:
        parser.print_help()

def main():
    """CLI entry point."""
    try:
        asyncio.run(run())
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()