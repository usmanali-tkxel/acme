"""Acme Shipments MCP server, served over Streamable HTTP.

Run it:
    uv run server.py    # listens on http://127.0.0.1:8000/mcp

Then connect any MCP client to that URL: client.py, chat_client.py,
the MCP Inspector (npx @modelcontextprotocol/inspector) or Claude Code.
"""
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from mcp.server import MCPServer
from mcp.server.mcpserver import Elicit, Resolve
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

import shipments_api as api

mcp = MCPServer("acme-shipments")
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)


# ---------- Tools: actions the model decides to take ----------

@mcp.tool(annotations=READ_ONLY)
def search_shipments(
    status: Literal["in_transit", "delayed", "delivered"] = "delayed",
    customer: str | None = None,
) -> list[dict]:
    """Find shipments by status, optionally for one customer.
    Use when the user has no shipment ID."""
    return api.search(status=status, customer=customer)


@mcp.tool(annotations=READ_ONLY)
def get_shipment(shipment_id: str) -> dict:
    """Get the full record for one shipment, e.g. S-104.
    Use when the user gives a shipment ID."""
    try:
        return api.get(shipment_id)
    except ValueError as e:
        raise ToolError(str(e))  # shown to the model


class Confirm(BaseModel):
    confirm: bool = Field(description="Apply this change?")


def ask_to_confirm(shipment_id: str, new_eta: str) -> Elicit[Confirm]:
    """Runs before update_eta: validate, then ask the user."""
    try:
        api.get(shipment_id)
        api.check_eta(new_eta)
    except ValueError as e:
        raise ToolError(str(e))
    question = f"Change the ETA of {shipment_id} to {new_eta}?"
    return Elicit(question, Confirm)


@mcp.tool(annotations=ToolAnnotations(
    destructiveHint=True, idempotentHint=True, openWorldHint=False))
def update_eta(
    shipment_id: str,
    new_eta: str,
    answer: Annotated[Confirm, Resolve(ask_to_confirm)],
) -> str:
    """Change a shipment's ETA. new_eta must be YYYY-MM-DD.
    The user is always asked to confirm first."""
    if not answer.confirm:
        return f"No change made to {shipment_id}."
    api.update_eta(shipment_id, new_eta)
    return f"ETA for {shipment_id} is now {new_eta}."


# ---------- Resource: context the app or user attaches ----------

@mcp.resource("shipments://{shipment_id}", mime_type="application/json")
def shipment_record(shipment_id: str) -> str:
    """Full shipment record as JSON."""
    return api.get_json(shipment_id)


# ---------- Prompt: a workflow the user starts ----------

@mcp.prompt()
def delay_report(customer: str) -> str:
    """Report on a customer's delayed shipments."""
    return (
        f"Use search_shipments to find delayed shipments "
        f"for {customer}. For each one, give the ID, days "
        "late and ETA, then suggest one next step."
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8000)
