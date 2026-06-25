import type { DiffFile } from "@/lib/types";
import { cn } from "@/lib/utils";

function lineClass(kind: "add" | "del" | "context" | "hunk"): string {
  if (kind === "add") return "bg-success/10";
  if (kind === "del") return "bg-critical/10";
  if (kind === "hunk") return "bg-muted text-muted-foreground";
  return "";
}

function linePrefix(kind: "add" | "del" | "context" | "hunk"): string {
  if (kind === "add") return "+";
  if (kind === "del") return "-";
  if (kind === "hunk") return " ";
  return " ";
}

export function DiffViewer({ files }: { files: DiffFile[] }) {
  if (files.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No diff available.</p>
    );
  }

  return (
    <div className="space-y-4">
      {files.map((file) => (
        <div key={file.path} className="overflow-hidden rounded-xl border border-border">
          {/* File header */}
          <div className="flex items-center justify-between border-b border-border bg-muted px-4 py-2 font-mono text-xs">
            <span className="font-medium text-foreground">{file.path}</span>
            <span className="flex gap-3 text-muted-foreground">
              <span className="text-success">+{file.additions}</span>
              <span className="text-critical">-{file.deletions}</span>
            </span>
          </div>

          {/* Line table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono">
              <tbody>
                {file.lines.map((line, i) => (
                  <tr key={i} className={cn("leading-5", lineClass(line.kind))}>
                    {/* Old line number */}
                    <td className="w-10 select-none px-2 text-right tabular-nums text-muted-foreground/60 align-top">
                      {line.kind !== "add" && line.kind !== "hunk" && line.oldNo != null
                        ? line.oldNo
                        : ""}
                    </td>
                    {/* New line number */}
                    <td className="w-10 select-none border-r border-border px-2 text-right tabular-nums text-muted-foreground/60 align-top">
                      {line.kind !== "del" && line.kind !== "hunk" && line.newNo != null
                        ? line.newNo
                        : ""}
                    </td>
                    {/* Prefix */}
                    <td className="w-5 select-none px-1 text-center align-top text-muted-foreground">
                      {linePrefix(line.kind)}
                    </td>
                    {/* Content */}
                    <td className="whitespace-pre px-2 align-top">{line.text}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
