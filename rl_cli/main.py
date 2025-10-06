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
    _parse_user,
)
from .commands import devbox, blueprint, object


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
        print(
            f"Update available: rl-cli {latest_version} (current: {current_version})",
            file=sys.stderr,
        )
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
    create_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.create(args))
    )
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
        help="Code mount dictionary",
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
    create_parser.add_argument(
        "--user", type=_parse_user, metavar="USER:UID", help="Run as this user"
    )

    # List
    list_parser = subparsers.add_parser("list", help="List devboxes")
    list_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.list_devboxes(args))
    )
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

    # Exec (synchronous)
    exec_parser = subparsers.add_parser("exec", help="Execute a command on a devbox")
    exec_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.execute(args))
    )
    exec_parser.add_argument("--id", required=True, help="Devbox ID")
    exec_parser.add_argument("--command", required=True, help="Command to execute")
    exec_parser.add_argument(
        "--shell_name", required=False, help="Shell name to use (optional)"
    )

    # Exec (asynchronous)
    exec_async_parser = subparsers.add_parser(
        "exec_async", help="Execute a command asynchronously on a devbox"
    )
    exec_async_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.execute_async(args))
    )
    exec_async_parser.add_argument("--id", required=True, help="Devbox ID")
    exec_async_parser.add_argument(
        "--command", required=True, help="Command to execute"
    )
    exec_async_parser.add_argument(
        "--shell_name", required=False, help="Shell name to use (optional)"
    )

    # Get async execution status
    get_async_parser = subparsers.add_parser(
        "get_async", help="Get status of an async execution"
    )
    get_async_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.get_async_exec(args))
    )
    get_async_parser.add_argument("--id", required=True, help="Devbox ID")
    get_async_parser.add_argument("--execution_id", required=True, help="Execution ID")

    # Send stdin to async execution
    send_stdin_parser = subparsers.add_parser(
        "send_stdin", help="Send stdin to a running async execution"
    )
    send_stdin_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.send_stdin(args))
    )
    send_stdin_parser.add_argument("--id", required=True, help="Devbox ID")
    send_stdin_parser.add_argument("--execution_id", required=True, help="Execution ID")
    stdin_group = send_stdin_parser.add_mutually_exclusive_group(required=True)
    stdin_group.add_argument("--text", help="Text content to send to stdin")
    stdin_group.add_argument(
        "--signal", choices=["EOF", "INTERRUPT"], help="Signal to send"
    )

    # Logs
    logs_parser = subparsers.add_parser("logs", help="View devbox logs")
    logs_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.logs(args)))
    logs_parser.add_argument("--id", required=True, help="Devbox ID")

    # Suspend / Resume / Shutdown
    suspend_parser = subparsers.add_parser("suspend", help="Suspend a devbox")
    suspend_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.suspend(args))
    )
    suspend_parser.add_argument("--id", required=True, help="Devbox ID")

    resume_parser = subparsers.add_parser("resume", help="Resume a devbox")
    resume_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.resume(args))
    )
    resume_parser.add_argument("--id", required=True, help="Devbox ID")

    shutdown_parser = subparsers.add_parser("shutdown", help="Shutdown a devbox")
    shutdown_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.shutdown(args))
    )
    shutdown_parser.add_argument("--id", required=True, help="Devbox ID")

    # SSH
    ssh_parser = subparsers.add_parser("ssh", help="SSH into a devbox")
    ssh_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.ssh(args)))
    ssh_parser.add_argument("--id", required=True, help="Devbox ID")
    ssh_parser.add_argument(
        "--config-only",
        dest="config_only",
        action="store_true",
        help="Print SSH config only",
    )
    ssh_parser.add_argument(
        "--no-wait",
        dest="no_wait",
        action="store_true",
        help="Do not wait for devbox to be ready",
    )
    ssh_parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Timeout in seconds to wait for readiness",
    )
    ssh_parser.add_argument(
        "--poll-interval",
        dest="poll_interval",
        type=int,
        default=3,
        help="Polling interval in seconds while waiting",
    )

    # SCP
    scp_parser = subparsers.add_parser(
        "scp", help="Copy files to/from a devbox using scp"
    )
    scp_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.scp(args)))
    scp_parser.add_argument("src", help="Source path. Use :remote_path for remote")
    scp_parser.add_argument("dst", help="Destination path. Use :remote_path for remote")
    scp_parser.add_argument("--id", required=True, help="Devbox ID")
    scp_parser.add_argument(
        "--scp-options", dest="scp_options", help="Additional scp options (quoted)"
    )

    # Rsync
    rsync_parser = subparsers.add_parser(
        "rsync", help="Sync files to/from a devbox using rsync"
    )
    rsync_parser.set_defaults(func=lambda args: asyncio.create_task(devbox.rsync(args)))
    rsync_parser.add_argument("src", help="Source path. Use :remote_path for remote")
    rsync_parser.add_argument(
        "dst", help="Destination path. Use :remote_path for remote"
    )
    rsync_parser.add_argument("--id", required=True, help="Devbox ID")
    rsync_parser.add_argument(
        "--rsync-options",
        dest="rsync_options",
        help="Additional rsync options (quoted)",
    )

    # Tunnel
    tunnel_parser = subparsers.add_parser(
        "tunnel", help="Create a port-forwarding tunnel to a devbox"
    )
    tunnel_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.tunnel(args))
    )
    tunnel_parser.add_argument("--id", required=True, help="Devbox ID")
    tunnel_parser.add_argument("ports", help="Port mapping in the form local:remote")

    # File operations via API wrappers
    read_file_parser = subparsers.add_parser(
        "read", help="Read a file from a devbox using the API"
    )
    read_file_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.devbox_read(args))
    )
    read_file_parser.add_argument("--id", required=True, help="ID of the devbox")
    read_file_parser.add_argument(
        "--remote", required=True, help="Remote file path to read from the devbox"
    )
    read_file_parser.add_argument(
        "--output", required=True, help="Local file path to write the contents to"
    )

    write_file_parser = subparsers.add_parser(
        "write", help="Write a file to a devbox using the API"
    )
    write_file_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.devbox_write(args))
    )
    write_file_parser.add_argument("--id", required=True, help="ID of the devbox")
    write_file_parser.add_argument(
        "--input", required=True, help="Local file path to read contents from"
    )
    write_file_parser.add_argument(
        "--remote", required=True, help="Remote file path to write to on the devbox"
    )

    upload_file_parser = subparsers.add_parser(
        "upload_file", help="Upload a file to a devbox"
    )
    upload_file_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.upload_file(args))
    )
    upload_file_parser.add_argument("--id", required=True, help="ID of the devbox")
    upload_file_parser.add_argument(
        "--path", required=True, help="Path where to save the file in the devbox"
    )
    upload_file_parser.add_argument(
        "--file", required=True, help="Path to the local file to upload"
    )

    download_file_parser = subparsers.add_parser(
        "download_file", help="Download a file from a devbox"
    )
    download_file_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.download_file(args))
    )
    download_file_parser.add_argument("--id", required=True, help="ID of the devbox")
    download_file_parser.add_argument(
        "--file_path", required=True, help="Path to the file in the devbox"
    )
    download_file_parser.add_argument(
        "--output_path",
        required=True,
        help="Local path where to save the downloaded file",
    )

    # Snapshot operations
    snapshot_parser = subparsers.add_parser("snapshot", help="Manage devbox snapshots")
    snapshot_subparsers = snapshot_parser.add_subparsers(dest="snapshot_subcommand")

    snapshot_create_parser = snapshot_subparsers.add_parser(
        "create", help="Create a snapshot of a devbox"
    )
    snapshot_create_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.snapshot(args))
    )
    snapshot_create_parser.add_argument("--devbox_id", required=True, help="Devbox ID")

    snapshot_status_parser = snapshot_subparsers.add_parser(
        "status", help="Get snapshot status"
    )
    snapshot_status_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.get_snapshot_status(args))
    )
    snapshot_status_parser.add_argument(
        "--snapshot_id", required=True, help="Snapshot ID"
    )

    snapshot_list_parser = snapshot_subparsers.add_parser("list", help="List snapshots")
    snapshot_list_parser.set_defaults(
        func=lambda args: asyncio.create_task(devbox.list_snapshots(args))
    )


