import Link from "next/link";
import {
  ArrowRight,
  Bug,
  Check,
  DollarSign,
  Gauge,
  GitBranch,
  ListChecks,
  ShieldAlert,
  Sparkles,
  Workflow,
} from "lucide-react";
import { Brand } from "@/components/app/brand";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const FEATURES = [
  { icon: Bug, title: "Correctness Review", body: "Logic errors, off-by-ones, unhandled nulls, missing awaits, and race conditions — caught before merge." },
  { icon: ShieldAlert, title: "Security Review", body: "Injection, hardcoded secrets, unsafe deserialization, and missing validation at trust boundaries." },
  { icon: Sparkles, title: "Style Review", body: "Your repo's own conventions, enforced via RAG over the codebase — not generic linting." },
  { icon: ListChecks, title: "Test Coverage", body: "Flags new or changed behavior that ships without corresponding tests or weakens assertions." },
];

const METRICS = [
  { value: "<30s", label: "p95 review time on a 200-line diff" },
  { value: "<$0.50", label: "hard cost ceiling per pull request" },
  { value: "80%+", label: "eval-gated findings-match accuracy" },
];

const TESTIMONIALS = [
  { quote: "It reviews against our actual conventions, not a generic rulebook. The RAG grounding is the difference.", name: "Jordan Lee", role: "Staff Engineer" },
  { quote: "Caught a SQL injection in a Friday PR that three humans had already approved.", name: "Priya N.", role: "Security Lead" },
  { quote: "Cost tracking per PR meant we could actually put this in front of finance.", name: "Marco D.", role: "Eng Manager" },
];

const PLANS = [
  { name: "Starter", price: "$0", blurb: "One repository, community support.", features: ["1 repository", "Webhook reviews", "Cost ceiling enforcement", "Dashboard"], cta: "Start free", highlight: false },
  { name: "Team", price: "$49", blurb: "Multi-repo, full observability.", features: ["Unlimited repositories", "RAG knowledge base", "Agent observability", "Eval gating"], cta: "Start trial", highlight: true },
  { name: "Enterprise", price: "Custom", blurb: "SSO, audit, on-prem options.", features: ["SSO & RBAC", "Self-hosted deploy", "Priority support", "Custom rules"], cta: "Contact us", highlight: false },
];

const ARCH = ["GitHub", "FastAPI", "LangGraph", "Claude", "GitHub"];

