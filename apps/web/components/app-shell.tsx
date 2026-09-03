"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { useSession, signIn, signOut } from "next-auth/react";
import { ChevronRight, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { breadcrumbFor, NAV_GROUPS, type NavItem } from "@/lib/nav";
import { can, type Permission } from "@/lib/permissions";
import type { Theme } from "@/lib/theme";
import { cn } from "@/lib/utils";

/** Highest-privilege role the user holds — what the top-bar chip shows. */
const ROLE_RANK = ["member", "approver", "builder", "dept_admin", "platform_admin"];

function primaryRole(roles: string[] | undefined): string | undefined {
  const known = (roles ?? []).filter((r) => ROLE_RANK.includes(r));
  if (known.length === 0) return roles?.[0];
  return known.sort((a, b) => ROLE_RANK.indexOf(b) - ROLE_RANK.indexOf(a))[0];
}

function visible(item: NavItem, roles: string[] | undefined): boolean {
  const required: Permission[] = item.permissions ?? [];
  return required.length === 0 || required.some((p) => can(roles, p));
}

function NavLink({ item, label }: { item: NavItem; label: string }) {
  const pathname = usePathname();
  // `/automations/new` must not light up `/automations` as well, so a nested
  // route only activates the deepest nav entry that matches it.
  const deepest = NAV_GROUPS.flatMap((g) => g.items)
    .filter((i) => pathname === i.href || pathname.startsWith(`${i.href}/`))
    .sort((a, b) => b.href.length - a.href.length)[0];
  const active = deepest?.href === item.href;
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex items-center gap-2.5 rounded-[var(--radius-md)] px-3 py-2 text-sm transition-colors",
        active
          ? "bg-[var(--accent-soft)] font-medium text-[var(--accent-foreground)]"
          : "text-[var(--muted-foreground)] hover:bg-[var(--surface-2)] hover:text-[var(--foreground)]",
      )}
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
      <span className="truncate">{label}</span>
    </Link>
  );
}

function Breadcrumb() {
  const pathname = usePathname();
  const tNav = useTranslations("nav");
  const tAdmin = useTranslations("admin");
  const crumbs = breadcrumbFor(pathname);
  const label = (c: { namespace: "nav" | "admin"; key: string }) =>
    c.namespace === "admin" ? tAdmin(c.key) : tNav(c.key);

  return (
    <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1.5">
      {crumbs.map((crumb, i) => {
        const last = i === crumbs.length - 1;
        return (
          <span key={crumb.href} className="flex min-w-0 items-center gap-1.5">
            {i > 0 && (
              <ChevronRight
                className="h-3.5 w-3.5 shrink-0 text-[var(--muted-foreground)]"
                aria-hidden="true"
              />
            )}
            {last ? (
              <h1 className="truncate text-sm font-semibold text-[var(--foreground)]">
                {label(crumb)}
              </h1>
            ) : (
              <Link
                href={crumb.href}
                className="truncate text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                {label(crumb)}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}

export function AppShell({ children, theme }: { children: React.ReactNode; theme: Theme }) {
  const t = useTranslations("nav");
  const tGroups = useTranslations("nav.groups");
  const tAuth = useTranslations("auth");
  const tRoles = useTranslations("admin.roleNames");
  const { data: session, status } = useSession();
  const roles = session?.roles;
  const role = primaryRole(roles);

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col gap-6 border-r border-[var(--border)] bg-[var(--sidebar)] px-3 py-4 md:flex">
        <Link
          href="/"
          className="flex items-center gap-2 px-3 text-base font-semibold tracking-tight"
        >
          <span
            aria-hidden="true"
            className="h-5 w-1.5 rounded-full bg-[var(--primary)]"
          />
          Fleet
        </Link>

        <nav className="flex flex-1 flex-col gap-5 overflow-y-auto">
          {NAV_GROUPS.map((group) => {
            const items = group.items.filter((i) => visible(i, roles));
            if (items.length === 0) return null;
            return (
              <div key={group.key} className="flex flex-col gap-1">
                <p className="px-3 pb-1 text-[0.6875rem] font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
                  {tGroups(group.key)}
                </p>
                {items.map((item) => (
                  <NavLink key={item.href} item={item} label={t(item.key)} />
                ))}
              </div>
            );
          })}
        </nav>

        <div className="flex flex-col gap-3 border-t border-[var(--border)] px-3 pt-3">
          <div className="flex items-center gap-2">
            <LocaleSwitcher />
            <ThemeSwitcher value={theme} />
          </div>
          {status === "authenticated" ? (
            <Button variant="outline" size="sm" onClick={() => signOut()}>
              <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
              {tAuth("signOut")}
            </Button>
          ) : (
            <Button size="sm" onClick={() => signIn("keycloak")}>
              {tAuth("signIn")}
            </Button>
          )}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--surface)] px-4 md:px-6">
          <Breadcrumb />
          {status === "authenticated" && (
            <div className="flex shrink-0 items-center gap-2">
              <span className="hidden text-sm text-[var(--muted-foreground)] sm:inline">
                {session.user?.name ?? session.user?.email}
              </span>
              {role && (
                <span className="rounded-full bg-[var(--surface-2)] px-2.5 py-0.5 text-xs font-medium text-[var(--muted-foreground)]">
                  {tRoles.has(role) ? tRoles(role) : role}
                </span>
              )}
            </div>
          )}
        </header>

        {/* Mobile nav: the sidebar is hidden under md, so the groups collapse
            into one horizontally scrolling strip rather than disappearing. */}
        <nav className="flex gap-1 overflow-x-auto border-b border-[var(--border)] bg-[var(--sidebar)] px-3 py-2 md:hidden">
          {NAV_GROUPS.flatMap((g) => g.items)
            .filter((i) => visible(i, roles))
            .map((item) => (
              <NavLink key={item.href} item={item} label={t(item.key)} />
            ))}
        </nav>

        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-6 md:py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
