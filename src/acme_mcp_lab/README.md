# Acme MCP lab — Session 2

Build an MCP server and client for a mock logistics API, then test them.
The server runs over Streamable HTTP, like a remote server would.

## Setup
    uv sync

## Run (two terminals)
    uv run server.py                # terminal 1: server at http://127.0.0.1:8000/mcp
    uv run client.py                # terminal 2: scripted client
    uv run chat_client.py           # terminal 2: Claude chooses the tools (needs ANTHROPIC_API_KEY)
    uv run pytest                   # automated tests (starts its own server; port 8000 must be free)

## Inspect
    npx @modelcontextprotocol/inspector
    # Transport: Streamable HTTP · URL: http://127.0.0.1:8000/mcp · Connect

## Files
- acme/shipments_api.py  mock of the client's system (replace with real API calls)
- server.py              the MCP server: 3 tools, 1 resource, 1 prompt, Streamable HTTP
- client.py              a scripted MCP client
- chat_client.py         an AI client: Claude + MCP tools
- tests/test_server.py   in-memory tests plus one live HTTP test

## Use it in Claude Code
    claude mcp add --transport http acme-shipments http://127.0.0.1:8000/mcp

## Use it in Claude Desktop or claude.ai
Add it as a custom connector. Connectors need a public HTTPS URL, so deploy the
server (or expose it through a tunnel) first. There is no authentication yet:
Session 3 adds OAuth before anything is exposed.
