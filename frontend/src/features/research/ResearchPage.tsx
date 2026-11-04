import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useSearchParams } from "react-router";
import { formatCop, formatDate } from "../../lib/format";
import { EconomicCycle, type EconomicCycleData } from "./EconomicCycle";
import { PublicPriceComparison, type PurchaseSide } from "./PublicPriceComparison";
import { ComparisonReadiness, type ReadinessAudit } from "./ComparisonReadiness";
import { HumanReviewNotice, type ResearchHumanReview } from "./HumanReviewNotice";

type Document = {
  id: string;
  name: string;
  stage: string;
  source_url: string | null;
  selected: boolean;
  downloaded: boolean;
  extraction_status: string;
  text_length: number;
  pages: number;
  error: string | null;
  coverage_complete: boolean | null;
};
type ProductEvidence = {
  description: string;
  document_name: string;
  fragment_id: string;
  source_locator: { page_number?: number };
};
type Process = {
  research_human_review?: ResearchHumanReview;
  economic_cycle?: EconomicCycleData;
  id: string;
  reference: string;
  entity: string;
  department: string;
  municipality: string;
  published_at: string;
  status: string;
  object: string;
  base_price_cop: string | null;
  source_url: string | null;
  facts_count: number;
  canonicals_count: number;
  conflicts: number;
  tv_confirmed?: boolean;
  tv_confirmation_status?: string;
  canonical_summaries?: {
    id: string;
    type: string;
    status: string;
    confidence: string;
    value: unknown;
    alternatives: unknown;
    fact_ids: string[];
  }[];
  lifecycle_covered: string[];
  lifecycle_missing: string[];
  warnings: string[];
  errors: { type: string; message: string }[];
  documents: Document[];
  contracts: {
    id_contrato: string;
    estado_contrato: string;
    proveedor_adjudicado: string;
    valor_del_contrato: string;
    fecha_de_firma: string | null;
  }[];
  products: {
    description: string;
    unit_price_cop: string | null;
    quantity: string | null;
    price_stage: string;
    warnings: string[];
    screen_size_inches?: number | null;
    resolution?: string | null;
    panel?: string | null;
    smart?: boolean | null;
    brand?: string | null;
    model?: string | null;
    total_cop?: string | null;
    vat_basis?: string;
    price_reliable?: boolean;
    evidence?: {
      text?: string;
      document_name?: string;
      fragment_id?: string;
      source_locator?: {
        page_number?: number;
        sources?: { original_name: string; locator: { page_number?: number } }[];
      };
    }[];
  }[];
  specification_evidence: ProductEvidence[];
};
type Report = {
  comparison_readiness?: ReadinessAudit;
  comparison_policy?: string;
  economic_cycle_summary?: {
    processes: number;
    products: number;
    verified_purchase_unit_prices: number;
    processes_with_verified_purchase_unit_price: number;
  };
  source: string;
  window_start?: string;
  window_before?: string;
  processes: Process[];
  signals: {
    id: string;
    title: string;
    entities: string[];
    processes: string[];
    difference_pct: string;
    absolute_difference_cop: string;
    comparability: string;
    sides?: PurchaseSide[];
    days_between?: number | null;
    limitations?: string[];
  }[];
  summary?: {
    processes_found: number;
    document_candidates: number;
    processes_with_documented_tv: number;
    tv_observations: number;
    reliable_purchase_unit_prices: number;
    comparisons_possible: number;
    documents_failed: number;
    extraction_failed?: number;
    partial_coverage_documents?: number;
  };
  comparability_counts?: Record<string, number>;
  signal_status: string;
  signal_reason: string;
  comparisons: {
    processes: string[];
    comparability: string;
    limitations: string[];
    difference_pct: string | null;
    unit_price_a_cop?: string | null;
    unit_price_b_cop?: string | null;
    comparison_eligible?: boolean;
  }[];
};

