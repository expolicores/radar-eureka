import { Link } from "react-router";
import { formatCop, formatDate } from "../../lib/format";

type DocumentEvidence = {
  source_document?: string;
  source_page?: number | null;
  extraction_method?: string;
  evidence_text?: string;
};
export type PurchaseSide = {
  entity: string;
  process_identity: string;
  process_code?: string | null;
  description: string;
  date: string | null;
  date_source: string | null;
  unit_price: string | null;
  quantity: string | null;
  unit: string | null;
  currency: string;
  tax_basis: string;
  price_stage: string;
  characteristics: Record<string, string | number | boolean | null>;
  evidence: {
    value_origin?: string;
    evidence?: DocumentEvidence[];
    acceptance_evidence?: DocumentEvidence[];
  }[];
};

export function PublicPriceComparison({
  sides,
  days,
  limitations,
}: {
  sides: PurchaseSide[];
  days: number | null;
  limitations: string[];
}) {
  const labels: Record<string, string> = {
    product_class: "Clase de producto",
    brand: "Marca",
    model: "Modelo",
    screen_size_inches: "Pulgadas",
    resolution: "Resolución",
    smart: "Smart TV",
    panel: "Pantalla",
  };
  const notes: Record<string, string> = {
    no_inflation_or_fx_adjustment: "Sin ajuste por inflación o TRM",
    temporal_proximity_does_not_guarantee_equal_conditions:
      "Fechas próximas no garantizan condiciones iguales",
    accessories_installation_warranty_delivery_conditions_not_fully_verified:
      "Accesorios, instalación, garantía y entrega requieren verificación de condiciones",
    tax_basis_unverified_requires_human_review: "Base IVA no verificada; requiere revisión manual",
    noncritical_budget_conflict_preserved:
      "Hay referencias presupuestales previas distintas; se conserva el precio contractual explícito",
    different_or_unknown_model: "Modelo diferente o no determinado",
    delivery_warranty_scope_unverified: "Alcance de entrega y garantía no verificado",
    exact_explicit_reference_brand_may_be_unknown:
      "Referencia explícita coincidente; la marca puede no estar publicada",
  };
  return (
    <details>
      <summary>Abrir ambos lados de la comparación y su evidencia</summary>
      <p>
        Días entre compras: {days ?? "Desconocidos"}. Sin ajuste por inflación o TRM. La proximidad
        temporal reduce, pero no elimina, diferencias de mercado y condiciones.
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Campo</th>
              {sides.map((side, index) => (
                <th key={side.process_identity}>Compra {index === 0 ? "A" : "B"}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Entidad</td>
              {sides.map((s) => (
                <td key={s.process_identity}>{s.entity}</td>
              ))}
            </tr>
            <tr>
              <td>Proceso</td>
              {sides.map((s) => (
                <td key={s.process_identity}>
                  <Link to={`/explorar?process=${encodeURIComponent(s.process_identity)}`}>
                    {s.process_code ?? s.process_identity}
                  </Link>
                </td>
              ))}
            </tr>
            <tr>
              <td>Producto</td>
              {sides.map((s) => (
                <td key={s.process_identity}>{s.description}</td>
              ))}
            </tr>
            <tr>
              <td>Fecha de compra</td>
              {sides.map((s) => (
                <td key={s.process_identity}>
                  {s.date ? formatDate(s.date) : "Sin fecha de compra verificada"}
                  <br />
                  <small>
                    {s.date_source === "socrata_jbjy-vk9h_fecha_de_firma"
                      ? "Firma del contrato · Socrata/SECOP"
                      : s.date_source}
                  </small>
                </td>
              ))}
            </tr>
            <tr>
              <td>Precio unitario</td>
              {sides.map((s) => (
                <td key={s.process_identity}>
                  {formatCop(s.unit_price ? Number(s.unit_price) : null)} {s.currency}
                  <br />
                  <small>
                    {s.price_stage === "contract" ? "Contrato" : "Adjudicación / oferta aceptada"}
                  </small>
                </td>
              ))}
            </tr>
            <tr>
              <td>Cantidad y unidad</td>
              {sides.map((s) => (
                <td key={s.process_identity}>
                  {s.quantity ?? "Desconocida"} · {s.unit ?? "Unidad desconocida"}
                </td>
              ))}
            </tr>
            {Object.entries(labels).map(([key, label]) => (
              <tr key={key}>
                <td>{label}</td>
                {sides.map((s) => (
                  <td key={s.process_identity}>
                    {s.characteristics[key] === null || s.characteristics[key] === undefined
                      ? "Desconocido"
                      : String(s.characteristics[key])}
                  </td>
                ))}
              </tr>
            ))}
            <tr>
              <td>IVA</td>
              {sides.map((s) => (
                <td key={s.process_identity}>
                  {s.tax_basis === "included"
                    ? "Incluido"
                    : s.tax_basis === "excluded"
                      ? "Excluido"
                      : "Base no verificada; revisar"}
                </td>
              ))}
            </tr>
            <tr>
              <td>Evidencia del precio</td>
              {sides.map((s) => (
                <td key={s.process_identity}>
                  {s.evidence.map((a, index) => (
                    <div key={index}>
                      <p>
                        {a.value_origin === "calculated"
                          ? "Calculado con total/cantidad documentados"
                          : "Explícito"}
                      </p>
                      {[...(a.evidence ?? []), ...(a.acceptance_evidence ?? [])].map((e, j) => (
                        <div key={j}>
                          <p>
                            {e.source_document} · página {e.source_page ?? "no determinada"} ·{" "}
                            {e.extraction_method}
                          </p>
                          <blockquote>{e.evidence_text}</blockquote>
                        </div>
                      ))}
                    </div>
                  ))}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <p>Limitaciones: {limitations.map((note) => notes[note] ?? note).join(" · ")}</p>
    </details>
  );
}
