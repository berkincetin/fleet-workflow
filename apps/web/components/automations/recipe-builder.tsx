"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useTranslations } from "next-intl";
import { AlertTriangle, GitBranch, Plus, Trash2 } from "lucide-react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { GlossaryTerm } from "@/components/layout/glossary";
import { RecipeSummary } from "@/components/automations/recipe-summary";
import {
  ACTIONS,
  ACTION_NAMES,
  CRON_PRESETS,
  OPERATORS,
  RECIPE_NAME_RE,
  slugify,
  type ActionName,
  type Operator,
} from "@/lib/recipe-actions";
import { type RecipeTemplate } from "@/lib/recipe-templates";
import { cn } from "@/lib/utils";
import type { components } from "@fleet/shared";

type AgentSummary = components["schemas"]["AgentSummaryOut"];
type RecipeOut = components["schemas"]["RecipeOut"];
type PreviewOut = components["schemas"]["PreviewOut"];

interface DraftAction {
  kind: "action";
  id: string;
  action: ActionName;
  params: Record<string, string>;
}

interface DraftCondition {
  kind: "condition";
  id: string;
  left: string;
  operator: Operator;
  right: string;
  then: DraftAction[];
  else: DraftAction[];
}

type DraftStep = DraftAction | DraftCondition;

function emptyParams(action: ActionName): Record<string, string> {
  return Object.fromEntries(ACTIONS[action].fields.map((f) => [f.name, ""]));
}

function newAction(index: number): DraftAction {
  return { kind: "action", id: `step${index}`, action: "pg.query", params: emptyParams("pg.query") };
}

/** Draft -> the API's recipe shape. Empty params are dropped so the server's
 * required-field errors are about what the user left blank, not about "". */
function toPayload(
  name: string,
  description: string,
  trigger: { type: "manual" } | { type: "schedule"; cron: string },
  steps: DraftStep[],
) {
  const action = (s: DraftAction) => ({
    type: "action" as const,
    id: s.id,
    action: s.action,
    params: Object.fromEntries(Object.entries(s.params).filter(([, v]) => v !== "")),
  });
  return {
    name,
    description,
    trigger,
    steps: steps.map((s) =>
      s.kind === "action"
        ? action(s)
        : {
            type: "condition" as const,
            id: s.id,
            left: s.left,
            operator: s.operator,
            right: s.right,
            then_steps: s.then.map(action),
            else_steps: s.else.map(action),
          },
    ),
  };
}

function fromRecipe(recipe: RecipeOut): {
  name: string;
  description: string;
  trigger: { type: "manual" } | { type: "schedule"; cron: string };
  steps: DraftStep[];
} {
  const definition = recipe.definition as {
    trigger: { type: "manual" } | { type: "schedule"; cron: string };
    steps: Record<string, unknown>[];
  };
  return {
    name: recipe.name,
    description: recipe.description,
    trigger: definition.trigger,
    steps: definition.steps.map((raw) =>
      raw.type === "action"
        ? {
            kind: "action",
            id: String(raw.id),
            action: raw.action as ActionName,
            params: {
              ...emptyParams(raw.action as ActionName),
              ...(raw.params as Record<string, string>),
            },
          }
        : {
            kind: "condition",
            id: String(raw.id),
            left: String(raw.left),
            operator: raw.operator as Operator,
            right: String(raw.right),
            then: (raw.then_steps as Record<string, unknown>[]).map((s) => ({
              kind: "action" as const,
              id: String(s.id),
              action: s.action as ActionName,
              params: {
                ...emptyParams(s.action as ActionName),
                ...(s.params as Record<string, string>),
              },
            })),
            else: (raw.else_steps as Record<string, unknown>[]).map((s) => ({
              kind: "action" as const,
              id: String(s.id),
              action: s.action as ActionName,
              params: {
                ...emptyParams(s.action as ActionName),
                ...(s.params as Record<string, string>),
              },
            })),
          },
    ),
  };
}

/**
 * A labelled field. The label element carries only the field's *name* — the
 * hint hangs off `aria-describedby` — so the input's accessible name is exactly
 * "Name", not "Name" plus a paragraph of help text. A wrapping <label> would
 * fold the hint into the accessible name, which is both worse for a screen
 * reader and unfindable by `getByLabel` in the e2e.
 */
function Field({
  id,
  label,
  hint,
  hintTone = "muted",
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  hintTone?: "muted" | "danger";
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1 text-sm">
      <label htmlFor={id}>{label}</label>
      {children}
      {hint && (
        <span
          id={`${id}-hint`}
          className={cn(
            "text-xs",
            hintTone === "danger" ? "text-[var(--danger)]" : "text-[var(--muted-foreground)]",
          )}
        >
          {hint}
        </span>
      )}
    </div>
  );
}

