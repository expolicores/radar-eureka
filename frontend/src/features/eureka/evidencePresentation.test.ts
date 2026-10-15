import { expect, it } from "vitest";
import { evidenceSummary, groupEvidence } from "./evidencePresentation";
import type { Evidence } from "./types";

const fact = (sources: unknown[], document = "pdf", id = "fact"): Evidence => ({
  canonical_fact_id: "canonical",
  structured_fact_id: id,
  document_version_id: document,
  content_fragment_id: null,
  evidence_text: "fallback",
  source_locator: { sources },
  confidence: "0.8",
  corroborated: true,
  rule_name: "item_row",
  rule_version: "v1",
});
const pdf = (page: number, text: string) => ({
  original_name: "Estudios.pdf",
  locator: { page_number: page },
  text,
});
const cell = (row: number, column: number, text: string) => ({
  original_name: "Propuesta.docx",
  locator: { kind: "docx_table_cell", table_number: 1, row_number: row, column_number: column },
  text,
});

it("conserva procedencia nativa y OCR aunque el texto sea idéntico", () => {
  const native = {
    ...pdf(3, "JUGO HIT"),
    locator: { page_number: 3, extraction_method: "native_pdf_text" },
  };
  const scanned = {
    ...pdf(3, "JUGO HIT"),
    locator: { page_number: 3, extraction_method: "ocr_text", document_coverage_complete: false },
  };
  const docs = groupEvidence([fact([native, scanned])]);
  expect(docs[0]!.entries[0]!.locations).toEqual([
    "página 3 · Texto nativo",
    "página 3 · OCR · Cobertura parcial",
  ]);
});

it("ordena páginas, agrupa documentos y deduplica citas exactas reteniendo sus localizadores", () => {
  const rows = [
    fact([pdf(15, "JUGO HIT"), pdf(3, "JUGO HIT"), pdf(2, "JUGOS HIT")]),
    fact([pdf(3, "JUGO HIT")], "pdf", "duplicate"),
  ];
  const before = JSON.stringify(rows);
  const documents = groupEvidence(rows);
  expect(documents).toHaveLength(1);
  expect(documents[0]!.entries).toEqual([
    { text: "JUGOS HIT", locations: ["página 2"] },
    { text: "JUGO HIT", locations: ["página 3", "página 15"] },
  ]);
  expect(JSON.stringify(rows)).toBe(before);
});

it("reconstruye una fila DOCX sin duplicar celdas ni encabezados", () => {
  const headers = [
    "ITEM",
    "DESCRIPCION DEL BIEN O SERVICIO",
    "CANT",
    "UNIDAD DE MEDIDA",
    "VALOR UNITARIO",
    "VALOR TOTAL",
  ];
  const values = ["1", "REFRIGERIOS PACK", "400", "PACK", "XXXXX", "XXXXXX"];
  const sources = [
    ...headers.map((text, i) => cell(1, i + 1, text)),
    ...values.map((text, i) => cell(2, i + 1, text)),
  ];
  const docs = groupEvidence([
    fact(sources, "docx"),
    fact(sources, "docx", "duplicate"),
    fact([pdf(3, "REFRIGERIOS PACK")]),
  ]);
  const docx = docs.find((doc) => doc.key === "docx")!;
  expect(docs).toHaveLength(2);
  expect(docx.entries).toEqual([
    {
      locations: ["tabla 1 · fila 2"],
      cells: values.map((text, i) => ({
        text,
        label: ["Ítem", "Descripción", "Cantidad", "Unidad", "Valor unitario", "Valor total"][i],
      })),
    },
  ]);
});

it("no adivina encabezados ni pierde diferencias o versiones documentales", () => {
  const docs = groupEvidence([
    fact([cell(2, 1, "400"), cell(2, 1, "450")], "version1"),
    fact([cell(2, 1, "400")], "version2"),
  ]);
  expect(docs).toHaveLength(2);
  expect(docs[0]!.entries[0]!.cells).toEqual([{ label: "Columna 1", text: "400\n450" }]);
  expect(groupEvidence([fact([])])[0]!.entries[0]!.text).toBe("fallback");
});

it("cuenta referencias únicas y conserva confianza y corroboración sin inventar datos", () => {
  expect(
    evidenceSummary([
      { structured_fact_ids: ["a", "b", "a"], confidence: "1.0", corroborated: true },
    ]),
  ).toBe("2 evidencias · confianza 1.0 · corroborado");
  expect(evidenceSummary([{}])).toBe("Conteo de evidencias no disponible");
});
