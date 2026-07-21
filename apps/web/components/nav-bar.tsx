"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useSession, signIn, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { LocaleSwitcher } from "@/components/locale-switcher";

export function NavBar() {
  const t = useTranslations("nav");
  const tAuth = useTranslations("auth");
  const { data: session, status } = useSession();

  return (
    <header className="border-b border-[var(--border)]">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <nav className="flex items-center gap-4">
          <Link href="/" className="text-sm font-semibold">
            Fleet
          </Link>
          <Link href="/knowledge" className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
            {t("knowledge")}
          </Link>
        </nav>
        <div className="flex items-center gap-3">
          <LocaleSwitcher />
          {status === "authenticated" ? (
            <div className="flex items-center gap-2">
              <span className="text-sm text-[var(--muted-foreground)]">
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
      </div>
    </header>
  );
}
