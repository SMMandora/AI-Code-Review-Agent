"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import type { Repo, Review, ReviewListFilter, ReviewStatus } from "@/lib/types";
import { listRepos, listReviews } from "@/lib/api/client";
import { PageHeader } from "@/components/app/page-header";
import { StatusBadge } from "@/components/app/badges";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { formatUsd, formatDateTime, formatDuration } from "@/lib/format";

const STATUS_OPTIONS: { value: ReviewStatus; label: string }[] = [
  { value: "completed", label: "Completed" },
  { value: "running", label: "Running" },
  { value: "queued", label: "Queued" },
  { value: "skipped", label: "Skipped" },
  { value: "failed", label: "Failed" },
  { value: "cost_exceeded", label: "Cost Exceeded" },
];

export default function HistoryPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ReviewStatus | "">("");
  const [repo, setRepo] = useState("");

  // Fetch repos once on mount
  useEffect(() => {
    listRepos().then(setRepos);
  }, []);

  // Fetch reviews whenever any filter changes
  useEffect(() => {
    let cancelled = false;
    const filter: ReviewListFilter = {};
    if (status) filter.status = status;
    if (repo) filter.repo = repo;
    if (query.trim()) filter.query = query.trim();

    listReviews(filter).then((data) => {
      if (!cancelled) {
        setReviews(data);
        setLoading(false);
      }
    });

    return () => {
      cancelled = true;
      setLoading(true);
    };
  }, [query, status, repo]);

  return (
    <>
      <PageHeader
        title="Review History"
        description="Filter and inspect past AI code-review runs."
      />

      {/* Filter bar */}
      <div className="mb-5 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by PR title or number…"
            className="pl-9"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <Select
          value={status || "all"}
          onValueChange={(v) => setStatus(!v || v === "all" ? "" : (v as ReviewStatus))}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {STATUS_OPTIONS.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={repo || "all"}
          onValueChange={(v) => setRepo(!v || v === "all" ? "" : v)}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All repositories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All repositories</SelectItem>
            {repos.map((r) => (
              <SelectItem key={r.id} value={r.fullName}>
                {r.fullName}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {loading ? "Loading…" : `${reviews.length} review${reviews.length !== 1 ? "s" : ""}`}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="space-y-3 p-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          ) : reviews.length === 0 ? (
            <div className="px-4 py-12 text-center text-sm text-muted-foreground">
              No reviews match your filters.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>PR</TableHead>
                  <TableHead className="hidden md:table-cell">Repository</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Findings</TableHead>
                  <TableHead className="hidden text-right sm:table-cell">Cost</TableHead>
                  <TableHead className="hidden text-right lg:table-cell">Duration</TableHead>
                  <TableHead className="hidden text-right sm:table-cell">Trigger</TableHead>
                  <TableHead className="hidden text-right lg:table-cell">When</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reviews.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>
                      <Link
                        href={`/reviews/${r.id}`}
                        className="font-medium hover:underline"
                      >
                        #{r.prNumber}
                      </Link>
                      <div className="max-w-[18rem] truncate text-xs text-muted-foreground">
                        {r.prTitle}
                      </div>
                    </TableCell>
                    <TableCell className="hidden font-mono text-xs text-muted-foreground md:table-cell">
                      {r.repo}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={r.status} />
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {r.findingsTotal}
                    </TableCell>
                    <TableCell className="hidden text-right tabular-nums sm:table-cell">
                      {formatUsd(r.costUsd, 3)}
                    </TableCell>
                    <TableCell className="hidden text-right tabular-nums text-muted-foreground lg:table-cell">
                      {formatDuration(r.durationMs)}
                    </TableCell>
                    <TableCell className="hidden text-right text-xs text-muted-foreground sm:table-cell capitalize">
                      {r.trigger}
                    </TableCell>
                    <TableCell className="hidden text-right text-xs text-muted-foreground lg:table-cell">
                      {formatDateTime(r.createdAt)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}
