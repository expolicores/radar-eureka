import { formatCop, formatDate } from "../../lib/format";

type Evidence = {
  source_stage: string;
  source_document: string;
  source_page: number | null;
  extraction_method: string;
  evidence_text: string;
};
type Alternative = {
  value: string;
  value_origin: string;
  confidence: string;
  source_stage: string;
  bidder?: string | null;
  evidence: Evidence[];
  calculation_inputs?: { field: string; value: string }[];
};
export type EconomicCycleData = {
  document_coverage: {
    document: string;
    stage: string;
    extraction_status: string;
    coverage_complete: boolean | null;
    pages_with_text: number[];
  }[];
  products: {
    id: string;
    item_description: string;
    normalized_product: string;
    quantity: string | null;
    brand: string | null;
    model: string | null;
    conflict_status: string;
    conflicts: string[];
    notes: string[];
    requires_manual_review: boolean;
    purchase_price: { column: string; value: string; origin: string } | null;
    purchase_date?: string | null;
    fields: Record<string, { value: string | null; status: string; alternatives: Alternative[] }>;
  }[];
};

const STAGES: Record<string, string> = {
  studies_previous: "Estudios previos / mercado",
  invitation: "Invitación",
  technical_specification: "Especificaciones técnicas",
  economic_offer: "Oferta económica",
  evaluation_report: "Evaluación (no adjudicación)",
  award: "Adjudicación / aceptación",
  contract: "Contrato",
  amendment: "Modificación",
  other: "Otro",
  unknown: "Etapa desconocida",
};
const FIELDS: Record<string, string> = {
  quantity: "Cantidad",
  unit: "Unidad",
  brand: "Marca",
  model: "Modelo",
  budget_total: "Presupuesto del ítem",
  budget_unit_price: "Presupuesto unitario",
  offer_total: "Oferta del ítem",
  offer_unit_price: "Oferta unitaria",
  evaluated_offer_total: "Oferta evaluada del ítem",
  evaluated_offer_unit_price: "Unitario evaluado (no confirma aceptación)",
  awarded_total: "Adjudicación del ítem",
  awarded_unit_price: "Unitario adjudicado",
  contract_total: "Contrato del ítem",
  contract_unit_price: "Unitario contractual",
  bidder: "Oferente",
  awarded_supplier: "Proveedor adjudicado",
  evaluated_bidder: "Oferente evaluado",
  contracted_supplier: "Proveedor contratado",
};
const STATUSES: Record<string, string> = {
  absent: "Sin evidencia",
  confirmed: "Consistente en la evidencia disponible",
  uncertain: "Alternativas sin resolver",
  conflicting: "Evidencia conflictiva",
};
const amount = (key: string, value: string) =>
  key.endsWith("total") || key.endsWith("unit_price") ? formatCop(Number(value)) : value;

export function EconomicCycle({ cycle }: { cycle: EconomicCycleData }) {
  return (
    <section aria-label="Reconstrucción económica por producto">
      <h3 style={{ marginTop: 20 }}>Reconstrucción económica por producto y etapa</h3>
      <p className="muted">
        Presupuestos y ofertas sin aceptación son contexto. Los valores globales del proceso no se
        distribuyen entre productos. Una evaluación o recomendación no confirma adjudicación.
      </p>
      <details>
        <summary>Cobertura documental por etapa</summary>
        {cycle.document_coverage.map((d, index) => (
          <p key={index}>
            <strong>{STAGES[d.stage] ?? d.stage}</strong> · {d.document} · {d.extraction_status}
            {d.coverage_complete === false ? " · Cobertura parcial" : ""}
            {d.pages_with_text.length
              ? ` · Páginas con texto: ${d.pages_with_text.join(", ")}`
              : " · Sin texto disponible"}
          </p>
        ))}
      </details>
      {!cycle.products.length && (
        <p>
          No se pudo reconstruir un ítem determinísticamente con los fragmentos disponibles.
          Requiere revisión manual.
        </p>
      )}
      {cycle.products.map((item) => (
        <details className="card" key={item.id}>
          <summary>
            {item.item_description.slice(0, 180)} ·{" "}
            {item.requires_manual_review ? "Revisión manual" : "Precio de compra verificable"}
          </summary>
          <p>{item.item_description}</p>
          <p>
            Precio de compra:{" "}
            {item.purchase_price
              ? `${amount(item.purchase_price.column, item.purchase_price.value)} (${item.purchase_price.origin === "calculated" ? "calculado" : "explícito"})`
              : "Desconocido"}
          </p>
          <p>Fecha de compra verificada: {item.purchase_date ? formatDate(item.purchase_date) : "Desconocida"}.</p>
          {!!item.conflicts.length && (
            <p role="note">
              Evidencia conflictiva: {item.conflicts.map((f) => FIELDS[f] ?? f).join(", ")}. Se
              conservan las alternativas.
            </p>
          )}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Campo</th>
                  <th>Valor del ítem</th>
                  <th>Evidencia y provenance</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(FIELDS).map(([key, label]) => {
                  const field = item.fields[key];
                  return (
                    <tr key={key}>
                      <td>{label}</td>
                      <td>
                        {field?.value ? amount(key, field.value) : "Desconocido"}
                        <br />
                        <small>{STATUSES[field?.status ?? "absent"] ?? "Sin evidencia"}</small>
                      </td>
                      <td>
                        {field?.alternatives.map((a, index) => (
                          <details key={index}>
                            <summary>
                              {amount(key, a.value)} ·{" "}
                              {a.value_origin === "calculated" ? "Calculado" : "Explícito"} ·{" "}
                              {STAGES[a.source_stage] ?? a.source_stage}
                            </summary>
                            {a.bidder && <p>Oferente: {a.bidder}</p>}
                            <p>Confianza de extracción: {a.confidence}</p>
                            {!!a.calculation_inputs?.length && (
                              <p>
                                Fórmula: total del ítem / cantidad del mismo ítem. Entradas:{" "}
                                {a.calculation_inputs
                                  .map((i) => `${i.field}=${i.value}`)
                                  .join("; ")}
                              </p>
                            )}
                            {a.evidence.map((e, j) => (
                              <div key={j}>
                                <p>
                                  {e.source_document} · página {e.source_page ?? "no determinada"} ·{" "}
                                  {e.extraction_method}
                                </p>
                                <blockquote>{e.evidence_text}</blockquote>
                              </div>
                            ))}
                          </details>
                        ))}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <details>
            <summary>Advertencias y límites de asociación</summary>
            <p>{item.notes.join(" · ") || "Sin advertencias adicionales"}</p>
          </details>
        </details>
      ))}
    </section>
  );
}
