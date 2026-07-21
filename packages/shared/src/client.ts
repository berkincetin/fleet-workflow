// Typed Fleet API client (CLAUDE.md: "API access only through packages/shared
// client"). Wraps openapi-fetch over the generated `paths` types so callers
// get compile-time-checked routes/bodies/responses without hand-written
// fetch boilerplate anywhere else in apps/web.
import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "./schema";

export function createFleetClient(opts: { baseUrl: string; accessToken?: string }) {
  const client = createClient<paths>({ baseUrl: opts.baseUrl });

  if (opts.accessToken) {
    const authMiddleware: Middleware = {
      async onRequest({ request }) {
        request.headers.set("Authorization", `Bearer ${opts.accessToken}`);
        return request;
      },
    };
    client.use(authMiddleware);
  }

  return client;
}

export type FleetClient = ReturnType<typeof createFleetClient>;
export type { paths, components } from "./schema";
