import type { ReactNode } from "react";

export type BadgeTone = "review" | "good" | "serious" | "critical" | "neutral" | "info";

export function Badge({ tone, children }: { tone: BadgeTone; children: ReactNode }) {
  return <span className={`badge b-${tone}`}>{children}</span>;
}
