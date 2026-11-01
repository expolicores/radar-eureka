import { formatBogotaEventDateTime, formatDate } from "../../lib/format";

export function SocrataAvailabilityNotice({ diagnostic }: { diagnostic: unknown }) {
  if (!diagnostic || typeof diagnostic !== "object") return null;
  const value = diagnostic as Record<string, unknown>;
  if (value.performed !== true) return null;
  const dateLabel = (raw: unknown) => {
    if (typeof raw !== "string" || !Number.isFinite(Date.parse(raw))) return "No disponible";
    return raw.length === 10 ? formatDate(raw) : formatBogotaEventDateTime(raw);
  };
  const before = value.query_window_before;
  const end = typeof before === "string" ? new Date(before + "T00:00:00Z") : null;
  if (end && Number.isFinite(end.getTime())) end.setUTCDate(end.getUTCDate() - 1);
  const lastDay = end && Number.isFinite(end.getTime()) ? end.toISOString().slice(0, 10) : null;
  const messages: Record<string, string> = {
    dataset_lag: "Es probable que el dataset aún no tenga cobertura para la ventana consultada.",
    no_rows_in_window:
      "El resultado vacío no parece explicarse por rezago del dataset. La fecha global no confirma cobertura para las regiones consultadas.",
    diagnostic_failed:
      "No fue posible verificar la fecha más reciente disponible en Socrata. La corrida conserva su resultado.",
  };
  return (
    <div role="status">
      <p>
        No se encontraron procesos en la ventana {dateLabel(value.query_window_start)}–
        {dateLabel(lastDay)} (Bogotá; días incluidos).
      </p>
      <p>Última fecha disponible en Socrata: {dateLabel(value.latest_available_date)}.</p>
      <p>{messages[String(value.status)]}</p>
    </div>
  );
}
