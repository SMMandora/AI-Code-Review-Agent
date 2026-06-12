# AI Code Review Agent

## 1. What it is

An autonomous code review agent that monitors a single GitHub repository, reviews pull
requests with Claude grounded in the repo's own conventions (RAG over pgvector), and posts
line-specific review comments as one GitHub review per PR head SHA. It runs as a single
Docker container — FastAPI webhook receiver, in-process background worker, LangGraph agent,
and a server-rendered dashboard — with Postgres (pgvector) as the only external service.

> **Dashboard screenshot placeholder** — `GET /` once the server is running.

See [docs/architecture.md](docs/architecture.md) for component diagrams and design decisions.

---

## 2. How a review works

1. GitHub delivers a `pull_request` webhook (opened / synchronize / reopened).
2. HMAC signature is verified; the event is enqueued and 202 returned within milliseconds.
3. The background worker pulls the job and starts the LangGraph graph.
4. The `fetch` node checks idempotency, fetches PR metadata and the unified diff, loads `.codereview.yml`, and runs a preflight cost estimate.
5. The `embed_context` node retrieves relevant code chunks and style history from pgvector.
6. Four check nodes run in parallel (correctness, security, style, test coverage) — each calls Claude once.
7. The `post` node deduplicates findings, composes a single review, and posts it to GitHub as one `POST /pulls/N/reviews` call.

---

## 3. Requirements

- Python 3.12+
- Postgres with pgvector — or Docker (compose file provided)
- GitHub personal access token (classic `repo` scope, or fine-grained: PR read/write + contents read)
- Anthropic API key (Claude calls)
- Voyage AI API key (embeddings)

---

## 4. Quick start (local)

```powershell
# Windows — PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1       # bash: . .venv/Scripts/activate
pip install -e .[dev]
cp .env.example .env             # fill in all values
docker compose up -d db
python scripts/smoke_github.py
python scripts/seed_index.py
uvicorn codereview.web.app:create_app --factory --port 8000
```

Open `http://localhost:8000/` for the dashboard.

---

## 5. GitHub setup

**PAT scopes** (classic token): `repo` (or `public_repo` for a public repository).
Fine-grained token minimum permissions: *Pull requests* read/write, *Contents* read.

**Webhook configuration** (repo or organisation → Settings → Webhooks → Add webhook):

| Field | Value |
|---|---|
| Payload URL | `https://<host>/webhooks/github` |
| Content type | `application/json` |
| Secret | value of `GITHUB_WEBHOOK_SECRET` |
| Events | *Pull requests*, *Issue comments*, *Pushes* |

---

## 6. `.codereview.yml` reference

Place this file in the root of the target repository's default branch. All keys are optional.

```yaml
skip_files: ["**/migrations/**", "*.lock", "dist/**"]   # gitignore-style globs
custom_rules:                                            # injected into every check prompt
  - "No print statements in library code; use the logger."
model: claude-sonnet-4-6        # claude-sonnet-4-6 | claude-opus-4-8 | claude-haiku-4-5
severity_threshold: low          # low | medium | high — minimum severity to post
```

Unknown keys are ignored with a warning. An invalid or unparseable file falls back to
defaults; both cases surface a warning line in the review body.

---

## 7. Slash command

Post `/review again` as a comment on any pull request to force a new review regardless of
whether the current head SHA has already been reviewed. The comment author must have
`OWNER`, `MEMBER`, or `COLLABORATOR` association on the repository.

---

## 8. Dashboard

`GET /` — shows the 50 most recent reviews, aggregate cost, average cost per review, p50/p95
latency (seconds), and an SVG cost-per-PR chart with the cost ceiling overlaid. `GET /healthz`
returns `{"ok": true, "db": true/false}`.

**The dashboard has no authentication — keep it network-restricted** (e.g. behind a VPN or
Fly.io private networking) and do not expose it to the public internet.

**Security note — `/review again` rate limiting.** The slash command is gated to
collaborators but is not rate-limited. A collaborator can repeatedly trigger paid reviews;
each individual review is capped by `COST_CEILING_USD` (default $0.50), and the in-process
queue caps the backlog at 100 items before returning 503. Monitor dashboard cost totals if
this is a concern.

---

## 9. Testing and quality gates

```bash
# Offline suite — no API keys, no network
.venv\Scripts\python.exe -m pytest

# pgvector integration tests (needs a running Postgres)
$env:DATABASE_URL="postgresql://codereview:codereview@localhost:5432/codereview"
.venv\Scripts\python.exe -m pytest -m pg

# Live adversarial prompt-regression gate (needs ANTHROPIC_API_KEY)
.venv\Scripts\python.exe scripts/run_prompt_regression.py

# Live release gate — must reach >= 80% findings-match rate (needs ANTHROPIC_API_KEY)
.venv\Scripts\python.exe -m evals.run_evals
```

`run_prompt_regression.py` accepts `--check security`, `--case NN`, and `--model M`.
`evals/run_evals.py` accepts `--pr pr_007`, `--limit N`, and `--model M`.

**Cost ceiling**: reviews are aborted (not posted) if the preflight estimate × 1.3 or the
actual post-run cost exceeds `COST_CEILING_USD`. The default is $0.50.

**Latency**: the four check nodes run in parallel (LangGraph superstep). p95 target is
under 30 s, measured on the dashboard.

---

## 10. Deploy

### Fly.io

```bash
fly launch --copy-config --no-deploy
fly secrets set \
  GITHUB_TOKEN=... \
  GITHUB_WEBHOOK_SECRET=... \
  ANTHROPIC_API_KEY=... \
  VOYAGE_API_KEY=... \
  GITHUB_REPO=owner/name \
  DATABASE_URL=postgresql://...
fly deploy
```

`fly.toml` is pre-configured: app `ai-code-review-agent`, region `iad`, internal port 8000,
HTTPS enforced, `/healthz` health check every 30 s, minimum 1 machine running.

### Railway / Render

Point at the `Dockerfile`; set the same six environment variables above. No further
configuration required — the container starts uvicorn on `$PORT` (default 8000).

---

## 11. Limitations and upgrade path

- **In-flight reviews are lost on restart.** The worker queue is in-process. Re-trigger
  any lost review with `/review again` on the PR.
- **Single repository per instance.** `GITHUB_REPO` is a single `owner/name` value; webhook
  events for other repositories are ignored (204).
- **Upgrade path — DB-backed job queue.** Replace the `asyncio.Queue` with a `jobs` table
  (status, payload, claimed_at). Workers poll or use `LISTEN`/`NOTIFY`. This survives
  restarts without losing jobs and allows horizontal scaling. The in-process queue is the
  documented starting point, not the ceiling.
