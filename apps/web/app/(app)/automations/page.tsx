import { getTranslations } from "next-intl/server";
import { auth } from "@/lib/auth";
import { fleetClient } from "@/lib/fleet-client";
import { can } from "@/lib/permissions";
import { WorkflowCard } from "@/components/automations/workflow-card";

const N8N_EDITOR_URL = process.env.NEXT_PUBLIC_N8N_EDITOR_URL ?? "http://localhost:5679";

export default async function AutomationsPage() {
  const t = await getTranslations("automations");
  const tCommon = await getTranslations("common");
  const session = await auth();
  const client = await fleetClient();
  const { data: workflows } = await client.GET("/v1/workflows");

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">{t("title")}</h1>
        <p className="text-sm text-[var(--muted-foreground)]">{t("subtitle")}</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {(workflows ?? []).map((w) => (
          <WorkflowCard key={w.slug} workflow={w} roles={session?.roles} />
        ))}
      </div>
      {can(session?.roles, "manage_agents") && (
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