const STAGES: Record<string, string> = {
  opening: "Apertura",
  specifications: "Estudios y especificaciones",
  budget: "Presupuesto",
  offer: "Oferta",
  award: "Evaluación / adjudicación",
  contract: "Contrato",
  execution: "Inicio de ejecución",
};
const LEVELS: Record<string, string> = {
  exact: "Exacto",
  high: "Altamente comparable",
  partial: "Parcialmente comparable",
  same_model: "Mismo modelo",
  highly_comparable: "Altamente comparable",
  partially_comparable: "Parcialmente comparable",
  not_comparable: "No comparable",
};
function secopUrl(value: string | null) {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    return url.protocol === "https:" &&
      url.hostname === "community.secop.gov.co" &&
      !url.username &&
      !url.password
      ? value
      : undefined;
  } catch {
    return undefined;
  }
}

export function ResearchPage({ view = "purchases" }: { view?: "purchases" | "signals" }) {
  const [pairLimit, setPairLimit] = useState(50);
  const [params, setParams] = useSearchParams();
  const report = useQuery<Report>({
    queryKey: ["investigation", "real-research"],
    queryFn: async () => {
      const response = await fetch(
        new Request(new URL("/api/v1/investigation/research", location.origin)),
      );
      if (!response.ok) throw new Error("research_unavailable");
      return (await response.json()) as Report;
    },
    retry: false,
  });
  const selected = report.data?.processes.find((p) => p.id === params.get("process"));
  const processes = report.data?.processes ?? [];
  const comparablePairs =
    report.data?.comparisons.filter((p) => p.comparability !== "not_comparable") ?? [];
  return (
    <section>
      <h1>{view === "signals" ? "Señales investigativas" : "Explorar compras reales"}</h1>
      <p className="sub">Investigación / observatorio · Televisores · Socrata / SECOP II</p>
      <div className="row" style={{ marginBottom: 18 }}>
        <span className="chip">Datos reales · muestra exploratoria</span>
        <Link to={view === "signals" ? "/explorar" : "/senales"}>
          {view === "signals" ? "Ver procesos y evidencia" : "Ver señales"}
        </Link>
        <Link to={view === "signals" ? "/demo/senales" : "/demo/explorar"} className="small muted">
          Ver demostración anterior (datos ficticios)
        </Link>
      </div>
      {report.isPending && <p role="status">Cargando investigación…</p>}
      {report.isError && (
        <div role="alert" className="notice">
          No fue posible cargar el informe real. No se sustituyó con datos de demostración.{" "}
          <button className="btn" onClick={() => void report.refetch()}>
            Reintentar
          </button>
        </div>
      )}
      {report.data && (
        <>
          {report.data.window_start && (
            <p className="small muted">
              Publicaciones desde {formatDate(report.data.window_start)} hasta antes de{" "}
              {formatDate(report.data.window_before!)}. La muestra es intencional y no representa
              todo el mercado.
            </p>
          )}
          <div className="grid g4" style={{ marginBottom: 18 }}>
            <div className="card">
              <span className="muted">Procesos reales</span>
              <h2>{processes.length}</h2>
            </div>
            <div className="card">
              <span className="muted">Documentos descargados</span>
              <h2>
                {processes.reduce((n, p) => n + p.documents.filter((d) => d.downloaded).length, 0)}
              </h2>
            </div>
            <div className="card">
              <span className="muted">Facts / canonicals</span>
              <h2>
                {processes.reduce((n, p) => n + p.facts_count, 0)} /{" "}
                {processes.reduce((n, p) => n + p.canonicals_count, 0)}
              </h2>
            </div>
            <div className="card">
              <span className="muted">Señales sustentadas</span>
              <h2>{report.data.signals.length}</h2>
            </div>
          </div>
          {report.data.summary && (
            <div className="row" style={{ marginBottom: 18 }}>
              <span className="chip">
                {report.data.summary.processes_found.toLocaleString("es-CO")} procesos encontrados
              </span>
              <span className="chip">
                {report.data.summary.document_candidates} candidatos documentales
              </span>
              <span className="chip">
                {report.data.summary.processes_with_documented_tv} procesos con TV documentados
              </span>
              <span className="chip">
                {report.data.summary.tv_observations} observaciones de producto
              </span>
              <span className="chip">
                {report.data.summary.reliable_purchase_unit_prices} precios de compra confiables
              </span>
              <span className="chip">
                {report.data.summary.comparisons_possible} comparaciones sustentadas
              </span>
              <span className="chip">
                {report.data.summary.documents_failed} descargas fallidas
              </span>
              <span className="chip">
                {report.data.summary.extraction_failed ?? 0} extracciones fallidas
              </span>
              <span className="chip">
                {report.data.summary.partial_coverage_documents ?? 0} documentos con cobertura
                parcial
              </span>
            </div>
          )}
          {report.data.economic_cycle_summary && (
            <p className="muted">
              Ciclo económico reconstruido en {report.data.economic_cycle_summary.processes}{" "}
              procesos · {report.data.economic_cycle_summary.products} registros de producto,
              incluidos parciales ·{" "}
              {report.data.economic_cycle_summary.processes_with_verified_purchase_unit_price}{" "}
              procesos con precio unitario de compra verificable. Los registros parciales no
              equivalen a compras confirmadas.
            </p>
          )}
          {report.data.comparison_policy === "research-60d-v1" && (
            <p className="muted">
              Comparación transversal de 60 días con precios de compra documentados. La fecha de
              firma verificada determina los días entre compras; la publicación se usa para
              discovery. Sin umbral porcentual ni ajuste por inflación o TRM.
            </p>
          )}
          {view === "signals" ? (
            <>
              <div className="notice info">
                <div>
                  <strong>
                    {report.data.signals.length
                      ? "Señales documentadas para revisión humana"
                      : report.data.signal_status === "not_run"
                        ? "Pendiente de muestra real"
                        : "Evidencia insuficiente para publicar una señal"}
                  </strong>
                  <p>{report.data.signal_reason}</p>
                  <p>
                    Una diferencia de precio es un indicador para revisión humana; no es una
                    conclusión sobre la contratación.
                  </p>
                </div>
              </div>
              {report.data.signals.map((signal) => (
                <article className="card" key={signal.id} style={{ marginTop: 16 }}>
                  <h2>{signal.title}</h2>
                  <p>{signal.entities.join(" / ")}</p>
                  <p>
                    {LEVELS[signal.comparability] ?? signal.comparability} · diferencia:{" "}
                    {formatCop(Number(signal.absolute_difference_cop))} (
                    {Number(signal.difference_pct).toFixed(2)} % respecto al precio menor).
                  </p>
                  {signal.processes.map((p) => (
                    <p key={p}>
                      <Link to={`/explorar?process=${encodeURIComponent(p)}`}>
                        {p} · revisar evidencia
                      </Link>
                    </p>
                  ))}
                  {signal.sides && (
                    <PublicPriceComparison
                      sides={signal.sides}
                      days={signal.days_between ?? null}
                      limitations={signal.limitations ?? []}
                    />
                  )}
                  <p className="small muted">
                    Indicador investigativo. Requiere revisión humana; no es una alerta comercial ni
                    una conclusión de irregularidad.
                  </p>
                </article>
              ))}
              {report.data.comparison_readiness && (
                <ComparisonReadiness audit={report.data.comparison_readiness} />
              )}
              <h2 style={{ marginTop: 24 }}>Comparabilidad de la muestra</h2>
              {report.data.comparability_counts && (
                <p>
                  {Object.entries(report.data.comparability_counts)
                    .map(([level, count]) => `${LEVELS[level] ?? level}: ${count}`)
                    .join(" · ")}
                  . Se cuentan pares de observaciones, no entidades ni productos únicos.
                </p>
              )}
              {comparablePairs.length === 0 ? (
                <p>
                  No hay pares de ítems documentados suficientes para comparar precios unitarios.
                  Las especificaciones aisladas y los valores globales se conservan como evidencia.
                </p>
              ) : (
                comparablePairs.slice(0, pairLimit).map((pair, i) => (
                  <div className="card" key={i}>
                    <strong>{pair.processes.join(" / ")}</strong>
                    <p>
                      {LEVELS[pair.comparability] ?? pair.comparability} ·{" "}
                      {pair.difference_pct === null
                        ? "Sin diferencia calculable"
                        : `${Number(pair.difference_pct).toFixed(2)} % respecto al precio menor`}
                    </p>
                    {(pair.unit_price_a_cop || pair.unit_price_b_cop) && (
                      <p>
                        Precio A:{" "}
                        {formatCop(pair.unit_price_a_cop ? Number(pair.unit_price_a_cop) : null)} ·
                        Precio B:{" "}
                        {formatCop(pair.unit_price_b_cop ? Number(pair.unit_price_b_cop) : null)}.
                      </p>
                    )}
                    <p>
                      {pair.comparison_eligible
                        ? "Precios de compra documentados; revisar las limitaciones antes de interpretar la diferencia."
                        : "Parecido técnico preliminar. No constituye una comparación confirmada de precios de compra."}
                    </p>
                    <p>{pair.limitations.join(" · ")}</p>
                    {pair.processes.map((p) => (
                      <p key={p}>
                        <Link to={`/explorar?process=${encodeURIComponent(p)}`}>
                          {p} · evidencia
                        </Link>
                      </p>
                    ))}
                  </div>
                ))
              )}
              {comparablePairs.length > pairLimit && (
                <button className="btn" onClick={() => setPairLimit((n) => n + 50)}>
                  Mostrar más pares ({pairLimit} de {comparablePairs.length})
                </button>
              )}
            </>
          ) : (
            <>
              {processes.length === 0 && (
                <p role="status">Aún no hay procesos de una muestra real finalizada.</p>
              )}
              {!!processes.length && (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Proceso / entidad</th>
                        <th>Ubicación</th>
                        <th>Publicación</th>
                        <th>Estado</th>
                        <th>Presupuesto base</th>
                        <th>Contrato</th>
                        <th>Evidencia</th>
                      </tr>
                    </thead>
                    <tbody>
                      {processes.map((p) => (
                        <tr key={p.id}>
                          <td>
                            <button
                              type="button"
                              className="btn"
                              onClick={() => setParams({ process: p.id })}
                            >
                              {p.reference || p.id}
                            </button>
                            <p>{p.entity}</p>
                            <small>{p.id}</small>
                          </td>
                          <td>
                            {p.municipality} / {p.department}
                          </td>
                          <td>{formatDate(p.published_at)}</td>
                          <td>{p.status}</td>
                          <td>
                            {formatCop(p.base_price_cop === null ? null : Number(p.base_price_cop))}
                            <p className="small muted">No es precio unitario</p>
                          </td>
                          <td>
                            {p.contracts.length
                              ? p.contracts.map((c) => (
                                  <p key={c.id_contrato}>
                                    {c.id_contrato}
                                    <br />
                                    {c.estado_contrato}
                                    <br />
                                    {formatCop(Number(c.valor_del_contrato))}
                                  </p>
                                ))
                              : "No publicado en la consulta"}
                          </td>
                          <td>
                            {p.documents.filter((d) => d.downloaded).length} / {p.documents.length}{" "}
                            documentos
                            <br />
                            {p.facts_count} facts · {p.canonicals_count} canonicals
                            <br />
                            {p.conflicts} conflictos
                            <HumanReviewNotice review={p.research_human_review} />
                            {p.tv_confirmed !== undefined && (
                              <p>
                                {p.tv_confirmed
                                  ? "TV documentado"
                                  : "TV no confirmado en la evidencia procesada"}
                              </p>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {selected && (
                <section
                  className="card"
                  style={{ marginTop: 24 }}
                  aria-label="Detalle investigativo"
                >
                  <div className="row">
                    <h2>
                      {selected.reference} · {selected.entity}
                    </h2>
                    <button className="btn" onClick={() => setParams({})}>
                      Cerrar detalle
                    </button>
                  </div>
                  <p>{selected.object}</p>
                  <HumanReviewNotice review={selected.research_human_review} />
                  {secopUrl(selected.source_url) && (
                    <a
                      href={secopUrl(selected.source_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Abrir proceso oficial en SECOP ↗
                    </a>
                  )}
                  <h3 style={{ marginTop: 20 }}>Ciclo de vida · cobertura documental</h3>
                  <p>
                    {selected.lifecycle_covered.map((s) => STAGES[s] ?? s).join(" · ") ||
                      "Sin etapas con texto disponible"}
                  </p>
                  <p className="muted">
                    Faltantes:{" "}
                    {selected.lifecycle_missing.map((s) => STAGES[s] ?? s).join(" · ") ||
                      "Ninguna de las etapas buscadas"}
                    . La presencia de un archivo no confirma por sí sola su contenido.
                  </p>
                  {selected.contracts.map((c) => (
                    <div className="card" key={c.id_contrato}>
                      <strong>
                        {c.id_contrato} · {c.estado_contrato}
                      </strong>
                      <p>Adjudicatario publicado: {c.proveedor_adjudicado}</p>
                      <p>
                        Valor global: {formatCop(Number(c.valor_del_contrato))} · Firma:{" "}
                        {c.fecha_de_firma ? formatDate(c.fecha_de_firma) : "No publicada"}
                      </p>
                      <small>Fuente: Socrata jbjy-vk9h · vínculo exacto por portafolio BDOS.</small>
                    </div>
                  ))}
                  {selected.economic_cycle && <EconomicCycle cycle={selected.economic_cycle} />}
                  <h3 style={{ marginTop: 20 }}>Productos y precios documentados</h3>
                  {selected.products.length === 0 && (
                    <p>
                      Los extractores actuales no reconstruyeron una fila de compra de televisor con
                      precio unitario suficientemente trazable. No se dividió el valor global del
                      contrato.
                    </p>
                  )}
                  {selected.products.map((p, i) => (
                    <article className="card" key={i}>
                      <p>{p.description}</p>
                      <p>
                        Cantidad: {p.quantity ?? "No determinada"} ·{" "}
                        {p.price_reliable
                          ? "Precio unitario documentado"
                          : "Precio unitario orientativo"}
                        : {formatCop(p.unit_price_cop ? Number(p.unit_price_cop) : null)} · Etapa:{" "}
                        {STAGES[p.price_stage] ?? p.price_stage}
                      </p>
                      <p>
                        {[
                          p.brand,
                          p.model,
                          p.screen_size_inches ? `${p.screen_size_inches} pulgadas` : null,
                          p.resolution,
                          p.panel,
                          p.smart === true ? "Smart TV" : p.smart === false ? "No Smart TV" : null,
                        ]
                          .filter(Boolean)
                          .join(" · ") || "Especificaciones incompletas"}
                        . IVA:{" "}
                        {p.vat_basis === "included"
                          ? "incluido"
                          : p.vat_basis === "excluded"
                            ? "excluido"
                            : "no determinado"}
                        .
                      </p>
                      {p.warnings.includes(
                        "derived_row_price_ambiguous_header_requires_review",
                      ) && (
                        <p className="notice">
                          Revisar encabezado de precios: la fila permite comprobar la aritmética,
                          pero no confirma por sí sola el precio contratado ni sus impuestos.
                        </p>
                      )}
                      {p.price_stage !== "contract" && p.price_stage !== "award" && (
                        <p className="small muted">
                          Precio de oferta o presupuesto; no confirmado como precio de compra.
                        </p>
                      )}
                      {p.price_stage === "offer" && (
                        <p className="small muted">
                          No se verificó que esta fila corresponda a la oferta aceptada.
                        </p>
                      )}
                      {p.warnings.some((w) => w.includes("conflict")) && (
                        <p className="notice">
                          Existe evidencia conflictiva asociada a esta observación. Los valores se
                          conservan por documento y etapa; requieren verificación manual.
                        </p>
                      )}
                      {p.evidence?.map((e, j) => (
                        <details key={j}>
                          <summary>Evidencia de la observación {j + 1}</summary>
                          <p style={{ whiteSpace: "pre-wrap" }}>{e.text}</p>
                          {e.source_locator?.sources?.map((s, k) => (
                            <p key={k}>
                              {s.original_name} · página {s.locator.page_number ?? "no registrada"}
                            </p>
                          ))}
                          {e.document_name && (
                            <p>
                              {e.document_name} · página{" "}
                              {e.source_locator?.page_number ?? "no registrada"}
                            </p>
                          )}
                        </details>
                      ))}
                    </article>
                  ))}
                  <h3 style={{ marginTop: 20 }}>
                    Especificaciones encontradas · evidencia parcial
                  </h3>
                  {selected.specification_evidence.map((e, i) => (
                    <details key={`${e.fragment_id}-${i}`} className="eureka-evidence-panel">
                      <summary>
                        {e.document_name} · página {e.source_locator.page_number ?? "no registrada"}
                      </summary>
                      <p style={{ whiteSpace: "pre-wrap" }}>{e.description}</p>
                      <small>
                        Fragmento {e.fragment_id}. No equivale a precio de compra confirmado.
                      </small>
                    </details>
                  ))}
                  <h3 style={{ marginTop: 20 }}>Hechos canónicos · valores y conflictos</h3>
                  {(selected.canonical_summaries ?? []).map((c) => (
                    <details key={c.id} className="eureka-evidence-panel">
                      <summary>
                        {c.type} ·{" "}
                        {c.status === "conflict" ? "Evidencia conflictiva · verificar" : c.status} ·
                        confianza {c.confidence}
                      </summary>
                      <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
                        {JSON.stringify(
                          c.status === "conflict" ? c.alternatives : c.value,
                          null,
                          2,
                        )}
                      </pre>
                      <small>
                        Canonical: {c.id}
                        <br />
                        Facts de soporte: {c.fact_ids.join(", ")}
                      </small>
                    </details>
                  ))}
                  <h3 style={{ marginTop: 20 }}>Documentos y cobertura</h3>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Documento</th>
                          <th>Etapa orientativa</th>
                          <th>Adquisición / extracción</th>
                          <th>Cobertura</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selected.documents.map((d) => (
                          <tr key={d.id}>
                            <td>
                              {secopUrl(d.source_url) ? (
                                <a
                                  href={secopUrl(d.source_url)}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  {d.name}
                                </a>
                              ) : (
                                d.name
                              )}
                            </td>
                            <td>{STAGES[d.stage] ?? "Fuera del alcance documental"}</td>
                            <td>
                              {!d.selected
                                ? "No seleccionado"
                                : d.downloaded
                                  ? d.extraction_status
                                  : "Descarga fallida"}
                              {d.error && <p>{d.error}</p>}
                            </td>
                            <td>
                              {d.text_length.toLocaleString("es-CO")} caracteres ·{" "}
                              {d.pages > 0 ? `${d.pages} páginas` : "Paginación no determinada"}
                              {d.coverage_complete === false && <p>Parcial · revisar</p>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="small muted">Warnings: {selected.warnings.join(" · ")}</p>
                  {selected.errors.map((e, i) => (
                    <p role="alert" key={i}>
                      {e.type}: {e.message}
                    </p>
                  ))}
                </section>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
