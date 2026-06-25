import type { RunNode } from "@/lib/types";
import { CHECK_STATE_META, formatDuration } from "@/lib/format";
import { CheckStateIcon } from "@/components/app/badges";

export function RunStatusChecklist({ nodes }: { nodes: RunNode[] }) {
  const total = nodes.length;
  const passed = nodes.filter((n) => n.state === "passed").length;
  const pct = total > 0 ? Math.round((passed / total) * 100) : 0;

  // SVG ring constants
  const size = 80;
  const cx = size / 2;
  const cy = size / 2;
  const r = 30;
  const circumference = 2 * Math.PI * r;
  const dashOffset = circumference - (pct / 100) * circumference;

  return (
    <div className="space-y-4">
      {/* Circular progress ring */}
      <div className="flex items-center gap-4">
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="shrink-0"
          aria-label={`${pct}% passed`}
        >
          {/* Track */}
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke="var(--muted)"
            strokeWidth={6}
          />
          {/* Progress arc */}
          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke={passed === total && total > 0 ? "var(--success)" : "var(--low)"}
            strokeWidth={6}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            transform={`rotate(-90 ${cx} ${cy})`}
          />
          {/* Center text */}
          <text
            x={cx}
            y={cy}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="14"
            fontWeight="600"
            fill="currentColor"
          >
            {pct}%
          </text>
        </svg>
        <div className="text-sm text-muted-foreground">
          <span className="text-base font-semibold text-foreground">{passed}</span>
          {" / "}
          {total} checks passed
        </div>
      </div>

      {/* Node list */}
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
    </div>
  );
}
