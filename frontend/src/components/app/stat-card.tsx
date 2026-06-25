import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  hint,
  trend,
  accent = "text-blue-400",
}: {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  hint?: string;
  trend?: { value: string; positive?: boolean };
  accent?: string;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-semibold tracking-tight">{value}</p>
          </div>
          {Icon ? (
            <span className={cn("grid size-9 place-items-center rounded-lg bg-muted", accent)}>
              <Icon className="size-4.5" />
            </span>
          ) : null}
        </div>
        {hint || trend ? (
          <div className="mt-3 flex items-center gap-2 text-xs">
            {trend ? (
              <span className={trend.positive ? "text-success" : "text-critical"}>{trend.value}</span>
            ) : null}
            {hint ? <span className="text-muted-foreground">{hint}</span> : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
