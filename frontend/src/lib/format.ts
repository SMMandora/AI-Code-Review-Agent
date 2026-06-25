import type { CheckState, ReviewStatus, Severity } from "@/lib/types";

export function formatUsd(n: number, digits = 2): string {
  return `$${n.toFixed(digits)}`;
}

export function formatNumber(n: number): string {
  return n.toLocaleString("en-US");
}

export function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Absolute, locale-stable date — avoids SSR/CSR hydration drift from relative times. */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}, ${d.getUTCFullYear()}`;
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}, ${hh}:${mm}`;
}

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

/** Tailwind classes per severity (tokens defined in globals.css). */
export const severityClasses: Record<Severity, { text: string; bg: string; border: string; dot: string }> = {
  critical: { text: "text-critical", bg: "bg-critical/10", border: "border-critical/30", dot: "bg-critical" },
  high: { text: "text-high", bg: "bg-high/10", border: "border-high/30", dot: "bg-high" },
  medium: { text: "text-medium", bg: "bg-medium/10", border: "border-medium/30", dot: "bg-medium" },
  low: { text: "text-low", bg: "bg-low/10", border: "border-low/30", dot: "bg-low" },
};

export const STATUS_META: Record<ReviewStatus, { label: string; className: string }> = {
  completed: { label: "Completed", className: "text-success border-success/30 bg-success/10" },
  running: { label: "Running", className: "text-low border-low/30 bg-low/10" },
  queued: { label: "Queued", className: "text-muted-foreground border-border bg-muted" },
  skipped: { label: "Skipped", className: "text-muted-foreground border-border bg-muted" },
  failed: { label: "Failed", className: "text-critical border-critical/30 bg-critical/10" },
  cost_exceeded: { label: "Cost Exceeded", className: "text-high border-high/30 bg-high/10" },
};

export const CHECK_STATE_META: Record<CheckState, { label: string; className: string }> = {
  pending: { label: "Pending", className: "text-muted-foreground" },
  running: { label: "Running", className: "text-low" },
  passed: { label: "Passed", className: "text-success" },
  failed: { label: "Failed", className: "text-critical" },
};
