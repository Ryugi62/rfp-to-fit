"""MCP 클라이언트 — 선행 탐색을 MCP 도구 서버(stdio)에 위임한다. 서버를 바꾸면 검색기가 바뀐다."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

SRC = str(Path(__file__).resolve().parents[2])


class McpPriorArt:
    name = "MCP rfp-to-fit/search_prior_art (OpenAlex)"

    def __init__(self, command: str = sys.executable, args: list[str] | None = None):
        self.command = command
        self.args = args or ["-m", "rfp_to_fit.infrastructure.mcp_server"]

    async def _call(self, query: str, n: int):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        params = StdioServerParameters(command=self.command, args=self.args, env={"PYTHONPATH": SRC})
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                res = await s.call_tool("search_prior_art", {"query": query, "n": n})
                return json.loads(res.content[0].text) if res.content else []

    def search(self, query: str, n: int = 5) -> list[dict]:
        return asyncio.run(self._call(query, n))
