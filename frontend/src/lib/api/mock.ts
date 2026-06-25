// Deterministic mock dataset for the frontend. Seeded so every build produces identical
// data (no live clock / Math.random in the output), letting screens render stably without a
// backend. Swap to real /api/* by flipping NEXT_PUBLIC_USE_MOCKS — see client.ts.

import type {
  Chunk,
  CostAnalytics,
  CostPoint,
  DiffFile,
  Finding,
  IndexStats,
  OverviewStats,
  PullRequest,
  Repo,
  RepoConfig,
  Review,
  ReviewStatus,
  RunNode,
  Severity,
  User,
} from "@/lib/types";

// --- seeded PRNG (mulberry32) ---------------------------------------------------------------
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = rng(20260612);
const pick = <T>(arr: readonly T[]): T => arr[Math.floor(rand() * arr.length)];
const between = (lo: number, hi: number) => lo + Math.floor(rand() * (hi - lo + 1));

// Fixed anchor — all timestamps are offsets from here (deterministic, no clock read).
const BASE_MS = Date.UTC(2026, 5, 12, 12, 0, 0);
const iso = (msAgo: number) => new Date(BASE_MS - msAgo).toISOString();
const HOUR = 3600_000;
const DAY = 24 * HOUR;

export const repos: Repo[] = [
  { id: "r1", fullName: "acme/payments-api", defaultBranch: "main", indexedChunks: 1842, lastIndexedSha: "a1b2c3d" },
  { id: "r2", fullName: "acme/web-dashboard", defaultBranch: "main", indexedChunks: 2310, lastIndexedSha: "e4f5a6b" },
  { id: "r3", fullName: "acme/ml-pipeline", defaultBranch: "develop", indexedChunks: 967, lastIndexedSha: "c7d8e9f" },
];

export const currentUser: User = {
  login: "shubham",
  name: "Shubham Mandora",
  avatarUrl: "",
  role: "admin",
};

const TITLES = [
  "Add Redis caching layer",
  "Fix race condition in payment webhook",
  "Refactor auth middleware",
  "Implement rate limiting on public API",
  "Migrate user table to UUID keys",
  "Add pagination to search endpoint",
  "Harden file upload validation",
  "Optimize N+1 query in dashboard",
  "Introduce feature-flag service",
  "Add retry logic to embedding client",
  "Sanitize markdown in comment renderer",
  "Wire structured logging",
  "Cache repository config per SHA",
  "Add idempotency keys to checkout",
  "Parallelize report generation",
];
const AUTHORS = ["alice", "bob-dev", "carol-eng", "dmitri", "erin-k", "frank-q"];
const PATHS = [
  "app/payments/webhook.py",
  "app/auth/middleware.py",
  "src/api/search.ts",
  "src/components/Comment.tsx",
  "app/cache/redis.py",
  "src/lib/upload.ts",
  "app/models/user.py",
  "src/hooks/useDashboard.ts",
];
const FINDING_MSGS: Record<Severity, string[]> = {
  critical: [
    "User input is interpolated directly into the SQL query, allowing injection.",
    "Hardcoded API token committed to source — rotate and move to an environment variable.",
    "`innerHTML` is set from untrusted comment text, enabling stored XSS.",
  ],
  high: [
    "`await` is missing on the async call, so the coroutine never runs.",
    "Off-by-one: the loop reads one element past the end of the array.",
    "Division by `count` without a zero guard raises on empty input.",
  ],
  medium: [
    "Broad `except: pass` swallows errors and hides failures.",
    "Mutable default argument is shared across calls.",
    "Time-of-check/time-of-use race between the exists check and open.",
  ],
  low: [
    "`print()` debugging left in library code — use the logger.",
    "Dead code: this branch is unreachable.",
    "Function lacks a docstring per repo convention.",
  ],
};
const SUGGESTIONS: Record<Severity, string | undefined> = {
  critical: 'cur.execute("SELECT * FROM users WHERE name = %s", (name,))',
  high: "result = await send(payload)",
  medium: undefined,
  low: "logger.debug(value)",
};

const SEV_RANK: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3 };

function makeFindings(seedId: string, count: number): Finding[] {
  const cats = ["correctness", "security", "style", "test_coverage"] as const;
  const out: Finding[] = [];
  for (let i = 0; i < count; i++) {
    const severity = pick(["critical", "high", "medium", "low"] as Severity[]);
    out.push({
      id: `${seedId}-f${i}`,
      path: pick(PATHS),
      line: between(3, 180),
      severity,
      category: pick(cats),
      message: pick(FINDING_MSGS[severity]),
      suggestion: SUGGESTIONS[severity],
    });
  }
  return out.sort((a, b) => SEV_RANK[a.severity] - SEV_RANK[b.severity]);
}

