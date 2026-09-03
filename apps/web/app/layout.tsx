import { NextIntlClientProvider } from "next-intl";
import { getLocale } from "next-intl/server";
import { cookies } from "next/headers";
import { SessionProvider } from "next-auth/react";
import { auth } from "@/lib/auth";
import { AppShell } from "@/components/app-shell";
import { ToastProvider } from "@/components/ui/toast";
import { parseTheme, THEME_COOKIE, themeAttribute } from "@/lib/theme";
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
  const cookieStore = await cookies();
  const theme = parseTheme(cookieStore.get(THEME_COOKIE)?.value);

  return (
    <html lang={locale} data-theme={themeAttribute(theme)}>
      <body>
        <NextIntlClientProvider>
          <SessionProvider session={session}>
            <ToastProvider>
              <AppShell theme={theme}>{children}</AppShell>
            </ToastProvider>
          </SessionProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
