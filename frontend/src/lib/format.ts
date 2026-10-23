/** Formatos de presentación en español de Colombia (montos, fechas y fecha de corte). */

const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

const copFormatter = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
const integerFormatter = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });

/** `39600000` → `$39.600.000`; sin valor → `—`. */
export function formatCop(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }
  return `$${copFormatter.format(value)}`;
}

/** `1280` → `1.280`. */
export function formatInteger(value: number): string {
  return integerFormatter.format(value);
}

/** Fecha ISO `2026-08-14` → `14-ago-2026` (sin conversión de zona: es una fecha de negocio). */
export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.slice(0, 10).split("-");
  const monthName = MONTHS[Number(month) - 1];
  if (!year || !day || !monthName) {
    return isoDate;
  }
  return `${day}-${monthName}-${year}`;
}

const bogotaParts = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/Bogota",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

/** Marca de tiempo UTC → `06-oct-2026 03:10` en hora de Bogotá. */
export function formatBogotaDateTime(isoTimestamp: string): string {
  const parts = Object.fromEntries(
    bogotaParts.formatToParts(new Date(isoTimestamp)).map((part) => [part.type, part.value]),
  );
  const date = formatDate(`${parts.year}-${parts.month}-${parts.day}`);
  return `${date} ${parts.hour}:${parts.minute}`;
}

/** Timestamp persistido → DD/MM/YYYY HH:mm, siempre America/Bogota. */
export function formatBogotaNumericDateTime(isoTimestamp: string): string {
  const parts = Object.fromEntries(
    bogotaParts.formatToParts(new Date(isoTimestamp)).map((part) => [part.type, part.value]),
  );
  return `${parts.day}/${parts.month}/${parts.year} ${parts.hour}:${parts.minute}`;
}

/** Fecha de evento UTC → DD/MM/YYYY HH:mm:ss en Bogotá. */
export function formatBogotaEventDateTime(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  if (!Number.isFinite(date.getTime())) return "Fecha no registrada";
  const seconds = String(date.getUTCSeconds()).padStart(2, "0");
  return `${formatBogotaNumericDateTime(isoTimestamp)}:${seconds}`;
}

const percentFormatter = new Intl.NumberFormat("es-CO", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

/** Desviación decimal de la API (`"73.1"`) → `+73,1 %`. */
export function formatPercent(value: string | number): string {
  const number = Number(value);
  const sign = number > 0 ? "+" : "";
  return `${sign}${percentFormatter.format(number)} %`;
}
