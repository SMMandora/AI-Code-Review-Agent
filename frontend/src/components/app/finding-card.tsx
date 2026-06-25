import type { Finding } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { SeverityBadge } from "@/components/app/badges";
import { severityClasses } from "@/lib/format";
import { cn } from "@/lib/utils";

export function FindingCard({ finding }: { finding: Finding }) {
  const cls = severityClasses[finding.severity];
  return (
    <Card
      className={cn(
        "border-l-4 pl-0",
        cls.border,
      )}
    >
      <CardContent className="space-y-2 pt-4">
        <div className="flex flex-wrap items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground capitalize">
            {finding.category.replace("_", " ")}
          </span>
          <code className="ml-auto font-mono text-xs text-muted-foreground">
            {finding.path}:{finding.line}
          </code>
        </div>
        <p className="text-sm leading-snug">{finding.message}</p>
        {finding.suggestion ? (
          <pre className="overflow-x-auto rounded bg-muted p-3 text-xs font-mono leading-relaxed whitespace-pre-wrap">
            {finding.suggestion}
          </pre>
        ) : null}
      </CardContent>
    </Card>
  );
}
