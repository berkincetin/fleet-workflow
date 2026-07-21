import { NextIntlClientProvider } from "next-intl";
import { getLocale } from "next-intl/server";
import { SessionProvider } from "next-auth/react";
import { auth } from "@/lib/auth";
import { NavBar } from "@/components/nav-bar";
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
            <NavBar />
            <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
          </SessionProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
