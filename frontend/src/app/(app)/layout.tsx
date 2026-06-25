import { Brand } from "@/components/app/brand";
import { SidebarNav } from "@/components/app/sidebar-nav";
import { Topbar } from "@/components/app/topbar";
import { getCurrentUser, listRepos } from "@/lib/api/client";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const [repos, user] = await Promise.all([listRepos(), getCurrentUser()]);

  return (
    <div className="flex min-h-svh">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
        <div className="flex h-16 items-center border-b border-sidebar-border px-5">
          <Brand />
        </div>
        <div className="flex-1 overflow-y-auto py-4">
          <SidebarNav />
        </div>
        <div className="border-t border-sidebar-border p-4 text-xs text-muted-foreground">
          <div className="font-medium text-sidebar-foreground">Single-tenant</div>
          {repos.length} repositories connected
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar repos={repos} user={user} />
        <main className="flex-1 overflow-x-hidden px-4 py-6 md:px-8">
          <div className="mx-auto w-full max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