export default function LandingPage() {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-6">
          <Brand href="/" />
          <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
            <a href="#features" className="hover:text-foreground">Features</a>
            <a href="#architecture" className="hover:text-foreground">Architecture</a>
            <a href="#pricing" className="hover:text-foreground">Pricing</a>
          </nav>
          <Button size="sm" render={<Link href="/dashboard" />}>Open dashboard</Button>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border bg-grid">
        <div className="pointer-events-none absolute left-1/2 top-[-10rem] size-[36rem] -translate-x-1/2 rounded-full bg-blue-500/15 blur-[120px]" />
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center px-6 py-24 text-center">
          <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground">
            <Sparkles className="size-3.5 text-blue-400" /> Grounded in your repository, not a generic model
          </span>
          <h1 className="max-w-3xl text-balance text-4xl font-semibold tracking-tight sm:text-6xl">
            AI Code Reviews <span className="text-gradient">Grounded in Your Repository</span>
          </h1>
          <p className="mt-5 max-w-2xl text-pretty text-lg text-muted-foreground">
            Autonomous pull-request review powered by Claude with RAG over your own code and conventions.
            Inline comments, full observability, and a hard cost ceiling on every review.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button size="lg" render={<Link href="/dashboard" />}>
              <GitBranch className="size-4" /> Connect GitHub Repository
            </Button>
            <Button size="lg" variant="outline" render={<Link href="/dashboard" />}>
              View Demo <ArrowRight className="size-4" />
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto w-full max-w-6xl px-6 py-20">
        <h2 className="text-center text-3xl font-semibold tracking-tight">Four reviewers, one pass</h2>
        <p className="mx-auto mt-3 max-w-xl text-center text-muted-foreground">
          Every pull request runs through four specialized check nodes in parallel, each grounded in your codebase.
        </p>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <Card key={f.title}>
              <CardContent className="space-y-3 p-6">
                <span className="grid size-10 place-items-center rounded-lg bg-gradient-to-br from-blue-500/20 to-violet-500/20 text-blue-300">
                  <f.icon className="size-5" />
                </span>
                <h3 className="font-semibold">{f.title}</h3>
                <p className="text-sm text-muted-foreground">{f.body}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="border-y border-border bg-card/40">
        <div className="mx-auto w-full max-w-6xl px-6 py-20">
          <h2 className="text-center text-3xl font-semibold tracking-tight">Architecture</h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-muted-foreground">
            A webhook-driven LangGraph agent — fetch, embed context, four parallel checks, dedup, one review.
          </p>
          <div className="mt-12 flex flex-wrap items-center justify-center gap-3">
            {ARCH.map((node, i) => (
              <div key={`${node}-${i}`} className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-3 text-sm font-medium">
                  {node === "LangGraph" ? <Workflow className="size-4 text-violet-400" /> : null}
                  {node}
                </div>
                {i < ARCH.length - 1 ? <ArrowRight className="size-4 text-muted-foreground" /> : null}
              </div>
            ))}
          </div>
          <div className="mt-12 grid gap-4 sm:grid-cols-3">
            {METRICS.map((m) => (
              <Card key={m.label}>
                <CardContent className="p-6 text-center">
                  <div className="text-4xl font-semibold tracking-tight text-gradient">{m.value}</div>
                  <div className="mt-2 text-sm text-muted-foreground">{m.label}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="mx-auto w-full max-w-6xl px-6 py-20">
        <h2 className="text-center text-3xl font-semibold tracking-tight">Trusted on real pull requests</h2>
        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {TESTIMONIALS.map((t) => (
            <Card key={t.name}>
              <CardContent className="space-y-4 p-6">
                <p className="text-sm leading-relaxed">&ldquo;{t.quote}&rdquo;</p>
                <div className="flex items-center gap-3 pt-2">
                  <span className="grid size-9 place-items-center rounded-full bg-gradient-to-br from-blue-500 to-violet-500 text-xs font-medium text-white">
                    {t.name.split(" ").map((p) => p[0]).join("")}
                  </span>
                  <div className="text-sm">
                    <div className="font-medium">{t.name}</div>
                    <div className="text-muted-foreground">{t.role}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="border-t border-border bg-card/40">
        <div className="mx-auto w-full max-w-6xl px-6 py-20">
          <div className="flex items-center justify-center gap-2">
            <Gauge className="size-5 text-blue-400" />
            <h2 className="text-3xl font-semibold tracking-tight">Pricing</h2>
          </div>
          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {PLANS.map((p) => (
              <Card key={p.name} className={p.highlight ? "border-blue-500/50 glow" : undefined}>
                <CardContent className="space-y-5 p-6">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">{p.name}</h3>
                      {p.highlight ? (
                        <span className="rounded-full bg-blue-500/15 px-2 py-0.5 text-xs text-blue-300">Popular</span>
                      ) : null}
                    </div>
                    <div className="text-3xl font-semibold tracking-tight">
                      {p.price}
                      {p.price.startsWith("$") && p.price.length <= 4 ? (
                        <span className="text-sm font-normal text-muted-foreground"> /mo</span>
                      ) : null}
                    </div>
                    <p className="text-sm text-muted-foreground">{p.blurb}</p>
                  </div>
                  <ul className="space-y-2 text-sm">
                    {p.features.map((f) => (
                      <li key={f} className="flex items-center gap-2">
                        <Check className="size-4 text-success" /> {f}
                      </li>
                    ))}
                  </ul>
                  <Button className="w-full" variant={p.highlight ? "default" : "outline"} render={<Link href="/dashboard" />}>
                    {p.cta}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
          <p className="mt-6 text-center text-xs text-muted-foreground">
            <DollarSign className="mr-1 inline size-3" />
            Demo pricing — this deployment is single-tenant and unmetered.
          </p>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 text-sm text-muted-foreground sm:flex-row">
          <Brand href="/" />
          <p>Built on FastAPI · LangGraph · pgvector · Claude</p>
        </div>
      </footer>
    </div>
  );
}
