import "next-auth";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    error?: string;
    /** Keycloak realm roles (task 6.5.5) — nav gating only; the API is the
     * real enforcement point regardless of what the UI shows/hides. */
    roles?: string[];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    accessTokenError?: string;
    roles?: string[];
  }
}
