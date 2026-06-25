# CodeGuardian Frontend — Design Spec

**Date:** 2026-06-12
**Status:** Approved to implement (user: "implement the frontend completely")
**Scope of this build:** The complete Next.js frontend application — all 10 mockup screens,
themed, responsive, running on a typed API client backed by realistic mock data, verified
with `npm run build`.

## 1. Scope boundary (read first)

**In scope now:** Next.js App Router app in `frontend/`; all 10 screens; dark theme matching
the mockup; responsive; shadcn/ui component system; Recharts charts; React Flow agent graph;
a typed API client (`src/lib/api/`) whose functions today return mock fixtures behind a
`USE_MOCKS` flag, so every screen renders and demos with zero backend dependency.

**Explicitly deferred (separate backend sub-projects, mocked at the API boundary here):**
GitHub OAuth + sessions, GitHub App + multi-repo schema migration, SSE run-streaming,
persisted findings, settings persistence, billing. The client targets a `/api/*` contract;
swapping `USE_MOCKS=false` later points it at the real backend once those endpoints exist.

**Locked product assumptions:** single-tenant / multi-user · multi-repo UI · pricing page
decorative · no real auth in this phase (a mock current-user + repo switcher stand in).

## 2. Stack

- Next.js (App Router) + TypeScript, `src/` dir, import alias `@/*`
- Tailwind CSS + shadcn/ui (new-york style, dark default)
- Recharts (line/area/bar/donut), `@xyflow/react` (LangGraph node graph)
- `lucide-react` icons, `next-themes` (dark default, theme toggle), `sonner` toasts
- No data-fetching library required; a thin async API module suffices. (TanStack Query is a
  later option when real endpoints land.)

## 3. Routes / screens

| Route | Screen | Primary data |
|---|---|---|
| `/` | Landing / marketing (hero, features, architecture, metrics, testimonials, pricing) | static |
| `/dashboard` | Repository Dashboard (stat cards, reviews/day, cost chart, severity split, recent table) | `listReviews`, `getOverviewStats` |
| `/pulls` | Pull Requests list (open/recent PRs with review status) | `listPullRequests` |
| `/pulls/[number]` | Pull Request Analysis View (PR meta, live AI review-status checklist + progress ring) | `getPullRequest`, `getRunStatus` |
| `/reviews/[id]` | AI Review Results (diff viewer + findings grouped by severity/category) | `getReview`, `getReviewFindings` |
| `/agent` | LangGraph Agent Visualization (node graph + per-node status/timing) | `getAgentRun` |
| `/knowledge` | Knowledge Base & RAG Explorer (index stats, search, embedding cloud, chunk list) | `getIndexStats`, `searchChunks` |
| `/costs` | Cost Analytics (token/cost cards, cost-over-time, by-repo, by-model donut, threshold alert) | `getCostAnalytics` |
| `/history` | Review History (filterable table: status, repo, date) | `listReviews` (filtered) |
| `/settings` | Settings & Configuration (.codereview.yml editor, webhook, masked secrets) | `getRepoConfig`, `saveRepoConfig` |

Mobile responsiveness is a per-screen Tailwind concern (collapsing sidebar → `Sheet`,
stacking cards), not a separate route. A final responsive-polish pass covers all screens.

## 4. App shell

- **Marketing layout** (`/`): standalone, full-bleed, own nav + footer, no app chrome.
- **App layout** (everything else): persistent left sidebar (Overview, Pull Requests,
  Knowledge Base, Cost Analytics, History, Settings) + top bar (repo switcher, global search
  input, theme toggle, user avatar menu). Sidebar collapses into a `Sheet` on mobile.
- Active-route highlighting; brand mark "CodeGuardian.AI" top-left.

## 5. Design tokens (match the mockup)

Dark, near-black canvas with slightly lighter cards, blue→violet accent gradients, soft glow.
Defined as CSS variables in `globals.css` (shadcn theme vars overridden):

- background `#0A0E17`, card `#121826`, popover `#121826`, border `#1E2533`, muted `#1A2130`
- foreground `#E6EAF2`, muted-foreground `#8A93A6`
- primary (accent) blue `#3B82F6`; gradient `#3B82F6 → #8B5CF6`
- severity: critical `#EF4444`, high `#F97316`, medium `#EAB308`, low/style `#3B82F6`,
  success/passed `#22C55E`
- radius `0.75rem`; cards use `border border-border bg-card` + subtle shadow

## 6. Shared types (`src/lib/types.ts`)