// --- reviews ---------------------------------------------------------------------------------
const STATUS_CYCLE: ReviewStatus[] = [
  "completed", "completed", "completed", "running", "completed", "queued",
  "completed", "failed", "completed", "completed", "skipped", "cost_exceeded",
];

export const reviews: Review[] = Array.from({ length: 28 }, (_, i) => {
  const status = STATUS_CYCLE[i % STATUS_CYCLE.length];
  const repo = repos[i % repos.length].fullName;
  const inputTokens = between(8000, 60000);
  const outputTokens = between(400, 4000);
  const model = pick(["claude-sonnet-4-6", "claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5"]);
  const price: Record<string, [number, number]> = {
    "claude-sonnet-4-6": [3, 15],
    "claude-opus-4-8": [5, 25],
    "claude-haiku-4-5": [1, 5],
  };
  const [pin, pout] = price[model];
  const costUsd = +(((inputTokens * pin + outputTokens * pout) / 1e6)).toFixed(4);
  const findingsTotal = status === "completed" ? between(0, 9) : 0;
  return {
    id: `rev_${1000 + i}`,
    repo,
    prNumber: 142 - i,
    prTitle: TITLES[i % TITLES.length],
    author: pick(AUTHORS),
    headSha: Math.abs(((i + 7) * 2654435761) >>> 0).toString(16).slice(0, 7),
    status,
    trigger: i % 5 === 0 ? "slash" : "webhook",
    model,
    findingsTotal,
    commentsPosted: Math.min(findingsTotal, 7),
    inputTokens,
    outputTokens,
    costUsd: status === "cost_exceeded" ? 0.62 : costUsd,
    durationMs: between(6000, 28000),
    createdAt: iso(i * 7 * HOUR + between(0, 3) * HOUR),
  };
});

const findingsByReview: Record<string, Finding[]> = {};
for (const r of reviews) {
  findingsByReview[r.id] = r.status === "completed" ? makeFindings(r.id, r.findingsTotal) : [];
}
export { findingsByReview };

// --- pull requests ---------------------------------------------------------------------------
export const pullRequests: PullRequest[] = reviews.slice(0, 9).map((r, i) => ({
  number: r.prNumber,
  title: r.prTitle,
  author: r.author,
  branch: `feature/${r.prTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 24)}`,
  additions: between(12, 480),
  deletions: between(2, 160),
  changedFiles: between(1, 14),
  reviewId: r.id,
  status: r.status,
  updatedAt: iso(i * 5 * HOUR),
}));

// --- live run status (for a running PR) ------------------------------------------------------
export const runNodes: RunNode[] = [
  { key: "fetch", label: "Fetching Content", state: "passed", durationMs: 1840 },
  { key: "embed_context", label: "Restoring Embeddings", state: "passed", durationMs: 920 },
  { key: "check_security", label: "Running Security Checks", state: "running" },
  { key: "check_correctness", label: "Running Correctness Checks", state: "running" },
  { key: "check_style", label: "Running Style Checks", state: "pending" },
  { key: "check_test_coverage", label: "Running Test Coverage Checks", state: "pending" },
  { key: "post", label: "Synthesizing Findings", state: "pending" },
];

// --- agent graph (LangGraph observability) ---------------------------------------------------
export const agentNodes: RunNode[] = [
  { key: "trigger", label: "Webhook Trigger", state: "passed", durationMs: 12 },
  { key: "fetch", label: "Fetch (diff + files)", state: "passed", durationMs: 1840 },
  { key: "embed_context", label: "Embed Context (RAG)", state: "passed", durationMs: 920 },
  { key: "check_correctness", label: "Correctness Check", state: "passed", durationMs: 8120 },
  { key: "check_security", label: "Security Check", state: "running" },
  { key: "check_style", label: "Style Check", state: "passed", durationMs: 6430 },
  { key: "check_test_coverage", label: "Test Coverage Check", state: "passed", durationMs: 7010 },
  { key: "dedup", label: "Dedup", state: "pending" },
  { key: "post", label: "Post Review", state: "pending" },
];

