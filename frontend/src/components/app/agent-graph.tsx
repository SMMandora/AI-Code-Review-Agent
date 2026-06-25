"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Position,
  type Node,
  type Edge,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { RunNode, CheckState } from "@/lib/types";
import { formatDuration } from "@/lib/format";

// Fixed left→right layout. Positions are keyed by node.key — deterministic, no random.
const FIXED_POSITIONS: Record<string, { x: number; y: number }> = {
  trigger:           { x: 0,   y: 180 },
  fetch:             { x: 180, y: 180 },
  embed_context:     { x: 360, y: 180 },
  check_correctness: { x: 560, y: 60  },
  check_security:    { x: 560, y: 160 },
  check_style:       { x: 560, y: 260 },
  check_test_coverage: { x: 560, y: 360 },
  dedup:             { x: 760, y: 180 },
  post:              { x: 940, y: 180 },
};

// Edges for the LangGraph pipeline
const STATIC_EDGES: Edge[] = [
  { id: "e-trigger-fetch",         source: "trigger",       target: "fetch"              },
  { id: "e-fetch-embed",           source: "fetch",         target: "embed_context"      },
  { id: "e-embed-correctness",     source: "embed_context", target: "check_correctness"  },
  { id: "e-embed-security",        source: "embed_context", target: "check_security"     },
  { id: "e-embed-style",           source: "embed_context", target: "check_style"        },
  { id: "e-embed-test",            source: "embed_context", target: "check_test_coverage"},
  { id: "e-correctness-dedup",     source: "check_correctness",  target: "dedup"         },
  { id: "e-security-dedup",        source: "check_security",     target: "dedup"         },
  { id: "e-style-dedup",           source: "check_style",        target: "dedup"         },
  { id: "e-test-dedup",            source: "check_test_coverage", target: "dedup"        },
  { id: "e-dedup-post",            source: "dedup",         target: "post"               },
];

const STATE_STYLES: Record<CheckState, { border: string; bg: string; text: string }> = {
  passed:  { border: "var(--success)",  bg: "rgba(34,197,94,0.08)",  text: "var(--success)" },
  running: { border: "var(--low)",      bg: "rgba(59,130,246,0.12)", text: "var(--low)" },
  pending: { border: "var(--border)",   bg: "rgba(30,37,51,0.6)",    text: "var(--muted-foreground)" },
  failed:  { border: "var(--critical)", bg: "rgba(239,68,68,0.08)",  text: "var(--critical)" },
};

function buildNodes(runNodes: RunNode[]): Node[] {
  return runNodes.map((rn) => {
    const pos = FIXED_POSITIONS[rn.key] ?? { x: 0, y: 0 };
    const style = STATE_STYLES[rn.state];
    const duration = rn.durationMs != null ? formatDuration(rn.durationMs) : null;

    return {
      id: rn.key,
      position: pos,
      data: {
        label: (
          <div style={{ textAlign: "center", color: style.text }}>
            <div style={{ fontSize: "11px", fontWeight: 600, lineHeight: 1.3 }}>
              {rn.label}
            </div>
            {duration && (
              <div style={{ fontSize: "10px", marginTop: "2px", opacity: 0.8 }}>
                {duration}
              </div>
            )}
          </div>
        ),
      },
      style: {
        background: style.bg,
        border: `1.5px solid ${style.border}`,
        borderRadius: "8px",
        padding: "8px 10px",
        minWidth: 120,
        animation: rn.state === "running" ? "pulse 2s cubic-bezier(0.4,0,0.6,1) infinite" : undefined,
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    };
  });
}

export function AgentGraph({ nodes }: { nodes: RunNode[] }) {
  const rfNodes = useMemo(() => buildNodes(nodes), [nodes]);
  const rfEdges = useMemo(
    () =>
      STATIC_EDGES.filter(
        (e) =>
          rfNodes.some((n) => n.id === e.source) &&
          rfNodes.some((n) => n.id === e.target),
      ),
    [rfNodes],
  );

  return (
    <div className="h-[460px] w-full rounded-lg border border-border overflow-hidden">
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        .react-flow__edge-path { stroke: var(--border); stroke-width: 1.5; }
        .react-flow__edge.selected .react-flow__edge-path { stroke: var(--low); }
        .react-flow__background { background: var(--background) !important; }
        .react-flow__controls { background: var(--card); border-color: var(--border); }
        .react-flow__controls-button { background: var(--card); border-color: var(--border); fill: var(--foreground); }
        .react-flow__controls-button:hover { background: var(--muted); }
      `}</style>
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag
        zoomOnScroll
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="var(--border)"
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
