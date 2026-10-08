import type { SignalSummary } from "../../api/client";
import { formatInteger } from "../../lib/format";

export function SignalsKpis({ summary }: { summary: SignalSummary | undefined }) {
  const value = (count: number | undefined) => (count === undefined ? "—" : formatInteger(count));
  const bySource = summary?.tv_purchases_by_source ?? {};
  const byConfidence = summary?.signals_by_confidence ?? {};
  return (
    <div className="grid g4" aria-label="Indicadores">
      <div className="card kpi">
        <div className="label">Compras de TV analizadas</div>
        <div className="value">{value(summary?.tv_purchases)}</div>
        <div className="hint">
          {value(bySource.secop_ii)} contratos SECOP II · {value(bySource.tvec)} órdenes TVEC ·
          2023–2026
        </div>
      </div>
      <div className="card kpi">
        <div className="label">Señales vigentes</div>
        <div className="value">{value(summary?.signals)}</div>
        <div className="hint">
          {value(byConfidence.high)} con confianza alta · {value(byConfidence.medium)} media ·{" "}
          {value(byConfidence.low)} baja
        </div>
      </div>
      <div className="card kpi">
        <div className="label">Comparaciones incompletas</div>
        <div className="value">{value(summary?.incomplete_comparisons)}</div>
        <div className="hint">IVA no comparable o comparables insuficientes</div>
      </div>
      <div className="card kpi">
        <div className="label">Sin información en la fuente</div>
        <div className="value">{value(summary?.without_source_information)}</div>
        <div className="hint">El documento publicado no trae precio unitario</div>
      </div>
    </div>
  );
}
