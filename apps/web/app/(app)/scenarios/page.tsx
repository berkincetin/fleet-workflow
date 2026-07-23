import { getTranslations } from "next-intl/server";
import { SCENARIOS } from "@/lib/scenarios";
import { ScenarioCard } from "@/components/scenarios/scenario-card";

export default async function ScenariosPage() {
  const t = await getTranslations("scenarios");

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">{t("title")}</h1>
        <p className="text-sm text-[var(--muted-foreground)]">{t("subtitle")}</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SCENARIOS.map((s) => (
          <ScenarioCard key={s.slug} scenario={s} />
        ))}
      </div>
    </div>
  );
}
