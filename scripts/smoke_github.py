"""Live GitHub API smoke test. Usage: python scripts/smoke_github.py (needs .env). Requires `pip install -e .` (run via .venv)."""

import asyncio
import sys

import httpx

from codereview.settings import Settings


async def main() -> int:
    s = Settings()
    if not s.github_token or not s.github_repo:
        print("FAIL: set GITHUB_TOKEN and GITHUB_REPO in .env")
        return 1
    headers = {
        "Authorization": f"Bearer {s.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ai-code-review-agent",
    }
    async with httpx.AsyncClient(base_url="https://api.github.com", headers=headers, timeout=30) as c:
        user = (await c.get("/user")).raise_for_status().json()
        repo = (await c.get(f"/repos/{s.github_repo}")).raise_for_status().json()
        pulls = (await c.get(f"/repos/{s.github_repo}/pulls", params={"state": "open"})).raise_for_status().json()
    print(f"OK: authenticated as {user['login']}")
    print(f"OK: repo {repo['full_name']} (default branch: {repo['default_branch']})")
    print(f"OK: {len(pulls)} open PR(s)")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
