# Hardcover MCP

A Model Context Protocol (MCP) server that exposes read-only access to the Hardcover.app GraphQL API. Tools are namespaced under `books.*`, `users.*`, and `series.*`, with resources and prompts to guide safe, low-volume querying.

## Requirements
- Python 3.11+
- A Hardcover API key (read-only Bearer token) from https://hardcover.app/account/api

## Installation
```bash
# Option A: with uv (recommended)
uv pip install -e .

# Option B: with pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Transport Protocol
This server currently only supports STDIO as the transport protocol

## Usage
1) Get an API key from https://hardcover.app/account/api. Copy the value exactly as provided (it already starts with `Bearer `).  
2) Export it for the server:
```bash
export HARDCOVER_API_KEY="Bearer <your-token>"
```

### Running the server directly
3) Start the MCP server:
```bash
uv run src/hardcover_mcp/main.py
```

### Configuring STDIO for a AI chat
Codex
```bash
[mcp_servers.hardcover_mcp]
command = "uv"
args = ["run", "src/hardcover_mcp/main.py"]
env = { "HARDCOVER_API_KEY" = "API KEY heRE" }
cwd = "full_path_to/hardcover_mcp"
```
The server registers the `books.*`, `users.*`, and `series.*` tool namespaces, plus resources like `hardcover/tag-categories` and usage prompts such as `hardcover/fantasy-this-year`.

### Running the test suite
```bash
pytest
```

## Troubleshooting
- `HARDCOVER_API_KEY environment variable is required`: ensure the variable is set in the same shell you start the server. Include the leading `Bearer ` prefix.
- `Hardcover API returned an error response` or 401/403: confirm the token is valid and not expired.
- Slow responses or timeouts: reduce `limit`/`offset` arguments; the API enforces rate limits. Start with `limit<=10`.
- SSL/HTTP transport issues: check local network/proxy settings and retry with a stable connection.
