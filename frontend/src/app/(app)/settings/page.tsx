"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import type { RepoConfig } from "@/lib/types";
import { MODELS } from "@/lib/types";
import { getRepoConfig, saveRepoConfig } from "@/lib/api/client";
import { PageHeader } from "@/components/app/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

const THRESHOLD_OPTIONS = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
] as const;

type ThresholdValue = "low" | "medium" | "high";

function buildYaml(
  skipFiles: string,
  customRules: string,
  model: string,
  severityThreshold: string,
): string {
  const skipLines = skipFiles
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  const ruleLines = customRules
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const skipSection =
    skipLines.length > 0
      ? skipLines.map((l) => `  - "${l}"`).join("\n")
      : '  # no patterns';

  const rulesSection =
    ruleLines.length > 0
      ? ruleLines.map((l) => `  - "${l}"`).join("\n")
      : '  # no custom rules';

  return [
    "# .codereview.yml",
    `model: ${model}`,
    `severity_threshold: ${severityThreshold}`,
    "skip_files:",
    skipSection,
    "custom_rules:",
    rulesSection,
  ].join("\n");
}

function ReviewConfigTab() {
  const [skipFiles, setSkipFiles] = useState("");
  const [customRules, setCustomRules] = useState("");
  const [model, setModel] = useState<string>(MODELS[0]);
  const [severityThreshold, setSeverityThreshold] = useState<ThresholdValue>("low");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    getRepoConfig().then((cfg: RepoConfig) => {
      setSkipFiles(cfg.skipFiles.join("\n"));
      setCustomRules(cfg.customRules.join("\n"));
      setModel(cfg.model);
      // Only use low/medium/high as threshold; critical falls back to high
      const t = cfg.severityThreshold;
      setSeverityThreshold(t === "critical" ? "high" : (t as ThresholdValue));
      setLoaded(true);
    });
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      const cfg: RepoConfig = {
        skipFiles: skipFiles.split("\n").map((l) => l.trim()).filter(Boolean),
        customRules: customRules.split("\n").map((l) => l.trim()).filter(Boolean),
        model,
        severityThreshold,
      };
      await saveRepoConfig(cfg);
      toast.success("Configuration saved");
    } finally {
      setSaving(false);
    }
  }

  const yaml = buildYaml(skipFiles, customRules, model, severityThreshold);

  if (!loaded) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground text-sm gap-2">
        <Loader2 className="size-4 animate-spin" />
        Loading configuration…
      </div>
    );
  }

  return (
    <div className="mt-4 grid gap-6 lg:grid-cols-2">
      {/* Form side */}
      <div className="space-y-5">
        {/* Model */}
        <div className="space-y-1.5">
          <Label htmlFor="model-select">Model</Label>
          <Select
            value={model}
            onValueChange={(v) => { if (v) setModel(v); }}
          >
            <SelectTrigger id="model-select" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MODELS.map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Severity threshold */}
        <div className="space-y-1.5">
          <Label htmlFor="threshold-select">Severity threshold</Label>
          <Select
            value={severityThreshold}
            onValueChange={(v) => { if (v) setSeverityThreshold(v as ThresholdValue); }}
          >
            <SelectTrigger id="threshold-select" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {THRESHOLD_OPTIONS.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Only findings at or above this severity are posted as PR comments.
          </p>
        </div>

        {/* Skip files */}
        <div className="space-y-1.5">
          <Label htmlFor="skip-files">Skip files</Label>
          <Textarea
            id="skip-files"
            placeholder={"**/migrations/**\n*.lock\ndist/**"}
            value={skipFiles}
            onChange={(e) => setSkipFiles(e.target.value)}
            className="font-mono text-xs min-h-[96px]"
          />
          <p className="text-xs text-muted-foreground">One glob pattern per line.</p>
        </div>

        {/* Custom rules */}
        <div className="space-y-1.5">
          <Label htmlFor="custom-rules">Custom rules</Label>
          <Textarea
            id="custom-rules"
            placeholder="No print statements in library code; use the logger."
            value={customRules}
            onChange={(e) => setCustomRules(e.target.value)}
            className="text-xs min-h-[96px]"
          />
          <p className="text-xs text-muted-foreground">One rule per line.</p>
        </div>

        <Button onClick={handleSave} disabled={saving} className="w-full sm:w-auto">
          {saving ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Saving…
            </>
          ) : (
            "Save changes"
          )}
        </Button>
      </div>

      {/* YAML preview */}
      <div className="space-y-1.5">
        <p className="text-sm font-medium">YAML preview</p>
        <pre className="rounded-xl bg-muted px-4 py-4 text-xs font-mono leading-relaxed overflow-x-auto whitespace-pre text-foreground/80 ring-1 ring-foreground/10 min-h-[280px]">
          {yaml}
        </pre>
      </div>
    </div>
  );
}

