# rl-cli
A command line utility for interacting with runloop APIs.

**NOTE: This project is still in early alpha release**

# Setup

(Homebrew instructions coming soon...)

## For developers
```commandline
# Clone the repo
mkdir -p ~/source/ && cd ~/source/
git clone https://github.com/runloopai/rl-cli.git
cd rl-cli/

# Setup the venv and dev tools
python3 -m venv .venv && pip install -r dev-requirements.txt

# Install to your local machine
# Use 'which python3' to find your system python
flit install --symlink --python </path/to/system/python>
```

```
# In a new terminal
export RUNLOOP_API_KEY=<your-api-key>
export GITHUB_TOKEN=<your-github-token>
rl --help
```

# Quick reference

## Devbox

### Create a devbox and run a single command
```commandline
rl devbox create --env_vars HELLO=world --entrypoint "echo \$HELLO"
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
}                                                                                                                              [1.03s]
```

### Observe logs
```commandline
rl devbox logs --id dbx_2xMDUOsKMiZBYKsvSRtMA
>
2024-08-09 11:52:38  Initializing devbox...
2024-08-09 11:52:38  Devbox setup complete
2024-08-09 11:52:38 -> echo $HELLO
2024-08-09 11:52:38  world
2024-08-09 11:52:38  world
2024-08-09 11:52:38  None
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
