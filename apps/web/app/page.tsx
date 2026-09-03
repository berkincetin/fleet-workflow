import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Bot, CheckSquare, CircleDollarSign, MessageSquare, Workflow } from "lucide-react";
import { auth } from "@/lib/auth";
import { fleetClient } from "@/lib/fleet-client";
import { can } from "@/lib/permissions";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/layout/empty-state";
import { PageHeader } from "@/components/layout/page-header";
import { StatTile } from "@/components/home/stat-tile";

/**
 * Role-aware Home dashboard (task 13.1).
 *
 * Replaces the flat "here are some links" card grid: what a user sees is the
 * state of the work they are actually allowed to touch — pending approvals for
 * an approver, spend for a platform admin, automation runs and live agents for
 * everyone. Every query is gated by the same permission the underlying screen
 * needs, so a `member` never triggers a request that would 403.
 */
export default async function Home() {
  const t = await getTranslations("home");
  const tNav = await getTranslations("nav");
  const session = await auth();

  if (!session) {
    const tAuth = await getTranslations("auth");
    return <p className="text-sm text-[var(--muted-foreground)]">{tAuth("signInPrompt")}</p>;
  }

  const roles = session.roles;
  const client = await fleetClient();

  const [approvalsRes, workflowsRes, agentsRes, costRes] = await Promise.all([
    can(roles, "approve")
      ? client.GET("/v1/approvals", { params: { query: { status: "pending" } } })
      : Promise.resolve({ data: undefined }),
    client.GET("/v1/workflows"),
    client.GET("/v1/agents"),
    can(roles, "manage_platform")
      ? client.GET("/v1/admin/cost/summary", { params: { query: { days: 1 } } })
      : Promise.resolve({ data: undefined }),
  ]);

  const pendingApprovals = approvalsRes.data?.length ?? 0;
  const workflows = workflowsRes.data ?? [];
  const agents = agentsRes.data ?? [];
  const todaySpend = costRes.data?.total_usd;

  const runs = workflows
    .filter((w) => w.last_run?.at)
    .sort((a, b) => String(b.last_run?.at).localeCompare(String(a.last_run?.at)));

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("greeting", { name: session.user?.name ?? "none" })}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {can(roles, "approve") && (
          <StatTile
            icon={CheckSquare}
            label={t("tileApprovals")}
            value={String(pendingApprovals)}
            hint={pendingApprovals > 0 ? t("tileApprovalsHint") : t("tileApprovalsHintEmpty")}
            href="/approvals"
            tone={pendingApprovals > 0 ? "attention" : "work"}
          />
        )}
        <StatTile
          icon={Workflow}
          label={t("tileAutomations")}
          value={String(workflows.filter((w) => w.active).length)}
          hint={t("tileAutomationsHint")}
          href="/automations"
          tone="automation"
        />
        <StatTile
          icon={Bot}
          label={t("tileAgents")}
          value={String(agents.length)}
          hint={t("tileAgentsHint")}
          href="/scenarios"
          tone="work"
        />
        {can(roles, "manage_platform") && (
          <StatTile
            icon={CircleDollarSign}
            label={t("tileSpend")}
            value={todaySpend === undefined ? "—" : `$${todaySpend.toFixed(2)}`}
            hint={t("tileSpendHint")}
            href="/admin/cost"
            tone="admin"
          />
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>{t("recentRuns")}</CardTitle>
            <Link
              href="/automations"
              className="text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
            >
              {tNav("automations")}
            </Link>
          </CardHeader>
          <CardContent>
            {runs.length === 0 ? (
              <EmptyState
                icon={Workflow}
                title={t("noRunsTitle")}
                description={t("noRunsDesc")}
                action={
                  <Button size="sm" asChild>
                    <Link href="/automations">{tNav("automations")}</Link>
                  </Button>
                }
              />
            ) : (
              <ul className="flex flex-col divide-y divide-[var(--border)]">
                {runs.slice(0, 5).map((w) => (
                  <li key={w.slug} className="flex items-center justify-between gap-2 py-2">
                    <span className="truncate text-sm">{w.slug}</span>
                    <span className="flex shrink-0 items-center gap-2">
                      <Badge variant={w.last_run?.status === "success" ? "success" : "error"}>
                        {String(w.last_run?.status ?? "—")}
                      </Badge>
                      <span className="text-xs text-[var(--muted-foreground)]">
                        {new Date(String(w.last_run?.at)).toLocaleString()}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>{t("activeAgents")}</CardTitle>
            <Link
              href="/chat"
              className="text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
            >
              {tNav("chat")}
            </Link>
          </CardHeader>
          <CardContent>
            {agents.length === 0 ? (
              <EmptyState
                icon={Bot}
                title={t("noAgentsTitle")}
                description={t("noAgentsDesc")}
              />
            ) : (
              <ul className="flex flex-wrap gap-2">
                {agents.map((a) => (
                  <li key={a.id}>
                    <Link
                      href={`/chat?agent=${encodeURIComponent(a.name)}`}
                      className="flex items-center gap-1.5 rounded-full border border-[var(--border)] px-3 py-1 text-sm transition-colors hover:border-[var(--border-strong)] hover:bg-[var(--surface-2)]"
                    >
                      <MessageSquare className="h-3.5 w-3.5 text-[var(--muted-foreground)]" />
                      {a.name}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
