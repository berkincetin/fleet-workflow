"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import type { components } from "@fleet/shared";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DocumentStatusBadge } from "@/components/knowledge/document-status-badge";
import { UploadForm } from "@/components/knowledge/upload-form";

type Collection = components["schemas"]["CollectionOut"];
type Document = components["schemas"]["DocumentOut"];

// Ingestion is asynchronous (arq); documents move pending/queued -> ready|error.
// Poll while any listed document is still in flight so status updates live
// without a manual refresh (AC 3.4).
const POLL_INTERVAL_MS = 2000;
const IN_FLIGHT_STATUSES = new Set(["pending", "queued"]);

export function KnowledgeBrowser({ initialCollections }: { initialCollections: Collection[] }) {
  const t = useTranslations("knowledge");
  const { data: session } = useSession();
  const [collections] = useState(initialCollections);
  const [selectedId, setSelectedId] = useState<number | null>(
    initialCollections[0]?.id ?? null,
  );
  const [documents, setDocuments] = useState<Document[]>([]);

  const loadDocuments = useCallback(
    async (collectionId: number) => {
      const client = browserFleetClient(session?.accessToken);
      const { data } = await client.GET("/v1/documents", {
        params: { query: { collection_id: collectionId } },
      });
      setDocuments(data ?? []);
    },
    [session?.accessToken],
  );

  useEffect(() => {
    if (selectedId == null) return;
    loadDocuments(selectedId);
  }, [selectedId, loadDocuments]);

  useEffect(() => {
    if (selectedId == null || session?.error) return;
    const hasInFlight = documents.some((d) => IN_FLIGHT_STATUSES.has(d.status));
    if (!hasInFlight) return;
    const timer = setInterval(() => loadDocuments(selectedId), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [selectedId, documents, loadDocuments, session?.error]);

  if (collections.length === 0) {
    return <p className="text-sm text-[var(--muted-foreground)]">{t("noCollections")}</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      <Card className="md:col-span-1">
        <CardHeader>
          <CardTitle>{t("collections")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-1">
          {collections.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedId(c.id)}
              className={`rounded-md px-3 py-2 text-left text-sm ${
                selectedId === c.id
                  ? "bg-[var(--muted)] font-medium"
                  : "hover:bg-[var(--muted)]"
              }`}
            >
              {c.name}
            </button>
          ))}
        </CardContent>
      </Card>

      <div className="flex flex-col gap-4 md:col-span-2">
        {selectedId != null && (
          <>
            <UploadForm
              collectionId={selectedId}
              onUploaded={() => loadDocuments(selectedId)}
            />
            <Card>
              <CardHeader>
                <CardTitle>{t("documents")}</CardTitle>
              </CardHeader>
              <CardContent>
                {documents.length === 0 ? (
                  <p className="text-sm text-[var(--muted-foreground)]">{t("noDocuments")}</p>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {documents.map((doc) => (
                      <li
                        key={doc.id}
                        className="flex items-center justify-between rounded-md border border-[var(--border)] px-3 py-2"
                      >
                        <span className="truncate text-sm">{doc.uri}</span>
                        <DocumentStatusBadge status={doc.status} />
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
