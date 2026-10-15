import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api, unwrap } from "../../api/client";
import { Pagination } from "../../components/Pagination";
import { categoryLabels, money, obj, str, priorityLabels } from "../eureka/types";
import { EvidenceDocuments } from "../eureka/EvidenceDocuments";
import { groupEvidence } from "../eureka/evidencePresentation";
import type { paths } from "../../api/schema";

type Filters = NonNullable<paths["/api/search"]["get"]["parameters"]["query"]>;
type Reason = {
  type: string;
  mode: string;
  field: string;
  value: unknown;
  canonical_fact_id?: string;
  fragment_id?: string;
};
type Hit = {
  process_id: string;
  secop_id: string;
  title: string;
  entity: string;
  department: string;
  municipality: string;
  budget_cop: number | null;
  score: number | null;
  priority: string | null;
  published_on: string | null;
  detail_url: string | null;
  source_url: string | null;
  matches: Reason[];
  products?: { value: unknown; origin: string }[];
};

function displayValue(value: unknown): string {
  if (typeof value === "string" || typeof value === "number") return String(value);
  const data = obj(value);
  if (data.name || data.description)
    return [data.name ?? data.description, data.presentation_value, data.presentation_unit]
      .filter((v): v is string | number => typeof v === "string" || typeof v === "number")
      .map(String)
      .join(" ");
  if (data.code) return str(data.code);
  if (data.value != null) return `${str(data.value)} ${str(data.unit ?? "")}`.trim();
  return JSON.stringify(value);
}
const origins: Record<string, string> = {
  canonical_match: "Hecho canónico vigente",
  structured_match: "Hecho estructurado · fallback",
  metadata_match: "Metadata del proceso",
  extracted_text_match: "Texto documental",
};
const modes: Record<string, string> = {
  exact_normalized: "Coincidencia exacta normalizada",
  explicit_alias: "Alias explícito",
  phrase: "Frase",
  full_text: "Texto completo",
  token_prefix: "Prefijo",
};
const fields: [string, string, string?][] = [
  ["product", "Producto"],
  ["brand", "Marca"],
  ["entity", "Entidad"],
  ["department", "Departamento"],
  ["municipality", "Municipio"],
  ["unspsc", "UNSPSC"],
  ["budget_min", "Presupuesto mínimo", "number"],
  ["budget_max", "Presupuesto máximo", "number"],
  ["published_from", "Desde", "date"],
  ["published_to", "Hasta (inclusive)", "date"],
];

