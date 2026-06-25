"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, DollarSign, Zap, ArrowDownToLine, ArrowUpFromLine } from "lucide-react";
import type { CostAnalytics } from "@/lib/types";
import { getCostAnalytics } from "@/lib/api/client";
import { PageHeader } from "@/components/app/page-header";
import { StatCard } from "@/components/app/stat-card";
import { CostAreaChart, CostBarChart, CostDonut } from "@/components/app/charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatUsd, formatTokens } from "@/lib/format";

export default function CostsPage() {
  const [data, setData] = useState<CostAnalytics | null>(null);

  useEffect(() => {
    getCostAnalytics().then(setData);
  }, []);

  return (
    <>
      <PageHeader title="Cost Analytics" description="Token usage and spend across all models and repositories." />

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Tokens"
          value={data ? formatTokens(data.totalTokens) : "—"}
          icon={Zap}
        />
        <StatCard
          label="Input Tokens"
          value={data ? formatTokens(data.inputTokens) : "—"}
          icon={ArrowDownToLine}
          accent="text-violet-400"
        />
        <StatCard
          label="Output Tokens"
          value={data ? formatTokens(data.outputTokens) : "—"}
          icon={ArrowUpFromLine}
          accent="text-cyan-400"
        />
        <StatCard
          label="Total Cost"
          value={data ? formatUsd(data.totalCostUsd, 2) : "—"}
          icon={DollarSign}
          accent="text-success"
        />
      </div>

      {/* Threshold alert */}
      {data?.overThreshold && (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-critical/30 bg-critical/10 px-4 py-3 text-critical">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          <div className="text-sm">
            <span className="font-semibold">Cost threshold exceeded</span>
            {" — "}review monthly spend. Ceiling:{" "}
            <span className="font-mono font-semibold">{formatUsd(data.ceilingUsd, 2)}</span>
          </div>
        </div>
      )}

      {/* Cost over time */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Cost over time</CardTitle>
        </CardHeader>
        <CardContent>
          {data ? (
            <CostAreaChart data={data.series} />
          ) : (
            <div className="flex h-72 items-center justify-center text-sm text-muted-foreground">
              Loading…
            </div>
          )}
        </CardContent>
      </Card>

      {/* By-repo + by-model */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Cost by repository</CardTitle>
          </CardHeader>
          <CardContent>
            {data ? (
              <CostBarChart data={data.byRepo} />
            ) : (
              <div className="flex h-72 items-center justify-center text-sm text-muted-foreground">
                Loading…
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Cost by model</CardTitle>
          </CardHeader>
          <CardContent>
            {data ? (
              <CostDonut data={data.byModel} />
            ) : (
              <div className="flex h-72 items-center justify-center text-sm text-muted-foreground">
                Loading…
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
