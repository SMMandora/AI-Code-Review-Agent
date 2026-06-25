"use client";

import { useEffect, useRef, useState } from "react";
import { Search, BookOpen, Code2, FileText, MessageSquare, GitCommit } from "lucide-react";
import type { Chunk, IndexStats } from "@/lib/types";
import { getIndexStats, searchChunks } from "@/lib/api/client";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { EmbeddingCloud } from "@/components/app/embedding-cloud";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { formatNumber, formatDate } from "@/lib/format";

type SourceType = Chunk["sourceType"];

const SOURCE_PILL: Record<SourceType, { label: string; className: string }> = {
  code: { label: "code", className: "bg-blue-500/15 text-blue-400 border border-blue-500/30" },
  style: { label: "style", className: "bg-violet-500/15 text-violet-400 border border-violet-500/30" },
  pr_comment: { label: "PR comment", className: "bg-amber-500/15 text-amber-400 border border-amber-500/30" },
};

function SourcePill({ type }: { type: SourceType }) {
  const m = SOURCE_PILL[type];
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", m.className)}>
      {m.label}
    </span>
  );
}

function SimilarityBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="w-9 text-right text-xs tabular-nums text-muted-foreground">{pct}%</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-blue-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function KnowledgePage() {
  const [stats, setStats] = useState<IndexStats | null>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load stats once on mount
  useEffect(() => {
    getIndexStats().then(setStats);
  }, []);

  // Initial load + debounced search. setLoading lives inside the deferred
  // callback (not the effect body) to avoid synchronous cascading renders.
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setLoading(true);
      searchChunks(query).then((data) => {
        setChunks(data);
        setLoading(false);
      });
    }, 280);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  return (
    <>
      <PageHeader
        title="Knowledge Base"
        description="Repository intelligence — indexed code, style, and past review comments."
      />

      {/* Stat row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard
          label="Total Chunks"
          value={stats ? formatNumber(stats.totalChunks) : "—"}
          icon={BookOpen}
        />
        <StatCard
          label="Files Indexed"
          value={stats ? formatNumber(stats.filesIndexed) : "—"}
          icon={FileText}
          accent="text-violet-400"
        />
        <StatCard
          label="Code Chunks"
          value={stats ? formatNumber(stats.codeChunks) : "—"}
          icon={Code2}
          accent="text-blue-400"
        />
        <StatCard
          label="Style Chunks"
          value={stats ? formatNumber(stats.styleChunks) : "—"}
          icon={FileText}
          accent="text-violet-400"
        />
        <StatCard
          label="PR Comment Chunks"
          value={stats ? formatNumber(stats.prCommentChunks) : "—"}
          icon={MessageSquare}
          accent="text-amber-400"
          hint={
            stats
              ? `SHA: ${stats.lastIndexedSha.slice(0, 7)} · ${formatDate(stats.lastIndexedAt)}`
              : undefined
          }
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        {/* Search + results */}
        <div className="space-y-4 lg:col-span-2">
          {/* Search bar */}
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search chunks by path or content…"
              className="pl-9"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>

          {/* Last indexed SHA note */}
          {stats && (
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <GitCommit className="size-3.5" />
              Last indexed:&nbsp;
              <code className="font-mono">{stats.lastIndexedSha.slice(0, 12)}</code>
              &nbsp;·&nbsp;{formatDate(stats.lastIndexedAt)}
            </p>
          )}

          {/* Results */}
          <div className="space-y-3">
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardContent className="p-4">
                    <div className="h-4 w-1/3 rounded bg-muted" />
                    <div className="mt-2 h-16 rounded bg-muted" />
                  </CardContent>
                </Card>
              ))
            ) : chunks.length === 0 ? (
              <div className="py-12 text-center text-sm text-muted-foreground">
                No chunks match your query.
              </div>
            ) : (
              chunks.map((chunk) => (
                <Card key={chunk.id}>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <SourcePill type={chunk.sourceType} />
                      <code className="text-xs font-mono text-muted-foreground">
                        {chunk.path}:{chunk.startLine}–{chunk.endLine}
                      </code>
                      {chunk.similarity !== undefined && (
                        <div className="ml-auto flex items-center gap-2 min-w-[120px]">
                          <SimilarityBar score={chunk.similarity} />
                        </div>
                      )}
                    </div>
                    <pre className="overflow-x-auto rounded-md bg-muted px-3 py-2 text-xs leading-relaxed line-clamp-4 whitespace-pre-wrap break-all">
                      {chunk.preview}
                    </pre>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>

        {/* Embedding cloud */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Embedding space</CardTitle>
            </CardHeader>
            <CardContent>
              <EmbeddingCloud className="w-full rounded-lg" />
              <p className="mt-3 text-center text-xs text-muted-foreground">
                Decorative projection of {stats ? formatNumber(stats.totalChunks) : "—"} indexed vectors
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
