import { getTranslations } from "next-intl/server";
import { auth } from "@/lib/auth";
import { fleetClient } from "@/lib/fleet-client";
import { can } from "@/lib/permissions";
import { templateById } from "@/lib/recipe-templates";
import { PageHeader } from "@/components/layout/page-header";
import { RecipeBuilder } from "@/components/automations/recipe-builder";
import { TemplatePicker } from "@/components/automations/template-picker";

export default async function NewAutomationPage({
  searchParams,
}: {
  searchParams: Promise<{ template?: string }>;
}) {
  const t = await getTranslations("builder");
  const tAdmin = await getTranslations("admin");
  const session = await auth();

  if (!can(session?.roles, "manage_agents")) {
    return <p className="text-sm text-[var(--muted-foreground)]">{tAdmin("noAccess")}</p>;
  }

  const client = await fleetClient();
  const { data: agents } = await client.GET("/v1/agents");
  // An unknown ?template= falls through to a blank builder rather than 404ing:
  // the parameter is a convenience, and a stale link should still open the
  // page it names.
  const { template } = await searchParams;
  const selected = templateById(template);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("title")}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />
      {/* The picker is offered only on a blank start. Once a template is
          chosen the form below is already filled with it, and showing the
          gallery again would just invite losing that work to a stray click. */}
      {!selected && <TemplatePicker />}
      <RecipeBuilder
        // Remounts the form when the template changes, so navigating from one
        // template to another actually reseeds `useState` instead of keeping
        // the first template's draft.
        key={selected?.id ?? "blank"}
        agents={agents ?? []}
        template={selected}
      />
    </div>
  );
}
