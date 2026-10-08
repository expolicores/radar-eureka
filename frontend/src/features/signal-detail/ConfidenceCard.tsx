import type { SignalDetail } from "../../api/client";
import { formatCop, formatPercent } from "../../lib/format";

const LEVEL_LABELS: Record<string, string> = { high: "Alta", medium: "Media", low: "Baja" };

export function ConfidenceCard({ detail }: { detail: SignalDetail }) {
  const { signal } = detail;
  return (
    <div className="card">
      <h3 className="muted" style={{ fontWeight: 600 }}>
        Desviación frente a la mediana pública
      </h3>
      <div className="big-delta">{formatPercent(signal.deviation_pct)}</div>
      <div className="small muted">
        Precio contratado {formatCop(signal.unit_price_cop)} vs. mediana{" "}
        {formatCop(signal.median_cop)} · supera el umbral de revisión (
        {formatCop(detail.threshold_cop)})
      </div>
      <hr style={{ border: "none", borderTop: "1px solid var(--grid)", margin: "12px 0" }} />
      <h3>
        Nivel de confianza: {LEVEL_LABELS[signal.confidence_level]} ({signal.confidence_score} /
        100)
      </h3>
      <div className="penalty">
        <span>Punto de partida</span>
        <b>100</b>
      </div>
      {detail.penalties.map((penalty) => (
        <div key={penalty.code} className="penalty">
          <span>{penalty.label}</span>
          <span>−{penalty.points}</span>
        </div>
      ))}
      <p className="small muted" style={{ margin: "8px 0 0" }}>
        Configuración analítica {detail.config_version_id} · ventanas, mínimos y umbrales
        configurables.
      </p>
    </div>
  );
}
