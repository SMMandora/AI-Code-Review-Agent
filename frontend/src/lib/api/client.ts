// The single API surface for the app. Components import from here and never fetch inline.
// Today these resolve against deterministic mocks; set NEXT_PUBLIC_USE_MOCKS=false to target
// the real backend `/api/*` once those endpoints exist (signatures stay identical).

import type {
  Chunk,
  CostAnalytics,
  DiffFile,
  Finding,
  IndexStats,
  OverviewStats,
  PullRequest,
  Repo,
  RepoConfig,
  Review,
  ReviewListFilter,
  RunNode,
  User,
} from "@/lib/types";
import * as mock from "@/lib/api/mock";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

const delay = (ms = 120) => new Promise((r) => setTimeout(r, ms));

async function real<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export async function listRepos(): Promise<Repo[]> {
  if (USE_MOCKS) return delay().then(() => mock.repos);
  return real("/repos");
}

export async function getCurrentUser(): Promise<User> {
  if (USE_MOCKS) return delay().then(() => mock.currentUser);
  return real("/me");
}

export async function getOverviewStats(): Promise<OverviewStats> {
  if (USE_MOCKS) return delay().then(() => mock.overviewStats);
  return real("/overview");
}

export async function listReviews(filter: ReviewListFilter = {}): Promise<Review[]> {
  if (USE_MOCKS) {
    return delay().then(() =>
      mock.reviews.filter(
        (r) =>
          (!filter.status || r.status === filter.status) &&
          (!filter.repo || r.repo === filter.repo) &&
          (!filter.query ||
            r.prTitle.toLowerCase().includes(filter.query.toLowerCase()) ||
            String(r.prNumber).includes(filter.query)),
      ),
    );
  }
  const qs = new URLSearchParams(filter as Record<string, string>).toString();
  return real(`/reviews${qs ? `?${qs}` : ""}`);
}

export async function getReview(id: string): Promise<Review | undefined> {
  if (USE_MOCKS) return delay().then(() => mock.reviews.find((r) => r.id === id));
  return real(`/reviews/${id}`);
}

export async function getReviewFindings(id: string): Promise<Finding[]> {
  if (USE_MOCKS) return delay().then(() => mock.findingsByReview[id] ?? []);
  return real(`/reviews/${id}/findings`);
}

export async function getReviewDiff(id: string): Promise<DiffFile[]> {
  if (USE_MOCKS) return delay().then(() => mock.sampleDiff);
  return real(`/reviews/${id}/diff`);
}

export async function listPullRequests(): Promise<PullRequest[]> {
  if (USE_MOCKS) return delay().then(() => mock.pullRequests);
  return real("/pulls");
}

export async function getPullRequest(n: number): Promise<PullRequest | undefined> {
  if (USE_MOCKS) return delay().then(() => mock.pullRequests.find((p) => p.number === n));
  return real(`/pulls/${n}`);
}

export async function getRunStatus(_n: number): Promise<RunNode[]> {
  if (USE_MOCKS) return delay().then(() => mock.runNodes);
  return real(`/pulls/${_n}/status`);
}

export async function getAgentRun(reviewId?: string): Promise<RunNode[]> {
  if (USE_MOCKS) return delay().then(() => mock.agentNodes);
  return real(reviewId ? `/agent/run?review=${reviewId}` : "/agent/run");
}

export async function getIndexStats(): Promise<IndexStats> {
  if (USE_MOCKS) return delay().then(() => mock.indexStats);
  return real("/knowledge/stats");
}

export async function searchChunks(query: string): Promise<Chunk[]> {
  if (USE_MOCKS) {
    return delay(200).then(() => {
      const q = query.trim().toLowerCase();
      const list = q
        ? mock.chunks.filter((c) => c.path.toLowerCase().includes(q) || c.preview.toLowerCase().includes(q))
        : mock.chunks;
      return [...list].sort((a, b) => (b.similarity ?? 0) - (a.similarity ?? 0));
    });
  }
  return real(`/knowledge/search?q=${encodeURIComponent(query)}`);
}

export async function getCostAnalytics(): Promise<CostAnalytics> {
  if (USE_MOCKS) return delay().then(() => mock.costAnalytics);
  return real("/costs");
}

export async function getRepoConfig(): Promise<RepoConfig> {
  if (USE_MOCKS) return delay().then(() => mock.repoConfig);
  return real("/settings/config");
}

export async function saveRepoConfig(cfg: RepoConfig): Promise<RepoConfig> {
  if (USE_MOCKS) return delay(300).then(() => cfg);
  return real("/settings/config", { method: "PUT", body: JSON.stringify(cfg) });
}
