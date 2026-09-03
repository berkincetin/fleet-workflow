import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { ArrowRight, Clock, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RECIPE_TEMPLATES } from "@/lib/recipe-templates";

/**
 * The ready-made recipes offered above the blank builder (task 13.7).
 *
 * Each card links to the same `/automations/new` route with `?template=`, so
 * picking one is a normal navigation — no client state, no modal — and the URL
 * of a half-built automation can be shared or reloaded.
 */
export async function TemplatePicker() {
  const t = await getTranslations("builder.templates");

  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <h3 className="text-sm font-semibold">{t("heading")}</h3>
        <p className="text-sm text-[var(--muted-foreground)]">{t("intro")}</p>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {RECIPE_TEMPLATES.map((tpl) => (
          <Link
            key={tpl.id}
            href={`/automations/new?template=${tpl.id}`}
            className="group block"
          >
            <Card className="relative flex h-full flex-col overflow-hidden transition-all hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)]">
              <span
                aria-hidden="true"
                className="absolute inset-y-0 left-0 w-1 bg-[var(--section)]"
              />
              <CardHeader className="flex-row items-start justify-between gap-2 pl-5">
                <CardTitle className="flex items-center gap-2">
                  {t(`${tpl.id}.title`)}
                  <ArrowRight
                    className="h-3.5 w-3.5 shrink-0 text-[var(--section)] opacity-0 transition-opacity group-hover:opacity-100"
                    aria-hidden="true"
                  />
                </CardTitle>
                {tpl.needsApproval && (
                  <Badge variant="pending">
                    <ShieldCheck className="h-3 w-3" aria-hidden="true" />
                    {t("needsApproval")}
                  </Badge>
                )}
              </CardHeader>
              <CardContent className="flex flex-col gap-2 pl-5">
                <p className="text-sm text-[var(--muted-foreground)]">
                  {t(`${tpl.id}.description`)}
                </p>
                <p className="flex items-center gap-1.5 text-xs text-[var(--muted-foreground)]">
                  <Clock className="h-3.5 w-3.5 text-[var(--section)]" aria-hidden="true" />
                  {t(`${tpl.id}.when`)}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}
