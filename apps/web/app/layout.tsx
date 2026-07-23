import { NextIntlClientProvider } from "next-intl";
import { getLocale } from "next-intl/server";
import { SessionProvider } from "next-auth/react";
import { auth } from "@/lib/auth";
import { AppShell } from "@/components/app-shell";
import { ToastProvider } from "@/components/ui/toast";
import "./globals.css";

export const metadata = {
  title: "Fleet",
  description: "Internal AI operations platform",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const session = await auth();

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider>
          <SessionProvider session={session}>
            <ToastProvider>
              <AppShell>{children}</AppShell>
            </ToastProvider>
          </SessionProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
