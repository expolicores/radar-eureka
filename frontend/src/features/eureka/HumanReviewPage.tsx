import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router";
import { ApiError } from "../../api/client";
import { formatBogotaNumericDateTime, formatBogotaEventDateTime } from "../../lib/format";
import { arr, obj, str, money, factValue } from "./types";

type Rating = "high" | "medium" | "low" | "discard" | "";
type Review = {
  canonical_identity: string;
  equivalent_identities?: string[];
  manual_assessments?: {
    canonical_identity: string;
    manual_note?: string;
    manual_rating?: string;
    reviewed_at?: string;
  }[];
  codigo_proceso: string;
  source_url?: string;
  entity_name?: string;
  municipality?: string;
  department?: string;
  object?: string;
  amount?: string | number;
  published_at?: string;
  deadline_at?: string;
  validity_status: string;
  sources: string[];
  score?: number | null;
  stage_max: string;
  commercial_decision: string;
  no_alert_reason: string;
  requires_manual_document_review: boolean;
  manual_review_reasons: string[];
  review_explanations?: string[];
  provider_source?: string;
  alert_ids: string[];
  has_alert: boolean;
  last_run_at: string;
  last_run_id: string;
  manual_rating?: Rating;
  manual_note: string;
  reviewed_at?: string;
  review_first_seen_at?: string | null;
  review_first_seen_origin?: string;
  reviewed_by?: string;
  history: { run_id: string; run_at: string; source: string; result?: Record<string, unknown> }[];
  evidence?: Record<string, unknown>;
  opportunity_id?: string;
};
type Page = {
  admission_policy?: { version: number; max_amount_cop: number };
  items: Review[];
  total: number;
  page: number;
  page_size: number;
  filter_options: Record<string, string[]>;
};
const sources: Record<string, string> = {
  socrata: "Socrata / Eureka",
  licitaciones_info_cdp: "Licitaciones.info (CDP)",
};
const ratings: Record<string, string> = {
  high: "Alta",
  medium: "Media",
  low: "Baja",
  discard: "Descartar",
};
const labels: Record<string, string> = {
  open: "Abierto",
  closed: "Cerrado",
  unknown: "Vigencia desconocida",
  metadata: "Metadatos",
  completed: "Completado",
  ingestion: "Persistencia",
  discovery: "Descubrimiento",
  pipeline: "Procesamiento",
  documents_sync: "Inventario documental",
  documents_download: "Descarga documental",
  extraction: "Extracción",
  structured: "Facts extraídos",
  alert_evaluation: "Decisión de alerta",
  already_seen: "Observado previamente",
  strong_exclusion: "Exclusión comercial",
  no_metadata_match: "Sin coincidencia comercial en metadatos",
  outside_region: "Fuera de alcance geográfico",
  outside_window: "Fuera de ventana reciente",
  stale: "Histórico",
  validity_closed: "Deadline vencido",
  validity_unknown: "Vigencia por verificar",
  attempts_exhausted: "Reintentos agotados",
  missing_or_invalid_offer_deadline: "Deadline por verificar",
  persisted_document_review: "Revisión documental persistida",
  canonical_reused: "Canonicals reutilizados",
  consolidation: "Consolidación",
  extraction_partial: "Extracción parcial",
  no_alert: "Sin alerta",
  metadata_object_exclusion: "Alerta provisional excluida por objeto",
  metadata_exclusion_policy_invalid: "Política de exclusión de alertas provisionales inválida",
  limit_deferred: "Diferido por límite",
  suspicious_fact: "Hechos sospechosos",
  suspicious_facts: "Hechos sospechosos",
  ocr_truncated: "OCR truncado",
  partial_document_coverage: "Cobertura documental parcial",
  extraction_failed: "Falló la extracción",
  unsupported_format: "Formato no soportado",
  missing_documents: "Documentos ausentes",
  document_download_failed: "Falló la descarga",
  official_budget_cop: "Presupuesto oficial",
  execution_term: "Plazo de ejecución",
  payment_term: "Plazo de pago",
  product: "Producto",
  quantity: "Cantidad",
  presentation: "Presentación",
  payment_method: "Forma de pago",
};
const label = (value: string) => labels[value] ?? value;
const timestamp = (value?: string) =>
  value
    ? formatBogotaNumericDateTime(
        /(?:Z|[+-]\d{2}:\d{2})$/.test(value)
          ? value
          : `${value.includes("T") ? value : value + "T00:00:00"}-05:00`,
      )
    : "No disponible";
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(
    new Request(new URL(`/api/eureka/revision${path}`, location.origin), init),
  );
  if (!response.ok) throw new ApiError(response.status, "No fue posible completar la revisión");
  return response.json() as Promise<T>;
}

