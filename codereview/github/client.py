import asyncio
import base64
import logging

import httpx

log = logging.getLogger(__name__)


class GitHubError(Exception):
    def __init__(self, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.status = status


class GitHubClient:
    """Async GitHub REST client scoped to one repository (spec §7)."""

    def __init__(
        self,
        token: str,
        repo: str,
        base_url: str = "https://api.github.com",
        timeout: float = 30.0,
    ) -> None:
        self.repo = repo
        self._client = httpx.AsyncClient(
            base_url=base_url,
            follow_redirects=True,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ai-code-review-agent",
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(
        self, method: str, url: str, *, retry: bool = True, **kwargs
    ) -> httpx.Response:
        resp = await self._client.request(method, url, **kwargs)
        rate_limited = resp.status_code == 429 or (
            resp.status_code == 403 and resp.headers.get("x-ratelimit-remaining") == "0"
        )
        if rate_limited and retry:
            wait = min(float(resp.headers.get("retry-after", "1") or "1"), 60.0)
            log.warning("rate limited on %s %s, retrying in %.0fs", method, url, wait)
            await asyncio.sleep(wait)
            return await self._request(method, url, retry=False, **kwargs)
        if resp.status_code >= 400:
            raise GitHubError(
                f"{method} {url} -> {resp.status_code}: {resp.text[:300]}",
                status=resp.status_code,
            )
        return resp

    async def get_pr(self, number: int) -> dict:
        return (await self._request("GET", f"/repos/{self.repo}/pulls/{number}")).json()

    async def resolve_pr_head(self, number: int) -> str:
        return (await self.get_pr(number))["head"]["sha"]

    async def get_pr_diff(self, number: int) -> str:
        resp = await self._request(
            "GET",
            f"/repos/{self.repo}/pulls/{number}",
            headers={"Accept": "application/vnd.github.diff"},
        )
        return resp.text

    async def get_file(self, path: str, ref: str) -> str | None:
        try:
            resp = await self._request(
                "GET", f"/repos/{self.repo}/contents/{path}", params={"ref": ref}
            )
        except GitHubError as exc:
            if exc.status == 404:
                return None
            raise
        data = resp.json()
        if isinstance(data, dict) and data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return None

    async def get_default_branch(self) -> str:
        return (await self._request("GET", f"/repos/{self.repo}")).json()["default_branch"]

    async def list_reviews(self, number: int) -> list[dict]:
        resp = await self._request(
            "GET", f"/repos/{self.repo}/pulls/{number}/reviews", params={"per_page": 100}
        )
        return resp.json()

    async def create_review(
        self, number: int, commit_id: str, body: str, comments: list[dict]
    ) -> dict:
        payload = {"commit_id": commit_id, "body": body, "event": "COMMENT", "comments": comments}
        resp = await self._request(
            "POST", f"/repos/{self.repo}/pulls/{number}/reviews", json=payload
        )
        return resp.json()

    async def list_recent_review_comments(self, limit: int = 200) -> list[dict]:
        out: list[dict] = []
        page = 1
        while len(out) < limit:
            resp = await self._request(
                "GET",
                f"/repos/{self.repo}/pulls/comments",
                params={"sort": "created", "direction": "desc", "per_page": 100, "page": page},
            )
            batch = resp.json()
            out.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return out[:limit]

    async def get_tarball(self, ref: str) -> bytes:
        resp = await self._request("GET", f"/repos/{self.repo}/tarball/{ref}")
        return resp.content
