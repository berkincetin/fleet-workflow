"use client";

import { useTranslations } from "next-intl";
import { Badge, type BadgeProps } from "@/components/ui/badge";

const VARIANT_BY_STATUS: Record<string, BadgeProps["variant"]> = {
  pending: "pending",
  queued: "pending",
  ready: "success",
  error: "error",
};

export function DocumentStatusBadge({ status }: { status: string }) {
  const t = useTranslations("knowledge.status");
  const label = (() => {
    switch (status) {
      case "pending":
        return t("pending");
      case "queued":
        return t("queued");
      case "ready":
        return t("ready");
      case "error":
        return t("error");
      default:
        return status;
    }
  })();

  return <Badge variant={VARIANT_BY_STATUS[status] ?? "default"}>{label}</Badge>;
}
