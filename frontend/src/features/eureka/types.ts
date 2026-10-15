import type { components } from "../../api/schema";
import { formatCop } from "../../lib/format";

export type EurekaList = components["schemas"]["EurekaListResponse"];
export type EurekaDetail = components["schemas"]["EurekaDetailResponse"];
export type Evidence = components["schemas"]["EurekaEvidenceResponse"];
export const priorityLabels: Record<string, string> = {
  high: "Alta",
  medium: "Media",
  low: "Baja",
};
export const categoryLabels: Record<string, string> = {
  packaged_food: "Alimentos empacados",
  office_supplies: "Papelería",
  basic_technology: "Tecnología básica",
  cleaning_cafeteria: "Aseo y cafetería",
  printing_customization: "Impresión",
  furniture_supplies: "Mobiliario",
  prepared_snacks: "Refrigerios preparados",
};
export const enrichmentLabels: Record<string, string> = {
  not_extracted: "Sin extracción",
  extracted: "Texto extraído",
  structured: "Hechos estructurados",
  consolidated: "Información consolidada",
  conflict: "Conflicto documental",
};
export const missingLabels: Record<string, string> = {
  RUP_REQUIRED: "RUP no determinado",
  EXPERIENCE_REQUIRED: "Experiencia no determinada",
  DELIVERY_COUNT: "Número de entregas no determinado",
};
export function obj(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}
export function arr(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}
export function str(value: unknown): string {
  return typeof value === "string" || typeof value === "number" ? String(value) : "No determinado";
}

export function productLabel(value: unknown): string {
  const name = str(value);
  return name
    .split(" ")
    .map((word, index) =>
      index === 0 || (index === 1 && name.toLowerCase().startsWith("jugo "))
        ? word.charAt(0).toUpperCase() + word.slice(1)
        : word,
    )
    .join(" ");
}
export function factValue(value: unknown): unknown {
  return obj(value).value;
}
export function money(value: unknown): string {
  return (typeof value === "number" || typeof value === "string") && Number.isFinite(Number(value))
    ? `${formatCop(Number(value))} COP`
    : "No determinado";
}
export function requirement(value: unknown): string {
  return value === "not_required"
    ? "No requerida"
    : value === "required"
      ? "Requerida"
      : "No determinada";
}
export function term(value: unknown): string {
  const data = obj(value);
  if (data.value == null) return "No determinado";
  return `${str(data.value)} días ${data.kind === "calendar" ? "calendario" : data.kind === "business" ? "hábiles" : "(tipo no determinado)"}${data.trigger ? ` · ${str(data.trigger)}` : ""}`;
}
export function location(value: unknown): string {
  const loc = obj(value);
  return (
    [
      loc.page_number ? `página ${str(loc.page_number)}` : "",
      loc.paragraph_number ? `párrafo ${str(loc.paragraph_number)}` : "",
      loc.table_number ? `tabla ${str(loc.table_number)}` : "",
      loc.row_number ? `fila ${str(loc.row_number)}` : "",
      loc.column_number ? `columna ${str(loc.column_number)}` : "",
      loc.sheet_name ? `hoja ${str(loc.sheet_name)}` : "",
      loc.cell_range ? `celda ${str(loc.cell_range)}` : "",
    ]
      .filter(Boolean)
      .join(" · ") || "Localizador no disponible"
  );
}
