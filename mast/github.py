from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class GitHubError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"error": self.code, "message": self.message}


@dataclass(frozen=True)
class IssueRef:
    repository: str
    number: int


@dataclass(frozen=True)
class IssueContext:
    repository: str
    number: int
    url: str
    title: str
    body: str
    labels: list[str]
    comments: list[dict[str, Any]]
    linked_pull_requests: list[dict[str, Any]]
    repository_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_issue_ref(value: str) -> IssueRef:
    value = value.strip()
    url_match = re.match(r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)(?:$|[?#])", value)
    short_match = re.match(r"([^/\s]+/[^#\s]+)#(\d+)$", value)
    match = url_match or short_match
    if not match:
        raise GitHubError("invalid_issue_ref", "expected GitHub issue URL or owner/repo#number")
    return IssueRef(match.group(1), int(match.group(2)))


class GhIssueClient:
    def _json(self, args: list[str]) -> dict[str, Any]:
        result = subprocess.run(["gh", *args], text=True, capture_output=True)
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "GitHub CLI command failed"
            code = "github_auth_or_access_error"
            if "rate limit" in stderr.lower():
                code = "github_rate_limit"
            elif "could not resolve" in stderr.lower() or "not found" in stderr.lower():
                code = "github_not_found"
            raise GitHubError(code, stderr)
        return json.loads(result.stdout)

    def fetch_issue(self, ref: IssueRef) -> IssueContext:
        issue = self._json(
            [
                "issue",
                "view",
                str(ref.number),
                "--repo",
                ref.repository,
                "--json",
                "url,title,body,labels,comments",
            ]
        )
        repo = self._json(
            [
                "repo",
                "view",
                ref.repository,
                "--json",
                "nameWithOwner,defaultBranchRef,isPrivate,url",
            ]
        )
        prs = self._json(
            [
                "pr",
                "list",
                "--repo",
                ref.repository,
                "--state",
                "all",
                "--search",
                f"{ref.repository}#{ref.number}",
                "--json",
                "number,title,url,state",
            ]
        )
        return IssueContext(
            repository=ref.repository,
            number=ref.number,
            url=issue["url"],
            title=issue["title"],
            body=issue.get("body") or "",
            labels=[label["name"] for label in issue.get("labels", [])],
            comments=issue.get("comments", []),
            linked_pull_requests=prs if isinstance(prs, list) else [],
            repository_metadata=repo,
        )


def save_issue_context(context: IssueContext, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(context.to_dict(), indent=2, sort_keys=True) + "\n")
    return target
