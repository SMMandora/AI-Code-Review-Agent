# CodeGuardian Frontend

The web UI for the AI Code Review Agent — a Next.js 16 (App Router) + React 19 +
Tailwind v4 + shadcn/ui dashboard. Dark, repository-aware, fully responsive.

It runs against a typed API client (`src/lib/api/client.ts`) backed by deterministic mock
data, so every screen renders and demos with **no backend required**. When the backend's
`/api/*` endpoints exist, set `NEXT_PUBLIC_USE_MOCKS=false` and the same client targets them.

## Run

```bash
npm install
npm run dev      # http://localhost:3000
# or: npm run build && npm run start
```

Other scripts: `npm run lint`, and `npm run screenshots` (captures the gallery below via
Playwright against a running `next start` on port 3100 — see `scripts/capture-screenshots.mjs`).

## Screens

| Landing | Dashboard |
|---|---|
| ![Landing](../docs/screenshots/landing.png) | ![Dashboard](../docs/screenshots/dashboard.png) |

| Pull Requests | Pull Request Analysis |
|---|---|
| ![Pull Requests](../docs/screenshots/pulls.png) | ![PR Analysis](../docs/screenshots/pr-analysis.png) |

| AI Review Results | LangGraph Agent Visualization |
|---|---|
| ![Review Results](../docs/screenshots/review-results.png) | ![Agent](../docs/screenshots/agent.png) |

| Knowledge Base & RAG Explorer | Cost Analytics |
|---|---|
| ![Knowledge](../docs/screenshots/knowledge.png) | ![Costs](../docs/screenshots/costs.png) |

| Review History | Settings |
|---|---|
| ![History](../docs/screenshots/history.png) | ![Settings](../docs/screenshots/settings.png) |

**Mobile (responsive):**

![Mobile dashboard](../docs/screenshots/mobile-dashboard.png)

## Stack

Next.js · React · TypeScript · Tailwind v4 · shadcn/ui (Base UI) · Recharts · React Flow
(`@xyflow/react`) · next-themes · lucide-react. See
[`docs/superpowers/specs/2026-06-12-frontend-design.md`](../docs/superpowers/specs/2026-06-12-frontend-design.md)
for the design spec and the deferred backend-wiring phase.