function WebhookTab() {
  const eventBadge = (label: string) => (
    <span
      key={label}
      className="inline-flex items-center rounded-full border border-border bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground"
    >
      {label}
    </span>
  );

  return (
    <div className="mt-4 max-w-xl space-y-4">
      <Card>
        <CardContent className="pt-4 space-y-4">
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Payload URL
            </p>
            <code className="block rounded-lg bg-muted px-3 py-2 font-mono text-sm text-foreground/90 break-all">
              https://&lt;your-host&gt;/webhooks/github
            </code>
          </div>

          <Separator />

          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Content type
            </p>
            <code className="font-mono text-sm">application/json</code>
          </div>

          <Separator />

          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Secret
            </p>
            <div className="flex items-center gap-3">
              <code className="font-mono text-sm tracking-widest">••••••••</code>
              <span className="text-xs text-muted-foreground">
                Set via <code className="font-mono">GITHUB_WEBHOOK_SECRET</code> env var.
              </span>
            </div>
          </div>

          <Separator />

          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Events
            </p>
            <div className="flex flex-wrap gap-2">
              {eventBadge("Pull requests")}
              {eventBadge("Issue comments")}
              {eventBadge("Pushes")}
            </div>
          </div>
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        Add this webhook to your GitHub repository settings under{" "}
        <strong>Settings → Webhooks → Add webhook</strong>.
      </p>
    </div>
  );
}

function SecretsTab() {
  const rows: { label: string; masked: string; envVar: string }[] = [
    { label: "GitHub Token", masked: "ghp_••••••••••••••••••••", envVar: "GITHUB_TOKEN" },
    { label: "Anthropic API Key", masked: "sk-ant-••••••••••••••••••••", envVar: "ANTHROPIC_API_KEY" },
    { label: "Voyage API Key", masked: "pa-••••••••••••••••••••", envVar: "VOYAGE_API_KEY" },
  ];

  return (
    <div className="mt-4 max-w-xl space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Environment secrets</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {rows.map((row, i) => (
            <div key={row.envVar}>
              {i > 0 && <Separator className="mb-4" />}
              <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">{row.label}</p>
                  <code className="font-mono text-xs text-muted-foreground">{row.envVar}</code>
                </div>
                <code className="font-mono text-sm tracking-widest text-muted-foreground">
                  {row.masked}
                </code>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        Secrets are injected at runtime via environment variables and are never stored in the UI
        or database. Set them in your <code className="font-mono">.env</code> file or deployment
        secrets manager.
      </p>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        title="Settings"
        description="Repository review configuration"
      />

      <Tabs defaultValue="review-config">
        <TabsList>
          <TabsTrigger value="review-config">Review config</TabsTrigger>
          <TabsTrigger value="webhook">Webhook</TabsTrigger>
          <TabsTrigger value="secrets">Secrets</TabsTrigger>
        </TabsList>

        <TabsContent value="review-config">
          <ReviewConfigTab />
        </TabsContent>

        <TabsContent value="webhook">
          <WebhookTab />
        </TabsContent>

        <TabsContent value="secrets">
          <SecretsTab />
        </TabsContent>
      </Tabs>
    </>
  );
}
