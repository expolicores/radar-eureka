import { useState } from "react";

import { formatCop } from "../lib/format";

export interface StripPoint {
  id: string;
  value: number;
  shape: "circle" | "diamond";
  tooltip: string[];
}

interface StripPlotProps {
  points: StripPoint[];
  target: { value: number; label: string; tooltip: string[] };
  q1: number;
  median: number;
  q3: number;
  threshold: number;
  ariaLabel: string;
}

const WIDTH = 760;
const HEIGHT = 190;
const MARGIN = { left: 16, right: 24, top: 30, bottom: 40 };
const COLORS = { circle: "var(--series-1)", diamond: "var(--series-3)" };

function niceTicks(min: number, max: number): number[] {
  const step =
    [250_000, 500_000, 1_000_000, 2_000_000].find((s) => (max - min) / s <= 8) ?? 5_000_000;
  const ticks: number[] = [];
  for (let value = Math.ceil(min / step) * step; value <= max; value += step) {
    ticks.push(value);
  }
  return ticks;
}

/** Franja de puntos: distribución de comparables, caja Q1–Q3, mediana, umbral y la compra analizada. */
export function StripPlot({
  points,
  target,
  q1,
  median,
  q3,
  threshold,
  ariaLabel,
}: StripPlotProps) {
  const [hovered, setHovered] = useState<{ x: number; y: number; lines: string[] } | null>(null);
  const values = [...points.map((p) => p.value), target.value, threshold];
  const padding = (Math.max(...values) - Math.min(...values)) * 0.06 || 100_000;
  const min = Math.min(...values) - padding;
  const max = Math.max(...values) + padding;
  const x = (value: number) =>
    MARGIN.left + ((value - min) / (max - min)) * (WIDTH - MARGIN.left - MARGIN.right);
  const cy = HEIGHT / 2 + 4;
  const show = (value: number, y: number, lines: string[]) => setHovered({ x: x(value), y, lines });

  return (
    <div className="chart-box">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        width="100%"
        role="img"
        aria-label={ariaLabel}
        onMouseLeave={() => setHovered(null)}
      >
        {niceTicks(min, max).map((tick) => (
          <g key={tick}>
            <line
              x1={x(tick)}
              x2={x(tick)}
              y1={MARGIN.top}
              y2={HEIGHT - MARGIN.bottom}
              stroke="var(--grid)"
            />
            <text
              x={x(tick)}
              y={HEIGHT - MARGIN.bottom + 18}
              fontSize="11"
              fill="var(--text-secondary)"
              textAnchor="middle"
            >
              {(tick / 1_000_000).toLocaleString("es-CO", { minimumFractionDigits: 1 })} M
            </text>
          </g>
        ))}
        <text
          x={WIDTH - MARGIN.right}
          y={HEIGHT - 6}
          fontSize="11"
          fill="var(--text-muted)"
          textAnchor="end"
        >
          Precio unitario con IVA (COP)
        </text>
        <rect
          x={x(q1)}
          y={cy - 26}
          width={Math.max(1, x(q3) - x(q1))}
          height={52}
          rx={4}
          fill="#eef3fb"
        />
        {[
          { value: q1, label: "Q1", width: 1.5 },
          { value: median, label: "Mediana", width: 2.5 },
          { value: q3, label: "Q3", width: 1.5 },
        ].map((line) => (
          <g key={line.label}>
            <line
              x1={x(line.value)}
              x2={x(line.value)}
              y1={cy - 30}
              y2={cy + 30}
              stroke="var(--ref-line)"
              strokeWidth={line.width}
            />
            <text
              x={x(line.value)}
              y={MARGIN.top - 8}
              fontSize="11"
              fill="var(--text-secondary)"
              textAnchor="middle"
            >
              {line.label}
            </text>
          </g>
        ))}
        <line
          x1={x(threshold)}
          x2={x(threshold)}
          y1={MARGIN.top}
          y2={HEIGHT - MARGIN.bottom}
          stroke="#3d3c39"
          strokeWidth={2}
          strokeDasharray="4 3"
        />
        <text x={x(threshold) + 6} y={MARGIN.top + 4} fontSize="11" fill="var(--text-primary)">
          Umbral {formatCop(threshold)}
        </text>
        {points.map((point, index) => {
          const px = x(point.value);
          const py = cy + ((index % 5) - 2) * 8;
          return (
            <g
              key={point.id}
              onMouseEnter={() => show(point.value, py, point.tooltip)}
              data-testid="strip-point"
            >
              <circle cx={px} cy={py} r={12} fill="transparent" />
              {point.shape === "circle" ? (
                <circle
                  cx={px}
                  cy={py}
                  r={5}
                  fill={COLORS.circle}
                  stroke="#fff"
                  strokeWidth={1.5}
                />
              ) : (
                <rect
                  x={px - 4.5}
                  y={py - 4.5}
                  width={9}
                  height={9}
                  transform={`rotate(45 ${px} ${py})`}
                  fill={COLORS.diamond}
                  stroke="#fff"
                  strokeWidth={1.5}
                />
              )}
            </g>
          );
        })}
        <g onMouseEnter={() => show(target.value, cy, target.tooltip)}>
          <circle cx={x(target.value)} cy={cy} r={16} fill="transparent" />
          <circle
            cx={x(target.value)}
            cy={cy}
            r={8}
            fill="var(--series-2)"
            stroke="#fff"
            strokeWidth={2}
          />
        </g>
        <text
          x={x(target.value)}
          y={cy - 16}
          fontSize="12"
          fontWeight="600"
          fill="var(--text-primary)"
          textAnchor="middle"
        >
          {target.label}
        </text>
      </svg>
      {hovered ? (
        <div
          className="tooltip"
          role="tooltip"
          style={{ left: `${(hovered.x / WIDTH) * 100}%`, top: `${(hovered.y / HEIGHT) * 100}%` }}
        >
          {hovered.lines.map((line) => (
            <div key={line}>{line}</div>
          ))}
        </div>
      ) : null}
      <div className="legend">
        <span>
          <svg width="12" height="12" aria-hidden="true">
            <circle cx="6" cy="6" r="5" fill={COLORS.circle} />
          </svg>
          Compra SECOP II
        </span>
        <span>
          <svg width="12" height="12" aria-hidden="true">
            <rect
              x="1.5"
              y="1.5"
              width="9"
              height="9"
              transform="rotate(45 6 6)"
              fill={COLORS.diamond}
            />
          </svg>
          Orden TVEC
        </span>
        <span>
          <svg width="14" height="14" aria-hidden="true">
            <circle cx="7" cy="7" r="6" fill="var(--series-2)" stroke="#fff" strokeWidth="2" />
          </svg>
          Compra analizada
        </span>
        <span>
          <svg width="18" height="10" aria-hidden="true">
            <line x1="0" y1="5" x2="18" y2="5" stroke="var(--ref-line)" strokeWidth="2" />
          </svg>
          Q1 · mediana · Q3
        </span>
        <span>
          <svg width="18" height="10" aria-hidden="true">
            <line
              x1="0"
              y1="5"
              x2="18"
              y2="5"
              stroke="#3d3c39"
              strokeWidth="2"
              strokeDasharray="4 3"
            />
          </svg>
          Umbral de revisión
        </span>
      </div>
    </div>
  );
}
