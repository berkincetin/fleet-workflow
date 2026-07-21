import NextAuth from "next-auth";
import Keycloak from "next-auth/providers/keycloak";

const KEYCLOAK_ISSUER =
  process.env.KEYCLOAK_ISSUER ?? "http://localhost:8080/realms/fleet";
const KEYCLOAK_CLIENT_ID = process.env.KEYCLOAK_CLIENT_ID ?? "fleet-api";
const KEYCLOAK_CLIENT_SECRET =
  process.env.KEYCLOAK_CLIENT_SECRET ?? "fleet-api-dev-secret";

async function refreshAccessToken(refreshToken: string) {
  const resp = await fetch(`${KEYCLOAK_ISSUER}/protocol/openid-connect/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: KEYCLOAK_CLIENT_ID,
      client_secret: KEYCLOAK_CLIENT_SECRET,
      refresh_token: refreshToken,
    }),
  });
  if (!resp.ok) {
    throw new Error(`refresh failed: ${resp.status}`);
  }
  return (await resp.json()) as {
    access_token: string;
    expires_in: number;
    refresh_token?: string;
  };
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Keycloak({
      clientId: KEYCLOAK_CLIENT_ID,
      clientSecret: KEYCLOAK_CLIENT_SECRET,
      issuer: KEYCLOAK_ISSUER,
    }),
  ],
  callbacks: {
    // Keycloak access tokens are short-lived (~5 min); the Knowledge UI polls
    // for live ingestion status over a session that easily outlasts that, so
    // the token is refreshed here rather than left to expire mid-session.
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.accessTokenExpires = Date.now() + (account.expires_in as number) * 1000;
        return token;
      }

      if (token.accessTokenExpires && Date.now() < (token.accessTokenExpires as number) - 5000) {
        return token;
      }

      if (!token.refreshToken) {
        return token;
      }

      try {
        const refreshed = await refreshAccessToken(token.refreshToken as string);
        token.accessToken = refreshed.access_token;
        token.accessTokenExpires = Date.now() + refreshed.expires_in * 1000;
        token.refreshToken = refreshed.refresh_token ?? token.refreshToken;
      } catch {
        token.accessTokenError = "RefreshAccessTokenError";
      }
      return token;
    },
    async session({ session, token }) {
      if (token.accessToken) {
        session.accessToken = token.accessToken as string;
      }
      if (token.accessTokenError) {
        session.error = token.accessTokenError as string;
      }
      return session;
    },
  },
  session: { strategy: "jwt" },
});
