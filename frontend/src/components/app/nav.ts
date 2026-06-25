import {
  LayoutDashboard,
  GitPullRequest,
  Database,
  DollarSign,
  History,
  Settings,
  Workflow,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Pull Requests", href: "/pulls", icon: GitPullRequest },
  { label: "Agent", href: "/agent", icon: Workflow },
  { label: "Knowledge Base", href: "/knowledge", icon: Database },
  { label: "Cost Analytics", href: "/costs", icon: DollarSign },
  { label: "History", href: "/history", icon: History },
  { label: "Settings", href: "/settings", icon: Settings },
];
