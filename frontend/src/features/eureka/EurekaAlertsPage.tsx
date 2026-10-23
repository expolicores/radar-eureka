import { Link, useParams, useSearchParams } from "react-router";
import { Pagination } from "../../components/Pagination";
import { formatBogotaNumericDateTime } from "../../lib/format";
import { SecopProcessInfo } from "./SecopProcessInfo";
import { MetadataOnlyWarning } from "./MetadataOnlyWarning";
import { arr, money, obj, priorityLabels, productLabel, str } from "./types";
import { useEurekaAlerts, useRadarRuns } from "./useEureka";

function product(raw: unknown): string {
  const value = obj(raw);
  return [
    productLabel(value.name),
    value.presentation_value != null
      ? `${str(value.presentation_value)} ${str(value.presentation_unit)}`
      : "",
  ]
    .filter(Boolean)
    .join(" · ");
}
const reasonLabels: Record<string, string> = {
  new_process: "Proceso nuevo para Radar",
  region_match: "Región objetivo",
  budget: "Presupuesto",
  budget_review: "Presupuesto requiere revisión",
  execution_days: "Plazo de ejecución (días)",
  payment_days: "Plazo de pago (días)",
  guarantee_required: "Póliza",
  rup_required: "RUP",
  experience_required: "Experiencia",
  review: "Revisión de vigencia/fase",
  conditions_review: "Condiciones por revisar",
  participation_review: "Barrera por revisar",
};
const runLabels: Record<string, string> = {
  running: "En ejecución",
  completed: "Completada",
  partial: "Completada con fallos",
  failed: "Fallida",
  limited: "Límite alcanzado",
  interrupted: "Interrumpida",
};
const methodLabels: Record<string, string> = {
  "term/normalization": "término normalizado",
  "phrase/normalization": "frase normalizada",
  "brand/normalization": "marca normalizada",
  "alias/normalization": "alias normalizado",
  "broad_term/normalization": "necesidad preliminar",
  unspsc: "UNSPSC",
};
const originLabels: Record<string, string> = {
  metadata: "metadatos SECOP",
  canonical_fact: "hecho canónico documental",
};
function readable(value: unknown): string {
  if (value === true) return "Sí";
  if (value === false) return "No";
  if (value == null || value === "unknown") return "No determinado";
  if (value === "not_required") return "No requerida";
  if (value === "required") return "Requerida";
  if (value === "above_preferred") return "Superior al máximo preferido; no excluido";
  return str(value);
}

