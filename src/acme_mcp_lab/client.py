"""A minimal MCP client: connect, discover, call tools, read a resource.

Start the server first (uv run server.py), then:
    uv run client.py                          # connects to http://127.0.0.1:8000/mcp
    uv run client.py https://other-host/mcp   # or any other server URL
"""
import asyncio
import sys

from mcp import Client
from mcp.types import ElicitResult

MCP_URL = "http://127.0.0.1:8000/mcp"


async def on_elicit(context, params) -> ElicitResult:
    """Called when the server needs the user's input."""
    print(f"\n[server asks] {params.message}")
    reply = await asyncio.to_thread(input, "Confirm? [y/N] ")
    return ElicitResult(action="accept",
                        content={"confirm": reply.strip().lower() == "y"})


def server_url() -> str:
    """The server's URL; pass another one on the command line."""
    return sys.argv[1] if len(sys.argv) > 1 else MCP_URL


def text_of(result) -> str:
    return "\n".join(c.text for c in result.content if c.type == "text")


async def main() -> None:
    async with Client(server_url(), elicitation_callback=on_elicit) as client:
        # 1. Discover what the server offers
        tools = await client.list_tools()
        print("Tools:    ", [t.name for t in tools.tools])
        templates = await client.list_resource_templates()
        print("Resources:", [r.uri_template for r in templates.resource_templates])
        prompts = await client.list_prompts()
        print("Prompts:  ", [p.name for p in prompts.prompts])

        # 2. Call a read-only tool
        result = await client.call_tool("search_shipments", {"status": "delayed"})
        print("\nDelayed shipments:", result.structured_content["result"])

        # 3. Read a resource
        record = await client.read_resource("shipments://S-104")
        print("\nshipments://S-104 ->", record.contents[0].text)

        # 4. A bad argument returns an error the model could act on
        bad = await client.call_tool("get_shipment", {"shipment_id": "X-1"})
        print("\nError?", bad.is_error, "->", text_of(bad))

        # 5. A write tool: the server asks us to confirm first
        result = await client.call_tool(
            "update_eta", {"shipment_id": "S-104", "new_eta": "2026-10-26"})
        print("Result:", text_of(result))


if __name__ == "__main__":
    asyncio.run(main())