function Evidence({ hit, reason }: { hit: Hit; reason: Reason }) {
  const [open, setOpen] = useState(false);
  const query = useQuery({
    queryKey: ["search-evidence", hit.process_id, reason.canonical_fact_id, reason.fragment_id],
    enabled: open,
    queryFn: async () =>
      unwrap(
        await api.GET("/api/search/processes/{process_id}/evidence", {
          params: {
            path: { process_id: hit.process_id },
            query: reason.canonical_fact_id
              ? { canonical_fact_id: reason.canonical_fact_id }
              : { fragment_id: reason.fragment_id },
          },
        }),
      ),
  });
  const facts = (query.data ?? []).map((value) => ({
    evidence_text: str(value.evidence_text),
    source_locator: obj(value.source_locator),
  }));
  if (!reason.canonical_fact_id && !reason.fragment_id) return null;
  return (
    <details onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary>Ver evidencia</summary>
      {open && (
        <>
          {query.isPending && <p role="status">Cargando evidencia…</p>}
          {query.isError && (
            <p role="alert">
              No fue posible recuperar evidencia vigente.{" "}
              <button onClick={() => void query.refetch()}>Reintentar</button>
            </p>
          )}
          <EvidenceDocuments documents={groupEvidence(facts)} />
        </>
      )}
    </details>
  );
}

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number(params.get("page")) || 1);
  const filters: Filters = { page, page_size: 20 };
  for (const [key, value] of params) {
    if (key === "budget_min" || key === "budget_max") filters[key] = Number(value);
    else if (key !== "page" && key !== "page_size") Object.assign(filters, { [key]: value });
  }
  const query = useQuery({
    queryKey: ["transversal-search", filters],
    queryFn: async () => unwrap(await api.GET("/api/search", { params: { query: filters } })),
  });
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const next = new URLSearchParams();
    for (const [key, value] of new FormData(event.currentTarget))
      if (typeof value === "string" && value.trim()) next.set(key, value.trim());
    setParams(next);
  };
  return (
    <section className="eureka-detail">
      <h1>Búsqueda transversal</h1>
      <p className="sub">
        Procesos SECOP persistidos, hechos vigentes y evidencia documental. El score Eureka se
        muestra sin recalcularlo.
      </p>
      <form key={params.toString()} onSubmit={submit}>
        <label>
          Buscar{" "}
          <input
            name="q"
            className="input"
            defaultValue={params.get("q") ?? ""}
            placeholder="Ej. jugo hit, chocorramo, televisor"
            maxLength={200}
          />
        </label>
        <details>
          <summary>Filtros</summary>
          <div className="filters eureka-filters">
            {fields.map(([key, label, type]) => (
              <label key={key}>
                {label}
                <input
                  name={key}
                  type={type ?? "text"}
                  min={type === "number" ? 0 : undefined}
                  defaultValue={params.get(key) ?? ""}
                />
              </label>
            ))}
            <label>
              Categoría
              <select name="category" defaultValue={params.get("category") ?? ""}>
                <option value="">Todas</option>
                {Object.entries(categoryLabels).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Prioridad
              <select name="priority" defaultValue={params.get("priority") ?? ""}>
                <option value="">Todas</option>
                <option value="high">Alta</option>
                <option value="medium">Media</option>
                <option value="low">Baja</option>
              </select>
            </label>
          </div>
        </details>
        <button className="btn primary" type="submit">
          Buscar
        </button>{" "}
        <button className="btn" type="button" onClick={() => setParams({})}>
          Limpiar
        </button>
      </form>
      {query.isPending ? (
        <p role="status">Buscando procesos…</p>
      ) : query.isError ? (
        <div role="alert">
          <p>{query.error.message}</p>
          <button className="btn" onClick={() => void query.refetch()}>
            Reintentar
          </button>
        </div>
      ) : (
        <>
          <p>
            {query.data.total} procesos · {query.data.duration_ms} ms
          </p>
          {!query.data.items.length && (
            <p>
              {page > 1
                ? "No hay resultados en esta página."
                : "Sin coincidencias para esta búsqueda."}
            </p>
          )}
          {(query.data.items as Hit[]).map((hit) => (
            <article className="card" key={hit.process_id}>
              <h2>{hit.title || hit.secop_id}</h2>
              <p>
                {hit.entity} · {hit.municipality} · {hit.department}
              </p>
              <p>
                {hit.published_on ?? "Fecha desconocida"} · {money(hit.budget_cop)}
                {hit.score != null && ` · Score Eureka ${hit.score}`}{" "}
                {hit.priority && ` · ${priorityLabels[hit.priority] ?? hit.priority}`}
              </p>
              {!!hit.products?.length && (
                <p>Productos: {hit.products.map((p) => displayValue(p.value)).join(" · ")}</p>
              )}
              {hit.matches.map((reason, index) => (
                <div key={index}>
                  <p className="small">
                    <b>{origins[reason.type]}</b> · {modes[reason.mode]} · {reason.field}
                  </p>
                  <p>{displayValue(reason.value)}</p>
                  {index === 0 && <Evidence hit={hit} reason={reason} />}
                </div>
              ))}
              {hit.detail_url ? (
                <Link className="btn" to={hit.detail_url}>
                  Ver detalle Eureka
                </Link>
              ) : (
                <p className="small">Sin oportunidad Eureka · proceso persistido</p>
              )}
              {hit.source_url && (
                <a href={hit.source_url} target="_blank" rel="noreferrer">
                  Consultar SECOP
                </a>
              )}
            </article>
          ))}
          <Pagination
            page={page}
            pageSize={20}
            total={query.data.total}
            itemLabel="procesos"
            onPageChange={(value) =>
              setParams((current) => {
                const next = new URLSearchParams(current);
                next.set("page", String(value));
                return next;
              })
            }
          />
        </>
      )}
    </section>
  );
}
