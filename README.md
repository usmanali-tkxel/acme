# Acme MCP Lab

An MCP (Model Context Protocol) server and clients for a mock Acme Logistics
shipments API. The server runs over Streamable HTTP, the same way a remote
server would, so any MCP client (Claude Code, the MCP Inspector, or the
included Python clients) can connect to it.

## What the server exposes

| Kind     | Name                        | What it does                                                        |
|----------|-----------------------------|---------------------------------------------------------------------|
| Tool     | `search_shipments`          | Find shipments by status (`in_transit`, `delayed`, `delivered`), optionally for one customer. Read-only. |
| Tool     | `get_shipment`              | Full record for one shipment ID, e.g. `S-104`. Read-only.           |
| Tool     | `update_eta`                | Change a shipment's ETA (`YYYY-MM-DD`). Validates the input, then asks the user to confirm through elicitation before writing. |
| Resource | `shipments://{shipment_id}` | Full shipment record as JSON.                                       |
| Prompt   | `delay_report`              | Starts a report on a customer's delayed shipments.                  |

The data is an in-memory mock (`shipments_api.py`) with four sample shipments
across the customers `ACME-UK` and `GLOBEX`. To connect a real system, replace
the function bodies in `shipments_api.py`. `server.py` doesn't need to change.

## Project layout

```
acme-mcp-lab/
├── README.md
├── pyproject.toml
└── src/acme_mcp_lab/
    ├── server.py          MCP server: 3 tools, 1 resource, 1 prompt (http://127.0.0.1:8000/mcp)
    ├── shipments_api.py   mock shipments backend
    ├── client.py          scripted MCP client (discover, call tools, read a resource)
    ├── chat_client.py     AI client: Claude picks and calls the MCP tools
    ├── test_server.py     in-memory tests plus one live HTTP test
    ├── pyproject.toml     lab dependencies
    └── README.md          lab notes
```

## Requirements

- Python 3.13 (see `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- `ANTHROPIC_API_KEY`, only for `chat_client.py`
- Node.js, only for the MCP Inspector

## Setup

```bash
cd src/acme_mcp_lab
uv sync
```

## Run

Start the server in one terminal:

```bash
cd src/acme_mcp_lab
uv run server.py        # serves http://127.0.0.1:8000/mcp
```

Then connect a client from a second terminal:

```bash
cd src/acme_mcp_lab
uv run client.py                      # scripted client
uv run client.py https://host/mcp     # or point it at another server

export ANTHROPIC_API_KEY=...
uv run chat_client.py                 # Claude chooses which tools to call
```

`chat_client.py` uses `claude-sonnet-5-5` by default. Set `ANTHROPIC_MODEL` to use a different model.

## Test

```bash
cd src/acme_mcp_lab
uv run pytest
```

The tests start their own server, so port 8000 must be free.

## Inspect

```bash
npx @modelcontextprotocol/inspector
```

Choose the **Streamable HTTP** transport, enter the URL `http://127.0.0.1:8000/mcp`, and click **Connect**.

## Use it from Claude

**Claude Code**, with the server running locally:

```bash
claude mcp add --transport http acme-shipments http://127.0.0.1:8000/mcp
```

**Claude Desktop / claude.ai**: add the server as a custom connector. Connectors
need a public HTTPS URL, so you must deploy the server or expose it through a
tunnel first.

> **Note:** The server has no authentication yet. Don't expose it publicly
> until OAuth is added.
