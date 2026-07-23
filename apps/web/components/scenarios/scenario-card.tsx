"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Scenario } from "@/lib/scenarios";

export function ScenarioCard({ scenario }: { scenario: Scenario }) {
  const t = useTranslations("scenarios");
  const name = t(`items.${scenario.slug}.name`);
  const desc = t(`items.${scenario.slug}.desc`);

  const statusBadge =
    scenario.status === "live" ? (
      <Badge variant="success">{t("statusLive")}</Badge>
    ) : scenario.status === "partial" ? (
      <Badge variant="pending">{t("statusPartial")}</Badge>
    ) : (
      <Badge>{t("comingSoonAt", { sprint: scenario.targetTask ?? "" })}</Badge>
    );

  const body = (
    <Card className={scenario.status === "coming_soon" ? "opacity-70" : undefined}>
      <CardHeader className="flex-row items-start justify-between gap-2">
        <CardTitle>{name}</CardTitle>
        {statusBadge}
      </CardHeader>
      <CardContent>
        <p className="text-sm text-[var(--muted-foreground)]">{desc}</p>
        <p className="mt-2 text-xs text-[var(--muted-foreground)]">{scenario.department}</p>
      </CardContent>
    </Card>
  );

  if (scenario.href && scenario.status !== "coming_soon") {
    return (
      <Link href={scenario.href} className="block transition-opacity hover:opacity-90">
        {body}
      </Link>
    );
  }
  return body;
}
