"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useTranslations } from "next-intl";
import { Eye, EyeOff, ExternalLink, RefreshCw } from "lucide-react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/layout/empty-state";
import { useToast } from "@/components/ui/toast";
import type { components } from "@fleet/shared";

type ServicesOut = components["schemas"]["ServicesOut"];
type ServiceOut = components["schemas"]["ServiceOut"];
type RevealedCredentialOut = components["schemas"]["RevealedCredentialOut"];

const GROUP_ORDER = ["core", "provider", "automation", "worker", "observability"];

function statusVariant(service: ServiceOut) {
  if (service.status === "healthy") return "success" as const;
  if (service.optional) return "pending" as const;
  if (service.status === "unknown") return "default" as const;
  return "error" as const;
}

/**
 * Admin -> Services (task 13.3).
 *
 * The whole board is refetched on demand rather than polled: this screen is
 * opened to answer a question ("did the stack come up?"), and a background
 * poll firing HTTP probes at fifteen services would be a real cost for no
 * benefit while nobody is looking.
 *
 * Credentials arrive masked. Revealing one is an explicit per-service request
 * to `POST /v1/admin/services/{name}/reveal` — the plaintext never rides along
 * with the page load, so it is not in the HTML, not in the RSC payload, and
 * not in a `platform_admin`'s browser until they ask for it.
 */
export function ServicesBoard({
  initial,
  canReveal,
}: {
  initial: ServicesOut | null;
  canReveal: boolean;
}) {
  const t = useTranslations("services");
  const tAdmin = useTranslations("admin");
  const tCommon = useTranslations("common");
  const { data: session } = useSession();
  const { show } = useToast();

  const [board, setBoard] = useState<ServicesOut | null>(initial);
  const [busy, setBusy] = useState(false);
  const [revealed, setRevealed] = useState<Record<string, RevealedCredentialOut[]>>({});

  async function refresh() {
    setBusy(true);
    const client = browserFleetClient(session?.accessToken);
    const { data } = await client.GET("/v1/admin/services");
    setBusy(false);
    if (data) setBoard(data);
    else show(tCommon("error"), "error");
  }

  async function toggleReveal(name: string) {
    if (revealed[name]) {
      setRevealed((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
      return;
    }
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/admin/services/{name}/reveal", {
      params: { path: { name } },
    });
    if (error || !data) {
      show(t("revealError"), "error");
      return;
    }
    setRevealed((prev) => ({ ...prev, [name]: data.credentials }));
  }

  if (!board) {
    return (
      <EmptyState icon={RefreshCw} title={t("emptyTitle")} description={t("emptyDesc")} />
    );
  }

  const groups = GROUP_ORDER.filter((g) => board.services.some((s) => s.group === g));

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm">
          <Badge variant="success">{t("healthyCount", { count: board.healthy })}</Badge>
          {board.down > 0 && (
            <Badge variant="error">{t("downCount", { count: board.down })}</Badge>
          )}
        </div>
        <Button size="sm" variant="outline" onClick={refresh} disabled={busy}>
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          {t("refresh")}
        </Button>
      </div>

      {!canReveal && (
        <p className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-xs text-[var(--muted-foreground)]">
          {t("revealRestricted")}
        </p>
      )}

      {groups.map((group) => (
        <section key={group} className="flex flex-col gap-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)]">
            {t(`groups.${group}`)}
          </h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {board.services
              .filter((s) => s.group === group)
              .map((service) => (
                <Card
                  key={service.name}
                  className={
                    service.status === "healthy" || service.optional
                      ? undefined
                      : "border-[var(--danger)]"
                  }
                >
                  <CardHeader className="flex-row items-start justify-between gap-2">
                    <CardTitle className="font-mono">{service.name}</CardTitle>
                    <Badge variant={statusVariant(service)}>
                      {service.status === "healthy"
                        ? t("statusHealthy")
                        : service.optional
                          ? t("statusNotRunning")
                          : service.status === "unknown"
                            ? t("statusUnknown")
                            : t("statusDown")}
                    </Badge>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-2">
                    <p className="text-sm text-[var(--muted-foreground)]">
                      {t.has(`purpose.${service.name}`)
                        ? t(`purpose.${service.name}`)
                        : t("purposeUnknown")}
                    </p>

                    <dl className="flex flex-col gap-1 text-xs text-[var(--muted-foreground)]">
                      {service.url && (
                        <div className="flex items-center gap-1">
                          <dt className="sr-only">{t("url")}</dt>
                          <dd>
                            <a
                              href={service.url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 font-mono text-[var(--link)] hover:underline"
                            >
                              {service.url}
                              <ExternalLink className="h-3 w-3" aria-hidden="true" />
                            </a>
                          </dd>
                        </div>
                      )}
                      {service.latency_ms !== null && service.latency_ms !== undefined && (
                        <div className="flex gap-1">
                          <dt>{t("latency")}:</dt>
                          <dd className="tabular-nums">{service.latency_ms} ms</dd>
                        </div>
                      )}
                      {service.queue_depth !== null && service.queue_depth !== undefined && (
                        <div className="flex gap-1">
                          <dt>{t("queueDepth")}:</dt>
                          <dd className="tabular-nums">{service.queue_depth}</dd>
                        </div>
                      )}
                      {service.detail && (
                        <div className="flex gap-1">
                          <dt>{t("detail")}:</dt>
                          <dd className="font-mono">{service.detail}</dd>
                        </div>
                      )}
                    </dl>

                    {service.optional && service.status !== "healthy" && (
                      <p className="text-xs text-[var(--warning)]">
                        {t.has(`optionalHint.${service.name}`)
                          ? t(`optionalHint.${service.name}`)
                          : t("optionalHintGeneric")}
                      </p>
                    )}

                    {service.has_credentials && (
                      <div className="flex flex-col gap-1.5 rounded-[var(--radius-md)] bg-[var(--surface-2)] p-2">
                        {(revealed[service.name] ?? service.credentials).map((cred) => (
                          <div key={cred.label} className="flex flex-col text-xs">
                            <span className="text-[var(--muted-foreground)]">{cred.label}</span>
                            <span className="break-all font-mono">
                              {cred.username ? `${cred.username} / ` : ""}
                              {"secret" in cred
                                ? (cred as RevealedCredentialOut).secret
                                : (cred as components["schemas"]["CredentialOut"]).secret_masked}
                            </span>
                          </div>
                        ))}
                        {canReveal && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="self-start"
                            onClick={() => toggleReveal(service.name)}
                          >
                            {revealed[service.name] ? (
                              <>
                                <EyeOff className="h-3.5 w-3.5" aria-hidden="true" />
                                {t("hide")}
                              </>
                            ) : (
                              <>
                                <Eye className="h-3.5 w-3.5" aria-hidden="true" />
                                {t("reveal")}
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
          </div>
        </section>
      ))}

      <p className="text-xs text-[var(--muted-foreground)]">{tAdmin("servicesFooter")}</p>
    </div>
  );
}
