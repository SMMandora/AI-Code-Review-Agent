import { ShieldCheck } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export function Brand({ href = "/dashboard", className }: { href?: string; className?: string }) {
  return (
    <Link href={href} className={cn("flex items-center gap-2 font-semibold", className)}>
      <span className="grid size-8 place-items-center rounded-lg bg-gradient-to-br from-blue-500 to-violet-500 text-white shadow-lg">
        <ShieldCheck className="size-5" />
      </span>
      <span className="text-[15px] tracking-tight">
        CodeGuardian<span className="text-muted-foreground">.AI</span>
      </span>
    </Link>
  );
}
