import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { auth } from "@/lib/auth";
import { fleetClient } from "@/lib/fleet-client";
import { can } from "@/lib/permissions";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default async function Home() {
  const t = await getTranslations("home");
  const session = await auth();

  if (!session) {
    const tAuth = await getTranslations("auth");
    return <p className="text-sm text-[var(--muted-foreground)]">{tAuth("signInPrompt")}</p>;
  }

  const roles = session.roles;
  let pendingApprovals = 0;
  if (can(roles, "approve")) {
    const client = await fleetClient();
    const { data } = await client.GET("/v1/approvals", { params: { query: { status: "pending" } } });
    pendingApprovals = data?.length ?? 0;
  }

  const cards = [
    { href: "/chat", title: t("cardChatTitle"), desc: t("cardChatDesc") },
    { href: "/automations", title: t("cardAutomationsTitle"), desc: t("cardAutomationsDesc") },
    { href: "/examples", title: t("cardExamplesTitle"), desc: t("cardExamplesDesc") },
  ];

  if (can(roles, "approve")) {
    cards.push({
      href: "/approvals",
      title: t("cardApprovalsTitle"),
      desc:
        pendingApprovals > 0
          ? t("cardApprovalsDesc", { count: pendingApprovals })
          : t("cardApprovalsDescEmpty"),
    });
  }

  if (can(roles, "manage_agents") || can(roles, "manage_platform")) {
    cards.push({ href: "/admin", title: t("cardAdminTitle"), desc: t("cardAdminDesc") });
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">
          {t("greeting", { name: session.user?.name ?? "none" })}
        </h1>
        <p className="text-sm text-[var(--muted-foreground)]">{t("subtitle")}</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <Link key={c.href} href={c.href} className="block transition-opacity hover:opacity-90">
            <Card>
              <CardHeader>
                <CardTitle>{c.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-[var(--muted-foreground)]">{c.desc}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
