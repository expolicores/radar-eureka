import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router";
import { api, unwrap } from "../../api/client";
import { obj, str, money } from "../eureka/types";
import { formatBogotaEventDateTime } from "../../lib/format";

const labels: Record<string, string> = {
  processes_total: "Procesos totales",
  recent_processes: "Procesos recientes",
  open_processes: "Procesos recientes abiertos",
  closed_processes: "Procesos recientes cerrados",
  unknown_validity_processes: "Procesos recientes con vigencia desconocida",
  document_capable: "Abiertos con capacidad documental",
  metadata_only: "Procesados por metadata",
  processed: "Procesos procesados",
  review_candidates: "Candidatos a revisión humana",
  received: "Recibidos",
  unique: "Únicos",
  recent: "Recientes",
  SECOP_II: "SECOP II recientes",
  open: "Abiertos",
  documents: "Documentos inventariados",
  documents_selected: "Documentos seleccionados",
  extraction_attempted: "Extracciones intentadas",
  extraction_succeeded: "Extracciones con texto útil",
  extraction_failed: "Extracciones fallidas",
  process_warnings: "Procesos con advertencias",
  process_errors: "Procesos con errores",
  canonicalized: "Canonicalizados",
  commercially_eligible: "Elegibles comerciales",
  scored: "Evaluados por Eureka",
  alert_candidates: "Candidatos a alerta",
  alerts_created: "Alertas creadas",
  duplicate_alerts_skipped: "Alertas duplicadas omitidas",
  manual_review: "Revisión documental manual",
  secop_ii_total: "SECOP II totales",
  secop_ii_recent: "SECOP II recientes",
  secop_ii_open: "SECOP II abiertos",
  secop_ii_closed: "SECOP II cerrados",
  secop_ii_unknown: "SECOP II sin vigencia determinada",
  provider_status_deadline_conflicts: "Conflictos estado/deadline",
};
const statuses: Record<string, string> = {
  running: "En ejecución",
  completed: "Completada",
  completed_with_warnings: "Completada con advertencias",
  failed: "Fallida",
  session_unavailable: "Sesión no disponible",
  interrupted: "Interrumpida",
};
const reasons: Record<string, string> = {
  stale: "Fuera de ventana reciente",
  not_secop_ii: "Diferimiento histórico por fuente (regla retirada)",
  metadata_only: "Sin documentos disponibles; evaluación basada en metadata",
  commercially_not_eligible: "Sin elegibilidad comercial confirmada",
  incomplete_row: "Información mínima insuficiente",
  unknown_source: "Origen por verificar; se conserva la metadata útil",
  validity_closed: "Deadline vencido",
  validity_unknown: "Vigencia no determinada",
  duplicate_canonical: "Ya existe alerta para el proceso canónico",
  limit_deferred: "Diferido por límite documental",
  missing_canonical_identity: "Identidad estable no disponible",
  process_error: "Error recuperable del proceso",
  network_error: "Error de red",
  document_download_failed: "Falló la descarga documental",
  extraction_failed: "Falló la extracción",
  unsupported_format: "Formato documental no compatible",
  partial_coverage: "Cobertura documental parcial",
  partial_document_coverage: "Cobertura documental parcial",
  ocr_truncated: "OCR limitado a 20 páginas",
  suspicious_fact: "Hechos que requieren revisión",
  missing_documents: "Documentos requeridos ausentes",
};
const timestamp = (value: unknown) =>
  typeof value === "string"
    ? new Date(
        value.includes("T") && !/(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? `${value}-05:00` : value,
      ).toLocaleString("es-CO", { timeZone: "America/Bogota" })
    : "No disponible";
const stages: Record<string, string> = {
  preflight: "Verificación de sesión",
  metadata: "Metadatos",
  ingestion: "Persistencia",
  discovery: "Descubrimiento",
  documents_sync: "Inventario documental",
  documents_download: "Descarga",
  extraction: "Extracción",
  extraction_partial: "Extracción parcial",
  structured: "Hechos",
  consolidation: "Consolidación",
  canonical_reused: "Canónicos reutilizados",
  completed: "Completado",
  documents_pending: "Documentos pendientes",
};
const outcomes: Record<string, string> = {
  skipped: "Descartado o diferido",
  failed: "Fallido",
  no_alert: "Sin alerta",
  duplicate: "Duplicado omitido",
  alert: "Alerta creada",
};
const issueList = (value: unknown): unknown[] => (Array.isArray(value) ? (value as unknown[]) : []);

function eventTime(value: unknown) {
  return typeof value === "string" ? formatBogotaEventDateTime(value) : "No registrada (histórico)";
}

function RunEvents({
  run,
}: {
  run: { id: string; metrics: Record<string, unknown>; errors: unknown[]; items: unknown[] };
}) {
  const metrics = run.metrics;
  const entries = [
    ...issueList(metrics.warnings),
    ...issueList(metrics.process_warning_details),
    ...issueList(metrics.process_error_details),
    ...run.errors,
    ...issueList(obj(metrics.preflight).warnings),
    ...issueList(metrics.queries).flatMap((q) => [
      ...issueList(obj(q).warnings),
      ...(obj(q).error ? [obj(q).error] : []),
    ]),
    ...run.items.flatMap((raw) => [...issueList(obj(raw).warnings), ...issueList(obj(raw).errors)]),
    ...run.items.flatMap((raw) => (obj(raw).discard_event ? [obj(raw).discard_event] : [])),
  ];
  const serverGroups = obj(metrics.event_groups);
  const classifiedEntries = Object.keys(serverGroups).length
    ? Object.values(serverGroups).flatMap(issueList)
    : entries;
  const unique = new Map<string, Record<string, unknown>>();
  classifiedEntries.forEach((raw) => {
    const e = typeof raw === "string" ? { code: raw } : obj(raw);
    const key = JSON.stringify([
      e.run_id ?? run.id,
      e.code,
      e.process_identity ?? e.process_reference,
      e.generated_at,
      e.search_id,
      e.document_version_id,
    ]);
    unique.set(key, e);
  });
  const discards = new Set([
    "outside_local_scope",
    "stale",
    "validity_closed",
    "validity_unknown",
    "limit_deferred",
    "commercially_not_eligible",
    "metadata_object_exclusion",
    "unenriched_row_skipped",
    "incomplete_row",
  ]);
  const errors = new Set([
    "network_error",
    "extraction_failed",
    "document_download_failed",
    "invalid_response",
    "process_error",
    "source_error",
  ]);
  return (
    <>
      {[
        ["discard", "Descartes del funnel"],
        ["warning", "Advertencias"],
        ["error", "Errores"],
      ].map(([kind, label]) => {
        const rows = [...unique.entries()].filter(
          ([, e]) =>
            (e.event_type ??
              (discards.has(str(e.code))
                ? "discard"
                : errors.has(str(e.code))
                  ? "error"
                  : "warning")) === kind,
        );
        return (
          <details key={kind}>
            <summary>
              {label} ({rows.length})
            </summary>
            <p>
              Fechas en America/Bogota. Los eventos históricos sin hora registrada no usan la fecha
              de corrida como sustituto.
            </p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    {[
                      "Fecha/Hora",
                      "Código",
                      "Proceso / identidad",
                      "Mensaje",
                      "Etapa",
                      "Fuente",
                      "Corrida",
                    ].map((t) => (
                      <th key={t}>{t}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map(([key, e]) => (
                    <tr key={key}>
                      <td>{eventTime(e.generated_at)}</td>
                      <td>{str(e.code)}</td>
                      <td>
                        {str(e.codigo_proceso)}{" "}
                        {str(e.process_identity ?? e.process_reference) || "General"}
                      </td>
                      <td>{e.message ? str(e.message) : reasons[str(e.code)] || str(e.code)}</td>
                      <td>{stages[str(e.stage)] ?? str(e.stage)}</td>
                      <td>{str(e.source) || "No registrada"}</td>
                      <td>{e.run_id ? str(e.run_id) : run.id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        );
      })}
    </>
  );
}

export function LicitacionesPage() {
  const cache = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);
  const runs = useQuery({
    queryKey: ["cdp-runs"],
    queryFn: async () => unwrap(await api.GET("/api/eureka/licitaciones-cdp/runs")),
    refetchInterval: 3000,
  });
  const activeId = selected ?? runs.data?.items[0]?.id;
  const detail = useQuery({
    queryKey: ["cdp-run", activeId],
    enabled: Boolean(activeId),
    queryFn: async () =>
      unwrap(
        await api.GET("/api/eureka/licitaciones-cdp/runs/{identifier}", {
          params: { path: { identifier: activeId! } },
        }),
      ),
    refetchInterval: (query) => (query.state.data?.status === "running" ? 2000 : false),
  });
  const start = useMutation({
    mutationFn: async () => unwrap(await api.POST("/api/eureka/licitaciones-cdp/runs")),
    onSuccess: (result) => {
      setSelected(str(result.id));
      void cache.invalidateQueries({ queryKey: ["cdp-runs"] });
    },
  });
  const run = detail.data;
  const metrics = run?.metrics ?? {};
  return (
    <section className="eureka-detail">
      <h1>Licitaciones.info (CDP)</h1>
      <p className="sub">
        Fuente independiente, mismo pipeline comercial y misma bandeja de alertas Eureka. Ejecución
        exclusivamente manual.
      </p>
      <details>
        <summary>Preparar Edge y la sesión</summary>
        <p>Desde backend, si Edge CDP no está abierto:</p>
        <code>.\.venv\Scripts\python.exe scripts\licitaciones_cdp_open.py</code>
        <p>
          Inicia sesión manualmente, selecciona Vila Frontier y deja abierta una sola pestaña
          Contratos desktop. Luego vuelve aquí. No se automatiza login ni CAPTCHA.
        </p>
        <p>
          Seis búsquedas secuenciales, pausa de cuatro segundos, siete días recientes y página 1.
          Hasta tres procesos abiertos y dos documentos por proceso. Sin scheduler.
        </p>
      </details>
      <button className="btn" disabled={start.isPending} onClick={() => start.mutate()}>
        Ejecutar corrida Licitaciones.info
      </button>
      <Link className="btn" to="/eureka/alerts">
        Ver bandeja compartida de alertas
      </Link>
      {(start.isError || runs.isError || detail.isError) && (
        <p role="alert">
          No se pudo iniciar o consultar la corrida. Revisa la conexión y si ya hay una corrida
          activa.
        </p>
      )}
      {runs.isPending && <p role="status">Cargando corridas…</p>}
      {runs.data && !runs.data.items.length && <p>No hay corridas Licitaciones.info todavía.</p>}
      <label>
        Corrida{" "}
        <select value={activeId ?? ""} onChange={(e) => setSelected(e.target.value)}>
          {runs.data?.items.map((r) => (
            <option key={r.id} value={r.id}>
              {timestamp(r.started_at)} · {statuses[r.status] ?? r.status}
            </option>
          ))}
        </select>
      </label>
      {run && (
        <>
          <h2>{statuses[run.status] ?? run.status}</h2>
          {run.status === "running" && (
            <p role="status">Etapa actual: {stages[str(metrics.stage)] ?? "Preparando corrida"}</p>
          )}
          <p>
            Inicio: {timestamp(run.started_at)} · Fin: {timestamp(run.finished_at)} · Duración:{" "}
            {str(metrics.duration_seconds ?? "En curso")} s
          </p>
          {run.status === "session_unavailable" && (
            <p role="alert">
              Sesión de Licitaciones.info no disponible. Abre el Edge CDP, inicia sesión, selecciona
              Vila Frontier y deja abierta la vista Contratos. Luego vuelve a ejecutar.
            </p>
          )}
          {obj(metrics.preflight).preflight_status === "inconclusive" && (
            <p role="alert">
              Preflight inconcluso: muestra SECOP insuficiente (insufficient_secop_sample). La
              corrida no continuó. Este resultado no indica sesión expirada ni requiere otro login.
            </p>
          )}
          {obj(metrics.preflight).preflight_status === "unhealthy_response" && (
            <p role="alert">
              Preflight bloqueado por respuesta no saludable: {str(obj(metrics.preflight).reason)}.
            </p>
          )}
          {obj(metrics.preflight).preflight_status === "healthy" && <p>Preflight saludable.</p>}
          <h2>Funnel y resultado</h2>
          {metrics.extraction_metrics_version !== 2 && metrics.extracted !== undefined && (
            <p>
              Corrida histórica: el contador de extracción incluía resultados fallidos. No se
              dispone del desglose de éxitos y fallos en este resumen.
            </p>
          )}
          <dl>
            {Object.entries(labels).map(([key, label]) => (
              <div key={key}>
                <dt>{label}</dt>
                <dd>
                  {str(
                    metrics[key] ??
                      (key.startsWith("extraction_") || key.startsWith("process_") ? "—" : 0),
                  )}
                </dd>
              </div>
            ))}
          </dl>
          <RunEvents
            run={{ id: run.id, metrics, errors: run.errors ?? [], items: run.items ?? [] }}
          />
          {metrics.by_source != null && (
            <details>
              <summary>Composición por fuente</summary>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Fuente</th>
                      <th>Total</th>
                      <th>Recientes</th>
                      <th>Abiertos</th>
                      <th>Procesados</th>
                      <th>Alertas</th>
                      <th>Revisión</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(obj(metrics.by_source)).map(([source, raw]) => {
                      const counts = obj(raw);
                      return (
                        <tr key={source}>
                          <td>{source}</td>
                          {[
                            "processes_total",
                            "recent_processes",
                            "open_processes",
                            "processed",
                            "alerts_created",
                            "review_candidates",
                          ].map((key) => (
                            <td key={key}>{str(counts[key] ?? 0)}</td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </details>
          )}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {[
                    "Proceso",
                    "Entidad",
                    "Fuente",
                    "Objeto",
                    "Ubicación",
                    "Publicado",
                    "Deadline",
                    "Vigencia",
                    "Monto",
                    "Etapa",
                    "Resultado / motivo",
                    "Revisión",
                    "Alerta creada",
                  ].map((x) => (
                    <th key={x}>{x}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(run.items ?? []).map((raw) => {
                  const item = obj(raw);
                  const m = obj(item.metadata);
                  const issues = [...issueList(item.warnings), ...issueList(item.errors)];
                  return (
                    <tr key={str(item.secop_id)}>
                      <td>{str(m.codigo_proceso)}</td>
                      <td>{str(m.entity_name)}</td>
                      <td>{str(m.provider_source) || "No registrada"}</td>
                      <td>{str(m.object)}</td>
                      <td>
                        {str(m.department)} · {str(m.municipality)}
                      </td>
                      <td>{timestamp(m.published_at)}</td>
                      <td>{timestamp(m.deadline_at)}</td>
                      <td>
                        {m.validity_status === "open"
                          ? "Abierto"
                          : m.validity_status === "closed"
                            ? "Cerrado"
                            : "No determinada"}
                      </td>
                      <td>{money(m.amount)}</td>
                      <td>{stages[str(item.stage)] ?? str(item.stage)}</td>
                      <td>
                        {outcomes[str(item.outcome)] ?? str(item.outcome)} ·{" "}
                        {reasons[str(item.reason)] ?? str(item.reason)}
                        {issues.map((entry, index) => {
                          const warning = obj(entry);
                          return (
                            <div key={index}>
                              {eventTime(warning.generated_at)} · {str(warning.code)} ·{" "}
                              {warning.message ? str(warning.message) : reasons[str(warning.code)]}
                            </div>
                          );
                        })}
                      </td>
                      <td>
                        {item.requires_manual_document_review
                          ? "Requiere revisión documental manual"
                          : m.validity_warning === "provider_status_deadline_conflict"
                            ? "Estado del proveedor contradice el deadline"
                            : m.validity_warning === "invalid_deadline_at"
                              ? "Fecha límite inválida"
                              : "—"}
                      </td>
                      <td>{item.alert_created ? "Sí" : "No"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
