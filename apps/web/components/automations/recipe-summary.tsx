"use client";

import { useTranslations } from "next-intl";
import { ArrowRight, Clock, GitBranch, Play } from "lucide-react";
import { Badge } from "@/components/ui/badge";

/**
 * Plain-language rendering of a recipe (task 13.5).
 *
 * The structure comes from the API (`describe_recipe`), so the builder's
 * preview and an automation card always describe the same recipe the same way;
 * only the sentence wording is assembled here, where it can be translated.
 */

type SummaryEntry = Record<string, unknown>;

function paramsLine(params: Record<string, unknown> | undefined): string {
  if (!params) return "";
  return Object.entries(params)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(" · ");
}

function ActionLine({ entry }: { entry: SummaryEntry }) {
  const t = useTranslations("builder");
  return (
    <li className="flex flex-col gap-0.5">
      <span className="flex flex-wrap items-center gap-2 text-sm">
        <ArrowRight className="h-3.5 w-3.5 text-[var(--muted-foreground)]" aria-hidden="true" />
        {t(`actions.${String(entry.action)}.label`)}
        {entry.write_external === true && (
          <Badge variant="pending">{t("needsApproval")}</Badge>
        )}
      </span>
      <span className="break-words pl-5 text-xs text-[var(--muted-foreground)]">
        {paramsLine(entry.params as Record<string, unknown>)}
      </span>
    </li>
  );
}

export function RecipeSummary({ summary }: { summary: SummaryEntry[] }) {
  const t = useTranslations("builder");

  return (
    <ol className="flex flex-col gap-2">
      {summary.map((entry, index) => {
        if (entry.kind === "trigger") {
          return (
            <li key={index} className="flex items-center gap-2 text-sm">
              {entry.trigger === "schedule" ? (
                <>
                  <Clock className="h-3.5 w-3.5 text-[var(--muted-foreground)]" aria-hidden="true" />
                  {t("summaryScheduleTrigger", { cron: String(entry.cron) })}
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 text-[var(--muted-foreground)]" aria-hidden="true" />
                  {t("summaryManualTrigger")}
                </>
              )}
            </li>
          );
        }
        if (entry.kind === "action") {
          return <ActionLine key={index} entry={entry} />;
        }
        const thenSteps = (entry.then ?? []) as SummaryEntry[];
        const elseSteps = (entry.else ?? []) as SummaryEntry[];
        return (
          <li key={index} className="flex flex-col gap-1">
            <span className="flex items-center gap-2 text-sm">
              <GitBranch className="h-3.5 w-3.5 text-[var(--muted-foreground)]" aria-hidden="true" />
              {t("summaryCondition", {
                left: String(entry.left),
                operator: t(`operators.${String(entry.operator)}`),
                right: String(entry.right),
              })}
            </span>
            <div className="pl-5">
              <p className="text-xs font-medium text-[var(--muted-foreground)]">
                {t("thenLabel")}
              </p>
              <ol className="pl-2">
                {thenSteps.length === 0 ? (
                  <li className="text-xs text-[var(--muted-foreground)]">{t("branchEmpty")}</li>
                ) : (
                  thenSteps.map((s, i) => <ActionLine key={i} entry={s} />)
                )}
              </ol>
              <p className="mt-1 text-xs font-medium text-[var(--muted-foreground)]">
                {t("elseLabel")}
              </p>
              <ol className="pl-2">
                {elseSteps.length === 0 ? (
                  <li className="text-xs text-[var(--muted-foreground)]">{t("branchEmpty")}</li>
                ) : (
                  elseSteps.map((s, i) => <ActionLine key={i} entry={s} />)
                )}
              </ol>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
