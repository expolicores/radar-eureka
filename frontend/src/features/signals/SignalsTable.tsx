import { useNavigate } from "react-router";

import type { Signal } from "../../api/client";
import { Badge } from "../../components/Badge";
import { ConfidenceBadge } from "../../components/ConfidenceBadge";
import { formatCop, formatDate, formatPercent } from "../../lib/format";
import { MATCH_TYPE_LABELS } from "../../lib/labels";

export function SignalsTable({ signals }: { signals: Signal[] }) {
  const navigate = useNavigate();
  const open = (code: string) => void navigate(`/senales/${code}`);
  return (
    <table>
      <thead>
        <tr>
          <th>Señal</th>
          <th>Ítem</th>
          <th>Entidad compradora</th>
          <th>Proveedor</th>
          <th className="num">Precio unitario</th>
          <th className="num">Referencia</th>
          <th className="num">Desviación</th>
          <th>Comparación</th>
          <th>Confianza</th>
          <th>Fecha</th>
        </tr>
      </thead>
      <tbody>
        {signals.map((signal) => (
          <tr key={signal.code} className="click" onClick={() => open(signal.code)}>
            <td>
              <a
                href={`/senales/${signal.code}`}
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  open(signal.code);
                }}
              >
                <Badge tone="review">⚑ {signal.code}</Badge>
              </a>
            </td>
            <td>
              <b>
                {signal.item_description}
                {signal.quantity ? ` ×${signal.quantity}` : ""}
              </b>
              <div className="small muted">{signal.purchase_reference}</div>
            </td>
            <td>
              {signal.entity_name}
              <div className="small muted">{signal.entity_department}</div>
            </td>
            <td>{signal.supplier_name}</td>
            <td className="num">{formatCop(signal.unit_price_cop)}</td>
            <td className="num">
              {formatCop(signal.median_cop)}
              <div className="small muted">mediana pública</div>
            </td>
            <td className="num">
              <b>{formatPercent(signal.deviation_pct)}</b>
            </td>
            <td>
              <Badge tone="info">{MATCH_TYPE_LABELS[signal.match_type] ?? signal.match_type}</Badge>
            </td>
            <td>
              <ConfidenceBadge level={signal.confidence_level} />
            </td>
            <td style={{ whiteSpace: "nowrap" }}>{formatDate(signal.signed_on)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
