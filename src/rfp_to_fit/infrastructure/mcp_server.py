"""RFP-to-Fit MCP 서버 — 외부 검색기를 MCP 도구로 감싸 교체 가능하게(기획서 3절), 다른 AI 비서도 같은 도구를 쓸 수 있다.
실행: uv run python -m rfp_to_fit.infrastructure.mcp_server  (stdio)"""
from __future__ import annotations

import json

from mcp.server.mcpserver import MCPServer

from rfp_to_fit.adapters.openalex import search_works

mcp = MCPServer("rfp-to-fit")


@mcp.tool()
def search_prior_art(query: str, n: int = 5) -> str:
    """영문 키워드로 OpenAlex에서 2019년 이후 선행연구를 찾아 제목·연도·DOI·피인용수를 JSON으로 돌려준다."""
    return json.dumps(search_works(query, n), ensure_ascii=False)


@mcp.tool()
def check_quote(quote: str, text: str) -> bool:
    """인용 실재 검사: quote가 text 원문에 (공백·기호 무시) 그대로 있는지."""
    from rfp_to_fit.domain.quotes import verify_quote
    return verify_quote(quote, text)


if __name__ == "__main__":
    mcp.run()
