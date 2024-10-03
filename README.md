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
