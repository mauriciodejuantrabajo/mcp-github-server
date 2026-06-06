from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.tools.github import GitHubClient, GitHubError


API = "https://api.github.com"


@dataclass
class FakeResponse:
    status_code: int
    payload: Any
    text: str = ""

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        return self.response


def client_with(response: FakeResponse, token: str | None = None) -> tuple[GitHubClient, FakeSession]:
    client = GitHubClient(token=token)
    session = FakeSession(response)
    client._session = session
    return client, session


def test_list_repos_formatea_repositorios():
    client, session = client_with(
        FakeResponse(
            200,
            [
                {
                    "full_name": "octo/demo",
                    "stargazers_count": 7,
                    "updated_at": "2026-06-01T12:00:00Z",
                    "description": "Repo de prueba",
                }
            ],
        )
    )

    out = client.list_repos("octo")

    assert "octo/demo" in out
    assert "stars=7" in out
    assert session.calls[0]["url"] == f"{API}/users/octo/repos"
    assert session.calls[0]["headers"]["Accept"] == "application/vnd.github+json"


def test_get_repo_resume_metadata():
    client, _ = client_with(
        FakeResponse(
            200,
            {
                "full_name": "octo/demo",
                "description": "Demo",
                "stargazers_count": 10,
                "forks_count": 2,
                "language": "Python",
                "default_branch": "main",
                "updated_at": "2026-06-01T12:00:00Z",
                "html_url": "https://github.com/octo/demo",
            },
        )
    )

    out = client.get_repo("octo", "demo")

    assert "Repo: octo/demo" in out
    assert "Language: Python" in out


def test_list_issues_excluye_pull_requests():
    client, _ = client_with(
        FakeResponse(
            200,
            [
                {"number": 1, "title": "Bug real", "state": "open", "comments": 3},
                {
                    "number": 2,
                    "title": "PR disfrazado",
                    "state": "open",
                    "comments": 0,
                    "pull_request": {},
                },
            ],
        )
    )

    out = client.list_issues("octo", "demo")

    assert "#1 Bug real" in out
    assert "PR disfrazado" not in out


def test_create_issue_requiere_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    client = GitHubClient(token=None)

    try:
        client.create_issue("octo", "demo", "Titulo")
    except GitHubError as exc:
        assert "GITHUB_TOKEN" in str(exc)
    else:
        raise AssertionError("create_issue debio exigir token")


def test_create_issue_envia_payload_y_authorization():
    client, session = client_with(
        FakeResponse(
            201,
            {"number": 42, "html_url": "https://github.com/octo/demo/issues/42"},
        ),
        token="ghp_test",
    )

    out = client.create_issue(
        "octo",
        "demo",
        "Nuevo issue",
        body="detalle",
        labels=["bug"],
    )

    request = session.calls[0]
    assert "Issue creada: #42" in out
    assert request["url"] == f"{API}/repos/octo/demo/issues"
    assert request["headers"]["Authorization"] == "Bearer ghp_test"
    assert request["json"]["labels"] == ["bug"]


def test_list_pull_requests_formatea_ramas():
    client, _ = client_with(
        FakeResponse(
            200,
            [
                {
                    "number": 5,
                    "title": "Mejora",
                    "state": "open",
                    "head": {"ref": "feature"},
                    "base": {"ref": "main"},
                }
            ],
        )
    )

    out = client.list_pull_requests("octo", "demo")

    assert "#5 Mejora" in out
    assert "feature -> main" in out


def test_get_pull_request_resume_detalle():
    client, _ = client_with(
        FakeResponse(
            200,
            {
                "number": 5,
                "title": "Mejora",
                "state": "open",
                "head": {"ref": "feature"},
                "base": {"ref": "main"},
                "user": {"login": "alice"},
                "mergeable": True,
                "changed_files": 4,
                "commits": 2,
                "html_url": "https://github.com/octo/demo/pull/5",
                "body": "detalle del PR",
            },
        )
    )

    out = client.get_pull_request("octo", "demo", 5)

    assert "PR: #5 Mejora" in out
    assert "Author: alice" in out


def test_error_http_es_legible():
    client, _ = client_with(
        FakeResponse(404, {"message": "Not Found"}, text='{"message":"Not Found"}')
    )

    try:
        client.get_repo("octo", "missing")
    except GitHubError as exc:
        assert "404" in str(exc)
        assert "Not Found" in str(exc)
    else:
        raise AssertionError("get_repo debio fallar")
