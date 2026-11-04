import { Link } from "react-router";
import { formatCop } from "../../lib/format";
import { HumanReviewNotice } from "./HumanReviewNotice";

export type ReadinessAudit = {
  summary: {
    initial_pairs: number;
    unique_processes: number;
    unique_observations: number;
    pairs_ready: number;
  };
  pairs: {
    number: number;
    id: string;
    processes: [string, string];
    observation_ids: [string, string];
    process_code_a: string;
    process_code_b: string;
    comparability_level: string;
    price_a: string | null;
    price_b: string | null;
    status: string;
    blockers_a: string[];
    blockers_b: string[];
    requires_manual_review: boolean;
    human_review_recommended?: boolean;
    human_review_reasons?: string[];
  }[];
};

const LABELS: Record<string, string> = {
  ready: "Listo para comparar",
  missing_both_prices: "Falta precio de compra en ambos lados",
  missing_price_a: "Falta precio de compra A",
  missing_price_b: "Falta precio de compra B",
  conflict_a: "Conflicto en A",
  conflict_b: "Conflicto en B",
  technical_mismatch: "Incompatibilidad técnica",
  manual_review: "Revisión manual",
  human_review_recommended: "Revisión humana recomendada",
  verified_item_purchase_unit_price: "Unitario de compra atribuible al TV",
  proof_of_winning_offer_acceptance: "Prueba de aceptación de esta oferta e ítem",
  verified_purchase_quantity_and_unit: "Cantidad y unidad de la compra verificadas",
  purchase_price_provenance: "Evidencia del precio de compra",
  verified_purchase_date: "Fecha atribuible a la compra",
  local_economic_document: "Documento económico local",
  model_reused_for_incompatible_sizes: "Misma referencia con pulgadas incompatibles",
};

export function ComparisonReadiness({ audit }: { audit: ReadinessAudit }) {
  return (
    <section aria-label="Cierre económico de pares técnicos" className="notice">
      <p>
        {audit.summary.pairs_ready === 0
          ? `${audit.summary.initial_pairs} pares técnicamente comparables evaluados; ninguno alcanzó evidencia económica suficiente en ambos lados.`
          : `${audit.summary.pairs_ready} de ${audit.summary.initial_pairs} pares alcanzaron evidencia económica suficiente.`}
      </p>
      <p className="small muted">
        {audit.summary.unique_processes} procesos únicos · {audit.summary.unique_observations}{" "}
        observaciones. Solo evidencia local; sin ampliar el universo. Las repeticiones de un proceso
        corresponden a observaciones distintas.
      </p>
      <details>
        <summary>Ver matriz de bloqueo de los {audit.summary.initial_pairs} pares</summary>
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>Par</th>
                <th>Proceso A / observación</th>
                <th>Proceso B / observación</th>
                <th>Comparabilidad</th>
                <th>Precio compra A / B</th>
                <th>Resultado</th>
                <th>Falta en A</th>
                <th>Falta en B</th>
              </tr>
            </thead>
            <tbody>
              {audit.pairs.map((pair) => (
                <tr key={pair.id}>
                  <td>{pair.number}</td>
                  <td>
                    <Link to={`/explorar?process=${encodeURIComponent(pair.processes[0])}`}>
                      {pair.process_code_a}
                    </Link>
                    <div className="small muted">{pair.observation_ids[0].slice(0, 12)}</div>
                  </td>
                  <td>
                    <Link to={`/explorar?process=${encodeURIComponent(pair.processes[1])}`}>
                      {pair.process_code_b}
                    </Link>
                    <div className="small muted">{pair.observation_ids[1].slice(0, 12)}</div>
                  </td>
                  <td>{pair.comparability_level === "exact" ? "Exacta" : "Alta"}</td>
                  <td>
                    {pair.price_a === null ? "No recuperado" : formatCop(Number(pair.price_a))} /{" "}
                    {pair.price_b === null ? "No recuperado" : formatCop(Number(pair.price_b))}
                  </td>
                  <td>
                    {pair.human_review_recommended ? (
                      <HumanReviewNotice
                        review={{
                          human_review_recommended: true,
                          human_review_reasons: pair.human_review_reasons ?? [],
                        }}
                      />
                    ) : (
                      <>
                        {LABELS[pair.status] ?? pair.status}
                        {pair.requires_manual_review && (
                          <div className="small">Revisión manual</div>
                        )}
                      </>
                    )}
                  </td>
                  <td>{pair.blockers_a.map((b) => LABELS[b] ?? b).join(" · ") || "—"}</td>
                  <td>{pair.blockers_b.map((b) => LABELS[b] ?? b).join(" · ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}
