import type { AnalysisStatus } from "../../api/client";
import { Badge, type BadgeTone } from "../../components/Badge";

/** Texto e insignia de cada estado que calcula la API (la SPA no decide el estado). */
const STATUS_BADGES: Record<AnalysisStatus, { tone: BadgeTone; label: string }> = {
  with_signal: { tone: "review", label: "⚑ Con señal" },
  compared_no_signal: { tone: "good", label: "✓ Comparado · sin señal" },
  insufficient_comparables: { tone: "neutral", label: "Comparables insuficientes" },
  pending_comparison: { tone: "info", label: "Pendiente de comparación" },
  no_unit_price: { tone: "neutral", label: "ⓘ Sin precio unitario · limitación de la fuente" },
  quality_review: { tone: "serious", label: "◐ En revisión de calidad" },
  vat_incomplete: { tone: "neutral", label: "IVA no comparable · comparación incompleta" },
  excluded: { tone: "neutral", label: "Excluido · no es compra de televisores" },
};

export function AnalysisStatusBadge({ status }: { status: AnalysisStatus }) {
  const { tone, label } = STATUS_BADGES[status];
  return <Badge tone={tone}>{label}</Badge>;
}
