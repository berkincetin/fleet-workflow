import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { Plus, Workflow } from "lucide-react";
import { auth } from "@/lib/auth";
import { fleetClient } from "@/lib/fleet-client";
import { can } from "@/lib/permissions";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/layout/empty-state";
import { PageHeader } from "@/components/layout/page-header";
import { WorkflowCard } from "@/components/automations/workflow-card";
import { RecipeCard } from "@/components/automations/recipe-card";

const N8N_EDITOR_URL = process.env.NEXT_PUBLIC_N8N_EDITOR_URL ?? "http://localhost:5679";

export default async function AutomationsPage() {
  const t = await getTranslations("automations");
  const tCommon = await getTranslations("common");
  const session = await auth();
  const client = await fleetClient();

  const [workflowsRes, recipesRes] = await Promise.all([
    client.GET("/v1/workflows"),
    client.GET("/v1/recipes"),
  ]);
  const workflows = workflowsRes.data ?? [];
  const recipes = recipesRes.data ?? [];
  const canBuild = can(session?.roles, "manage_agents");

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("title")}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
        actions={
          canBuild ? (
            <Button size="sm" asChild>
              <Link href="/automations/new">
                <Plus className="h-3.5 w-3.5" aria-hidden="true" />
                {t("newRecipe")}
              </Link>
            </Button>
          ) : undefined
        }
      />

      <section className="flex flex-col gap-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
          {t("catalogSection")}
        </h3>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {workflows.map((w) => (
            <WorkflowCard key={w.slug} workflow={w} roles={session?.roles} />
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
          {t("recipesSection")}
        </h3>
        {recipes.length === 0 ? (
          <EmptyState
            icon={Workflow}
            title={t("emptyTitle")}
            description={t("emptyDesc")}
            action={
              canBuild ? (
                <Button size="sm" asChild>
                  <Link href="/automations/new">{t("newRecipe")}</Link>
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {recipes.map((r) => (
              <RecipeCard key={r.id} recipe={r} roles={session?.roles} />
            ))}
          </div>
        )}
      </section>

      {canBuild && (
        <a
          href={N8N_EDITOR_URL}
          target="_blank"
          rel="noreferrer"
          className="text-sm text-[var(--muted-foreground)] underline hover:text-[var(--foreground)]"
        >
          {tCommon("advanced")}: {t("advancedEditorLink")}
        </a>
      )}
    </div>
  );
}
