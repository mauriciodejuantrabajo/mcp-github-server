> **Idioma / Language:** [English](README.md) · **Español**

# mcp-github-server

Servidor **MCP (Model Context Protocol)** para consultar y operar GitHub desde
clientes compatibles como Claude Desktop, Claude Code o Cursor.

Expone tools concretas para el trabajo diario con repos, issues y pull requests,
usando la API REST de GitHub y un `GITHUB_TOKEN` opcional para lectura y requerido
para escritura.

## Tools

| Tool | Que hace | Token |
|------|----------|-------|
| `list_repos` | Lista repos publicos de un owner | opcional |
| `get_repo` | Resume metadata de `owner/repo` | opcional |
| `list_issues` | Lista issues, excluyendo PRs | opcional |
| `create_issue` | Crea un issue | requerido |
| `list_pull_requests` | Lista PRs | opcional |
| `get_pull_request` | Resume un PR por numero | opcional |

## Instalacion

```bash
git clone https://github.com/mauriciodejuantrabajo/mcp-github-server.git
cd mcp-github-server

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edita `.env` y agrega `GITHUB_TOKEN` si vas a crear issues o quieres mayor rate
limit para consultas.

## Probar con MCP Inspector

```bash
mcp dev src/server.py
```

Pruebas sugeridas:

- `list_repos` con `owner = "openai"`
- `get_repo` con `owner = "modelcontextprotocol"`, `repo = "python-sdk"`
- `list_pull_requests` con `owner = "modelcontextprotocol"`, `repo = "python-sdk"`

## Claude Desktop

Usa [examples/claude_desktop_config.json](examples/claude_desktop_config.json) como
base y ajusta la ruta absoluta del repo.

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "C:\\ruta\\a\\mcp-github-server",
      "env": {
        "GITHUB_TOKEN": "ghp_reemplazar_por_tu_token"
      }
    }
  }
}
```

## Transportes

```bash
python -m src.server          # stdio
python -m src.server --http   # Streamable HTTP en 127.0.0.1:8001
```

## Tests

```bash
pytest
```

Los tests mockean HTTP, asi que no requieren token ni red real.

