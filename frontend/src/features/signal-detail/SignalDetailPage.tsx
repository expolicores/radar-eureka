import { Link, useParams } from "react-router";

import { ApiError } from "../../api/client";
import { Badge } from "../../components/Badge";
import { ConfidenceBadge } from "../../components/ConfidenceBadge";
import { SaveToCaseButton } from "../../components/SaveToCaseButton";
import { formatBogotaDateTime, formatDate } from "../../lib/format";
import { VAT_LABELS } from "../../lib/labels";
import { BenchmarkOneCard } from "./BenchmarkOneCard";
import { BenchmarkTwoCard } from "./BenchmarkTwoCard";
import { ConfidenceCard } from "./ConfidenceCard";
import { useSignal } from "./useSignal";

export function SignalDetailPage() {
  const { code = "" } = useParams();
  const query = useSignal(code);

  if (query.isPending) {
    return (
      <p className="table-state" role="status">
        Cargando señal…
      </p>
    );
  }
  if (query.isError) {
    const notFound = query.error instanceof ApiError && query.error.status === 404;
    return (
      <div className="table-state" role="alert">
        <p>
          {notFound
            ? "Señal no encontrada: no existe o ya no está vigente tras el último recálculo."
            : "No fue posible cargar la señal. Intenta de nuevo."}
        </p>
        <Link to="/senales">← Volver a la lista de señales</Link>
      </div>
    );
  }

  const detail = query.data;
  const { signal } = detail;
  return (
    <section>
      <div className="breadcrumb">
        <Link to="/senales">Señales</Link> › {signal.code}
      </div>
      <div className="row" style={{ alignItems: "flex-start" }}>
        <h1>
          {signal.item_description}
          {signal.quantity ? ` — ${signal.quantity} unidades` : ""}
        </h1>
        <span className="spacer" />
        <SaveToCaseButton kind="signal" reference={signal.code} />
      </div>
      <p className="sub" style={{ marginBottom: 8 }}>
        Compra <Link to={`/compras/${signal.purchase_id}`}>{signal.purchase_reference}</Link> ·{" "}
        {signal.entity_name} · {detail.modality} · Firmada el {formatDate(signal.signed_on)}
      </p>
      <div className="row">
        <Badge tone="review">⚑ Merece revisión</Badge>
        <ConfidenceBadge level={signal.confidence_level} prefix="Confianza " />
        <Badge tone="info">
          {signal.match_type === "same_model" ? "Mismo modelo" : "Producto equivalente"}
        </Badge>
        <Badge tone="good">
          ✓ IVA: misma base ({VAT_LABELS[detail.vat_basis] ?? detail.vat_basis})
        </Badge>
        <Badge tone="neutral">Configuración {detail.config_version_id} · vigente</Badge>
      </div>

      <div className="notice" role="note" style={{ margin: "14px 0" }}>
        <span aria-hidden="true">ⓘ</span>
        <div>
          Esta señal <b>no constituye una conclusión ni una acusación</b>. El precio puede
          explicarse por condiciones no publicadas (instalación incluida, garantía extendida,
          transporte a zona rural, especificaciones superiores). Revisa la evidencia de origen.
        </div>
      </div>

      <div className="grid g-main">
        <div className="grid">
          <BenchmarkOneCard detail={detail} />
          <BenchmarkTwoCard detail={detail} />
        </div>
        <div className="grid" style={{ alignContent: "start" }}>
          <ConfidenceCard detail={detail} />
          <div className="card">
            <h3>Evidencia de origen</h3>
            <p className="small">
              Los documentos del proceso (aceptación de oferta, invitación, anexos) se incorporan
              con la extracción documental. Esta señal usa el precio unitario publicado en los datos
              abiertos de demostración; todavía no hay un documento de origen que mostrar.
            </p>
            <p className="small muted" style={{ margin: "8px 0 0" }}>
              {detail.data_cutoff_at
                ? `Fecha de corte de los datos: ${formatBogotaDateTime(detail.data_cutoff_at)}`
                : null}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