// --- knowledge base / chunks -----------------------------------------------------------------
export const chunks: Chunk[] = Array.from({ length: 32 }, (_, i) => {
  const kind = pick(["code", "code", "code", "style", "pr_comment"] as Chunk["sourceType"][]);
  return {
    id: `c${i}`,
    sourceType: kind,
    path: kind === "style" ? "CONTRIBUTING.md" : pick(PATHS),
    startLine: between(1, 200),
    endLine: 0,
    preview:
      kind === "pr_comment"
        ? "Prefer the logger over print in library code."
        : "def handle(event):\n    validate(event)\n    return process(event)",
    similarity: +(0.62 + rand() * 0.36).toFixed(3),
  };
}).map((c) => ({ ...c, endLine: c.startLine + between(20, 60) }));

export const indexStats: IndexStats = {
  totalChunks: 1842,
  codeChunks: 1503,
  styleChunks: 88,
  prCommentChunks: 251,
  filesIndexed: 312,
  lastIndexedSha: "a1b2c3d",
  lastIndexedAt: iso(4 * HOUR),
};

// --- cost analytics --------------------------------------------------------------------------
const series: CostPoint[] = Array.from({ length: 60 }, (_, i) => {
  const day = 59 - i;
  const inputTokens = between(40000, 220000);
  const outputTokens = between(3000, 18000);
  return {
    date: new Date(BASE_MS - day * DAY).toISOString().slice(0, 10),
    inputTokens,
    outputTokens,
    costUsd: +(((inputTokens * 3 + outputTokens * 15) / 1e6)).toFixed(3),
  };
});
export const costAnalytics: CostAnalytics = {
  inputTokens: series.reduce((s, p) => s + p.inputTokens, 0),
  outputTokens: series.reduce((s, p) => s + p.outputTokens, 0),
  totalTokens: series.reduce((s, p) => s + p.inputTokens + p.outputTokens, 0),
  totalCostUsd: +series.reduce((s, p) => s + p.costUsd, 0).toFixed(2),
  ceilingUsd: 0.5,
  overThreshold: true,
  series,
  byRepo: repos.map((r, i) => ({ repo: r.fullName, costUsd: +(38 - i * 11).toFixed(2) })),
  byModel: [
    { model: "claude-sonnet-4-6", costUsd: 41.2 },
    { model: "claude-opus-4-8", costUsd: 18.6 },
    { model: "claude-haiku-4-5", costUsd: 4.3 },
  ],
};

// --- overview stats --------------------------------------------------------------------------
const completed = reviews.filter((r) => r.status === "completed");
export const overviewStats: OverviewStats = {
  totalReviews: reviews.length,
  avgFindings: +(completed.reduce((s, r) => s + r.findingsTotal, 0) / completed.length).toFixed(1),
  avgCostUsd: +(completed.reduce((s, r) => s + r.costUsd, 0) / completed.length).toFixed(3),
  monthlySpendUsd: 593.4,
  p50Seconds: 18,
  p95Seconds: 27,
  reviewsPerDay: Array.from({ length: 14 }, (_, i) => ({
    date: new Date(BASE_MS - (13 - i) * DAY).toISOString().slice(0, 10),
    count: between(1, 9),
  })),
  severitySplit: [
    { severity: "critical", count: 7 },
    { severity: "high", count: 19 },
    { severity: "medium", count: 24 },
    { severity: "low", count: 38 },
  ],
};

// --- repo config -----------------------------------------------------------------------------
export const repoConfig: RepoConfig = {
  skipFiles: ["**/migrations/**", "*.lock", "dist/**"],
  customRules: ["No print statements in library code; use the logger."],
  model: "claude-sonnet-4-6",
  severityThreshold: "low",
};

// --- a sample diff for the Review Results screen ---------------------------------------------
export const sampleDiff: DiffFile[] = [
  {
    path: "app/payments/webhook.py",
    additions: 6,
    deletions: 2,
    lines: [
      { kind: "hunk", text: "@@ -10,7 +10,11 @@ def handle_webhook(request):" },
      { kind: "context", oldNo: 10, newNo: 10, text: "    payload = request.body" },
      { kind: "del", oldNo: 11, text: "    user = db.execute('SELECT * FROM users WHERE id = ' + uid)" },
      { kind: "add", newNo: 11, text: "    user = db.execute('SELECT * FROM users WHERE id = %s', (uid,))" },
      { kind: "context", oldNo: 12, newNo: 12, text: "    if not verify(payload):" },
      { kind: "add", newNo: 13, text: "        log.warning('invalid signature')" },
      { kind: "context", oldNo: 13, newNo: 14, text: "        return 401" },
    ],
  },
];
