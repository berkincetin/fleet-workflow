import { getTranslations } from "next-intl/server";
import Link from "next/link";
import { auth } from "@/lib/auth";
import { can } from "@/lib/permissions";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const t = await getTranslations("admin");
  const session = await auth();
  const roles = session?.roles;

  if (!can(roles, "manage_agents") && !can(roles, "manage_platform")) {
    return <p className="text-sm text-[var(--muted-foreground)]">{t("noAccess")}</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">{t("title")}</h1>
      <nav className="flex gap-4 border-b border-[var(--border)] text-sm">
        <Link href="/admin/agents" className="px-1 pb-2 text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
          {t("agents")}
        </Link>
        {can(roles, "manage_platform") && (
          <>
            <Link href="/admin/models" className="px-1 pb-2 text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
              {t("models")}
            </Link>
            <Link href="/admin/api-keys" className="px-1 pb-2 text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
              {t("apiKeys")}
            </Link>
            <Link href="/admin/users" className="px-1 pb-2 text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
              {t("users")}
            </Link>
            <Link href="/admin/budgets" className="px-1 pb-2 text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
              {t("budgets")}
            </Link>
            <Link href="/admin/cost" className="px-1 pb-2 text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
              {t("cost")}
            </Link>
            <Link href="/admin/audit" className="px-1 pb-2 text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
              {t("audit")}
            </Link>
          </>
        )}
      </nav>
      {children}
    </div>
  );
}
