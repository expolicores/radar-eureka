import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router";
import { formatCop, formatBogotaEventDateTime } from "../../lib/format";
import { evidenceLabel, limitationLabel, rejectionLabel, sufficiencyLabel } from "./marketLabels";
import type { MarketReport, Observation } from "./marketTypes";
import "./MarketBenchmark.css";

export type { MarketReport } from "./marketTypes";
const money = (value: string | null | undefined, currency = "COP") =>
  value != null
    ? currency === "COP"
      ? formatCop(Number(value))
      : `${value} ${currency}`
    : "No verificable";

function ExternalLink({ url, children }: { url?: string | null; children: React.ReactNode }) {
  return url && /^https:\/\//i.test(url) ? (
    <a href={url} target="_blank" rel="noreferrer">
      {children} ↗
    </a>
  ) : (
    <span>{children}</span>
  );
}
export function EvidenceQualityBadge({ quality }: { quality?: string }) {
  return <span className="badge market-quality">{evidenceLabel(quality)}</span>;
}

function ObservationTable({
  rows,
  duplicates = false,
}: {
  rows: Observation[];
  duplicates?: boolean;
}) {
  return (
    <div className="table-scroll">
      <table className="market-observations">
        <thead>
          <tr>
            <th>Tienda / producto</th>
            <th>Referencia / identidad</th>
            <th>Precio</th>
            <th>Evidencia / captura</th>
            <th>Resultado</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((o, i) => (
            <tr key={`${o.url}-${i}`}>
              <td>
                <strong>{o.retailer}</strong>
                <p>{o.market_product_title}</p>
                <ExternalLink url={o.url}>Abrir oferta de {o.retailer}</ExternalLink>
                {o.listing_id && (
                  <p className="small">
                    Publicación: {o.listing_id} · vendedor:{" "}
                    {o.seller_name ?? o.seller_id ?? "no identificado"}
                  </p>
                )}
                {o.condition && <p className="small">Condición: {o.condition}</p>}
              </td>
              <td>
                {o.model ?? "Referencia no confirmada"}
                <p className="small">
                  {o.match_level} · {o.match_reason}
                </p>
                {o.page_type && (
                  <p className="small muted">
                    Página: {o.page_type} · prioridad: {o.discovery_score ?? "—"}
                  </p>
                )}
              </td>
              <td>
                {o.currency === null
                  ? `${o.price ?? "Sin precio"} · moneda no confirmada`
                  : money(o.price, o.currency)}
                {o.currency_inferred && (
                  <p className="small muted">COP inferido por contexto del proveedor</p>
                )}
                {typeof o.shipping === "string" && <p className="small">Envío: {o.shipping}</p>}
                {o.promotion_detected && <p className="small">Promoción registrada</p>}
              </td>
              <td>
                <EvidenceQualityBadge quality={o.price_evidence_level} />
                {o.price_evidence_level === "shopping_provider_price" && (
                  <p className="small muted">
                    Precio de proveedor; tienda y checkout sin verificar
                  </p>
                )}
                <p className="small">{formatBogotaEventDateTime(o.captured_at)} · Bogotá</p>
                {o.discovery_method && (
                  <p className="small muted">
                    Obtención: {o.discovery_method} · {o.extraction_method ?? "no registrada"}
                  </p>
                )}
              </td>
              <td>
                <span
                  className={`badge ${o.valid_for_benchmark && !duplicates ? "b-good" : "b-review"}`}
                >
                  {duplicates
                    ? "Duplicada · no contada"
                    : o.valid_for_benchmark
                      ? "Aceptada monetariamente"
                      : ["partial", "ambiguous"].includes(o.match_level)
                        ? "Ambigua · excluida"
                        : "Rechazada"}
                </span>
                {o.rejection_reason && (
                  <p className="small">{rejectionLabel(o.rejection_reason)}</p>
                )}
                {!o.valid_for_benchmark && !o.rejection_reason && !duplicates && (
                  <p className="small">Identidad incompleta; no entra en estadísticas.</p>
                )}
                {o.duplicate_of && <p className="small">Duplicada de: {o.duplicate_of}</p>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProviderStatus({ report }: { report: MarketReport }) {
  return (
    <details>
      <summary>Estado de las fuentes y diagnóstico</summary>
      {report.shopping_discovery && (
        <p className="small">
          SerpApi: {report.shopping_discovery.source_status ?? "no registrado"} ·{" "}
          {report.shopping_discovery.valid_observations ?? 0} referencias válidas ·{" "}
          {report.shopping_discovery.request_count ?? 0} consultas
        </p>
      )}
      {report.market_price_scout && (
        <p className="small">
          Market Price Scout: {report.market_price_scout.status} ·{" "}
          {report.market_price_scout.requested_missing_observations} observaciones faltantes ·{" "}
          {report.market_price_scout.candidates_received} ofertas recibidas
        </p>
      )}
      {report.web_discovery && (
        <p className="small">
          Búsqueda web: {report.web_discovery.queries_executed}/
          {report.web_discovery.queries_planned} consultas ·{" "}
          {report.web_discovery.unique_strong_page_urls} páginas concretas compatibles
          {report.web_discovery.canonical_model_used && (
            <> · referencia enriquecida: {report.web_discovery.canonical_model_used}</>
          )}
        </p>
      )}
      {report.mercadolibre && (
        <p className="small">
          Catálogo Mercado Libre:{" "}
          {report.mercadolibre.catalog_product_id ?? "sin selección confirmada"} ·{" "}
          {report.mercadolibre.catalog_selection_reason}
        </p>
      )}
      {report.errors?.map((e, i) => (
        <p className="small" key={i}>
          Fuente de mercado: {e.code}
          {e.http_status ? ` (HTTP ${e.http_status})` : ""}
        </p>
      ))}
    </details>
  );
}

export function MarketBenchmarkCard({
  report,
  signals = false,
}: {
  report: MarketReport;
  signals?: boolean;
}) {
  const b = report.benchmark,
    p = report.public_product,
    c = report.comparison;
  const accepted = b.observations.filter((o) => o.valid_for_benchmark);
  const excluded = b.observations.filter((o) => !o.valid_for_benchmark);
  const diverse = ["sufficient_diverse", "sufficient_diverse_market_evidence"].includes(
    b.evidence_sufficiency ?? "",
  );
  const partial = b.benchmark_status !== "ready" || !diverse;
  const limitations = [
    ...new Set([
      ...(report.preliminary_comparison?.limitations ?? []),
      ...b.limitations,
      ...(p?.evidence_warnings ?? []),
    ]),
  ];
  const degraded =
    report.shopping_discovery?.source_status === "degraded" ||
    report.mercadolibre?.source_status === "degraded" ||
    report.market_price_scout?.status === "degraded" ||
    !!report.errors?.length;
  return (
    <article className="card market-detail" aria-label="Benchmark mercado privado">
      <header className="market-header">
        <div>
          <p className="small muted">Evidencia pública → mercado privado → comparación → señal</p>
          <h2>
            {report.product.brand} {report.product.model}
          </h2>
          {report.product.canonical_model && (
            <p className="small">Referencia canónica: {report.product.canonical_model}</p>
          )}
          <p>
            {p?.public_process_code ?? "Proceso no vinculado"} ·{" "}
            {p?.public_entity ?? "Entidad no registrada"}
          </p>
        </div>
        <span className="badge b-review">
          {sufficiencyLabel(b.evidence_sufficiency, b.benchmark_status)}
        </span>
      </header>
      {degraded && (
        <p className="notice" role="status">
          Una fuente de mercado está degradada; el benchmark continúa con la evidencia disponible.
          Consulte el diagnóstico.
        </p>
      )}
      <div className="market-panels">
        <section aria-label="Evidencia pública" className="market-panel">
          <h3>Evidencia pública</h3>
          {p ? (
            <>
              <p className="market-price">{money(p.public_unit_price)}</p>
              <span className="badge b-review">
                {p.public_price_stage === "offer"
                  ? "Oferta documentada — aceptación/adjudicación no confirmada"
                  : p.public_price_stage === "contract"
                    ? "Contrato confirmado"
                    : p.public_price_stage === "awarded"
                      ? "Adjudicado confirmado"
                      : p.public_price_stage === "accepted_offer"
                        ? "Oferta aceptada confirmada"
                        : "Evidencia no resuelta"}
              </span>
              <dl className="market-facts">
                <dt>Producto</dt>
                <dd>
                  {p.public_product_description ??
                    `${report.product.brand} ${report.product.model}`}
                </dd>
                <dt>Cantidad</dt>
                <dd>{p.quantity ?? "No registrada"}</dd>
                <dt>Oferente / proveedor</dt>
                <dd>{p.supplier ?? "No registrado"}</dd>
                <dt>Documento</dt>
                <dd>
                  <ExternalLink url={p.public_document_url}>{p.public_document}</ExternalLink>
                </dd>
                <dt>Página</dt>
                <dd>{p.public_page_reference}</dd>
                <dt>Base tributaria</dt>
                <dd>
                  {p.price_tax_basis === "excludes_vat"
                    ? "Precio antes de IVA"
                    : p.price_tax_basis === "includes_vat"
                      ? "Incluye IVA"
                      : "No confirmada"}
                </dd>
                <dt>Fecha del precio público</dt>
                <dd>
                  {p.public_price_date
                    ? formatBogotaEventDateTime(p.public_price_date)
                    : "No acreditada"}
                </dd>
              </dl>
              {p.evidence_warnings?.map((w) => (
                <p className="notice small" key={w}>
                  {w === "document_process_reference_mismatch" && p.document_heading_process_code
                    ? `El documento contiene referencia ${p.document_heading_process_code} aunque está asociado al proceso ${p.public_process_code}. Requiere verificación manual.`
                    : limitationLabel(w)}
                </p>
              ))}
              <details>
                <summary>Referencia de evidencia</summary>
                <p className="small market-reference">{p.public_evidence_ref}</p>
              </details>
            </>
          ) : (
            <p>
              No se ha vinculado evidencia pública verificable. No se genera comparación ni señal.
            </p>
          )}
        </section>
        <section aria-label="Benchmark privado" className="market-panel">
          <h3>Benchmark privado</h3>
          <p className="market-price">
            {b.valid_observations_count}{" "}
            <span className="small">observaciones monetarias válidas</span>
          </p>
          {b.benchmark_status !== "ready" && (
            <p>{b.valid_observations_count} de 3 observaciones mínimas requeridas</p>
          )}
          <p>{b.independent_sources_count ?? b.retailers_count} fuentes/retailers independientes</p>
          {b.distinct_sellers_count !== undefined && (
            <p className="small">{b.distinct_sellers_count} vendedores Mercado Libre</p>
          )}
          <p className="small">Captura: {formatBogotaEventDateTime(b.captured_at)} · Bogotá</p>
          <p className="small">
            {accepted.map((o) => o.retailer).join(" · ") || "Sin ofertas aceptadas"}
          </p>
          <h4>{partial ? "Estadísticas parciales" : "Estadísticas del benchmark"}</h4>
          <dl className="market-stats">
            <div>
              <dt>Mínimo</dt>
              <dd>{money(b.min_price)}</dd>
            </div>
            <div>
              <dt>Mediana privada</dt>
              <dd>{money(b.median_price)}</dd>
            </div>
            <div>
              <dt>Máximo</dt>
              <dd>{money(b.max_price)}</dd>
            </div>
          </dl>
          {partial && (
            <p className="small muted">
              Referencias descriptivas; no constituyen un benchmark definitivo ni habilitan por sí
              solas una comparación.
            </p>
          )}
          {["marketplace_concentrated", "marketplace_concentrated_evidence"].includes(
            b.evidence_sufficiency ?? "",
          ) && (
            <p className="notice small">
              Evidencia concentrada en marketplace; varios vendedores no equivalen a fuentes
              diversas.
            </p>
          )}
        </section>
      </div>
      <section aria-label="Observaciones privadas">
        <h3>Ofertas de mercado</h3>
        {accepted.length ? (
          <ObservationTable rows={accepted} />
        ) : (
          <p>No hay observaciones monetarias aceptadas.</p>
        )}
        <details>
          <summary>Observaciones ambiguas o rechazadas ({excluded.length})</summary>
          {excluded.length ? (
            <ObservationTable rows={excluded} />
          ) : (
            <p>No hay ofertas excluidas.</p>
          )}
        </details>
        {!!b.duplicates?.length && (
          <details>
            <summary>Duplicados no contados ({b.duplicates.length})</summary>
            <ObservationTable rows={b.duplicates} duplicates />
          </details>
        )}
      </section>
      <div className="market-panels">
        <section className="market-panel" aria-label="Comparación">
          <h3>Comparación</h3>
          {c ? (
            <>
              <p>Comparación monetaria disponible según el backend.</p>
              <dl className="market-facts">
                <dt>Precio público</dt>
                <dd>{money(c.public_unit_price)}</dd>
                <dt>Mediana privada</dt>
                <dd>{money(c.private_median_price)}</dd>
                <dt>Diferencia absoluta</dt>
                <dd>{money(c.absolute_difference)}</dd>
                <dt>Diferencia porcentual</dt>
                <dd>{c.percentage_difference} %</dd>
                <dt>Comparabilidad</dt>
                <dd>{sufficiencyLabel(b.evidence_sufficiency, b.benchmark_status)}</dd>
              </dl>
              <p className="small">
                Fecha pública: {formatBogotaEventDateTime(c.public_price_date)} · Mercado:{" "}
                {formatBogotaEventDateTime(c.market_captured_at)} · Separación temporal:{" "}
                {c.time_gap_days} días
              </p>
            </>
          ) : (
            <>
              <p>
                <strong>Comparación monetaria no generada</strong>
              </p>
              <p className="small">
                No se calcula una diferencia ni un porcentaje en esta vista. Revise las limitaciones
                de evidencia indicadas abajo.
              </p>
            </>
          )}
        </section>
        <section className="market-panel" aria-label="Señal">
          <h3>Señal</h3>
          {report.signal ? (
            <>
              <p>
                <strong>Diferencia cuantificada reportada por el backend</strong>
              </p>
              <p>{report.signal.meaning}</p>
              {signals && <p className="small">{report.signal.type}</p>}
            </>
          ) : (
            <>
              <p>
                <strong>Sin señal definitiva</strong>
              </p>
              <p className="small">
                El backend no emitió una señal. La evidencia disponible y sus limitaciones se
                conservan para revisión.
              </p>
            </>
          )}
        </section>
      </div>
      <section aria-label="Limitaciones">
        <h3>Limitaciones y comparabilidad</h3>
        {limitations.length ? (
          <ul>
            {limitations.map((l) => (
              <li key={l}>{limitationLabel(l)}</li>
            ))}
          </ul>
        ) : (
          <p>No hay limitaciones registradas en el recibo.</p>
        )}
      </section>
      <ProviderStatus report={report} />
    </article>
  );
}

const reportKey = (r: MarketReport) =>
  r.report_id ?? r.public_product?.public_evidence_ref ?? `${r.product.brand}-${r.product.model}`;
export function MarketBenchmarks({ signals = false }: { signals?: boolean }) {
  const [params] = useSearchParams();
  const query = useQuery<{ reports: MarketReport[] }>({
    queryKey: [
      "investigation",
      "private-market",
      params.get("private_run") ?? params.get("market_run"),
    ],
    retry: false,
    queryFn: async () => {
      const response = await fetch(
        new Request(
          new URL(
            "/api/v1/investigation/private-market" +
              ((params.get("private_run") ?? params.get("market_run"))
                ? `?run_id=${encodeURIComponent((params.get("private_run") ?? params.get("market_run"))!)}`
                : ""),
            location.origin,
          ),
        ),
      );
      if (!response.ok) throw new Error("market_report_unavailable");
      const data = (await response.json()) as { reports: MarketReport[] };
      if (!Array.isArray(data.reports)) throw new Error("market_report_unavailable");
      return data;
    },
  });
  if (query.isPending) return <p role="status">Cargando comparaciones de mercado…</p>;
  if (query.isError)
    return (
      <div className="notice" role="alert">
        No fue posible cargar los recibos de mercado. No se sustituyeron por datos de demostración.{" "}
        <button className="btn" onClick={() => void query.refetch()}>
          Reintentar carga de mercado
        </button>
      </div>
    );
  const selected = query.data.reports.find((r) => reportKey(r) === params.get("market"));
  const back = new URLSearchParams(params);
  back.delete("market");
  if (params.has("market"))
    return (
      <section className="market-view">
        <Link to={`/explorar?${back}`}>← Volver al contexto del proceso</Link>
        {selected ? (
          <MarketBenchmarkCard report={selected} signals={signals} />
        ) : (
          <p role="status">
            Recibo no disponible. Puede haber sido sustituido por una publicación más reciente.
          </p>
        )}
      </section>
    );
  const process = params.get("process");
  const reports = query.data.reports.filter(
    (r) =>
      !process ||
      [r.public_product?.public_process_identity, r.public_product?.public_process_code].includes(
        process,
      ),
  );
  return (
    <section className="market-view" aria-label="Comparaciones de mercado">
      <h2>Estado vs mercado privado</h2>
      {!reports.length && (
        <p className="muted">
          Benchmark no ejecutado o recibo no disponible{process ? " para este proceso" : ""}. Esta
          vista solo lee resultados publicados; no realiza búsquedas.
        </p>
      )}
      {reports.map((r) => {
        const link = new URLSearchParams(params);
        link.set("market", reportKey(r));
        const identity = r.public_product?.public_process_identity;
        if (identity) link.set("process", identity);
        return (
          <article key={reportKey(r)} className="card market-preview">
            <div>
              <h3>
                {r.product.brand} {r.product.model}
              </h3>
              <p>
                {r.public_product?.public_process_code ?? "Sin proceso vinculado"} ·{" "}
                {r.public_product?.public_entity ?? "Entidad no registrada"}
              </p>
              <p className="small">
                {r.benchmark.valid_observations_count} observaciones válidas ·{" "}
                {sufficiencyLabel(r.benchmark.evidence_sufficiency, r.benchmark.benchmark_status)}
              </p>
            </div>
            <Link className="btn" to={`/explorar?${link}`}>
              Ver comparación de mercado
            </Link>
          </article>
        );
      })}
    </section>
  );
}
