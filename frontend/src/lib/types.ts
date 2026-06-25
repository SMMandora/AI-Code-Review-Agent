// Shared domain types for the CodeGuardian frontend.
// Mirrors the backend's review model; extended with UI-only shapes (run status, agent graph).

export type Severity = "critical" | "high" | "medium" | "low";
export type Category = "correctness" | "security" | "style" | "test_coverage";
export type ReviewStatus =
  | "completed"
  | "running"
  | "queued"
  | "skipped"
  | "failed"
  | "cost_exceeded";
export type CheckState = "pending" | "running" | "passed" | "failed";

export interface Repo {
  id: string;
  fullName: string;
  defaultBranch: string;
  indexedChunks: number;
  lastIndexedSha: string;
}

export interface User {
  login: string;
  name: string;
  avatarUrl: string;
  role: "admin" | "reviewer" | "viewer";
}

export interface Finding {
  id: string;
  path: string;
  line: number;
  severity: Severity;
  category: Category;
  message: string;
  suggestion?: string;
}

export interface Review {
  id: string;
  repo: string;
  prNumber: number;
  prTitle: string;
  author: string;
  headSha: string;
  status: ReviewStatus;
  trigger: "webhook" | "slash";
  model: string;
  findingsTotal: number;
  commentsPosted: number;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  durationMs: number;
  createdAt: string; // ISO
}

export interface RunNode {
  key: string;
  label: string;
  state: CheckState;
  durationMs?: number;
}

export interface PullRequest {
  number: number;
  title: string;
  author: string;
  branch: string;
  additions: number;
  deletions: number;
  changedFiles: number;
  reviewId?: string;
  status: ReviewStatus;
  updatedAt: string;
}

export interface DiffLine {
  kind: "add" | "del" | "context" | "hunk";
  oldNo?: number;
  newNo?: number;
  text: string;
}

export interface DiffFile {
  path: string;
  additions: number;
  deletions: number;
  lines: DiffLine[];
}

export interface Chunk {
  id: string;
  sourceType: "code" | "style" | "pr_comment";
  path: string;
  startLine: number;
  endLine: number;
  preview: string;
  similarity?: number;
}

export interface CostPoint {
  date: string; // YYYY-MM-DD
  costUsd: number;
  inputTokens: number;
  outputTokens: number;
}

export interface OverviewStats {
  totalReviews: number;
  avgFindings: number;
  avgCostUsd: number;
  monthlySpendUsd: number;
  p50Seconds: number;
  p95Seconds: number;
  reviewsPerDay: { date: string; count: number }[];
  severitySplit: { severity: Severity; count: number }[];
}

export interface IndexStats {
  totalChunks: number;
  codeChunks: number;
  styleChunks: number;
  prCommentChunks: number;
  filesIndexed: number;
  lastIndexedSha: string;
  lastIndexedAt: string;
}

export interface CostAnalytics {
  totalTokens: number;
  inputTokens: number;
  outputTokens: number;
  totalCostUsd: number;
  ceilingUsd: number;
  overThreshold: boolean;
  series: CostPoint[];
  byRepo: { repo: string; costUsd: number }[];
  byModel: { model: string; costUsd: number }[];
}

export interface RepoConfig {
  skipFiles: string[];
  customRules: string[];
  model: string;
  severityThreshold: Severity;
}

export interface ReviewListFilter {
  status?: ReviewStatus;
  repo?: string;
  query?: string;
}

export const SEVERITIES: Severity[] = ["critical", "high", "medium", "low"];
export const CATEGORIES: Category[] = ["correctness", "security", "style", "test_coverage"];
export const MODELS = ["claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5"] as const;
