/**
 * Sidebar structure + route titles (task 13.1).
 *
 * One source for three consumers: the grouped sidebar, the top bar's page
 * title, and the breadcrumb. Adding a screen means adding one entry here, not
 * touching three components.
 *
 * `permission` gates visibility only — hiding a link is a courtesy, the API's
 * `require_permission` is the real boundary (see lib/permissions.ts).
 */

import {
  BookOpen,
  CheckSquare,
  Compass,
  FileText,
  Home,
  LayoutGrid,
  MessageSquare,
  Plus,
  Settings,
  Workflow,
} from "lucide-react";
import type { Permission } from "@/lib/permissions";

export type NavIcon = typeof Home;

/**
 * The four colour families in globals.css. A group's key *is* its section, and
 * `sectionFor()` below maps any route back to one, so the accent a screen
 * paints and the sidebar group it lives under can never disagree.
 */
export type Section = "work" | "automation" | "knowledge" | "admin";

export interface NavItem {
  href: string;
  /** Key under the `nav` i18n namespace. */
  key: string;
  icon: NavIcon;
  /** Visible only if the user holds at least one of these (empty = everyone). */
  permissions?: Permission[];
}

export interface NavGroup {
  /** Key under the `nav.groups` i18n namespace — also the section accent. */
  key: Section;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    key: "work",
    items: [
      { href: "/", key: "home", icon: Home },
      { href: "/guide", key: "guide", icon: Compass },
      { href: "/chat", key: "chat", icon: MessageSquare },
      { href: "/scenarios", key: "scenarios", icon: LayoutGrid },
      { href: "/approvals", key: "approvals", icon: CheckSquare, permissions: ["approve"] },
    ],
  },
  {
    key: "automation",
    items: [
      { href: "/automations", key: "automations", icon: Workflow },
      {
        href: "/automations/new",
        key: "newAutomation",
        icon: Plus,
        permissions: ["manage_agents"],
      },
    ],
  },
  {
    key: "knowledge",
    items: [
      { href: "/knowledge", key: "knowledge", icon: BookOpen },
      { href: "/examples", key: "examples", icon: FileText },
    ],
  },
  {
    key: "admin",
    items: [
      {
        href: "/admin",
        key: "admin",
        icon: Settings,
        permissions: ["manage_agents", "manage_platform"],
      },
    ],
  },
];

/** Longest-prefix route -> `nav`/`admin` title key, for the top bar. */
const ROUTE_TITLES: { prefix: string; namespace: "nav" | "admin"; key: string }[] = [
  { prefix: "/admin/agents", namespace: "admin", key: "agents" },
  { prefix: "/admin/models", namespace: "admin", key: "models" },
  { prefix: "/admin/api-keys", namespace: "admin", key: "apiKeys" },
  { prefix: "/admin/users", namespace: "admin", key: "users" },
  { prefix: "/admin/budgets", namespace: "admin", key: "budgets" },
  { prefix: "/admin/cost", namespace: "admin", key: "cost" },
  { prefix: "/admin/audit", namespace: "admin", key: "audit" },
  { prefix: "/admin/services", namespace: "admin", key: "services" },
  { prefix: "/admin", namespace: "nav", key: "admin" },
  { prefix: "/automations/new", namespace: "nav", key: "newAutomation" },
  { prefix: "/automations", namespace: "nav", key: "automations" },
  { prefix: "/chat", namespace: "nav", key: "chat" },
  { prefix: "/guide", namespace: "nav", key: "guide" },
  { prefix: "/scenarios", namespace: "nav", key: "scenarios" },
  { prefix: "/examples", namespace: "nav", key: "examples" },
  { prefix: "/knowledge", namespace: "nav", key: "knowledge" },
  { prefix: "/approvals", namespace: "nav", key: "approvals" },
  { prefix: "/", namespace: "nav", key: "home" },
];

export interface Crumb {
  namespace: "nav" | "admin";
  key: string;
  href: string;
}

/**
 * Breadcrumb for a pathname: the section it lives in, then the page itself.
 * `/admin/models` -> [Admin, Models]; `/chat` -> [Chat] (a top-level page is
 * its own only crumb, rather than repeating itself twice).
 */
export function breadcrumbFor(pathname: string): Crumb[] {
  const match = ROUTE_TITLES.find(
    (r) => pathname === r.prefix || pathname.startsWith(`${r.prefix}/`) || r.prefix === "/",
  );
  if (!match) return [];

  const crumbs: Crumb[] = [];
  const parent = ROUTE_TITLES.find(
    (r) =>
      r.prefix !== match.prefix &&
      r.prefix !== "/" &&
      match.prefix.startsWith(`${r.prefix}/`),
  );
  if (parent) crumbs.push({ namespace: parent.namespace, key: parent.key, href: parent.prefix });
  crumbs.push({ namespace: match.namespace, key: match.key, href: match.prefix });
  return crumbs;
}

/**
 * The section accent a route paints, derived from the sidebar group that owns
 * it (longest matching href wins, so `/automations/new` and `/automations`
 * both resolve to Automation). Routes with no nav entry of their own — the
 * admin sub-pages, `/automations/:id/edit` — fall through to their prefix.
 *
 * Deriving this rather than hard-coding a second table is the point: a screen
 * cannot end up amber in the sidebar and teal in its own header.
 */
export function sectionFor(pathname: string): Section {
  let best: { section: Section; len: number } | undefined;
  for (const group of NAV_GROUPS) {
    for (const item of group.items) {
      const hit = pathname === item.href || pathname.startsWith(`${item.href}/`);
      if (hit && (!best || item.href.length > best.len)) {
        best = { section: group.key, len: item.href.length };
      }
    }
  }
  return best?.section ?? "work";
}
