/**
 * Client-side mirror of `fleet_api.recipes.schema`'s action allowlist and per-
 * action parameter models (task 13.5).
 *
 * Same arrangement as lib/permissions.ts mirroring rbac.py: this drives the
 * builder's generated form only. The API re-validates every recipe against the
 * Pydantic models and the compiler refuses anything it does not recognise, so
 * a drift here is a worse form, never a weaker gate. Keep it in step with
 * `PARAMS_BY_ACTION` by hand.
 */

export const ACTION_NAMES = [
  "pg.query",
  "agent.run",
  "slack.post",
  "email.send",
  "http.notify",
] as const;

export type ActionName = (typeof ACTION_NAMES)[number];

export type FieldKind = "text" | "textarea" | "agent";

export interface ActionField {
  name: string;
  kind: FieldKind;
  maxLength: number;
}

export interface ActionSpec {
  fields: ActionField[];
  /** Mirrors WRITE_EXTERNAL_ACTIONS — drives the "needs approval" note. */
  writeExternal: boolean;
}

export const ACTIONS: Record<ActionName, ActionSpec> = {
  "pg.query": {
    fields: [{ name: "sql", kind: "textarea", maxLength: 4000 }],
    writeExternal: false,
  },
  "agent.run": {
    fields: [
      { name: "agent", kind: "agent", maxLength: 64 },
      { name: "question", kind: "textarea", maxLength: 4000 },
    ],
    writeExternal: false,
  },
  "slack.post": {
    fields: [
      { name: "channel", kind: "text", maxLength: 80 },
      { name: "text", kind: "textarea", maxLength: 4000 },
    ],
    writeExternal: false,
  },
  "email.send": {
    fields: [
      { name: "to", kind: "text", maxLength: 254 },
      { name: "subject", kind: "text", maxLength: 200 },
      { name: "body", kind: "textarea", maxLength: 8000 },
    ],
    writeExternal: true,
  },
  "http.notify": {
    fields: [
      { name: "title", kind: "text", maxLength: 200 },
      { name: "message", kind: "textarea", maxLength: 4000 },
    ],
    writeExternal: false,
  },
};

export const OPERATORS = ["eq", "ne", "gt", "gte", "lt", "lte", "contains"] as const;
export type Operator = (typeof OPERATORS)[number];

/** Mirrors `_RECIPE_NAME_RE`. */
export const RECIPE_NAME_RE = /^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$/;
/** Mirrors `_STEP_ID_RE`. */
export const STEP_ID_RE = /^[a-z0-9_]{1,64}$/;

/** A few ready-made schedules so the common case needs no cron knowledge. */
export const CRON_PRESETS: { key: string; cron: string }[] = [
  { key: "everyMorning", cron: "0 9 * * *" },
  { key: "everyMonday", cron: "0 9 * * 1" },
  { key: "everyMonthFirst", cron: "0 9 1 * *" },
  { key: "everyHour", cron: "0 * * * *" },
];

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[ıİ]/g, "i")
    .replace(/ş/g, "s")
    .replace(/ğ/g, "g")
    .replace(/ü/g, "u")
    .replace(/ö/g, "o")
    .replace(/ç/g, "c")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}
