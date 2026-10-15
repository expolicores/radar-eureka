import { Link, useParams } from "react-router";
import { ApiError } from "../../api/client";
import { EvidencePanel } from "./EvidencePanel";
import { SecopProcessInfo } from "./SecopProcessInfo";
import {
  arr,
  categoryLabels,
  enrichmentLabels,
  factValue,
  missingLabels,
  money,
  obj,
  priorityLabels,
  productLabel,
  requirement,
  str,
  term,
} from "./types";
import { useEurekaDetail } from "./useEureka";

export function EurekaDetailPage() {
  const { opportunityId = "" } = useParams();
  const query = useEurekaDetail(opportunityId);
  if (query.isPending) return <p role="status">Cargando detalle Eureka…</p>;
  if (query.isError)
    return (
      <section role="alert">
        <h1>
          {query.error instanceof ApiError && query.error.status === 404
            ? "Oportunidad no encontrada"
            : "No fue posible cargar la oportunidad"}
        </h1>
        <Link to="/eureka">Volver a Eureka</Link>{" "}
        <button className="btn" onClick={() => void query.refetch()}>
          Reintentar
        </button>
      </section>
    );
  const { opportunity, details: data } = query.data;
  const c = data.commercial,
    execution = data.execution,
    payment = data.payment,
    quality = data.quality;
  const evidence = (key: string, label: string) => (
    <EvidencePanel id={opportunityId} label={label} references={data.evidence[key]} />
  );
  const field = (label: string, value: string, key: string) => (
    <div className="eureka-field">
      <dt>{label}</dt>
      <dd>{value}</dd>
      {evidence(key, label)}
    </div>
  );
  const policy = arr(data.requirements.guarantee_required).find(
    (value) => obj(factValue(value)).subject === "policy",
  );
  return (
    <section className="eureka-detail">
      <Link to="/eureka">← Volver a Eureka</Link>
      <h1>Referencia del proceso: {opportunity.reference || "No disponible"}</h1>
      <SecopProcessInfo process={opportunity} showReference={false} />
      <p className="sub">
        {opportunity.entity} ·{" "}
        {[opportunity.municipality, opportunity.department].filter(Boolean).join(" · ")}
      </p>
      <div className="card">
        <h2>Resumen</h2>
        <div className="row">
          <span className="chip">Score {data.score ?? "No determinado"}</span>
          <span className="chip">
            Prioridad {priorityLabels[data.priority ?? ""] ?? "No determinada"}
          </span>
          <span className="chip">
            {enrichmentLabels[data.enrichment_status] ?? data.enrichment_status}
          </span>
          <span className="chip">
            {data.review_required ? "Requiere revisión" : "Sin revisión pendiente"}
          </span>
        </div>
        <p>{data.category.map((code) => categoryLabels[code] ?? code).join(", ")}</p>
        {obj(quality.extraction_coverage).coverage_complete === false && (
          <p className="small" role="status">
            Cobertura documental parcial: quedan páginas o documentos pendientes de recuperación.
          </p>
        )}
        {arr(quality.discovery_review_notes).map((note, index) => (
          <p className="notice" key={index}>
            {str(note)}
          </p>
        ))}
        {data.enrichment_status !== "consolidated" && (
          <p className="notice">
            {data.enrichment_status === "conflict"
              ? "Hay discrepancias documentales. Revise los candidatos y sus evidencias."
              : "El enriquecimiento documental aún no está completo. Los datos no determinados permanecen visibles como tales."}
          </p>
        )}
      </div>
      <div className="card">
        <h2>Qué se compra</h2>
        <h3>Productos</h3>
        {arr(c.products).length ? (
          <ul>
            {arr(c.products).map((product, index) => {
              const value = obj(factValue(product));
              return (
                <li key={index}>
                  {productLabel(value.name)} · {str(value.presentation_value)}{" "}
                  {str(value.presentation_unit)}
                  {obj(product).status === "conflict" && " · En conflicto"}
                  <EvidencePanel
                    id={opportunityId}
                    label={productLabel(value.name)}
                    references={arr(data.evidence["commercial.products"]).filter(
                      (ref) => obj(ref).canonical_fact_id === obj(product).canonical_fact_id,
                    )}
                  />
                </li>
              );
            })}
          </ul>
        ) : (
          <p>No determinados</p>
        )}
        <h3>Ítems</h3>
        {arr(c.purchase_items).length ? (
          arr(c.purchase_items).map((item, index) => {
            const value = obj(factValue(item));
            return (
              <div className="eureka-item" key={index}>
                <p>{productLabel(value.description)}</p>
                <p>
                  Cantidad: {str(value.quantity)} {str(value.unit)}
                </p>
                <p>{money(value.unit_price_cop)} unitario</p>
                <p>{money(value.total_cop)} total</p>
                {obj(item).status === "conflict" && (
                  <p className="notice">
                    Ítem en conflicto: los campos disputados no tienen un valor seleccionado.
                  </p>
                )}
                <EvidencePanel
                  id={opportunityId}
                  label={`Ítem ${index + 1}`}
                  countSources
                  references={arr(data.evidence["commercial.purchase_items"]).filter(
                    (ref) => obj(ref).canonical_fact_id === obj(item).canonical_fact_id,
                  )}
                />
              </div>
            );
          })
        ) : (
          <p>No determinados</p>
        )}
        <dl>
          {field("Presupuesto", money(obj(factValue(c.budget_cop)).value), "commercial.budget_cop")}
          {field(
            "UNSPSC",
            arr(c.unspsc)
              .map((value) => str(obj(factValue(value)).code))
              .join(", ") || "No determinado",
            "commercial.unspsc",
          )}
        </dl>
      </div>
      <div className="g2">
        <div className="card">
          <h2>Ejecución</h2>
          <dl>
            {field(
              "Plazo de ejecución",
              term(factValue(execution.execution_term)),
              "execution.execution_term",
            )}
            {field(
              "Lugar de entrega",
              str(factValue(execution.delivery_location)),
              "execution.delivery_location",
            )}
            {field(
              "Número de entregas",
              factValue(execution.delivery_count) === "single"
                ? "Única"
                : factValue(execution.delivery_count) === "multiple"
                  ? "Múltiples"
                  : "No determinado",
              "execution.delivery_count",
            )}
          </dl>
        </div>
        <div className="card">
          <h2>Pago</h2>
          <dl>
            {field(
              "Modalidad",
              (
                {
                  single_payment: "Pago único",
                  partial_payments: "Pagos parciales",
                  on_delivery: "Contra entrega",
                } as Record<string, string>
              )[str(obj(factValue(payment.payment_method)).mode)] ?? "No determinada",
              "payment.payment_method",
            )}
            {field(
              "Porcentaje",
              obj(factValue(payment.payment_percentage)).value != null
                ? `${str(obj(factValue(payment.payment_percentage)).value)}%`
                : "No determinado",
              "payment.payment_percentage",
            )}
            {field("Plazo de pago", term(factValue(payment.payment_term)), "payment.payment_term")}
          </dl>
        </div>
      </div>
      <div className="card">
        <h2>Requisitos</h2>
        <dl>
          {field(
            "Póliza",
            requirement(obj(factValue(policy)).state),
            "requirements.guarantee_required",
          )}
          {field(
            "RUP",
            requirement(obj(factValue(data.requirements.rup_required)).state),
            "requirements.rup_required",
          )}
          {field(
            "Experiencia",
            requirement(obj(factValue(data.requirements.experience_required)).state),
            "requirements.experience_required",
          )}
        </dl>
        <h3>Observaciones operativas</h3>
        {arr(data.requirements.operational_observations).length ? (
          <ul>
            {arr(data.requirements.operational_observations).map((value, index) => (
              <li key={index}>{str(factValue(value))}</li>
            ))}
          </ul>
        ) : (
          <p>No determinadas</p>
        )}
        {evidence("requirements.operational_observations", "Observaciones operativas")}
      </div>
      <div className="card">
        <h2>Calidad documental</h2>
        <p>
          {arr(quality.conflicts).length} conflictos · {str(quality.canonical_fact_count)} canónicos
          · {str(quality.structured_fact_count)} hechos estructurados
        </p>
        <h3>Campos ausentes</h3>
        {arr(quality.missing_fields).length ? (
          <ul>
            {arr(quality.missing_fields).map((value, index) => (
              <li key={index}>{missingLabels[str(value)] ?? str(value)}</li>
            ))}
          </ul>
        ) : (
          <p>No hay campos ausentes en esta vista.</p>
        )}
        {arr(quality.conflicts).map((raw, index) => {
          const conflict = obj(raw);
          return (
            <details key={index}>
              <summary>Revisar conflicto: {str(conflict.type)}</summary>
              <pre>{JSON.stringify(conflict.candidates, null, 2)}</pre>
              {evidence(
                Object.keys(data.evidence).find((key) =>
                  arr(data.evidence[key]).some(
                    (ref) => obj(ref).canonical_fact_id === conflict.canonical_fact_id,
                  ),
                ) ?? "",
                "Conflicto",
              )}
            </details>
          );
        })}
      </div>
    </section>
  );
}
