from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


class GitHubError(Exception):
    """Raised when the GitHub API cannot satisfy a tool request."""


def _compact(value: str, limit: int = 240) -> str:
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _require_owner_repo(owner: str, repo: str) -> tuple[str, str]:
    owner = owner.strip()
    repo = repo.strip()
    if not owner or not repo:
        raise GitHubError("owner y repo son obligatorios.")
    return owner, repo


def _format_items(items: list[dict[str, Any]], empty: str) -> str:
    if not items:
        return empty
    return "\n".join(
        f"- {item['title']}" if "title" in item else f"- {item['name']}"
        for item in items
    )


@dataclass
class GitHubClient:
    token: str | None = None
    base_url: str = "https://api.github.com"
    timeout: float = 20.0

    def __post_init__(self) -> None:
        self.token = self.token or os.getenv("GITHUB_TOKEN")
        self.base_url = self.base_url.rstrip("/")
        self._session = requests.Session()

    @property
    def headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        require_token: bool = False,
    ) -> Any:
        if require_token and not self.token:
            raise GitHubError("Falta GITHUB_TOKEN para usar esta tool.")

        url = f"{self.base_url}{path}"
        try:
            response = self._session.request(
                method,
                url,
                params=params,
                json=json,
                headers=self.headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise GitHubError(f"No se pudo conectar con GitHub: {exc}") from exc

        if response.status_code >= 400:
            message = response.text
            try:
                message = response.json().get("message", response.text)
            except ValueError:
                pass
            raise GitHubError(
                f"GitHub API devolvio {response.status_code}: {_compact(message)}"
            )

        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise GitHubError("GitHub devolvio una respuesta no JSON.") from exc

    def list_repos(self, owner: str, limit: int = 10) -> str:
        owner = owner.strip()
        if not owner:
            raise GitHubError("owner es obligatorio.")
        limit = max(1, min(limit, 50))
        data = self._request(
            "GET",
            f"/users/{owner}/repos",
            params={"sort": "updated", "per_page": limit},
        )
        rows = [
            {
                "name": repo["full_name"],
                "title": (
                    f"{repo['full_name']} | stars={repo.get('stargazers_count', 0)} "
                    f"| updated={repo.get('updated_at', '?')} | "
                    f"{_compact(repo.get('description') or 'sin descripcion', 120)}"
                ),
            }
            for repo in data
        ]
        return _format_items(rows, "No se encontraron repositorios.")

    def get_repo(self, owner: str, repo: str) -> str:
        owner, repo = _require_owner_repo(owner, repo)
        data = self._request("GET", f"/repos/{owner}/{repo}")
        description = data.get("description") or "sin descripcion"
        return "\n".join(
            [
                f"Repo: {data['full_name']}",
                f"Descripcion: {description}",
                f"Stars: {data.get('stargazers_count', 0)}",
                f"Forks: {data.get('forks_count', 0)}",
                f"Language: {data.get('language') or 'n/a'}",
                f"Default branch: {data.get('default_branch') or 'n/a'}",
                f"Updated: {data.get('updated_at') or 'n/a'}",
                f"URL: {data.get('html_url') or 'n/a'}",
            ]
        )

    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 10,
    ) -> str:
        owner, repo = _require_owner_repo(owner, repo)
        state = state if state in {"open", "closed", "all"} else "open"
        limit = max(1, min(limit, 50))
        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": limit},
        )
        rows = []
        for issue in data:
            if "pull_request" in issue:
                continue
            rows.append(
                {
                    "title": (
                        f"#{issue['number']} {issue['title']} "
                        f"[{issue['state']}] comments={issue.get('comments', 0)}"
                    )
                }
            )
        return _format_items(rows, "No se encontraron issues.")

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
    ) -> str:
        owner, repo = _require_owner_repo(owner, repo)
        title = title.strip()
        if not title:
            raise GitHubError("title es obligatorio.")
        payload: dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            json=payload,
            require_token=True,
        )
        return f"Issue creada: #{data['number']} {data['html_url']}"

    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 10,
    ) -> str:
        owner, repo = _require_owner_repo(owner, repo)
        state = state if state in {"open", "closed", "all"} else "open"
        limit = max(1, min(limit, 50))
        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": limit},
        )
        rows = [
            {
                "title": (
                    f"#{pr['number']} {pr['title']} [{pr['state']}] "
                    f"{pr.get('head', {}).get('ref', '?')} -> "
                    f"{pr.get('base', {}).get('ref', '?')}"
                )
            }
            for pr in data
        ]
        return _format_items(rows, "No se encontraron pull requests.")

    def get_pull_request(self, owner: str, repo: str, number: int) -> str:
        owner, repo = _require_owner_repo(owner, repo)
        if number < 1:
            raise GitHubError("number debe ser mayor a 0.")
        data = self._request("GET", f"/repos/{owner}/{repo}/pulls/{number}")
        return "\n".join(
            [
                f"PR: #{data['number']} {data['title']}",
                f"State: {data['state']}",
                f"Branch: {data.get('head', {}).get('ref', '?')} -> "
                f"{data.get('base', {}).get('ref', '?')}",
                f"Author: {data.get('user', {}).get('login', 'n/a')}",
                f"Mergeable: {data.get('mergeable')}",
                f"Changed files: {data.get('changed_files', 'n/a')}",
                f"Commits: {data.get('commits', 'n/a')}",
                f"URL: {data.get('html_url') or 'n/a'}",
                f"Body: {_compact(data.get('body') or 'sin body')}",
            ]
        )

