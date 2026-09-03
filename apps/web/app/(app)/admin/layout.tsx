import { getTranslations } from "next-intl/server";
import { auth } from "@/lib/auth";
import { can } from "@/lib/permissions";
import { AdminTabs, type AdminTab } from "@/components/admin/admin-tabs";
import { PageHeader } from "@/components/layout/page-header";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const t = await getTranslations("admin");
  const session = await auth();
  const roles = session?.roles;

  if (!can(roles, "manage_agents") && !can(roles, "manage_platform")) {
    return <p className="text-sm text-[var(--muted-foreground)]">{t("noAccess")}</p>;
  }

  const tabs: AdminTab[] = [{ href: "/admin/agents", label: t("agents") }];
  if (can(roles, "manage_platform")) {
    tabs.push(
      { href: "/admin/models", label: t("models") },
      { href: "/admin/api-keys", label: t("apiKeys") },
      { href: "/admin/users", label: t("users") },
      { href: "/admin/budgets", label: t("budgets") },
      { href: "/admin/cost", label: t("cost") },
      { href: "/admin/audit", label: t("audit") },
      { href: "/admin/services", label: t("services") },
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("title")}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />
      <AdminTabs tabs={tabs} />
      {children}
    </div>
  );
}
