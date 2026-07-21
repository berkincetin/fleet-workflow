"use client";

import { createFleetClient } from "@fleet/shared";

const API_BASE_URL = process.env.NEXT_PUBLIC_FLEET_API_BASE_URL ?? "http://localhost:8000";

/** Browser-side Fleet API client — pass the session's access token per call. */
export function browserFleetClient(accessToken?: string) {
  return createFleetClient({ baseUrl: API_BASE_URL, accessToken });
}
