"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { browserFleetClient } from "@/lib/fleet-client-browser";
import { useToast } from "@/components/ui/toast";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import type { components } from "@fleet/shared";

type ModelOut = components["schemas"]["ModelOut"];

const badgeVariant = (status: string): "success" | "pending" | "error" =>
  status === "ok" ? "success" : status === "pending" ? "pending" : "error";

export function ModelsAdmin({ initialModels }: { initialModels: ModelOut[] }) {
  const t = useTranslations("admin");
  const { data: session } = useSession();
  const { show } = useToast();
  const [models, setModels] = useState(initialModels);
  const [form, setForm] = useState({
    name: "",
    provider: "",
    litellm_model_id: "",
    input_price_per_1k: "0",
    output_price_per_1k: "0",
    context_window: "8000",
    max_output_tokens: "1000",
    sensitivity_clearance: "internal",
  });

  async function addModel() {
    const client = browserFleetClient(session?.accessToken);
    const { data, error } = await client.POST("/v1/admin/models", {
      body: {
        name: form.name,
        provider: form.provider,
        litellm_model_id: form.litellm_model_id,
        input_price_per_1k: Number(form.input_price_per_1k),
        output_price_per_1k: Number(form.output_price_per_1k),
        context_window: Number(form.context_window),
        max_output_tokens: Number(form.max_output_tokens),
        sensitivity_clearance: form.sensitivity_clearance,
      },
    });
    if (error || !data) {
      show(t("addModel"), "error");
      return;
    }
    setModels((prev) => [...prev, data]);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("modelsTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Input placeholder={t("name")} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="provider" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} />
          <Input placeholder="litellm_model_id" value={form.litellm_model_id} onChange={(e) => setForm({ ...form, litellm_model_id: e.target.value })} />
          <Button size="sm" onClick={addModel}>
            {t("addModel")}
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("name")}</TableHead>
              <TableHead>{t("smokeStatus")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {models.map((m) => (
              <TableRow key={m.id}>
                <TableCell>{m.name}</TableCell>
                <TableCell>
                  <Badge variant={badgeVariant(m.smoke_status)}>{m.smoke_status}</Badge>
                  {m.smoke_latency_ms != null && (
                    <span className="ml-2 text-xs text-[var(--muted-foreground)]">
                      {m.smoke_latency_ms}ms
                    </span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
