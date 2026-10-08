import { useNavigate } from "react-router";

import type { PurchaseSummary } from "../../api/client";
import { formatCop, formatDate } from "../../lib/format";
import { AnalysisStatusBadge } from "./AnalysisStatusBadge";
import { SOURCE_LABELS } from "../../lib/labels";

export function PurchasesTable({ purchases }: { purchases: PurchaseSummary[] }) {
  const navigate = useNavigate();
  return (
    <table>
      <thead>
        <tr>
          <th>Compra</th>
          <th>Fuente</th>
          <th>Entidad</th>
          <th>Proveedor</th>
          <th>Objeto</th>
          <th className="num">Valor</th>
          <th>Estado del análisis</th>
          <th>Fecha</th>
        </tr>
      </thead>
      <tbody>
        {purchases.map((purchase) => (
          <tr
            key={purchase.id}
            className="click"
            onClick={() => void navigate(`/compras/${purchase.id}`)}
          >
            <td>
              <a
                href={`/compras/${purchase.id}`}
                onClick={(event) => {
                  // La fila ya navega: el enlace solo evita la recarga y existe para el teclado.
                  event.preventDefault();
                  event.stopPropagation();
                  void navigate(`/compras/${purchase.id}`);
                }}
              >
                <b>{purchase.reference}</b>
              </a>
            </td>
            <td>{SOURCE_LABELS[purchase.source] ?? purchase.source}</td>
            <td>
              {purchase.entity_name}
              <div className="small muted">{purchase.entity_department}</div>
            </td>
            <td>{purchase.supplier_name}</td>
            <td>{purchase.object_description}</td>
            <td className="num">{formatCop(purchase.total_value_cop)}</td>
            <td>
              <AnalysisStatusBadge status={purchase.analysis_status} />
            </td>
            <td style={{ whiteSpace: "nowrap" }}>{formatDate(purchase.signed_on)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
