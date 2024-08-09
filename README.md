# rl-cli
Runloop CLI for using runloop APIs

## Setup
```
python3 -m venv .venv && pip install -r requirements.txt
```

## Set up your environment
```commandline
export RUNLOOP_API_KEY=<your-api-key>
export GITHUB_TOKEN=<your-github-token>
```

## Test the devbox

### Create devbox
```commandline
python -m main --cmd create --env_vars HELLO=world --entrypoint "echo \$HELLO"
>
devbox created devbox={'id': 'dbx_2ws7NkWXJfhEwhnlVWfmy', 'status': 'provisioning', 'create_time_ms': 1718667134290}
```

### Observe logs
```commandline
python -m main --cmd logs --id dbx_2ws7IOtjxnJgLsBIpU9nn  
>
1718666928563 info Initializing devbox...
1718666928615 info Devbox setup complete
1718666928631 info world
```

### Devbox is automatically shutdown when entrypoint complete
```commandline
python -m main --cmd get --id dbx_2ws7IOtjxnJgLsBIpU9nn
>   
devboxes={'id': 'dbx_2ws7IOtjxnJgLsBIpU9nn', 'status': 'shutdown', 'create_time_ms': 1718666927593}
```

## Test with code and a devbox
Create a CodeHandle reference to repository
```commandline
python -m main --cmd create --res code --repo minimal-fastapi-postgres-template --owner rafsaf

>
{
    "id": "bnv_2wkCIPg4Ce25dGaW1pDVl",
    "repo_name": "minimal-fastapi-postgres-template",
    "owner": "rafsaf",
    "commit_hash": "ba24f1a5bae677a27e83dd4ac815c25bd4fcd36f"
}
```

Launch a devbox with code handle
```commandline
python -m main --cmd create --res devbox --id bnv_2wkCIPg4Ce25dGaW1pDVl \
 --entrypoint "set -eux && cd code && uv venv && source .venv/bin/activate \
  && poetry install && cp .env.example .env && docker compose up -d && pytest"
>
{
    "id": "dbx_2wkaVyVJmCfKpBJ6XX70F",
    "status": "provisioning"
}  
```

Query for devbox to be in running state
```commandline
python -m main --cmd get --res devbox --id dbx_2wkaVyVJmCfKpBJ6XX70F
>
{
    "id": "dbx_2wkaVyVJmCfKpBJ6XX70F",
    "status": "running"
}
```

Check out result of devbox executions
```commandline
python -m main --cmd logs --res devbox --id dbx_2wkaVyVJmCfKpBJ6XX70F
>
{
1717525731380 info app/tests/test_users/test_reset_password.py::test_reset_current_user_password_is_changed_in_db 
1717525731420 info app/tests/test_users/test_reset_password.py::test_reset_current_user_password_status_code 
1717525731431 info [gw1] [ 97%] PASSED app/tests/test_users/test_reset_password.py::test_reset_current_user_password_status_code 
1717525731922 info [gw0] [100%] PASSED app/tests/test_users/test_reset_password.py::test_reset_current_user_password_is_changed_in_db 
1717525731922 info 
1717525731922 info ---------- coverage: platform linux, python 3.12.3-final-0 -----------
1717525731922 info Name                            Stmts   Miss  Cover   Missing
1717525731922 info -------------------------------------------------------------
...
}
```
Shut down devbox
```commandline
python -m main --cmd shutdown --res devbox --id dbx_2wkaVyVJmCfKpBJ6XX70F
>
{
    "id": "dbx_2wkaVyVJmCfKpBJ6XX70F",
    "status": "shutdown"
}
```
