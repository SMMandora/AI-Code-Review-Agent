import Link from "next/link";
import { Activity, Bug, DollarSign, Timer } from "lucide-react";
import { getOverviewStats, listReviews } from "@/lib/api/client";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
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
import { formatUsd, formatDateTime, formatDuration } from "@/lib/format";

export default async function DashboardPage() {
  const [stats, reviews] = await Promise.all([getOverviewStats(), listReviews()]);
  const recent = reviews.slice(0, 8);
  const maxDay = Math.max(...stats.reviewsPerDay.map((d) => d.count), 1);

  return (
    <>
      <PageHeader title="Dashboard" description="Repository review activity, cost, and latency at a glance." />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Reviews" value={stats.totalReviews} icon={Activity} hint="last 30 days" />
        <StatCard label="Avg Findings / PR" value={stats.avgFindings} icon={Bug} accent="text-high" />
        <StatCard label="Avg Cost / PR" value={formatUsd(stats.avgCostUsd, 3)} icon={DollarSign} accent="text-success" />
        <StatCard
          label="p95 Latency"
          value={`${stats.p95Seconds}s`}
          icon={Timer}
          hint={`p50 ${stats.p50Seconds}s`}
          accent="text-low"
        />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Reviews per day</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-40 items-end gap-1.5">
              {stats.reviewsPerDay.map((d) => (
                <div key={d.date} className="flex h-full flex-1 flex-col justify-end">
                  <div
                    className="w-full rounded-t bg-gradient-to-t from-blue-500/40 to-blue-400"
                    style={{ height: `${Math.max((d.count / maxDay) * 100, 4)}%` }}
                    title={`${d.date}: ${d.count}`}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Findings by severity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {stats.severitySplit.map((s) => {
              const total = stats.severitySplit.reduce((a, b) => a + b.count, 0);
              return (
                <div key={s.severity} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="capitalize text-muted-foreground">{s.severity}</span>
                    <span className="font-medium">{s.count}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-current"
                      style={{
                        width: `${(s.count / total) * 100}%`,
                        color: `var(--${s.severity === "low" ? "low" : s.severity})`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Recent reviews</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>PR</TableHead>
                <TableHead className="hidden md:table-cell">Repository</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Findings</TableHead>
                <TableHead className="hidden text-right sm:table-cell">Cost</TableHead>
                <TableHead className="hidden text-right lg:table-cell">Duration</TableHead>
                <TableHead className="hidden text-right lg:table-cell">When</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recent.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>
                    <Link href={`/reviews/${r.id}`} className="font-medium hover:underline">
                      #{r.prNumber}
                    </Link>
                    <div className="max-w-[18rem] truncate text-xs text-muted-foreground">{r.prTitle}</div>
                  </TableCell>
                  <TableCell className="hidden font-mono text-xs text-muted-foreground md:table-cell">
                    {r.repo}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={r.status} />
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{r.findingsTotal}</TableCell>
                  <TableCell className="hidden text-right tabular-nums sm:table-cell">
                    {formatUsd(r.costUsd, 3)}
                  </TableCell>
                  <TableCell className="hidden text-right tabular-nums text-muted-foreground lg:table-cell">
                    {formatDuration(r.durationMs)}
                  </TableCell>
                  <TableCell className="hidden text-right text-xs text-muted-foreground lg:table-cell">
                    {formatDateTime(r.createdAt)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </>
  );
}