```ts
type Severity = "critical" | "high" | "medium" | "low";
type Category = "correctness" | "security" | "style" | "test_coverage";
type ReviewStatus = "completed" | "running" | "queued" | "skipped" | "failed" | "cost_exceeded";
type CheckState = "pending" | "running" | "passed" | "failed";

interface Repo { id: string; fullName: string; defaultBranch: string; indexedChunks: number; }
interface User { login: string; name: string; avatarUrl: string; role: "admin" | "reviewer" | "viewer"; }
interface Finding {
  id: string; path: string; line: number; severity: Severity; category: Category;
  message: string; suggestion?: string;
}
interface Review {
  id: string; repo: string; prNumber: number; prTitle: string; author: string;
  headSha: string; status: ReviewStatus; trigger: "webhook" | "slash";
  model: string; findingsTotal: number; commentsPosted: number;
  inputTokens: number; outputTokens: number; costUsd: number; durationMs: number;
  createdAt: string;
}
interface RunNode { key: string; label: string; state: CheckState; durationMs?: number; }
interface PullRequest {
  number: number; title: string; author: string; branch: string; additions: number;
  deletions: number; changedFiles: number; reviewId?: string; status: ReviewStatus;
}
interface Chunk { id: string; sourceType: "code" | "style" | "pr_comment"; path: string;
  startLine: number; endLine: number; preview: string; similarity?: number; }
interface CostPoint { date: string; costUsd: number; inputTokens: number; outputTokens: number; }
interface RepoConfig { skipFiles: string[]; customRules: string[]; model: string;
  severityThreshold: Severity; }
```

## 7. API client (`src/lib/api/`)

- `client.ts` — every screen calls these async functions; never `fetch` inline in a component.
  Signatures (return Promises): `listReviews(filter?)`, `getReview(id)`, `getReviewFindings(id)`,
  `getOverviewStats()`, `listPullRequests()`, `getPullRequest(n)`, `getRunStatus(id)`,
  `getAgentRun(id)`, `getIndexStats()`, `searchChunks(q)`, `getCostAnalytics()`,
  `getRepoConfig()`, `saveRepoConfig(cfg)`, `listRepos()`, `getCurrentUser()`.
- `mock/` — deterministic fixtures (≥ 24 reviews across statuses, findings spanning all
  severities/categories, a chunk set, 60-day cost series, etc.) + a small `delay()` to mimic
  network. Fixtures are seeded/static (no `Math.random` in render) so screens are stable.
- `USE_MOCKS` (default `true`, from `NEXT_PUBLIC_USE_MOCKS`) selects mock vs real `/api/*`
  fetch. Real branch is written but unused until backend endpoints exist.

## 8. Component inventory

- shadcn primitives: button, card, badge, table, tabs, input, textarea, select,
  dropdown-menu, avatar, progress, separator, sheet, dialog, skeleton, sonner, tooltip, switch.
- Custom: `StatCard`, `SeverityBadge`, `StatusBadge`, `FindingCard`, `RunStatusChecklist`
  (with circular progress), `AgentGraph` (React Flow), `DiffViewer` (line-numbered, inline
  finding markers), `CostChart`/`AreaChart`/`DonutChart` (Recharts wrappers), `EmbeddingCloud`
  (decorative SVG scatter), `RepoSwitcher`, `Sidebar`, `Topbar`, `EmptyState`, `PageHeader`.

## 9. Build order (phases)

1. **Foundation** — scaffold (done via create-next-app), theme tokens, shadcn init + add
   primitives, app shell (sidebar/topbar/layouts), types, API client + mock fixtures, landing
   page. Gate: `npm run build` passes, `/` and an empty `/dashboard` render.
2. **Core data screens** — Dashboard, Review History, AI Review Results (+ DiffViewer,
   FindingCard). Gate: build passes, screens render from mocks.
3. **PR + agent screens** — Pull Requests list, PR Analysis (RunStatusChecklist), Agent
   Visualization (React Flow graph).
4. **Knowledge + cost** — RAG Explorer (search + embedding cloud), Cost Analytics (charts +
   threshold alert).
5. **Settings + responsive polish** — Settings (.codereview.yml editor), mobile pass over all
   screens, final `npm run build` + `npm run lint`.

## 10. Quality bar

- `npm run build` (production build) passes with no type errors after every phase.
- `npm run lint` clean.
- Every route renders without runtime errors on mock data (verified by building + a smoke
  check of the rendered routes).
- No `Math.random()`/`Date.now()` in render paths (stable output); fixtures are static.
- Accessibated where cheap: semantic landmarks, alt text, focus-visible (shadcn defaults).

## 11. Deferred follow-on (documented, not built here)

Backend JSON API (`/api/*`), GitHub OAuth, GitHub App + multi-repo schema, SSE run streaming,
findings persistence, settings store, billing. When built, set `NEXT_PUBLIC_USE_MOCKS=false`
and the existing client targets them unchanged.