function AssessmentForm({ row }: { row: Review }) {
  const [rating, setRating] = useState<Rating>(row.manual_rating || "");
  const [note, setNote] = useState(row.manual_note || "");
  const client = useQueryClient();
  const save = useMutation({
    mutationFn: () =>
      request(`/${encodeURIComponent(row.canonical_identity)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ manual_rating: rating || null, manual_note: note }),
      }),
    onSuccess: () => void client.invalidateQueries({ queryKey: ["human-review"] }),
  });
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <h2>Evaluación humana</h2>
      <p>
        Se guarda por identidad del proceso y permanece entre corridas. No cambia el score ni crea
        alertas.
      </p>
      <label>
        Evaluación manual{" "}
        <select value={rating} onChange={(e) => setRating(e.target.value as Rating)}>
          <option value="">Sin evaluación</option>
          {Object.entries(ratings).map(([v, t]) => (
            <option key={v} value={v}>
              {t}
            </option>
          ))}
        </select>
      </label>
      <label>
        Nota manual{" "}
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          maxLength={5000}
          rows={4}
        />
      </label>
      <button className="btn" disabled={save.isPending}>
        Guardar evaluación
      </button>
      {row.reviewed_at && (
        <p>
          Última revisión: {timestamp(row.reviewed_at)} · Analista: {row.reviewed_by}
        </p>
      )}
      {save.isSuccess && <p role="status">Evaluación guardada</p>}
      {save.isError && (
        <p role="alert">No se pudo guardar la evaluación. Tu nota permanece en el formulario.</p>
      )}
    </form>
  );
}

function ReviewEntry({ row }: { row: Review }) {
  return (
    <>
      {row.review_first_seen_at
        ? formatBogotaEventDateTime(row.review_first_seen_at)
        : "No registrada (histórico)"}
      {row.review_first_seen_origin === "historical_backfill" && (
        <small> · Registro histórico: fecha original de entrada desconocida</small>
      )}
    </>
  );
}

function Detail({ identity }: { identity: string }) {
  const query = useQuery({
    queryKey: ["human-review", "detail", identity],
    queryFn: () => request<Review>(`/${encodeURIComponent(identity)}`),
  });
  if (query.isPending) return <p role="status">Cargando revisión…</p>;
  if (query.isError)
    return (
      <p role="alert">
        No fue posible cargar el proceso. <Link to="/eureka/revision">Volver</Link>
      </p>
    );
  const row = query.data;
  const evidence = row.evidence ?? {};
  const suspicious = new Map<string, Record<string, unknown>>();
  row.history.forEach((h) =>
    arr(obj(h.result?.document_review).facts).forEach((f) => {
      const fact = obj(f);
      if (fact.suspicious) suspicious.set(str(fact.id), fact);
    }),
  );
  const canonical = obj(evidence.canonicals);
  return (
    <section>
      <Link to="/eureka/revision">← Merecen Revisión</Link>
      <h1>{row.codigo_proceso}</h1>
      <p>
        {row.entity_name} · {row.municipality}, {row.department}
      </p>
      <p>{row.object}</p>
      <p>
        {money(row.amount)} · {label(row.validity_status)}
      </p>
      <p>
        Publicado: {timestamp(row.published_at)} · Deadline: {timestamp(row.deadline_at)} (Bogotá)
      </p>
      <p>
        Entró a revisión: <ReviewEntry row={row} /> (Bogotá)
      </p>
      <p>Fuente: {row.sources.map((s) => sources[s]).join(" · ")}</p>
      <p>Identidad del proceso: {row.canonical_identity}</p>
      {(row.equivalent_identities?.length ?? 0) > 1 && (
        <p>
          Identidades históricas vinculadas:{" "}
          {row.equivalent_identities
            ?.filter((identity) => identity !== row.canonical_identity)
            .join(" · ")}
        </p>
      )}
      <p>Fuente de origen: {row.provider_source ?? "No registrada"}</p>
      {row.review_explanations?.map((message) => (
        <p key={message}>{message}</p>
      ))}
      <p>
        <strong>Score Eureka: {row.score ?? "Sin calcular"}</strong> · Decisión comercial:{" "}
        {row.commercial_decision}
      </p>
      <p>Motivo de no alerta: {row.no_alert_reason}</p>
      <p>Etapa máxima: {label(row.stage_max)}</p>
      <p>
        Revisión documental: {row.requires_manual_document_review ? "Sí" : "No"} ·{" "}
        {row.manual_review_reasons.map(label).join(" · ")}
      </p>
      {row.alert_ids.map((id) => (
        <p key={id}>
          <Link to={`/eureka/alerts/${id}`}>Alerta existente · {id}</Link>
        </p>
      ))}
      {row.opportunity_id && (
        <p>
          <Link to={`/eureka/${row.opportunity_id}`}>Ver detalle y evidencia Eureka</Link>
        </p>
      )}
      <AssessmentForm key={row.canonical_identity} row={row} />
      {!!row.manual_assessments?.length && (
        <details>
          <summary>Evaluaciones conservadas por identidad</summary>
          {row.manual_assessments.map((assessment) => (
            <p key={assessment.canonical_identity}>
              {assessment.canonical_identity}: {assessment.manual_rating ?? "Sin clasificación"} ·{" "}
              {assessment.manual_note || "Sin nota"}
            </p>
          ))}
        </details>
      )}
      <h2>Canonicals relevantes</h2>
      {Object.entries({
        Presupuesto: obj(canonical.commercial).budget_cop,
        "Plazo de ejecución": obj(canonical.execution).execution_term,
        "Plazo de pago": obj(canonical.payment).payment_term,
      }).map(([key, value]) => (
        <p key={key}>
          {key}: {value ? JSON.stringify(factValue(obj(value))) : "No confirmado"}
        </p>
      ))}
      <h2>Documentos procesados</h2>
      {arr(evidence.documents).length === 0 && <p>No hay documentos procesados disponibles.</p>}
      {arr(evidence.documents).map((raw) => {
        const d = obj(raw);
        return (
          <article key={str(d.document_version_id)}>
            <h3>{str(d.name)}</h3>
            <p>
              {str(d.extraction_mode)} · {str(d.status)} · Páginas {str(d.processed_pages)}/
              {str(d.total_pages)} · Cobertura{" "}
              {d.coverage_ratio == null
                ? "Desconocida"
                : `${Math.round(Number(d.coverage_ratio) * 100)}%`}
            </p>
            {Boolean(d.warning) && <p>{label(str(d.warning))}</p>}
          </article>
        );
      })}
      <h2>Suspicious facts persistidos</h2>
      {[...suspicious.values()].map((f) => (
        <blockquote key={str(f.id)}>
          {str(f.evidence_text)} · {label(str(f.fact_type))}
        </blockquote>
      ))}
      {suspicious.size === 0 && <p>No hay anotaciones sospechosas persistidas.</p>}
      <details>
        <summary>Facts principales ({arr(evidence.facts).length})</summary>
        {arr(evidence.facts).map((raw) => {
          const f = obj(raw);
          return (
            <p key={str(f.id)}>
              {label(str(f.fact_type))}: {str(f.evidence_text)}
            </p>
          );
        })}
      </details>
      <h2>Historial de corridas y provenance</h2>
      {row.history.map((h) => (
        <details key={`${h.run_id}-${h.source}`}>
          <summary>
            {timestamp(h.run_at)} · {sources[h.source]} · {h.run_id}
          </summary>
          <p>
            Etapa: {label(str(h.result?.stage))} · Resultado:{" "}
            {label(str(h.result?.reason ?? h.result?.outcome))}
          </p>
          {arr(h.result?.warnings)
            .concat(arr(h.result?.errors))
            .map((w, i) => (
              <p key={i}>{label(typeof w === "string" ? w : str(obj(w).code))}</p>
            ))}
        </details>
      ))}
    </section>
  );
}

export function HumanReviewPage() {
  const { identity } = useParams();
  return identity ? <Detail identity={identity} /> : <ReviewList />;
}

function ReviewList() {
  const [filters, setFilters] = useState<Record<string, string>>({ validity: "active" });
  const [applied, setApplied] = useState(filters);
  const [page, setPage] = useState(1);
  const search = new URLSearchParams({
    ...Object.fromEntries(Object.entries(applied).filter(([, v]) => v !== "")),
    validity: applied.validity || "all",
    page: String(page),
  });
  const query = useQuery({
    queryKey: ["human-review", "list", search.toString()],
    queryFn: () => request<Page>(`?${search}`),
    staleTime: 0,
    refetchOnMount: "always",
    refetchOnWindowFocus: "always",
    refetchInterval: 15_000,
  });
  const input = (key: string, title: string, type = "text") => (
    <label key={key}>
      {title}
      <input
        type={type}
        value={filters[key] ?? ""}
        onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}
      />
    </label>
  );
  const select = (key: string, title: string, options: Record<string, string>) => (
    <label key={key}>
      {title}
      <select
        value={filters[key] ?? ""}
        onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}
      >
        <option value="">Todos</option>
        {Object.entries(options).map(([v, t]) => (
          <option key={v} value={v}>
            {t}
          </option>
        ))}
      </select>
    </label>
  );
  return (
    <section>
      <h1>Merecen Revisión</h1>
      <p>
        Compras y suministros pertinentes que requieren análisis humano y aún no tienen alerta. Los
        procesos con alerta se revisan únicamente en Alertas. Se muestran procesos observados en los
        últimos 7 días.
      </p>
      {query.data?.admission_policy && (
        <p>
          Tope de presupuesto para esta bandeja: {money(query.data.admission_policy.max_amount_cop)}
          .
        </p>
      )}
      <p>
        Solo datos persistidos. La evaluación humana no modifica Score Eureka ni genera alertas.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setPage(1);
          setApplied({ ...filters });
        }}
      >
        <div className="filters">
          {input("q", "Buscar código, entidad u objeto")}
          {select("source", "Fuente", sources)}
          {select("validity", "Vigencia", {
            active: "Activos y vigencia desconocida",
            open: "Abiertos",
            closed: "Cerrados",
            unknown: "Desconocida",
            all: "Todas",
          })}
          {input("department", "Departamento")}
          {input("municipality", "Municipio")}
          {input("score_min", "Score mínimo", "number")}
          {input("score_max", "Score máximo", "number")}
          {input("amount_min", "Monto mínimo", "number")}
          {input("amount_max", "Monto máximo", "number")}
          {input("deadline_from", "Deadline desde", "date")}
          {input("deadline_to", "Deadline hasta", "date")}
          {select(
            "funnel_state",
            "Estado del funnel",
            Object.fromEntries(
              (query.data?.filter_options.funnel_state ?? []).map((v) => [v, label(v)]),
            ),
          )}
          {select("requires_manual_document_review", "Revisión documental", {
            true: "Sí",
            false: "No",
          })}
          <label>
            <input
              type="checkbox"
              checked={filters.include_excluded === "true"}
              onChange={(e) =>
                setFilters({ ...filters, include_excluded: String(e.target.checked) })
              }
            />{" "}
            Incluir históricos y fuera de alcance
          </label>
        </div>
        <button className="btn">Aplicar filtros</button>
      </form>
      {query.isPending && <p role="status">Cargando procesos…</p>}
      {query.isError && (
        <p role="alert">
          No fue posible cargar Merecen Revisión.{" "}
          <button onClick={() => void query.refetch()}>Reintentar</button>
        </p>
      )}
      {query.data && (
        <>
          <p>
            {query.data.total} procesos · Página {page}
          </p>
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  {[
                    "Código",
                    "Entidad",
                    "URL del proceso",
                    "Municipio",
                    "Departamento",
                    "Objeto",
                    "Monto",
                    "Publicación",
                    "Deadline",
                    "Entró a revisión",
                    "Vigencia",
                    "Fuente",
                    "Score Eureka",
                    "Evaluación manual",
                    "Etapa máxima",
                    "Decisión comercial",
                    "Motivo de no alerta",
                    "Revisión documental",
                    "manual_review_reasons",
                    "Alerta existente",
                    "Última corrida / provenance",
                  ].map((h) => (
                    <th key={h}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((r) => (
                  <tr key={r.canonical_identity}>
                    <td>
                      <Link to={`/eureka/revision/${encodeURIComponent(r.canonical_identity)}`}>
                        {r.codigo_proceso}
                      </Link>
                    </td>
                    <td>{r.entity_name}</td>
                    <td>
                      {r.source_url && /^https?:\/\//i.test(r.source_url) ? (
                        <a
                          href={r.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          title={r.source_url}
                        >
                          Abrir proceso
                        </a>
                      ) : (
                        "Sin URL disponible"
                      )}
                    </td>
                    <td>{r.municipality}</td>
                    <td>{r.department}</td>
                    <td>{r.object}</td>
                    <td>{money(r.amount)}</td>
                    <td>{timestamp(r.published_at)}</td>
                    <td>{timestamp(r.deadline_at)}</td>
                    <td>
                      <ReviewEntry row={r} />
                    </td>
                    <td>{label(r.validity_status)}</td>
                    <td>
                      {r.sources.map((s) => sources[s]).join(" · ")}
                      {r.provider_source && <div>Origen: {r.provider_source}</div>}
                    </td>
                    <td>{r.score ?? "Sin calcular"}</td>
                    <td>{ratings[r.manual_rating ?? ""] ?? "Sin evaluación"}</td>
                    <td>{label(r.stage_max)}</td>
                    <td>{r.commercial_decision}</td>
                    <td>{r.no_alert_reason}</td>
                    <td>{r.requires_manual_document_review ? "Sí" : "No"}</td>
                    <td>
                      {(r.review_explanations ?? r.manual_review_reasons.map(label)).join(" · ") ||
                        "—"}
                    </td>
                    <td>
                      {r.has_alert
                        ? r.alert_ids.map((id) => (
                            <Link key={id} to={`/eureka/alerts/${id}`}>
                              Alerta existente{" "}
                            </Link>
                          ))
                        : "No"}
                    </td>
                    <td>
                      {timestamp(r.last_run_at)}
                      <details>
                        <summary>Ver corridas ({r.history.length})</summary>
                        {r.history.map((h) => (
                          <p key={`${h.run_id}-${h.source}`}>
                            {sources[h.source]} · {h.run_id}
                          </p>
                        ))}
                      </details>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {query.data.total === 0 && <p>No hay procesos con estos filtros.</p>}
          <button disabled={page === 1} onClick={() => setPage(page - 1)}>
            Anterior
          </button>{" "}
          <button
            disabled={page * query.data.page_size >= query.data.total}
            onClick={() => setPage(page + 1)}
          >
            Siguiente
          </button>
        </>
      )}
    </section>
  );
}