export function EurekaAlertsPage() {
  const [params, setParams] = useSearchParams();
  const { alertId } = useParams();
  const page = Math.max(1, Number(params.get("page")) || 1);
  const query = useEurekaAlerts(page, alertId),
    runs = useRadarRuns();
  return (
    <section className="eureka-detail">
      <Link to="/eureka">← Volver a oportunidades</Link>
      <h1>Eureka · alertas comerciales</h1>
      <Link className="btn" to="/eureka/notifications">
        Ver notificaciones
      </Link>
      <p className="sub">
        Coincidencias preliminares y confirmadas por documentos. La prioridad orienta la revisión;
        la alerta no determina vigencia ni recomienda participar.
      </p>
      {query.isPending && <p role="status">Cargando alertas…</p>}
      {query.isError && (
        <div role="alert">
          No fue posible cargar las alertas.{" "}
          <button className="btn" onClick={() => void query.refetch()}>
            Reintentar
          </button>
        </div>
      )}
      {query.data && (
        <>
          {!query.data.items.length && <p>No hay alertas para esta página.</p>}
          {query.data.items.map((alert) => {
            const snapshot = alert.snapshot;
            const metadataOnly =
              alert.evidence_level === "metadata_only" ||
              snapshot.evidence_level === "metadata_only";
            const categories = [
              ...new Set(arr(snapshot.confirmed_matches).map((raw) => str(obj(raw).label))),
            ];
            return (
              <article className="card" key={alert.id}>
                <h2>
                  Nueva oportunidad Eureka · {priorityLabels[alert.priority] ?? alert.priority}
                </h2>
                <p>
                  Fuente:{" "}
                  {alert.source === "licitaciones_info_cdp"
                    ? "Licitaciones.info (CDP)"
                    : "Socrata / SECOP"}
                </p>
                {snapshot.requires_manual_document_review === true && (
                  <p role="note">Requiere revisión documental manual</p>
                )}
                {(metadataOnly || alert.document_status === "unavailable") && (
                  <MetadataOnlyWarning />
                )}
                <SecopProcessInfo
                  process={alert.process ?? { secop_id: str(snapshot.secop_id) }}
                  opportunityId={alert.opportunity_id}
                />
                <p>
                  Fecha alerta:{" "}
                  <time dateTime={alert.created_at} title="America/Bogota">
                    {formatBogotaNumericDateTime(alert.created_at)}
                  </time>{" "}
                  (Bogotá)
                </p>
                <p>{str(snapshot.entity)}</p>
                <p>
                  {[snapshot.municipality, snapshot.department].filter(Boolean).map(str).join(", ")}{" "}
                  · {money(snapshot.budget)}
                </p>
                <p>
                  {categories.join(" · ") || "Categoría no determinada"} · Score{" "}
                  {str(snapshot.score)}
                </p>
                <div className="row">
                  <span className="chip">
                    {metadataOnly
                      ? "Alerta provisional · solo metadata"
                      : "Coincidencia comercial confirmada"}
                  </span>
                  <span className="chip">Coincidencia preliminar: metadata</span>
                  {alert.review_required && <span className="chip">Requiere revisión</span>}
                </div>
                <h3>Productos detectados</h3>
                {arr(snapshot.products).length ? (
                  <ul>
                    {arr(snapshot.products).map((value, index) => (
                      <li key={index}>{product(value)}</li>
                    ))}
                  </ul>
                ) : (
                  <p>
                    {metadataOnly
                      ? "Productos pendientes de validación documental."
                      : "Afinidad confirmada en la descripción documental del ítem."}
                  </p>
                )}
                <p>
                  Plazo: {readable(snapshot.execution_days)} días · Pago:{" "}
                  {readable(snapshot.payment_days)} días · Póliza:{" "}
                  {readable(snapshot.guarantee_required)}
                </p>
                <p>
                  {metadataOnly
                    ? "Alerta provisional por región objetivo y coincidencias comerciales en metadata. Documentos pendientes; se reintentará su adquisición."
                    : "Alerta generada por región objetivo y afinidad comercial confirmada documentalmente."}
                </p>
                <Link to={`/eureka/${alert.opportunity_id}`}>
                  Ver oportunidad · {str(snapshot.secop_id)}
                </Link>
                <details>
                  <summary>Por qué se generó esta alerta</summary>
                  <ul>
                    {alert.reasons
                      .filter((reason) => reason.code !== "document_evidence")
                      .map((reason, index) => (
                        <li key={index}>
                          {reason.code === "candidate_match" ||
                          reason.code === "confirmed_commercial_match" ? (
                            <>
                              {reason.code === "candidate_match"
                                ? "Coincidencia preliminar"
                                : "Coincidencia confirmada"}
                              : {str(reason.concept)} ·{" "}
                              {methodLabels[str(reason.method)] ?? str(reason.method)} ·{" "}
                              {originLabels[str(reason.origin)] ?? str(reason.origin)}
                            </>
                          ) : reason.code === "unspsc_match" ? (
                            <>UNSPSC documental: {str(reason.concept)}</>
                          ) : reason.code === "score_reference" ? (
                            <>
                              Score {str(reason.value)} · referencia {str(reason.threshold)} · sin
                              umbral obligatorio
                            </>
                          ) : (
                            <>
                              {reasonLabels[str(reason.code)] ?? str(reason.code)}:{" "}
                              {reason.code === "budget"
                                ? money(reason.value)
                                : readable(reason.value)}
                            </>
                          )}
                        </li>
                      ))}
                  </ul>
                  <details>
                    <summary>Ver trazabilidad técnica de la alerta</summary>
                    <pre>
                      {JSON.stringify(
                        {
                          rule_version: alert.rule_version,
                          run_id: alert.run_id,
                          reasons: alert.reasons,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  </details>
                </details>
              </article>
            );
          })}
          <Pagination
            page={query.data.page}
            pageSize={query.data.page_size}
            total={query.data.total}
            itemLabel="alertas"
            onPageChange={(next) => setParams({ page: String(next) })}
          />
        </>
      )}
      <div className="card">
        <h2>Últimas corridas Radar</h2>
        {runs.isPending && <p role="status">Cargando corridas…</p>}
        {runs.isError && <p role="alert">No fue posible consultar las corridas.</p>}
        {runs.data && !runs.data.items.length && <p>No hay corridas registradas.</p>}
        {runs.data?.items.map((run) => (
          <details key={run.id}>
            <summary>
              {new Date(run.started_at).toLocaleString("es-CO")} ·{" "}
              {runLabels[run.status] ?? run.status}
            </summary>
            <p>
              Ventana: {run.start_date} → {run.before_date} (fin exclusivo) ·{" "}
              {run.regions.join(", ")}
            </p>
            <p>
              {run.processes_seen} leídos · {run.new_processes} nuevos · {run.candidates} candidatos
              · {run.enriched} enriquecidos · {run.alerts_created} alertas · {run.skipped} omitidos
              · {run.failures} fallos
            </p>
            <p>Reglas: {run.rule_version}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
