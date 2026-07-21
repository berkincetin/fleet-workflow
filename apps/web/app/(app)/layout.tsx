import { getTranslations } from "next-intl/server";
import { auth } from "@/lib/auth";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) {
    const t = await getTranslations("auth");
    return (
      <p className="text-sm text-[var(--muted-foreground)]">{t("signInPrompt")}</p>
    );
  }
  return <>{children}</>;
}
