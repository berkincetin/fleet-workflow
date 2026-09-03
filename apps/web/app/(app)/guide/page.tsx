import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { ArrowRight, Clock, Compass } from "lucide-react";
import { WALKTHROUGHS } from "@/lib/guide";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { GlossaryList } from "@/components/layout/glossary";

/**
 * The in-app guide (task 13.7).
 *
 * Server-rendered and static: it holds no live data, so it stays readable when
 * the API, n8n or the model gateway are down — which is exactly when someone
 * is most likely to come looking for "how is this supposed to work".
 */
export default async function GuidePage() {
  const t = await getTranslations("guide");
  const tw = await getTranslations("guide.walkthroughs");

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={t("title")}
        intro={t("intro")}
        howToLabel={t("howToLabel")}
        howTo={t.raw("howTo") as string[]}
      />

      <section className="flex flex-col gap-3">
        <h3 className="text-sm font-semibold">{t("walkthroughsHeading")}</h3>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {WALKTHROUGHS.map((w) => (
            <Card
              key={w.id}
              data-section={w.section}
              className="relative flex flex-col overflow-hidden"
            >
              <span
                aria-hidden="true"
                className="absolute inset-y-0 left-0 w-1 bg-[var(--section)]"
              />
              <CardHeader className="flex-row items-start justify-between gap-2 pl-5">
                <CardTitle className="flex items-center gap-2">
                  <Compass className="h-4 w-4 text-[var(--section)]" aria-hidden="true" />
                  {tw(`${w.id}.title`)}
                </CardTitle>
                <Badge variant="info">
                  <Clock className="h-3 w-3" aria-hidden="true" />
                  {t("minutes", { count: w.minutes })}
                </Badge>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col gap-3 pl-5">
                <p className="text-sm text-[var(--muted-foreground)]">
                  {tw(`${w.id}.intro`)}
                </p>
                <ol className="flex list-decimal flex-col gap-1.5 pl-4 text-sm text-[var(--muted-foreground)]">
                  {Array.from({ length: w.steps }, (_, i) => (
                    <li key={i}>{tw(`${w.id}.s${i + 1}`)}</li>
                  ))}
                </ol>
                <div className="mt-auto pt-1">
                  <Button size="sm" asChild>
                    <Link href={w.href}>
                      {tw(`${w.id}.cta`)}
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h3 className="text-sm font-semibold">{t("glossaryHeading")}</h3>
        <p className="text-sm text-[var(--muted-foreground)]">{t("glossaryIntro")}</p>
        <GlossaryList />
      </section>
    </div>
  );
}
