"use client";

import { useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type UploadState = "idle" | "uploading" | "success" | "error";

export function UploadForm({
  collectionId,
  onUploaded,
}: {
  collectionId: number;
  onUploaded: () => void;
}) {
  const t = useTranslations("knowledge");
  const { data: session } = useSession();
  const inputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<UploadState>("idle");

  async function handleUpload() {
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    setState("uploading");
    const client = browserFleetClient(session?.accessToken);
    // The generated multipart schema types `file` as `string` (OpenAPI has no
    // binary-file TS representation); openapi-fetch's own documented pattern
    // for uploads is to pass the real File through unsafely-cast and build the
    // actual FormData in bodySerializer.
    const { error } = await client.POST("/v1/documents", {
      params: { query: { collection_id: collectionId } },
      body: { file: file as unknown as string },
      bodySerializer: () => {
        const form = new FormData();
        form.append("file", file);
        return form;
      },
    });

    if (error) {
      setState("error");
      return;
    }
    setState("success");
    if (inputRef.current) inputRef.current.value = "";
    onUploaded();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("upload")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm text-[var(--muted-foreground)]">{t("uploadPrompt")}</p>
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="file"
            className="text-sm"
            disabled={state === "uploading"}
          />
          <Button size="sm" onClick={handleUpload} disabled={state === "uploading"}>
            {state === "uploading" ? t("uploading") : t("upload")}
          </Button>
        </div>
        {state === "success" && (
          <p className="text-sm text-green-700 dark:text-green-400">{t("uploadSuccess")}</p>
        )}
        {state === "error" && (
          <p className="text-sm text-[var(--danger)]">{t("uploadError")}</p>
        )}
      </CardContent>
    </Card>
  );
}
