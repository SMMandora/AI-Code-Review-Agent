import Link from "next/link";
import { listPullRequests } from "@/lib/api/client";
import { PageHeader } from "@/components/app/page-header";
import { StatusBadge } from "@/components/app/badges";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDateTime } from "@/lib/format";

export default async function PullsPage() {
  const pulls = await listPullRequests();

  return (
    <>
      <PageHeader
        title="Pull Requests"
        description="Open and recently reviewed pull requests across your repositories."
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{pulls.length} pull requests</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>PR</TableHead>
                <TableHead className="hidden sm:table-cell">Author</TableHead>
                <TableHead className="hidden md:table-cell">Branch</TableHead>
                <TableHead className="hidden lg:table-cell">Changes</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="hidden sm:table-cell text-right">Updated</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pulls.map((pr) => (
                <TableRow key={pr.number}>
                  <TableCell>
                    <Link
                      href={`/pulls/${pr.number}`}
                      className="font-medium hover:underline"
                    >
                      #{pr.number}
                    </Link>
                    <div className="max-w-[22rem] truncate text-xs text-muted-foreground">
                      {pr.title}
                    </div>
                  </TableCell>
                  <TableCell className="hidden text-sm text-muted-foreground sm:table-cell">
                    {pr.author}
                  </TableCell>
                  <TableCell className="hidden md:table-cell">
                    <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                      {pr.branch}
                    </code>
                  </TableCell>
                  <TableCell className="hidden lg:table-cell">
                    <span className="tabular-nums text-xs">
                      <span className="text-success">+{pr.additions}</span>
                      {" / "}
                      <span className="text-critical">-{pr.deletions}</span>
                      <span className="ml-1.5 text-muted-foreground">
                        ({pr.changedFiles} file{pr.changedFiles !== 1 ? "s" : ""})
                      </span>
                    </span>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={pr.status} />
                  </TableCell>
                  <TableCell className="hidden text-right text-xs text-muted-foreground sm:table-cell">
                    {formatDateTime(pr.updatedAt)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </>
  );
}
