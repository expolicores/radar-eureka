import type { ConfidenceLevel } from "../api/client";

const LEVELS: Record<ConfidenceLevel, { bars: number; label: string }> = {
  high: { bars: 3, label: "Alta" },
  medium: { bars: 2, label: "Media" },
  low: { bars: 1, label: "Baja" },
};

/** Nivel de confianza con barras y texto (el texto evita depender solo del color). */
export function ConfidenceBadge({
  level,
  prefix = "",
}: {
  level: ConfidenceLevel;
  prefix?: string;
}) {
  const { bars, label } = LEVELS[level];
  return (
    <span className="badge b-neutral">
      <span className={`conf c${bars}`} aria-hidden="true">
        <i />
        <i />
        <i />
      </span>
      {prefix}
      {label}
    </span>
  );
}
