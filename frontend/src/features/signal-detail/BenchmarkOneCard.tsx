import { useState } from "react";
import { Link } from "react-router";

import type { SignalDetail } from "../../api/client";
import { StripPlot } from "../../components/StripPlot";
import { formatCop, formatDate, formatInteger } from "../../lib/format";
import { MATCH_TYPE_LABELS, SOURCE_LABELS } from "../../lib/labels";

export function BenchmarkOneCard({ detail }: { detail: SignalDetail }) {
  const [asTable, setAsTable] = useState(false);
  const { signal, comparables } = detail;
  const secop = comparables.filter((c) => c.source === "secop_ii").length;
  const tvec = comparables.length - secop;
  const match = MATCH_TYPE_LABELS[signal.match_type] ?? signal.match_type;
  const rule =
    detail.threshold_rule === "iqr"
      ? "Umbral de revisión: Q3 + 1,5 × RIC"
      : "Umbral porcentual (muestra pequeña o heterogénea)";
  const stats: [string, string][] = [
    ["Observaciones", `${formatInteger(comparables.length)} · ${tvec} TVEC / ${secop} SECOP`],
    ["Q1", formatCop(detail.q1_cop)],
    ["Mediana", formatCop(signal.median_cop)],
    ["Q3", formatCop(detail.q3_cop)],
    ["Umbral de revisión", formatCop(detail.threshold_cop)],
  ];

  return (
    <div className="card">
      <div className="row">
        <h2 style={{ margin: 0 }}>Benchmark 1 · Compras públicas comparables</h2>
        <span className="spacer" />
        <button type="button" className="btn sm" onClick={() => setAsTable((value) => !value)}>
          {asTable ? "Ocultar tabla" : "Ver como tabla"}
        </button>
      </div>
      <p className="small muted" style={{ margin: "4px 0 0" }}>
        Televisores {match.toLowerCase()}s ({signal.item_description}) comprados por entidades
        públicas en ±{detail.window_months} meses de la fecha de la compra ·{" "}
        {formatInteger(comparables.length)} observaciones · SECOP II y TVEC · precios con IVA ·{" "}
        {rule}
      </p>
      <div className="stat-row">
        {stats.map(([label, value]) => (
          <div key={label} className="stat">
            <div className="l">{label}</div>
            <div className="v">{value}</div>
          </div>
        ))}
      </div>
      <StripPlot
        ariaLabel={`Distribución de ${comparables.length} precios unitarios de compras comparables y precio de la compra analizada (${formatCop(signal.unit_price_cop)})`}
        points={comparables.map((c) => ({
          id: `${c.purchase_id}`,
          value: c.unit_price_cop,
          shape: c.source === "tvec" ? "diamond" : "circle",
          tooltip: [
            `${SOURCE_LABELS[c.source] ?? c.source} · ${c.entity_name}`,
            `${formatCop(c.unit_price_cop)} · ${formatDate(c.signed_on)}`,
          ],
        }))}
        target={{
          value: signal.unit_price_cop,
          label: `Compra analizada ${formatCop(signal.unit_price_cop)}`,
          tooltip: [
            `Compra analizada · ${signal.entity_name}`,
            `${formatCop(signal.unit_price_cop)} · ${formatDate(signal.signed_on)}`,
          ],
        }}
        q1={detail.q1_cop}
        median={signal.median_cop}
        q3={detail.q3_cop}
        threshold={detail.threshold_cop}
      />
      {asTable ? (
        <div className="table-wrap" style={{ marginTop: 12 }}>
          <table>
            <thead>
              <tr>
                <th>Fuente</th>
                <th>Compra</th>
                <th>Entidad</th>
                <th>Fecha</th>
                <th>Emparejamiento</th>
                <th className="num">Precio unitario</th>
              </tr>
            </thead>
            <tbody>
              {comparables.map((c) => (
                <tr key={`${c.purchase_id}-${c.unit_price_cop}`}>
                  <td>{SOURCE_LABELS[c.source] ?? c.source}</td>
                  <td>
                    <Link to={`/compras/${c.purchase_id}`}>{c.reference}</Link>
                  </td>
                  <td>{c.entity_name}</td>
                  <td>{formatDate(c.signed_on)}</td>
                  <td>{c.same_model ? "Mismo modelo" : "Equivalente"}</td>
                  <td className="num">{formatCop(c.unit_price_cop)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
