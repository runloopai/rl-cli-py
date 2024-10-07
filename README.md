# rl-cli
A command line utility for interacting with runloop APIs.

**NOTE: This project is still in early alpha release**

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