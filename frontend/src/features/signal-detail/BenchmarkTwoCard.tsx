import type { SignalDetail } from "../../api/client";
import { Badge } from "../../components/Badge";
import { formatCop, formatDate, formatPercent } from "../../lib/format";
import { METHOD_LABELS, STORE_LABELS } from "../../lib/labels";

const STATUS = {
  reference: { tone: "good", label: "Referencia de mercado (≥ 3 observaciones de ≥ 2 tiendas)" },
  limited: { tone: "neutral", label: "Referencia de mercado disponible · evidencia limitada" },
  unavailable: { tone: "neutral", label: "No disponible · evidencia insuficiente" },
} as const;

export function BenchmarkTwoCard({ detail }: { detail: SignalDetail }) {
  const status = STATUS[detail.market_status];
  const observations = detail.market_observations;
  const stores = new Set(observations.map((o) => o.store)).size;
  return (
    <div className="card">
      <div className="row">
        <h2 style={{ margin: 0 }}>Benchmark 2 · Mercado</h2>
        <span className="spacer" />
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>
      <p className="small muted" style={{ margin: "4px 0 10px" }}>
        {observations.length} observaciones de {stores} tiendas en ±30 días de la compra. Se
        requieren ≥ 3 observaciones de ≥ 2 tiendas para una referencia estadística. Solo vendedor =
        la tienda · precio efectivo de venta.
      </p>
      {observations.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Fuente</th>
              <th>Producto observado</th>
              <th className="num">Precio efectivo</th>
              <th>Fecha</th>
              <th>Método</th>
            </tr>
          </thead>
          <tbody>
            {observations.map((o) => (
              <tr key={`${o.store}-${o.observed_on}-${o.product_description}`}>
                <td>{STORE_LABELS[o.store] ?? o.store}</td>
                <td>{o.product_description}</td>
                <td className="num">{formatCop(o.effective_price_cop)}</td>
                <td>{formatDate(o.observed_on)}</td>
                <td>
                  <Badge tone="neutral">{METHOD_LABELS[o.method] ?? o.method}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {detail.market_deviation_pct !== null && detail.market_reference_cop !== null ? (
        <p className="small muted" style={{ margin: "10px 0 0" }}>
          {detail.market_status === "reference"
            ? "Desviación del precio contratado frente a la mediana de mercado: "
            : "Desviación del precio contratado frente a la observación más alta: "}
          <b>{formatPercent(detail.market_deviation_pct)}</b>
          {detail.market_status === "reference"
            ? ` (${formatCop(detail.market_reference_cop)}).`
            : '. No se presenta como "precio de mercado" por evidencia limitada.'}
        </p>
      ) : null}
    </div>
  );
}
