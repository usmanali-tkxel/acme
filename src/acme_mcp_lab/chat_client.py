"""An AI client: Claude decides which MCP tools to call.

This is what a host like Claude Desktop does internally, in about 60 lines.

Start the server first (uv run server.py), then:
    export ANTHROPIC_API_KEY=...
    uv run chat_client.py
"""
import asyncio
import json
import os

from anthropic import AsyncAnthropic
from mcp import Client

from client import on_elicit, server_url, text_of

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")


def to_claude_tools(mcp_tools) -> list[dict]:
    """Convert MCP tool definitions to Claude API tools."""
    return [
        {"name": t.name, "description": t.description or "",
         "input_schema": t.input_schema}
        for t in mcp_tools
    ]


async def answer(client: Client, llm, tools: list[dict], question: str) -> str:
    """The agent loop: ask Claude, run any tools it picks, repeat until it answers."""
    messages = [{"role": "user", "content": question}]
    while True:
        response = await llm.messages.create(
            model=MODEL, max_tokens=1024, tools=tools, messages=messages)
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  -> {block.name}({json.dumps(block.input)})")
                result = await client.call_tool(block.name, block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": text_of(result), "is_error": bool(result.is_error)})
        messages.append({"role": "user", "content": results})


async def main() -> None:
    llm = AsyncAnthropic()
    async with Client(server_url(), elicitation_callback=on_elicit) as client:
        tools = to_claude_tools((await client.list_tools()).tools)
        print(f"Connected. {len(tools)} tools available. Type 'quit' to exit.")
        while True:
            question = await asyncio.to_thread(input, "\nYou: ")
            if question.strip().lower() in {"quit", "exit"}:
                break
            print("Claude:", await answer(client, llm, tools, question))


if __name__ == "__main__":
    asyncio.run(main())
