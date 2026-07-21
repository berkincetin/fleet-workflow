import { createFleetClient } from "@fleet/shared";
import { auth } from "@/lib/auth";

const API_BASE_URL = process.env.FLEET_API_BASE_URL ?? "http://localhost:8000";

/** Server-side Fleet API client bound to the current session's access token. */
export async function fleetClient() {
  const session = await auth();
  return createFleetClient({ baseUrl: API_BASE_URL, accessToken: session?.accessToken });
}
