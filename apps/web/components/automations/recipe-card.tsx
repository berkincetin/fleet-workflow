"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useTranslations } from "next-intl";
import { Pencil, Trash2 } from "lucide-react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import { RecipeSummary } from "@/components/automations/recipe-summary";
import { can } from "@/lib/permissions";
import type { components } from "@fleet/shared";

type RecipeOut = components["schemas"]["RecipeOut"];

/** A user-defined automation on the Automations page (task 13.5). Mirrors
 * WorkflowCard's affordances for the built-in catalog, plus edit/delete. */
export function RecipeCard({
  recipe,
  roles,
}: {
  recipe: RecipeOut;
  roles: string[] | undefined;
}) {
  const t = useTranslations("automations");
  const tCommon = useTranslations("common");
  const router = useRouter();
  const { data: session } = useSession();
  const { show } = useToast();
  const [state, setState] = useState(recipe);
  const [busy, setBusy] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const canOperate = can(roles, "manage_agents");

  async function toggleActive() {
    setBusy(true);
    const client = browserFleetClient(session?.accessToken);
    const path = state.active
      ? "/v1/recipes/{recipe_id}/deactivate"
      : "/v1/recipes/{recipe_id}/activate";
    const { data, error } = await client.POST(path, {
      params: { path: { recipe_id: state.id } },
    });
    setBusy(false);
    if (error || !data || data.status !== "ok") {
      show(data?.detail ?? t("runUnreachable"), "error");
      return;
    }
    setState((prev) => ({ ...prev, active: !prev.active }));
  }

  async function run() {
    setBusy(true);
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/recipes/{recipe_id}/run", {
      params: { path: { recipe_id: state.id } },
    });
    setBusy(false);
    if (error || !data) {
      show(t("runUnreachable"), "error");
      return;
    }
    if (data.status === "ok") show(t("runAccepted"), "success");
    else if (data.status === "not_deployed") show(t("runInactive"), "error");
    else show(t("runUnreachable"), "error");
  }

  async function remove() {
    setConfirmOpen(false);
    setBusy(true);
    const client = browserFleetClient(session?.accessToken);
    const { error } = await client.DELETE("/v1/recipes/{recipe_id}", {
      params: { path: { recipe_id: state.id } },
    });
    setBusy(false);
    if (error) {
      show(t("deleteError"), "error");
      return;
    }
    show(t("deleted"), "success");
    router.refresh();
  }

  return (
    // A stable hook for the e2e: matching a card by its rendered class list is
    // brittle, and the recipe name alone appears in several places on the page.
    <Card data-testid={`recipe-${state.name}`}>
      <CardHeader className="flex-row items-start justify-between gap-2">
        <CardTitle className="font-mono">{state.name}</CardTitle>
        {state.n8n_workflow_id === null ? (
          <Badge variant="error">{t("notDeployed")}</Badge>
        ) : state.active ? (
          <Badge variant="success">{t("statusActive")}</Badge>
        ) : (
          <Badge variant="pending">{t("statusInactive")}</Badge>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {state.description && (
          <p className="text-sm text-[var(--muted-foreground)]">{state.description}</p>
        )}
        <RecipeSummary summary={state.summary as Record<string, unknown>[]} />
        {state.deploy_error && (
          <p className="text-sm text-[var(--danger)]">{t("deployFailed")}</p>
        )}

        {canOperate && (
          <div className="flex flex-wrap items-center gap-2">
            <Button size="sm" onClick={run} disabled={busy || !state.active}>
              {tCommon("runNow")}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={toggleActive}
              disabled={busy || state.n8n_workflow_id === null}
            >
              {state.active ? t("deactivate") : t("activate")}
            </Button>
            <Button size="sm" variant="outline" asChild>
              <Link href={`/automations/${state.id}/edit`}>
                <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
                {t("editRecipe")}
              </Link>
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setConfirmOpen(true)} disabled={busy}>
              <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
              {t("deleteRecipe")}
            </Button>
          </div>
        )}

        {/* An in-app confirmation rather than window.confirm: a native dialog
            cannot be styled, is invisible to the theme, and blocks the whole
            renderer thread. */}
        <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
          <DialogContent aria-describedby={`confirm-${state.id}`}>
            <DialogHeader>
              <DialogTitle>{t("deleteRecipe")}</DialogTitle>
              <DialogDescription id={`confirm-${state.id}`}>
                {t("deleteConfirm")}
              </DialogDescription>
            </DialogHeader>
            <div className="flex justify-end gap-2">
              <DialogClose asChild>
                <Button size="sm" variant="outline">
                  {tCommon("cancel")}
                </Button>
              </DialogClose>
              <Button size="sm" variant="danger" onClick={remove} disabled={busy}>
                {tCommon("delete")}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
