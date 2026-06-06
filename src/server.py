"""
Servidor MCP que expone operaciones frecuentes de GitHub como tools.

Ejecutar:
    python -m src.server
o por HTTP:
    python -m src.server --http
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .tools.github import GitHubClient, GitHubError

load_dotenv()

mcp = FastMCP(
    "mcp-github-server",
    instructions=(
        "Servidor MCP para consultar repositorios, issues y pull requests de GitHub. "
        "Usa GITHUB_TOKEN para aumentar rate limits y habilitar acciones de escritura."
    ),
)

_github = GitHubClient()


@mcp.tool(description="Lista repositorios publicos de un owner/usuario de GitHub.")
def list_repos(owner: str, limit: int = 10) -> str:
    """Lista repositorios de `owner`, ordenados por actualizacion reciente."""
    try:
        return _github.list_repos(owner, limit)
    except GitHubError as exc:
        return f"Error: {exc}"


@mcp.tool(description="Obtiene metadata resumida de un repositorio.")
def get_repo(owner: str, repo: str) -> str:
    """Devuelve metadata de `owner/repo`."""
    try:
        return _github.get_repo(owner, repo)
    except GitHubError as exc:
        return f"Error: {exc}"


@mcp.tool(description="Lista issues de un repositorio, excluyendo pull requests.")
def list_issues(owner: str, repo: str, state: str = "open", limit: int = 10) -> str:
    """Lista issues de `owner/repo`. `state`: open, closed o all."""
    try:
        return _github.list_issues(owner, repo, state, limit)
    except GitHubError as exc:
        return f"Error: {exc}"


@mcp.tool(description="Crea un issue en un repositorio. Requiere GITHUB_TOKEN.")
def create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str = "",
    labels: list[str] | None = None,
) -> str:
    """Crea un issue en `owner/repo`."""
    try:
        return _github.create_issue(owner, repo, title, body, labels)
    except GitHubError as exc:
        return f"Error: {exc}"


@mcp.tool(description="Lista pull requests de un repositorio.")
def list_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> str:
    """Lista PRs de `owner/repo`. `state`: open, closed o all."""
    try:
        return _github.list_pull_requests(owner, repo, state, limit)
    except GitHubError as exc:
        return f"Error: {exc}"


@mcp.tool(description="Obtiene un resumen de un pull request.")
def get_pull_request(owner: str, repo: str, number: int) -> str:
    """Devuelve detalle resumido del PR `number` en `owner/repo`."""
    try:
        return _github.get_pull_request(owner, repo, number)
    except GitHubError as exc:
        return f"Error: {exc}"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Servidor MCP para GitHub.")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Servir por Streamable HTTP en vez de stdio.",
    )
    args = parser.parse_args(argv)

    if args.http:
        os.environ.setdefault("FASTMCP_HOST", "127.0.0.1")
        os.environ.setdefault("FASTMCP_PORT", "8001")
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

