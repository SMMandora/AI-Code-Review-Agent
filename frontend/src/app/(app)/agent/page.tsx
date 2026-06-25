"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/app/page-header";
import { CheckStateIcon } from "@/components/app/badges";
import { AgentGraph } from "@/components/app/agent-graph";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getAgentRun } from "@/lib/api/client";
import { formatDuration, CHECK_STATE_META } from "@/lib/format";
import type { RunNode } from "@/lib/types";

export default function AgentPage() {
  const [nodes, setNodes] = useState<RunNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAgentRun().then((data) => {
      setNodes(data);
      setLoading(false);
    });
  }, []);

  return (
    <>
      <PageHeader
        title="Agent"
        description="LangGraph observability — live run trace"
      />

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-[460px] w-full rounded-lg" />
          <Skeleton className="h-48 w-full rounded-lg" />
        </div>
      ) : (
        <div className="space-y-6">
          {/* React Flow graph */}
          <AgentGraph nodes={nodes} />

          {/* Legend / node list */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Node Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {nodes.map((node) => {
                  const meta = CHECK_STATE_META[node.state];
                  return (
                    <div key={node.key} className="flex items-center gap-2.5">
                      <CheckStateIcon state={node.state} className="shrink-0" />
                      <span className="flex-1 text-sm">{node.label}</span>
                      <span className={`text-xs tabular-nums ${meta.className}`}>
                        {node.durationMs != null
                          ? formatDuration(node.durationMs)
                          : meta.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}
