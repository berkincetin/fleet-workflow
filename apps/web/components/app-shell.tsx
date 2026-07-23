"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { useSession, signIn, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { can } from "@/lib/permissions";
import { cn } from "@/lib/utils";

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link
      href={href}
      className={cn(
        "rounded-md px-3 py-2 text-sm transition-colors",
        active
          ? "bg-[var(--muted)] text-[var(--foreground)] font-medium"
          : "text-[var(--muted-foreground)] hover:bg-[var(--muted)] hover:text-[var(--foreground)]",
      )}
    >
      {label}
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const t = useTranslations("nav");
  const tAuth = useTranslations("auth");
  const { data: session, status } = useSession();
  const roles = session?.roles;

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl gap-6 px-4 py-6">
      <aside className="flex w-56 shrink-0 flex-col gap-4">
        <Link href="/" className="px-3 text-lg font-semibold">
          Fleet
        </Link>
        <nav className="flex flex-col gap-1">
          <NavLink href="/" label={t("home")} />
          <NavLink href="/chat" label={t("chat")} />
          <NavLink href="/scenarios" label={t("scenarios")} />
          <NavLink href="/automations" label={t("automations")} />
          <NavLink href="/examples" label={t("examples")} />
          <NavLink href="/knowledge" label={t("knowledge")} />
          <NavLink href="/approvals" label={t("approvals")} />
          {(can(roles, "manage_agents") || can(roles, "manage_platform")) && (
            <NavLink href="/admin" label={t("admin")} />
          )}
        </nav>
        <div className="mt-auto flex flex-col gap-3 px-3">
          <LocaleSwitcher />
          {status === "authenticated" ? (
            <div className="flex flex-col gap-2">
              <span className="text-xs text-[var(--muted-foreground)]">
                {session.user?.name ?? session.user?.email}
              </span>
              <Button variant="outline" size="sm" onClick={() => signOut()}>
                {tAuth("signOut")}
              </Button>
            </div>
          ) : (
            <Button size="sm" onClick={() => signIn("keycloak")}>
              {tAuth("signIn")}
            </Button>
          )}
        </div>
      </aside>
      <main className="min-w-0 flex-1 py-2">{children}</main>
    </div>
  );
}
