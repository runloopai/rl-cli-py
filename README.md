# rl-cli
A command line utility for interacting with runloop APIs.

**NOTE: This project is still in early alpha release**

# Table of Contents
- [Setup](#setup)
  - [Install using pipx](#install-using-pipx)
  - [For developers](#for-developers)
- [Quick Reference](#quick-reference)
  - [Devbox](#devbox)
  - [Blueprint](#blueprint)
  - [Snapshot](#snapshot)
- [Command Reference](#command-reference)
  - [Devbox Commands](#devbox-commands)
    - [Create a Devbox](#create-a-devbox)
    - [List Devboxes](#list-devboxes)
    - [Get Devbox Details](#get-devbox-details)
    - [Execute Commands](#execute-commands)
    - [SSH Access](#ssh-access)
    - [File Transfer](#file-transfer)
    - [Port Forwarding](#port-forwarding)
    - [Devbox Management](#devbox-management)
  - [Blueprint Commands](#blueprint-commands)
    - [Create Blueprint](#create-blueprint)
    - [Preview Blueprint](#preview-blueprint)
    - [List Blueprints](#list-blueprints)
    - [Get Blueprint Details](#get-blueprint-details)
    - [View Blueprint Logs](#view-blueprint-logs)
  - [Snapshot Commands](#snapshot-commands)
    - [Create Snapshot](#create-snapshot)
    - [Check Snapshot Status](#check-snapshot-status)
    - [List Snapshots](#list-snapshots)
  - [Invocation Commands](#invocation-commands)
    - [Get Invocation Details](#get-invocation-details)

# Setup

## Install using pipx

```
➜  ~  pipx install rl-cli
  installed package rl-cli 0.0.1, installed using Python 3.12.6
  These apps are now globally available
```

## For developers
```commandline
# Clone the repo
mkdir -p ~/source/ && cd ~/source/
git clone https://github.com/runloopai/rl-cli.git
cd rl-cli/

# Setup the venv and dev tools
python3 -m venv .venv && source .venv/bin/activate && pip install -r dev-requirements.txt

# Install to your venv with flink
# Use 'which python3' to find your system python
flit install --symlink --python </path/to/system/python>

# Install to your venv using pip
pip install rl-cli
```

```
# In a new terminal
export RUNLOOP_API_KEY=<your-api-key>
rl --help
```

# Quick reference

## Devbox

### Create a devbox and run a single command
```commandline
rl devbox create --env_vars HELLO=world --entrypoint 'echo $HELLO'
>
create devbox={
    "id": "dbx_2xMDUOsKMiZBYKsvSRtMA",
    "blueprint_id": null,
    "create_time_ms": 1723229557715,
    "end_time_ms": null,
    "initiator_id": null,
    "initiator_type": "invocation",
    "name": null,
    "status": "provisioning"
}
```

### Observe logs
```commandline
rl devbox logs --id dbx_2xMDUOsKMiZBYKsvSRtMA
>
2024-08-09 12:15:01.701  Initializing devbox...
2024-08-09 12:15:01.734  Devbox setup complete
2024-08-09 12:15:01.769 [entrypoint] -> echo $HELLO
2024-08-09 12:15:01.798 [entrypoint]  world
2024-08-09 12:15:01.798  world
2024-08-09 12:15:01.800 [entrypoint] -> exit_code=0
```

### Check the devbox status
```commandline
rl devbox get --id dbx_2ws7IOtjxnJgLsBIpU9nn
>   
# Note that the devbox status="shutdown" after the entrypoint completes.
devbox={
    "id": "dbx_2xMDUOsKMiZBYKsvSRtMA",
    "blueprint_id": null,
    "create_time_ms": 1723229557715,
    "end_time_ms": 1723229561620,
    "initiator_id": null,
    "initiator_type": "invocation",
    "name": null,
    "status": "shutdown"
}
```


### Use scp to copy files to/from the devbox
```commandline
To use the SCP command:
   rl devbox scp local_file.txt :remote_file.txt --id <devbox_id>

To copy a file from the devbox to your local machine:
   rl devbox scp :remote_file.txt local_file.txt --id <devbox_id>
```

### Use rsync to copy files to/from the devbox
```commandline
To use the rsync command:
   rl devbox rsync local_file.txt :remote_file.txt --id <devbox_id>

To copy a file from the devbox to your local machine:
   rl devbox rsync :remote_file.txt local_file.txt --id <devbox_id>

Note that the rsync implementation will recurse by default and copy directory contents.

To use the rsync command:
   rl devbox rsync local_dir :remote_dir --id <devbox_id>
```

### Use port forwarding to create a tunnel to remote devbox
```commandline
To use the tunnel command:
   rl devbox tunnel --id <devbox_id> <local_port>:<remote_port>

Note that this is a blocking command that will block for duration of tunnel.
```

## Blueprint

### Create a Blueprint with setup commands
```commandline
rl blueprint create --name=<blueprint_name> --system_setup_commands "<setup commands>"
```

## Snapshot

### Create a Snapshot of devbox (asynchronous)
```commandline
rl devbox snapshot create --devbox_id=<devbox_id>
```

### Check Snapshot Status
```commandline
rl devbox snapshot status --snapshot_id=<snapshot_id>
```

# Command Reference

## Devbox Commands

### Create a Devbox
```commandline
rl devbox create [options]

Options:
  --launch_commands      Devbox initialization commands (can be specified multiple times)
  --entrypoint          Devbox entrypoint command
  --blueprint_id        ID of the blueprint to use
  --blueprint_name      Name of the blueprint to use
  --snapshot_id         ID of the snapshot to use
  --env_vars           Environment variables in key=value format (can be specified multiple times)
  --code_mounts        Code mount configuration in JSON format
  --idle_time          Time in seconds after which idle action will be triggered
  --idle_action        Action to take when devbox becomes idle (shutdown/suspend)
  --prebuilt           Use a non-standard prebuilt image
  --resources          Devbox resource specification (SMALL/MEDIUM/LARGE/X_LARGE/XX_LARGE)
```

### List Devboxes
```commandline
rl devbox list [options]

Options:
  --status             Filter by devbox status (initializing/running/suspending/suspended/resuming/failure/shutdown)
```

### Get Devbox Details
```commandline
rl devbox get --id <devbox_id>
```

### Execute Commands

#### Synchronous Execution
```commandline
rl devbox exec --id <devbox_id> --command "<command>"
```

#### Asynchronous Execution
```commandline
# Start async execution
rl devbox exec_async --id <devbox_id> --command "<command>"

# Get execution status
rl devbox get_async --id <devbox_id> --execution_id <execution_id>
```

### SSH Access
```commandline
# SSH into devbox
rl devbox ssh --id <devbox_id>

# Print SSH config only
rl devbox ssh --id <devbox_id> --config-only
```

### File Transfer

#### SCP
```commandline
# Copy to devbox
rl devbox scp local_file.txt :remote_file.txt --id <devbox_id>

# Copy from devbox
rl devbox scp :remote_file.txt local_file.txt --id <devbox_id>

# Additional options
rl devbox scp --scp-options "-r" local_dir :remote_dir --id <devbox_id>
```

#### Rsync
```commandline
# Copy to devbox
rl devbox rsync local_dir :remote_dir --id <devbox_id>

# Copy from devbox
rl devbox rsync :remote_dir local_dir --id <devbox_id>

# Additional options
rl devbox rsync --rsync-options "-avz" local_dir :remote_dir --id <devbox_id>
```

### Port Forwarding
```commandline
rl devbox tunnel --id <devbox_id> <local_port>:<remote_port>
```

### Devbox Management

#### Suspend Devbox
```commandline
rl devbox suspend --id <devbox_id>
```

#### Resume Devbox
```commandline
rl devbox resume --id <devbox_id>
```

#### Shutdown Devbox
```commandline
rl devbox shutdown --id <devbox_id>
```

#### View Logs
```commandline
rl devbox logs --id <devbox_id>
```

## Blueprint Commands

### Create Blueprint
```commandline
rl blueprint create [options]

Options:
  --name               Blueprint name (required)
  --system_setup_commands  System initialization commands (can be specified multiple times)
  --dockerfile        Dockerfile contents as text
  --dockerfile_path   Path to Dockerfile
  --resources         Resource specification (SMALL/MEDIUM/LARGE/X_LARGE/XX_LARGE)
  --available_ports   List of available ports (can be specified multiple times)
```

### Preview Blueprint
```commandline
rl blueprint preview [options]

Options:
  --name               Blueprint name (required)
  --dockerfile        Dockerfile contents as text
  --system_setup_commands  System initialization commands (can be specified multiple times)
```

### List Blueprints
```commandline
rl blueprint list [options]

Options:
  --name              Filter by blueprint name
```

### Get Blueprint Details
```commandline
rl blueprint get --id <blueprint_id>
```

### View Blueprint Logs
```commandline
rl blueprint logs --id <blueprint_id>
```

## Snapshot Commands

### Create Snapshot (Asynchronous)
```commandline
rl devbox snapshot create --devbox_id <devbox_id>
```

### Get Snapshot Status
```commandline
rl devbox snapshot status --snapshot_id <snapshot_id>
```

### List Snapshots
```commandline
rl devbox snapshot list
```

## Invocation Commands

### Get Invocation Details
```commandline
rl invocation get --id <invocation_id>
```
