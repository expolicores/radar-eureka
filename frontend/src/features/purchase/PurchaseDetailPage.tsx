import { Link, useParams } from "react-router";

import { ApiError } from "../../api/client";
import { Badge } from "../../components/Badge";
import { SaveToCaseButton } from "../../components/SaveToCaseButton";
import { formatBogotaDateTime, formatCop, formatDate } from "../../lib/format";
import {
  CLASSIFICATION_LABELS,
  OUTCOME_LABELS,
  PRICE_STATUS_LABELS,
  SOURCE_LABELS,
  VAT_LABELS,
} from "../../lib/labels";
import { AnalysisStatusBadge } from "../explore/AnalysisStatusBadge";
import { usePurchase } from "./usePurchase";

export function PurchaseDetailPage() {
  const { purchaseId = "" } = useParams();
  const query = usePurchase(purchaseId);

  if (query.isPending) {
    return (
      <p className="table-state" role="status">
        Cargando compra…
      </p>
    );
  }
  if (query.isError) {
    const notFound = query.error instanceof ApiError && [400, 404].includes(query.error.status);
    return (
      <div className="table-state" role="alert">
        <p>
          {notFound
            ? "Compra no encontrada."
            : "No fue posible cargar la compra. Intenta de nuevo."}
        </p>
        <Link to="/explorar">← Volver a Explorar compras</Link>
      </div>
    );
  }

  const purchase = query.data;
  const supplier = purchase.supplier_is_natural_person
    ? purchase.supplier_name
    : `${purchase.supplier_name}${purchase.supplier_nit ? ` · NIT ${purchase.supplier_nit}` : ""}`;
  return (
    <section>
      <div className="breadcrumb">
        <Link to="/explorar">Explorar compras</Link> › {purchase.reference}
      </div>
      <div className="row">
        <h1>Ficha de la compra {purchase.reference}</h1>
        <span className="spacer" />
        <AnalysisStatusBadge status={purchase.analysis_status} />
        <SaveToCaseButton kind="purchase" reference={purchase.id} />
      </div>
      <p className="sub">
        {purchase.data_cutoff_at
          ? `Datos actualizados al ${formatBogotaDateTime(purchase.data_cutoff_at)} · `
          : ""}
        Fuente: {SOURCE_LABELS[purchase.source] ?? purchase.source}
        {purchase.source_url
          ? null
          : " · enlace a la fuente no disponible en los datos de demostración"}
      </p>

      <div className="grid g2">
        <div className="card">
          <h3>Datos clave</h3>
          <dl className="kv">
            <dt>Entidad</dt>
            <dd>{purchase.entity_name}</dd>
            <dt>Proveedor</dt>
            <dd>{supplier}</dd>
            <dt>Objeto</dt>
            <dd>{purchase.object_description}</dd>
            <dt>Modalidad</dt>
            <dd>{purchase.modality}</dd>
            <dt>Valor de la compra</dt>
            <dd>
              {formatCop(purchase.total_value_cop)}{" "}
              <span className="muted small">
                (dato de referencia publicado; no se usa como precio unitario)
              </span>
            </dd>
            <dt>Fecha de firma</dt>
            <dd>{formatDate(purchase.signed_on)}</dd>
            <dt>Ubicación</dt>
            <dd>
              {[purchase.entity_municipality, purchase.entity_department]
                .filter(Boolean)
                .join(", ")}
            </dd>
            {purchase.proceso_de_compra ? (
              <>
                <dt>Proceso</dt>
                <dd>{purchase.proceso_de_compra}</dd>
              </>
            ) : null}
          </dl>
        </div>
        <div className="card">
          <h3>Ítems de la compra</h3>
          <table>
            <thead>
              <tr>
                <th>Ítem</th>
                <th>Clasificación</th>
                <th className="num">Cant.</th>
                <th className="num">Precio unitario</th>
                <th>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {purchase.items.map((item) => (
                <tr key={item.line_number}>
                  <td>
                    {item.description}
                    <div className="small muted">
                      {VAT_LABELS[item.vat_basis] ?? item.vat_basis} · precio{" "}
                      {PRICE_STATUS_LABELS[item.unit_price_status] ?? item.unit_price_status}
                    </div>
                  </td>
                  <td>
                    <Badge tone={item.classification === "included" ? "good" : "neutral"}>
                      {CLASSIFICATION_LABELS[item.classification] ?? item.classification}
                    </Badge>
                  </td>
                  <td className="num">{item.quantity ?? "—"}</td>
                  <td className="num">{formatCop(item.unit_price_cop)}</td>
                  <td>
                    {item.signal_code ? (
                      <Link to={`/senales/${item.signal_code}`}>
                        <Badge tone="review">⚑ Señal {item.signal_code}</Badge>
                      </Link>
                    ) : item.comparison_outcome ? (
                      <span className="small">
                        {OUTCOME_LABELS[item.comparison_outcome] ?? item.comparison_outcome}
                      </span>
                    ) : (
                      <span className="small muted">Fuera de categoría</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
