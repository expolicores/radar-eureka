// Presentation labels only. Decisions and numbers always come from the receipt.
const quality: Record<string, string> = {
  api_verified_price: "API verificada",
  page_verified_price: "Página verificada",
  shopping_provider_price: "Proveedor de shopping",
  snippet_price: "Snippet / evidencia débil",
};
const rejection: Record<string, string> = {
  wrong_model: "Modelo diferente",
  wrong_size: "Tamaño diferente",
  wrong_product_type: "Tipo de producto diferente",
  wrong_brand: "Marca diferente",
  accessory_or_replacement: "Accesorio o repuesto",
  no_price: "Sin precio verificable",
  ambiguous_price: "Precio ambiguo",
  generic_page: "Página general",
  unavailable: "No disponible",
  blocked: "Acceso bloqueado",
  stale_or_cache_only: "Evidencia cacheada/no verificada",
  verification_failed: "No fue posible verificar",
  currency_unknown: "Moneda no confirmada",
};
const limitations: Record<string, string> = {
  offer_acceptance_not_confirmed:
    "El precio público es una oferta documentada; aceptación/adjudicación no confirmada.",
  tax_basis_not_aligned_no_price_difference_calculated:
    "Base tributaria no alineada: no se calcula diferencia sin homologar impuestos.",
  document_process_reference_mismatch:
    "Conflicto documental: el encabezado menciona otro código de proceso; requiere verificación manual.",
  insufficient_market_evidence:
    "Evidencia privada insuficiente: faltan observaciones monetarias válidas.",
  limited_retailer_diversity: "Diversidad de tiendas limitada.",
  availability_unknown: "Disponibilidad no confirmada.",
  marketplace_concentrated_evidence_not_diverse_benchmark:
    "Evidencia concentrada en marketplace; no equivale a fuentes diversas.",
  scout_insufficient: "Scout no aportó suficientes ofertas verificables.",
  scout_degraded: "Scout no estuvo disponible; se conserva la evidencia restante.",
  "shopping:partial_provider_response":
    "El proveedor entregó detalles parciales de algún producto.",
  "shopping:product_without_stores": "Algún producto no devolvió tiendas.",
  "shopping:page_token_absent": "Algún producto no permitió consultar tiendas adicionales.",
};
export const evidenceLabel = (value?: string) => quality[value ?? ""] ?? "Calidad no registrada";
export const rejectionLabel = (value: string) => rejection[value] ?? value;
export const limitationLabel = (value: string) => limitations[value] ?? value;
export function sufficiencyLabel(value?: string, status?: string) {
  if (["sufficient_diverse", "sufficient_diverse_market_evidence"].includes(value ?? ""))
    return "Evidencia suficiente y diversa";
  if (["marketplace_concentrated", "marketplace_concentrated_evidence"].includes(value ?? ""))
    return "Evidencia concentrada en marketplace";
  if (value === "limited_source_diversity") return "Diversidad de fuentes limitada";
  if (value === "insufficient_market_evidence" || status === "insufficient_market_evidence")
    return "Evidencia de mercado insuficiente";
  return "Suficiencia no registrada";
}
