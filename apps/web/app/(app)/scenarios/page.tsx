import { getTranslations } from "next-intl/server";
import { SCENARIOS } from "@/lib/scenarios";
import { ScenarioCard } from "@/components/scenarios/scenario-card";
import { PageHeader } from "@/components/layout/page-header";

export default async function ScenariosPage() {
  const t = await getTranslations("scenarios");

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("title")}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SCENARIOS.map((s) => (
          <ScenarioCard key={s.slug} scenario={s} />
        ))}
      </div>
    </div>
  );
}
