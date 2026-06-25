import { getReview, getReviewFindings, getReviewDiff } from "@/lib/api/client";
import { PageHeader } from "@/components/app/page-header";
import { StatusBadge, SeverityBadge } from "@/components/app/badges";
import { FindingCard } from "@/components/app/finding-card";
import { DiffViewer } from "@/components/app/diff-viewer";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { formatUsd, formatDuration, formatDateTime } from "@/lib/format";
import { SEVERITIES } from "@/lib/types";
import type { Severity } from "@/lib/types";

export default async function ReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  const [review, findings, diff] = await Promise.all([
    getReview(id),
    getReviewFindings(id),
    getReviewDiff(id),
  ]);

  if (!review) {
    return (
      <Card className="mx-auto max-w-md mt-16">
        <CardContent className="py-12 text-center text-muted-foreground text-sm">
          Review <code className="font-mono">{id}</code> was not found.
        </CardContent>
      </Card>
    );
  }

  // Group findings by severity in canonical order
  const bySeverity = Object.fromEntries(
    SEVERITIES.map((s) => [s, findings.filter((f) => f.severity === s)]),
  ) as Record<Severity, typeof findings>;

  const severityCounts = SEVERITIES.map((s) => ({
    severity: s,
    count: bySeverity[s].length,
  })).filter((s) => s.count > 0);

  return (
    <>
      <PageHeader
        title={review.prTitle}
        description={
          `#${review.prNumber} · ${review.repo} · by ${review.author}`
        }
        actions={<StatusBadge status={review.status} />}
      />

      {/* Meta row */}
      <div className="mb-6 flex flex-wrap gap-x-6 gap-y-1 text-sm text-muted-foreground">
        <span>
          <span className="font-medium text-foreground">Model</span>{" "}
          <code className="font-mono text-xs">{review.model}</code>
        </span>
        <span>
          <span className="font-medium text-foreground">Cost</span>{" "}
          {formatUsd(review.costUsd, 3)}
        </span>
        <span>
          <span className="font-medium text-foreground">Duration</span>{" "}
          {formatDuration(review.durationMs)}
        </span>
        <span>
          <span className="font-medium text-foreground">When</span>{" "}
          {formatDateTime(review.createdAt)}
        </span>
        <span>
          <span className="font-medium text-foreground">Trigger</span>{" "}
          <span className="capitalize">{review.trigger}</span>
        </span>
      </div>

      {/* Severity summary strip */}
      {severityCounts.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {severityCounts.map(({ severity, count }) => (
            <div key={severity} className="flex items-center gap-1.5">
              <SeverityBadge severity={severity} />
              <span className="text-sm font-medium tabular-nums">{count}</span>
            </div>
          ))}
        </div>
      )}

      {/* Main layout — stacked mobile, 2-col desktop */}
      {/* Mobile: Tabs to switch between Findings and Diff */}
      <div className="block lg:hidden">
        <Tabs defaultValue="findings">
          <TabsList className="mb-4">
            <TabsTrigger value="findings">
              Findings ({findings.length})
            </TabsTrigger>
            <TabsTrigger value="diff">Diff</TabsTrigger>
          </TabsList>
          <TabsContent value="findings">
            <FindingsPanel bySeverity={bySeverity} totalCount={findings.length} />
          </TabsContent>
          <TabsContent value="diff">
            <DiffViewer files={diff} />
          </TabsContent>
        </Tabs>
      </div>

      {/* Desktop: 2-column grid */}
      <div className="hidden lg:grid lg:grid-cols-[1fr_420px] lg:gap-6">
        {/* Left: Diff */}
        <div>
          <h2 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Diff
          </h2>
          <DiffViewer files={diff} />
        </div>

        {/* Right: Findings */}
        <div>
          <h2 className="mb-3 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Findings ({findings.length})
          </h2>
          <FindingsPanel bySeverity={bySeverity} totalCount={findings.length} />
        </div>
      </div>
    </>
  );
}

function FindingsPanel({
  bySeverity,
  totalCount,
}: {
  bySeverity: Record<Severity, { id: string; path: string; line: number; severity: Severity; category: import("@/lib/types").Category; message: string; suggestion?: string }[]>;
  totalCount: number;
}) {
  if (totalCount === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          No findings for this review.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {SEVERITIES.map((severity) => {
        const group = bySeverity[severity];
        if (group.length === 0) return null;
        return (
          <div key={severity}>
            <div className="mb-2 flex items-center gap-2">
              <SeverityBadge severity={severity} />
              <span className="text-xs text-muted-foreground">{group.length}</span>
            </div>
            <div className="space-y-2">
              {group.map((finding) => (
                <FindingCard key={finding.id} finding={finding} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
