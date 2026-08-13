"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { components } from "@fleet/shared";

type CostSummaryOut = components["schemas"]["CostSummaryOut"];
type SpendByKey = components["schemas"]["SpendByKey"];

function BarList({ rows }: { rows: SpendByKey[] }) {
  const max = Math.max(1, ...rows.map((r) => r.total_usd));
  return (
    <ul className="flex flex-col gap-2">
      {rows.map((row) => (
        <li key={row.key} className="flex items-center gap-2 text-sm" title={`$${row.total_usd}`}>
          <span className="w-28 shrink-0 truncate text-[var(--muted-foreground)]">{row.key}</span>
          <span className="h-2 flex-1 overflow-hidden rounded-full bg-[var(--muted)]">
            <span
              className="block h-full rounded-full bg-[var(--primary)]"
              style={{ width: `${Math.max(4, (row.total_usd / max) * 100)}%` }}
            />
          </span>
          <span className="w-20 shrink-0 text-right tabular-nums">${row.total_usd.toFixed(2)}</span>
        </li>
      ))}
    </ul>
  );
}

function BurnDownChart({ points }: { points: CostSummaryOut["burn_down"] }) {
  const max = Math.max(1, ...points.map((p) => p.total_usd));
  const barWidth = 100 / Math.max(1, points.length);
  return (
    <svg viewBox="0 0 100 40" className="h-32 w-full" preserveAspectRatio="none" role="img">
      {points.map((p, i) => {
        const h = (p.total_usd / max) * 36;
        return (
          <rect
            key={p.date}
            x={i * barWidth + barWidth * 0.15}
            y={38 - h}
            width={barWidth * 0.7}
            height={h}
            rx={0.6}
            fill="var(--primary)"
          >
            <title>{`${p.date}: $${p.total_usd.toFixed(2)}`}</title>
          </rect>
        );
      })}
    </svg>
  );
}

export function CostDashboard({ initialSummary }: { initialSummary: CostSummaryOut | null }) {
  const t = useTranslations("admin");

  if (!initialSummary) {
    return (
      <Card>
        <CardContent className="p-6 text-sm text-[var(--muted-foreground)]">
          {t("costNoData")}
        </CardContent>
      </Card>
    );
  }

  const { total_usd, by_dept, by_agent, by_model, burn_down, cache_hit_ratio } = initialSummary;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-2">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-[var(--muted-foreground)]">{t("totalSpend")}</p>
            <p className="text-2xl font-semibold tabular-nums">${total_usd.toFixed(2)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-[var(--muted-foreground)]">{t("cacheHitRatio")}</p>
            <p className="text-2xl font-semibold tabular-nums">
              {(cache_hit_ratio * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("burnDown")}</CardTitle>
        </CardHeader>
        <CardContent>
          {burn_down.length > 0 ? (
            <BurnDownChart points={burn_down} />
          ) : (
            <p className="text-sm text-[var(--muted-foreground)]">{t("costNoData")}</p>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>{t("spendByDept")}</CardTitle>
          </CardHeader>
          <CardContent>
            <BarList rows={by_dept} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{t("spendByAgent")}</CardTitle>
          </CardHeader>
          <CardContent>
            <BarList rows={by_agent} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{t("spendByModel")}</CardTitle>
          </CardHeader>
          <CardContent>
            <BarList rows={by_model} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
