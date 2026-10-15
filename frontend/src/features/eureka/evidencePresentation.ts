import { arr, location, obj, str } from "./types";

function sourceLocation(locator: Record<string, unknown>): string {
  const method =
    locator.extraction_method ??
    (locator.extractor_name === "pdf-text" ? "native_pdf_text" : undefined);
  const origin =
    method === "ocr_text" ? " · OCR" : method === "native_pdf_text" ? " · Texto nativo" : "";
  const incomplete = locator.document_coverage_complete === false ? " · Cobertura parcial" : "";
  return `${location(locator)}${origin}${incomplete}`;
}

type Source = { text: string; locator: Record<string, unknown> };
export type EvidenceEntry = {
  locations: string[];
  text?: string;
  cells?: { label: string; text: string }[];
};
export type EvidenceDocument = { key: string; name: string; entries: EvidenceEntry[] };
const headerLabels: Record<string, string> = {
  ITEM: "Ítem",
  "DESCRIPCION DEL BIEN O SERVICIO": "Descripción",
  DESCRIPCION: "Descripción",
  CANT: "Cantidad",
  CANTIDAD: "Cantidad",
  "UNIDAD DE MEDIDA": "Unidad",
  UNIDAD: "Unidad",
  "VALOR UNITARIO": "Valor unitario",
  "VALOR TOTAL": "Valor total",
};
function header(text: string): string | undefined {
  return headerLabels[
    text
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "")
      .trim()
      .replace(/\s+/g, " ")
      .toUpperCase()
  ];
}
function order(a: Source, b: Source): number {
  for (const field of [
    "page_number",
    "table_number",
    "row_number",
    "column_number",
    "paragraph_number",
    "block_index",
  ]) {
    const delta = Number(a.locator[field] ?? 0) - Number(b.locator[field] ?? 0);
    if (delta) return delta;
  }
  return location(a.locator).localeCompare(location(b.locator), "es", { numeric: true });
}

/** Presentation only: original API records remain untouched for the technical view. */
export function groupEvidence(
  facts: { evidence_text: string; source_locator: unknown; document_version_id?: string }[],
): EvidenceDocument[] {
  const documents = new Map<string, { name: string; sources: Source[] }>();
  for (const fact of facts) {
    const sources = arr(obj(fact.source_locator).sources);
    for (const raw of sources.length ? sources : [{ text: fact.evidence_text }]) {
      const source = obj(raw),
        locator = obj(source.locator);
      const name = str(source.original_name ?? locator.original_name ?? "Documento sin nombre");
      const key = str(
        locator.document_version_id ?? source.document_version_id ?? fact.document_version_id,
      );
      const doc = documents.get(key) ?? { name, sources: [] };
      doc.sources.push({
        text: typeof source.text === "string" ? source.text : fact.evidence_text,
        locator,
      });
      documents.set(key, doc);
    }
  }
  return [...documents]
    .map(([key, doc]) => {
      const unique = new Map<string, Source>();
      for (const source of doc.sources)
        unique.set(JSON.stringify([sourceLocation(source.locator), source.text]), source);
      const sources = [...unique.values()].sort(order);
      const entries: EvidenceEntry[] = [];
      const rows = new Map<string, Source[]>();
      for (const source of sources) {
        const loc = source.locator;
        if (loc.kind === "docx_table_cell" && loc.table_number != null && loc.row_number != null) {
          const rowKey = `${str(loc.table_number)}:${str(loc.row_number)}`;
          rows.set(rowKey, [...(rows.get(rowKey) ?? []), source]);
        }
      }
      const headers = new Map<string, Map<string, string>>();
      const headerRows = new Set<string>();
      for (const [rowKey, cells] of rows) {
        if (cells.every((cell) => header(cell.text))) {
          const table = str(cells[0]!.locator.table_number);
          // Hide recognized headers only when a data row is available in this evidence.
          if (
            [...rows].some(
              ([other, data]) =>
                other !== rowKey &&
                str(data[0]!.locator.table_number) === table &&
                data.some((cell) => !header(cell.text)),
            )
          ) {
            headerRows.add(rowKey);
            headers.set(
              table,
              new Map(cells.map((cell) => [str(cell.locator.column_number), header(cell.text)!])),
            );
          }
        }
      }
      const seenRows = new Set<string>();
      for (const source of sources) {
        const loc = source.locator,
          rowKey = `${str(loc.table_number)}:${str(loc.row_number)}`;
        if (loc.kind === "docx_table_cell" && rows.has(rowKey)) {
          if (seenRows.has(rowKey) || headerRows.has(rowKey)) continue;
          seenRows.add(rowKey);
          const cells = new Map<string, { label: string; text: string }>();
          for (const cell of rows.get(rowKey)!) {
            const column = str(cell.locator.column_number);
            const existing = cells.get(column);
            cells.set(column, {
              label: headers.get(str(loc.table_number))?.get(column) ?? `Columna ${column}`,
              text: existing ? `${existing.text}\n${cell.text}` : cell.text,
            });
          }
          entries.push({
            locations: [location({ table_number: loc.table_number, row_number: loc.row_number })],
            cells: [...cells.values()],
          });
        } else {
          const existing = entries.find((entry) => entry.text === source.text);
          const label = sourceLocation(loc);
          if (existing) {
            if (!existing.locations.includes(label)) existing.locations.push(label);
          } else entries.push({ locations: [label], text: source.text });
        }
      }
      return { key, name: doc.name, entries };
    })
    .sort((a, b) => a.name.localeCompare(b.name, "es"));
}

export function evidenceSummary(references: unknown, sourceCount?: number): string {
  const refs = arr(references).map(obj);
  const ids = new Set(
    refs.flatMap((ref) => arr(ref.structured_fact_ids).filter((id) => typeof id === "string")),
  );
  const confidence = [
    ...new Set(refs.map((ref) => ref.confidence).filter((value) => value != null)),
  ];
  const corroborated = refs.length > 0 && refs.every((ref) => ref.corroborated === true);
  return [
    sourceCount != null
      ? `${sourceCount} ${sourceCount === 1 ? "fuente" : "fuentes"} ${corroborated && sourceCount > 0 ? (sourceCount === 1 ? "concordante" : "concordantes") : sourceCount === 1 ? "documental" : "documentales"}`
      : ids.size
        ? `${ids.size} ${ids.size === 1 ? "evidencia" : "evidencias"}`
        : "Conteo de evidencias no disponible",
    confidence.length === 1 ? `confianza ${str(confidence[0])}` : "",
    sourceCount == null && corroborated ? "corroborado" : "",
  ]
    .filter(Boolean)
    .join(" · ");
}
