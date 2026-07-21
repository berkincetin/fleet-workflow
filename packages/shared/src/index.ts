// Re-export the generated OpenAPI types. Regenerate with `make client`.
export type { paths, components } from "./schema";
export { createFleetClient } from "./client";
export type { FleetClient } from "./client";
