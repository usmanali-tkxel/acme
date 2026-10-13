"""Automated tests.

Most tests use an in-memory client (fast, no network). The last one starts
server.py for real and talks to it over Streamable HTTP.
"""
import socket
import subprocess
import sys
import time

import pytest

from mcp import Client
from mcp.types import ElicitResult

import shipments_api as api
from server import mcp

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def fresh_data():
    api.reset()


def confirm_with(answer: bool):
    async def callback(context, params):
        return ElicitResult(action="accept", content={"confirm": answer})
    return callback


async def test_lists_expected_tools():
    async with Client(mcp) as client:
        names = {t.name for t in (await client.list_tools()).tools}
    assert names == {"search_shipments", "get_shipment", "update_eta"}


async def test_search_returns_delayed_shipments():
    async with Client(mcp) as client:
        result = await client.call_tool("search_shipments", {"status": "delayed"})
    ids = [s["id"] for s in result.structured_content["result"]]
    assert ids == ["S-104", "S-221"]


async def test_unknown_id_returns_actionable_error():
    async with Client(mcp) as client:
        result = await client.call_tool("get_shipment", {"shipment_id": "X-1"})
    assert result.is_error
    assert "S-104" in result.content[0].text  # tells the model what an ID looks like


async def test_resource_returns_full_record():
    async with Client(mcp) as client:
        record = await client.read_resource("shipments://S-104")
    assert '"days_late": 3' in record.contents[0].text


async def test_update_eta_applies_change_when_confirmed():
    async with Client(mcp, elicitation_callback=confirm_with(True)) as client:
        result = await client.call_tool("update_eta", {"shipment_id": "S-104", "new_eta": "2026-10-26"})
    assert not result.is_error
    assert api.get("S-104")["eta"] == "2026-10-26"


async def test_update_eta_changes_nothing_when_user_says_no():
    async with Client(mcp, elicitation_callback=confirm_with(False)) as client:
        await client.call_tool("update_eta", {"shipment_id": "S-104", "new_eta": "2026-10-26"})
    assert api.get("S-104")["eta"] == "2026-10-24"


async def test_bad_date_is_rejected_before_asking_the_user():
    asked = []

    async def callback(context, params):
        asked.append(params.message)
        return ElicitResult(action="accept", content={"confirm": True})

    async with Client(mcp, elicitation_callback=callback) as client:
        result = await client.call_tool("update_eta", {"shipment_id": "S-104", "new_eta": "next week"})
    assert result.is_error and not asked
    assert "YYYY-MM-DD" in result.content[0].text


async def test_prompt_mentions_customer():
    async with Client(mcp) as client:
        prompt = await client.get_prompt("delay_report", {"customer": "ACME-UK"})
    assert "ACME-UK" in prompt.messages[0].content.text


# ---------- The real thing: server.py over Streamable HTTP ----------

def wait_for_port(port: int, timeout: float = 10) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise TimeoutError(f"Nothing listening on port {port}")


@pytest.fixture
def live_server():
    proc = subprocess.Popen([sys.executable, "server.py"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_for_port(8000)
    yield "http://127.0.0.1:8000/mcp"
    proc.terminate()
    proc.wait()


async def test_update_eta_over_http(live_server):
    async with Client(live_server, elicitation_callback=confirm_with(True)) as client:
        result = await client.call_tool(
            "update_eta", {"shipment_id": "S-104", "new_eta": "2026-10-26"})
    assert result.content[0].text == "ETA for S-104 is now 2026-10-26."
