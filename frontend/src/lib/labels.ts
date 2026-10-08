/** Etiquetas de presentación de códigos que entrega la API. */
export const SOURCE_LABELS: Record<string, string> = { secop_ii: "SECOP II", tvec: "TVEC" };

export const MATCH_TYPE_LABELS: Record<string, string> = {
  same_model: "Mismo modelo",
  equivalent: "Equivalente",
};

export const STORE_LABELS: Record<string, string> = {
  alkosto: "Alkosto",
  falabella: "Falabella",
};

export const METHOD_LABELS: Record<string, string> = {
  simulated: "Simulado (demo)",
  sitemap: "Sitemap / datos estructurados",
  structured_data: "Sitemap / datos estructurados",
  manual: "✎ Observación manual",
};

export const VAT_LABELS: Record<string, string> = {
  included: "IVA incluido",
  excluded: "Sin IVA",
  undetermined: "IVA indeterminado",
};

export const CLASSIFICATION_LABELS: Record<string, string> = {
  included: "Incluido",
  excluded_accessory: "Excluido · accesorio",
  excluded_service: "Excluido · servicio",
  undetermined: "Clasificación dudosa",
};

export const PRICE_STATUS_LABELS: Record<string, string> = {
  explicit: "explícito",
  derived: "derivado",
  not_published: "no publicado",
  pending_review: "en revisión",
};

export const OUTCOME_LABELS: Record<string, string> = {
  signal: "⚑ Señal",
  no_signal: "✓ Comparado · sin señal",
  low_price_review: "◐ Precio bajo · revisión de calidad",
  insufficient_comparables: "Comparables insuficientes",
  vat_incomplete: "IVA no comparable",
  no_unit_price: "Sin precio unitario",
  quality_review: "◐ En revisión de calidad",
};