def setup_blueprint_parser(subparsers):
    """Setup the blueprint command parser."""
    parser = subparsers.add_parser("blueprint", help="Manage blueprints")
    subparsers = parser.add_subparsers(dest="subcommand")

    # List
    list_parser = subparsers.add_parser("list", help="List blueprints")
    list_parser.add_argument("--name", help="Blueprint name.", type=str, required=False)
    list_parser.set_defaults(
        func=lambda args: asyncio.create_task(blueprint.list_blueprints(args))
    )

    # Create
    create_parser = subparsers.add_parser("create", help="Create blueprint")
    create_parser.set_defaults(
        func=lambda args: asyncio.create_task(blueprint.create(args))
    )
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
    create_parser.add_argument(
        "--user", type=_parse_user, metavar="USER:UID", help="Run as this user"
    )

    # Preview
    preview_parser = subparsers.add_parser(
        "preview", help="Preview blueprint before creation"
    )
    preview_parser.set_defaults(
        func=lambda args: asyncio.create_task(blueprint.preview(args))
    )
    preview_parser.add_argument("--name", required=True, help="Blueprint name")
    preview_parser.add_argument(
        "--system_setup_commands",
        help="System setup commands",
        action="append",
    )
    preview_parser.add_argument("--dockerfile", help="Dockerfile contents")

    # Get
    get_parser = subparsers.add_parser("get", help="Get blueprint details")
    get_parser.set_defaults(func=lambda args: asyncio.create_task(blueprint.get(args)))
    get_parser.add_argument("--id", required=True, help="Blueprint ID")

    # Logs
    logs_parser = subparsers.add_parser("logs", help="Get blueprint build logs")
    logs_parser.set_defaults(
        func=lambda args: asyncio.create_task(blueprint.logs(args))
    )
    logs_parser.add_argument("--id", required=True, help="Blueprint ID")


