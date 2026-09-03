import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { auth } from "@/lib/auth";
import { fleetClient } from "@/lib/fleet-client";
import { can } from "@/lib/permissions";
import { PageHeader } from "@/components/layout/page-header";
import { RecipeBuilder } from "@/components/automations/recipe-builder";

export default async function EditAutomationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const t = await getTranslations("builder");
  const tAdmin = await getTranslations("admin");
  const session = await auth();

  if (!can(session?.roles, "manage_agents")) {
    return <p className="text-sm text-[var(--muted-foreground)]">{tAdmin("noAccess")}</p>;
  }

  const { id } = await params;
  const client = await fleetClient();
  const [{ data: agents }, { data: recipe }] = await Promise.all([
    client.GET("/v1/agents"),
    client.GET("/v1/recipes/{recipe_id}", { params: { path: { recipe_id: Number(id) } } }),
  ]);
  if (!recipe) notFound();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("editTitle", { name: recipe.name })}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />
      <RecipeBuilder agents={agents ?? []} existing={recipe} />
    </div>
  );
}
