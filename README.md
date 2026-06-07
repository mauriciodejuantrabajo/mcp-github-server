> **Idioma / Language:** **English** · [Español](README.es.md)

# mcp-github-server

**MCP (Model Context Protocol)** server to query and operate GitHub from
compatible clients such as Claude Desktop, Claude Code or Cursor.

It exposes concrete tools for day-to-day work with repos, issues and pull
requests, using the GitHub REST API and an optional `GITHUB_TOKEN` (optional for
reading, required for writing).

## Tools

| Tool | What it does | Token |
|------|--------------|-------|
| `list_repos` | Lists an owner's public repos | optional |
| `get_repo` | Summarizes metadata of `owner/repo` | optional |
| `list_issues` | Lists issues, excluding PRs | optional |
| `create_issue` | Creates an issue | required |
| `list_pull_requests` | Lists PRs | optional |
| `get_pull_request` | Summarizes a PR by number | optional |

## Installation

```bash
git clone https://github.com/mauriciodejuantrabajo/mcp-github-server.git
cd mcp-github-server

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and add `GITHUB_TOKEN` if you plan to create issues or want a higher
rate limit for queries.

## Test with MCP Inspector

```bash
mcp dev src/server.py
```

Suggested tests:

- `list_repos` with `owner = "openai"`
- `get_repo` with `owner = "modelcontextprotocol"`, `repo = "python-sdk"`
- `list_pull_requests` with `owner = "modelcontextprotocol"`, `repo = "python-sdk"`

## Claude Desktop

Use [examples/claude_desktop_config.json](examples/claude_desktop_config.json) as
a base and adjust the absolute path of the repo.

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\path\\to\\mcp-github-server",
      "env": {
        "GITHUB_TOKEN": "ghp_replace_with_your_token"
      }
    }
  }
}
```

## Transports

```bash
python -m src.server          # stdio
python -m src.server --http   # Streamable HTTP on 127.0.0.1:8001
```

## Tests

```bash
pytest
```

The tests mock HTTP, so they require no token and no real network.