def setup_object_parser(subparsers):
    """Setup the object command parser."""
    parser = subparsers.add_parser("object", help="Manage objects")
    subparsers = parser.add_subparsers(dest="subcommand")

    # List
    list_parser = subparsers.add_parser("list", help="List objects")
    list_parser.set_defaults(
        func=lambda args: asyncio.create_task(object.list_objects(args))
    )
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
    download_parser = subparsers.add_parser(
        "download", help="Download object to local file"
    )
    download_parser.set_defaults(
        func=lambda args: asyncio.create_task(object.download(args))
    )
    download_parser.add_argument("--id", required=True, help="Object ID")
    download_parser.add_argument(
        "--path", required=True, help="Local path to save the file"
    )
    download_parser.add_argument(
        "--extract",
        action="store_true",
        help="Extract downloaded archive after download (supports .zip, .tar.gz, .tgz, .zst, .tar.zst)",
    )
    download_parser.add_argument(
        "--duration_seconds",
        type=int,
        help="Duration in seconds for the presigned URL validity (default: 3600)",
        default=3600,
    )

    # Upload
    upload_parser = subparsers.add_parser("upload", help="Upload a file as an object")
    upload_parser.set_defaults(
        func=lambda args: asyncio.create_task(object.upload(args))
    )
    upload_parser.add_argument(
        "--path", required=True, help="Path to the file to upload"
    )
    upload_parser.add_argument("--name", required=True, help="Name for the object")
    upload_parser.add_argument(
        "--content_type",
        help="Content type: unspecified|text|binary|gzip|tar|tgz (auto-detected if omitted)",
        choices=["unspecified", "text", "binary", "gzip", "tar", "tgz"],
    )

    # Delete
    delete_parser = subparsers.add_parser(
        "delete", help="Delete an object (irreversible)"
    )
    delete_parser.set_defaults(
        func=lambda args: asyncio.create_task(object.delete(args))
    )
    delete_parser.add_argument("--id", required=True, help="Object ID to delete")


async def run():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Perform various devbox operations.")
    parser.add_argument("--version", action="version", version=f"rl-cli {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Setup command parsers
    setup_devbox_parser(subparsers)
    setup_blueprint_parser(subparsers)
    setup_object_parser(subparsers)

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
