"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import type { components } from "@fleet/shared";

type BudgetOut = components["schemas"]["BudgetOut"];

const SCOPE_TYPES = ["global", "dept", "agent", "user"] as const;
const PERIODS = ["monthly", "daily"] as const;

export function BudgetsAdmin({ initialBudgets }: { initialBudgets: BudgetOut[] }) {
  const t = useTranslations("admin");
  const { data: session } = useSession();
  const [budgets, setBudgets] = useState(initialBudgets);
  const [scopeType, setScopeType] = useState<string>("dept");
  const [scopeId, setScopeId] = useState("");
  const [period, setPeriod] = useState<string>("monthly");
  const [limitUsd, setLimitUsd] = useState("");
  const [softPct, setSoftPct] = useState("80");
  const [error, setError] = useState<string | null>(null);

  async function createBudget() {
    setError(null);
    const client = browserFleetClient(session?.accessToken);
    const { data, error: apiError } = await client.POST("/v1/admin/budgets", {
      body: {
        scope_type: scopeType,
        scope_id: scopeType === "global" ? null : scopeId.trim() || null,
        period,
        limit_usd: Number(limitUsd),
        soft_pct: Number(softPct),
      },
    });
    if (apiError || !data) {
      setError(t("budgetCreateError"));
      return;
    }
    setBudgets((prev) => [...prev, data]);
    setScopeId("");
    setLimitUsd("");
  }

  async function updateLimit(budget: BudgetOut, limit: number, soft: number) {
    const client = browserFleetClient(session?.accessToken);
    const { data, error: apiError } = await client.PATCH("/v1/admin/budgets/{budget_id}", {
      params: { path: { budget_id: budget.id } },
      body: {
        scope_type: budget.scope_type,
        scope_id: budget.scope_id,
        period: budget.period,
        limit_usd: limit,
        soft_pct: soft,
      },
    });
    if (apiError || !data) return;
    setBudgets((prev) => prev.map((b) => (b.id === budget.id ? data : b)));
  }

  async function deleteBudget(budget: BudgetOut) {
    const client = browserFleetClient(session?.accessToken);
    const { error: apiError } = await client.DELETE("/v1/admin/budgets/{budget_id}", {
      params: { path: { budget_id: budget.id } },
    });
    if (apiError) return;
    setBudgets((prev) => prev.filter((b) => b.id !== budget.id));
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("budgetsTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {error && <p className="text-sm text-red-600">{error}</p>}

        {budgets.some((b) => b.soft_exceeded || b.hard_exceeded) && (
          <div className="rounded-md border border-amber-500/40 bg-amber-50 p-3 text-sm dark:bg-amber-950">
            <p className="font-medium">{t("budgetWarningBanner")}</p>
            <ul className="mt-1 list-inside list-disc">
              {budgets
                .filter((b) => b.soft_exceeded || b.hard_exceeded)
                .map((b) => (
                  <li key={b.id}>
                    {t(`budgetScope.${b.scope_type}` as never)}
                    {b.scope_id ? ` (${b.scope_id})` : ""} — ${b.spent_usd.toFixed(2)} / $
                    {b.limit_usd.toFixed(2)}
                  </li>
                ))}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap items-end gap-2">
          <Select value={scopeType} onValueChange={setScopeType}>
            <SelectTrigger className="w-32">
              <SelectValue>{t(`budgetScope.${scopeType}` as never)}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {SCOPE_TYPES.map((s) => (
                <SelectItem key={s} value={s}>
                  {t(`budgetScope.${s}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {scopeType !== "global" && (
            <Input
              placeholder={t("budgetScopeId")}
              value={scopeId}
              onChange={(e) => setScopeId(e.target.value)}
              className="w-28"
            />
          )}
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-28">
              <SelectValue>{t(`budgetPeriod.${period}` as never)}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {PERIODS.map((p) => (
                <SelectItem key={p} value={p}>
                  {t(`budgetPeriod.${p}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            type="number"
            placeholder={t("limitUsd")}
            value={limitUsd}
            onChange={(e) => setLimitUsd(e.target.value)}
            className="w-28"
          />
          <Input
            type="number"
            placeholder={t("softPct")}
            value={softPct}
            onChange={(e) => setSoftPct(e.target.value)}
            className="w-24"
          />
          <Button size="sm" onClick={createBudget}>
            {t("createBudget")}
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("budgetScopeCol")}</TableHead>
              <TableHead>{t("budgetPeriodCol")}</TableHead>
              <TableHead>{t("limitUsd")}</TableHead>
              <TableHead>{t("softPct")}</TableHead>
              <TableHead>{t("budgetSpent")}</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {budgets.map((budget) => (
              <TableRow key={budget.id}>
                <TableCell>
                  {t(`budgetScope.${budget.scope_type}` as never)}
                  {budget.scope_id ? ` (${budget.scope_id})` : ""}
                </TableCell>
                <TableCell>{t(`budgetPeriod.${budget.period}` as never)}</TableCell>
                <TableCell>
                  <Input
                    type="number"
                    defaultValue={budget.limit_usd}
                    className="w-24"
                    onBlur={(e) => {
                      const v = Number(e.target.value);
                      if (v > 0 && v !== budget.limit_usd) updateLimit(budget, v, budget.soft_pct);
                    }}
                  />
                </TableCell>
                <TableCell>
                  <Input
                    type="number"
                    defaultValue={budget.soft_pct}
                    className="w-20"
                    onBlur={(e) => {
                      const v = Number(e.target.value);
                      if (v >= 0 && v <= 100 && v !== budget.soft_pct)
                        updateLimit(budget, budget.limit_usd, v);
                    }}
                  />
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className="tabular-nums">${budget.spent_usd.toFixed(2)}</span>
                    {budget.hard_exceeded ? (
                      <Badge variant="error">{t("budgetHardExceeded")}</Badge>
                    ) : budget.soft_exceeded ? (
                      <Badge variant="pending">{t("budgetSoftExceeded")}</Badge>
                    ) : null}
                  </div>
                </TableCell>
                <TableCell className="flex justify-end">
                  <Button size="sm" variant="outline" onClick={() => deleteBudget(budget)}>
                    {t("delete")}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
