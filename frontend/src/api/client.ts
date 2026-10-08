/** Cliente tipado de la API, generado desde el contrato OpenAPI del backend (`npm run generate:api`). */
import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

export type PurchaseSummary = components["schemas"]["PurchaseSummary"];
export type PurchaseList = components["schemas"]["PurchaseList"];
export type PurchaseDetail = components["schemas"]["PurchaseDetail"];
export type FilterOptions = components["schemas"]["FilterOptions"];
export type AnalysisStatus = PurchaseSummary["analysis_status"];
export type Source = PurchaseSummary["source"];

export type PurchaseQuery = NonNullable<paths["/api/v1/purchases"]["get"]["parameters"]["query"]>;

export type Signal = components["schemas"]["Signal"];
export type SignalList = components["schemas"]["SignalList"];
export type SignalSummary = components["schemas"]["SignalSummaryResponse"];
export type ConfidenceLevel = Signal["confidence_level"];
export type SignalDetail = components["schemas"]["SignalDetailResponse"];
export type CaseSummary = components["schemas"]["CaseSummaryResponse"];
export type CaseDetail = components["schemas"]["CaseDetailResponse"];
export type CaseItemKind = components["schemas"]["CaseItemCreate"]["kind"];
export type SignalQuery = NonNullable<paths["/api/v1/signals"]["get"]["parameters"]["query"]>;

/** Error de la API con el *problem details* que devolvió el backend. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly title: string,
  ) {
    super(title);
    this.name = "ApiError";
  }
}

export const api = createClient<paths>({
  // Mismo origen que la SPA (en desarrollo, el proxy de Vite lleva /api al backend).
  baseUrl: globalThis.location.origin,
  // Resuelve `fetch` en cada llamada: permite simularlo en las pruebas.
  fetch: (request) => globalThis.fetch(request),
});

/** Devuelve los datos o lanza `ApiError`; las vistas muestran su propio mensaje en español. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.data === undefined) {
    const problem = result.error as { title?: string } | undefined;
    throw new ApiError(result.response.status, problem?.title ?? "Error");
  }
  return result.data;
}
