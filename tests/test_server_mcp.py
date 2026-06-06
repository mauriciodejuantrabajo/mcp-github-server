from __future__ import annotations

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from src.server import mcp


def _text(result) -> str:
    parts = [c.text for c in result.content if getattr(c, "type", None) == "text"]
    return "\n".join(parts)


@pytest.mark.asyncio
async def test_lista_las_6_tools():
    async with create_connected_server_and_client_session(mcp._mcp_server) as client:
        await client.initialize()
        tools = (await client.list_tools()).tools
        names = {tool.name for tool in tools}
        assert names == {
            "list_repos",
            "get_repo",
            "list_issues",
            "create_issue",
            "list_pull_requests",
            "get_pull_request",
        }
        for tool in tools:
            assert tool.description
            assert tool.inputSchema


@pytest.mark.asyncio
async def test_create_issue_por_mcp_sin_token_devuelve_error(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    import importlib

    import src.server as server_mod

    importlib.reload(server_mod)
    async with create_connected_server_and_client_session(
        server_mod.mcp._mcp_server
    ) as client:
        await client.initialize()
        result = await client.call_tool(
            "create_issue",
            {"owner": "octo", "repo": "demo", "title": "Nuevo issue"},
        )
        assert "Error" in _text(result)
        assert "GITHUB_TOKEN" in _text(result)
    importlib.reload(server_mod)