/**
 * The automation builder (task 13.5).
 *
 * A form, not a canvas: pick a trigger, add steps from the fixed action list,
 * optionally add one condition, then read back what it will do in plain
 * language before saving. The preview is not rendered locally — it is the
 * server's own `POST /v1/recipes/preview`, so what the user reads is produced
 * by the same code that compiles the workflow, and a recipe the compiler would
 * refuse is refused here rather than at save time.
 */
export function RecipeBuilder({
  agents,
  existing,
  template,
}: {
  agents: AgentSummary[];
  existing?: RecipeOut;
  /**
   * Seeds a new draft from a ready-made recipe (task 13.7). It goes through
   * the same `fromRecipe` path an edit does rather than a second parser, so a
   * template can never produce a draft shape the editor cannot round-trip.
   * `existing` wins: editing a saved recipe is never overridden by a stray
   * ?template= in the URL.
   */
  template?: RecipeTemplate;
}) {
  const t = useTranslations("builder");
  const tCommon = useTranslations("common");
  const tAuto = useTranslations("automations");
  const router = useRouter();
  const { data: session } = useSession();
  const { show } = useToast();

  const initial = existing
    ? fromRecipe(existing)
    : template
      ? fromRecipe({
          name: template.name,
          description: t(`templates.${template.id}.description`),
          definition: { trigger: template.trigger, steps: template.steps },
        } as unknown as RecipeOut)
      : null;
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [trigger, setTrigger] = useState<
    { type: "manual" } | { type: "schedule"; cron: string }
  >(initial?.trigger ?? { type: "manual" });
  const [steps, setSteps] = useState<DraftStep[]>(initial?.steps ?? [newAction(1)]);
  const [preview, setPreview] = useState<PreviewOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const nameValid = RECIPE_NAME_RE.test(name);
  const hasCondition = steps.some((s) => s.kind === "condition");

  function patchStep(index: number, patch: Partial<DraftAction> | Partial<DraftCondition>) {
    setSteps((prev) =>
      prev.map((s, i) => (i === index ? ({ ...s, ...patch } as DraftStep) : s)),
    );
    setPreview(null);
  }

  function patchBranchStep(
    conditionIndex: number,
    branch: "then" | "else",
    stepIndex: number,
    patch: Partial<DraftAction>,
  ) {
    setSteps((prev) =>
      prev.map((s, i) => {
        if (i !== conditionIndex || s.kind !== "condition") return s;
        const list = s[branch].map((b, j) => (j === stepIndex ? { ...b, ...patch } : b));
        return { ...s, [branch]: list };
      }),
    );
    setPreview(null);
  }

  async function runPreview(): Promise<PreviewOut | null> {
    setError(null);
    const client = browserFleetClient(session?.accessToken);
    const { data, error: apiError } = await client.POST("/v1/recipes/preview", {
      body: toPayload(name, description, trigger, steps),
    });
    if (apiError || !data) {
      setError(
        typeof (apiError as { detail?: unknown })?.detail === "string"
          ? String((apiError as { detail?: unknown }).detail)
          : t("previewError"),
      );
      return null;
    }
    setPreview(data);
    return data;
  }

  async function save() {
    setBusy(true);
    const ok = await runPreview();
    if (!ok) {
      setBusy(false);
      return;
    }
    const client = browserFleetClient(session?.accessToken);
    const body = toPayload(name, description, trigger, steps);
    const result = existing
      ? await client.PUT("/v1/recipes/{recipe_id}", {
          params: { path: { recipe_id: existing.id } },
          body,
        })
      : await client.POST("/v1/recipes", { body });
    setBusy(false);

    if (result.error || !result.data) {
      const detail = (result.error as { detail?: unknown })?.detail;
      setError(typeof detail === "string" ? detail : t("saveError"));
      return;
    }
    if (result.data.deploy_error) {
      show(t("savedButNotDeployed"), "error");
    } else {
      show(t("saved"), "success");
    }
    router.push("/automations");
    router.refresh();
  }

  const stepIds = steps.flatMap((s) =>
    s.kind === "action" ? [s.id] : [s.id, ...s.then.map((b) => b.id), ...s.else.map((b) => b.id)],
  );

  return (
    <div className="flex flex-col gap-6">
      {/* 1 — identity */}
      <Card>
        <CardHeader>
          <CardTitle>{t("sectionBasics")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Field
            id="recipe-name"
            label={t("name")}
            hint={existing ? t("nameLocked") : t("nameHint")}
            hintTone={name && !nameValid ? "danger" : "muted"}
          >
            <Input
              id="recipe-name"
              aria-describedby="recipe-name-hint"
              value={name}
              disabled={Boolean(existing)}
              onChange={(e) => setName(slugify(e.target.value))}
              placeholder={t("namePlaceholder")}
            />
          </Field>
          <Field id="recipe-description" label={t("description")}>
            <Input
              id="recipe-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Field>
        </CardContent>
      </Card>

      {/* 2 — trigger */}
      <Card>
        <CardHeader>
          <CardTitle>{t("sectionTrigger")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={trigger.type === "manual" ? "default" : "outline"}
              onClick={() => {
                setTrigger({ type: "manual" });
                setPreview(null);
              }}
            >
              {t("triggerManual")}
            </Button>
            <Button
              size="sm"
              variant={trigger.type === "schedule" ? "default" : "outline"}
              onClick={() => {
                setTrigger({ type: "schedule", cron: "0 9 * * 1" });
                setPreview(null);
              }}
            >
              {t("triggerSchedule")}
            </Button>
          </div>
          <p className="text-xs text-[var(--muted-foreground)]">
            {trigger.type === "manual" ? t("triggerManualHint") : t("triggerScheduleHint")}
          </p>
          {trigger.type === "schedule" && (
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap gap-2">
                {CRON_PRESETS.map((preset) => (
                  <Button
                    key={preset.key}
                    size="sm"
                    variant={trigger.cron === preset.cron ? "default" : "outline"}
                    onClick={() => {
                      setTrigger({ type: "schedule", cron: preset.cron });
                      setPreview(null);
                    }}
                  >
                    {t(`cronPresets.${preset.key}`)}
                  </Button>
                ))}
              </div>
              <Field id="recipe-cron" label={t("cronExpression")}>
                <Input
                  id="recipe-cron"
                  value={trigger.cron}
                  onChange={(e) => {
                    setTrigger({ type: "schedule", cron: e.target.value });
                    setPreview(null);
                  }}
                />
              </Field>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 3 — steps */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle>{t("sectionSteps")}</CardTitle>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setSteps((prev) => [...prev, newAction(stepIds.length + 1)]);
                setPreview(null);
              }}
            >
              <Plus className="h-3.5 w-3.5" aria-hidden="true" />
              {t("addStep")}
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={hasCondition}
              onClick={() => {
                setSteps((prev) => [
                  ...prev,
                  {
                    kind: "condition",
                    id: `cond${prev.length + 1}`,
                    left: "",
                    operator: "gt",
                    right: "0",
                    then: [{ ...newAction(stepIds.length + 1), id: `then${prev.length + 1}` }],
                    else: [],
                  },
                ]);
                setPreview(null);
              }}
            >
              <GitBranch className="h-3.5 w-3.5" aria-hidden="true" />
              {t("addCondition")}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-xs text-[var(--muted-foreground)]">{t("referenceHint")}</p>
          {steps.map((step, index) =>
            step.kind === "action" ? (
              <ActionEditor
                key={step.id}
                step={step}
                agents={agents}
                onChange={(patch) => patchStep(index, patch)}
                onRemove={() => {
                  setSteps((prev) => prev.filter((_, i) => i !== index));
                  setPreview(null);
                }}
              />
            ) : (
              <div
                key={step.id}
                className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-[var(--border-strong)] p-3"
              >
                <div className="flex flex-wrap items-end gap-2">
                  <span className="flex items-center gap-1 text-sm font-medium">
                    <GitBranch className="h-4 w-4" aria-hidden="true" />
                    {t("ifLabel")}
                  </span>
                  <Input
                    className="max-w-xs"
                    value={step.left}
                    placeholder="{{steps.step1.row_count}}"
                    onChange={(e) => patchStep(index, { left: e.target.value })}
                  />
                  <select
                    aria-label={t("operator")}
                    className="h-9 rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface)] px-2 text-sm"
                    value={step.operator}
                    onChange={(e) =>
                      patchStep(index, { operator: e.target.value as Operator })
                    }
                  >
                    {OPERATORS.map((op) => (
                      <option key={op} value={op}>
                        {t(`operators.${op}`)}
                      </option>
                    ))}
                  </select>
                  <Input
                    className="max-w-[8rem]"
                    value={step.right}
                    onChange={(e) => patchStep(index, { right: e.target.value })}
                  />
                  <Button
                    size="icon"
                    variant="ghost"
                    aria-label={tCommon("delete")}
                    onClick={() => {
                      setSteps((prev) => prev.filter((_, i) => i !== index));
                      setPreview(null);
                    }}
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </div>

                {(["then", "else"] as const).map((branch) => (
                  <div key={branch} className="flex flex-col gap-2 pl-4">
                    <div className="flex items-center gap-2">
                      <Badge variant={branch === "then" ? "success" : "default"}>
                        {t(branch === "then" ? "thenLabel" : "elseLabel")}
                      </Badge>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setSteps((prev) =>
                            prev.map((s, i) =>
                              i === index && s.kind === "condition"
                                ? {
                                    ...s,
                                    [branch]: [
                                      ...s[branch],
                                      {
                                        ...newAction(stepIds.length + 1),
                                        id: `${branch}${s[branch].length + 1}_${s.id}`,
                                      },
                                    ],
                                  }
                                : s,
                            ),
                          );
                          setPreview(null);
                        }}
                      >
                        <Plus className="h-3.5 w-3.5" aria-hidden="true" />
                        {t("addStep")}
                      </Button>
                    </div>
                    {step[branch].map((branchStep, branchIndex) => (
                      <ActionEditor
                        key={branchStep.id}
                        step={branchStep}
                        agents={agents}
                        onChange={(patch) =>
                          patchBranchStep(index, branch, branchIndex, patch)
                        }
                        onRemove={() => {
                          setSteps((prev) =>
                            prev.map((s, i) =>
                              i === index && s.kind === "condition"
                                ? { ...s, [branch]: s[branch].filter((_, j) => j !== branchIndex) }
                                : s,
                            ),
                          );
                          setPreview(null);
                        }}
                      />
                    ))}
                  </div>
                ))}
              </div>
            ),
          )}
        </CardContent>
      </Card>

      {/* 4 — preview + save */}
      <Card>
        <CardHeader>
          <CardTitle>{t("sectionPreview")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {error && (
            <p className="rounded-[var(--radius-md)] bg-[var(--danger-bg)] px-3 py-2 text-sm text-[var(--danger-fg)]">
              {error}
            </p>
          )}
          {preview ? (
            <>
              <RecipeSummary summary={preview.summary} />
              {preview.has_write_external && (
                <p className="flex flex-wrap items-center gap-1 rounded-[var(--radius-md)] bg-[var(--warning-bg)] px-3 py-2 text-sm text-[var(--warning-fg)]">
                  <AlertTriangle className="h-4 w-4" aria-hidden="true" />
                  {t("writeExternalWarning")}
                  <GlossaryTerm term="writeExternal" />
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-[var(--muted-foreground)]">{t("previewHint")}</p>
          )}
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={runPreview} disabled={busy}>
              {t("preview")}
            </Button>
            <Button onClick={save} disabled={busy || !nameValid || steps.length === 0}>
              {existing ? tCommon("save") : tAuto("newRecipe")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ActionEditor({
  step,
  agents,
  onChange,
  onRemove,
}: {
  step: DraftAction;
  agents: AgentSummary[];
  onChange: (patch: Partial<DraftAction>) => void;
  onRemove: () => void;
}) {
  const t = useTranslations("builder");
  const tCommon = useTranslations("common");
  const spec = ACTIONS[step.action];

  return (
    <div className="flex flex-col gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-2)] p-3">
      <div className="flex flex-wrap items-center gap-2">
        <code className="rounded bg-[var(--surface-3)] px-1.5 py-0.5 text-xs">{step.id}</code>
        <select
          aria-label={t("action")}
          className="h-8 rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface)] px-2 text-sm"
          value={step.action}
          onChange={(e) => {
            const next = e.target.value as ActionName;
            onChange({ action: next, params: emptyParams(next) });
          }}
        >
          {ACTION_NAMES.map((action) => (
            <option key={action} value={action}>
              {t(`actions.${action}.label`)}
            </option>
          ))}
        </select>
        {spec.writeExternal && <Badge variant="pending">{t("needsApproval")}</Badge>}
        <Button
          size="icon"
          variant="ghost"
          className="ml-auto"
          aria-label={tCommon("delete")}
          onClick={onRemove}
        >
          <Trash2 className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
      <p className="text-xs text-[var(--muted-foreground)]">
        {t(`actions.${step.action}.help`)}
      </p>
      {spec.fields.map((field) => {
        const fieldId = `${step.id}-${field.name}`;
        const value = step.params[field.name] ?? "";
        const update = (next: string) =>
          onChange({ params: { ...step.params, [field.name]: next } });
        return (
          <Field key={field.name} id={fieldId} label={t(`fields.${field.name}`)}>
            {field.kind === "agent" ? (
              <select
                id={fieldId}
                className="h-9 rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface)] px-2 text-sm"
                value={value}
                onChange={(e) => update(e.target.value)}
              >
                <option value="">{t("selectAgent")}</option>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.name}>
                    {agent.name}
                  </option>
                ))}
              </select>
            ) : field.kind === "textarea" ? (
              <Textarea
                id={fieldId}
                rows={3}
                maxLength={field.maxLength}
                value={value}
                onChange={(e) => update(e.target.value)}
              />
            ) : (
              <Input
                id={fieldId}
                maxLength={field.maxLength}
                value={value}
                onChange={(e) => update(e.target.value)}
              />
            )}
          </Field>
        );
      })}
    </div>
  );
}
