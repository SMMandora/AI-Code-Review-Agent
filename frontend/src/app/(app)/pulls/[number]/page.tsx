import Link from "next/link";
import { GitBranch, FileCode2, Plus, Minus } from "lucide-react";
import { getPullRequest, getRunStatus } from "@/lib/api/client";
import { PageHeader } from "@/components/app/page-header";
import { StatusBadge } from "@/components/app/badges";
import { RunStatusChecklist } from "@/components/app/run-status-checklist";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default async function PullRequestPage({
  params,
}: {
  params: Promise<{ number: string }>;
}) {
  const { number: rawNumber } = await params;
  const n = Number(rawNumber);

  const [pr, runNodes] = await Promise.all([getPullRequest(n), getRunStatus(n)]);

  if (!pr) {
    return (
      <Card className="mx-auto max-w-md mt-16">
        <CardContent className="py-12 text-center text-muted-foreground text-sm">
          Pull request <span className="font-mono font-medium">#{n}</span> was not found.
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <PageHeader
        title={pr.title}
        description={`#${pr.number} · by ${pr.author}`}
        actions={<StatusBadge status={pr.status} />}
      />

      {/* Branch + meta row */}
      <div className="mb-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <GitBranch className="size-3.5" />
          <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{pr.branch}</code>
        </span>
        <span className="flex items-center gap-1.5">
          <FileCode2 className="size-3.5" />
          {pr.changedFiles} file{pr.changedFiles !== 1 ? "s" : ""} changed
        </span>
        <span className="flex items-center gap-1.5">
          <Plus className="size-3.5 text-success" />
          <span className="text-success tabular-nums">{pr.additions}</span>
        </span>
        <span className="flex items-center gap-1.5">
          <Minus className="size-3.5 text-critical" />
          <span className="text-critical tabular-nums">{pr.deletions}</span>
        </span>
      </div>

      {/* Diff stats as small inline cards */}
      <div className="mb-6 grid grid-cols-3 gap-3 sm:grid-cols-3 max-w-sm">
        <div className="rounded-lg border border-border bg-card px-3 py-2 text-center">
          <div className="text-xs text-muted-foreground">Additions</div>
          <div className="text-base font-semibold tabular-nums text-success">+{pr.additions}</div>
        </div>
        <div className="rounded-lg border border-border bg-card px-3 py-2 text-center">
          <div className="text-xs text-muted-foreground">Deletions</div>
          <div className="text-base font-semibold tabular-nums text-critical">-{pr.deletions}</div>
        </div>
        <div className="rounded-lg border border-border bg-card px-3 py-2 text-center">
          <div className="text-xs text-muted-foreground">Files</div>
          <div className="text-base font-semibold tabular-nums">{pr.changedFiles}</div>
        </div>
      </div>

      {/* AI Review Status */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <CardTitle className="text-base">AI Review Status</CardTitle>
          {pr.reviewId ? (
            <Button
              variant="outline"
              size="sm"
              render={<Link href={`/reviews/${pr.reviewId}`} />}
            >
              View Results
            </Button>
          ) : null}
        </CardHeader>
        <CardContent>
          <RunStatusChecklist nodes={runNodes} />
        </CardContent>
      </Card>
    </>
  );
}
