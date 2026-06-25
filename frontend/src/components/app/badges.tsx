import { CheckCircle2, CircleDashed, Loader2, XCircle } from "lucide-react";
import type { CheckState, ReviewStatus, Severity } from "@/lib/types";
import { cn } from "@/lib/utils";
import { SEVERITY_LABEL, STATUS_META, severityClasses } from "@/lib/format";

export function SeverityBadge({ severity }: { severity: Severity }) {
  const s = severityClasses[severity];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
        s.bg,
        s.text,
        s.border,
      )}
    >
      <span className={cn("size-1.5 rounded-full", s.dot)} />
      {SEVERITY_LABEL[severity]}
    </span>
  );
}

export function StatusBadge({ status }: { status: ReviewStatus }) {
  const meta = STATUS_META[status];
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        meta.className,
      )}
    >
      {meta.label}
    </span>
  );
}

export function CheckStateIcon({ state, className }: { state: CheckState; className?: string }) {
  const base = cn("size-4", className);
  if (state === "passed") return <CheckCircle2 className={cn(base, "text-success")} />;
  if (state === "failed") return <XCircle className={cn(base, "text-critical")} />;
  if (state === "running") return <Loader2 className={cn(base, "animate-spin text-low")} />;
  return <CircleDashed className={cn(base, "text-muted-foreground")} />;
}
