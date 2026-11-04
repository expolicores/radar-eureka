import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EconomicCycle, type EconomicCycleData } from "./EconomicCycle";

function data(): EconomicCycleData {
  return {
    document_coverage: [
      {
        document: "EVALUACION.pdf",
        stage: "evaluation_report",
        extraction_status: "completed",
        coverage_complete: false,
        pages_with_text: [3],
      },
    ],
    products: [
      {
        id: "item",
        item_description: "Televisor 55 pulgadas",
        normalized_product: "televisor",
        quantity: "5",
        brand: null,
        model: null,
        conflict_status: "uncertain",
        conflicts: [],
        notes: ["no_verified_purchase_unit_price"],
        requires_manual_review: true,
        purchase_price: null,
        fields: {
          budget_unit_price: {
            value: "960861",
            status: "confirmed",
            alternatives: [
              {
                value: "960861",
                value_origin: "calculated",
                confidence: "0.8",
                source_stage: "studies_previous",
                calculation_inputs: [
                  { field: "item_total", value: "4804305" },
                  { field: "quantity", value: "5" },
                ],
                evidence: [
                  {
                    source_stage: "studies_previous",
                    source_document: "ESTUDIOS.pdf",
                    source_page: 3,
                    extraction_method: "tesseract",
                    evidence_text: "Total del ítem 4804305, cantidad 5",
                  },
                ],
              },
            ],
          },
        },
      },
    ],
  };
}

describe("reconstrucción económica", () => {
  it("muestra valor calculado, entradas y documento/página sin promoverlo a compra", () => {
    render(<EconomicCycle cycle={data()} />);
    expect(screen.getByText(/Precio de compra: Desconocido/)).toBeInTheDocument();
    expect(screen.getByText(/Calculado · Estudios previos/)).toBeInTheDocument();
    expect(screen.getByText(/item_total=4804305; quantity=5/)).toBeInTheDocument();
    expect(screen.getByText(/ESTUDIOS.pdf · página 3 · tesseract/)).toBeInTheDocument();
    expect(screen.getByText(/Evaluación \(no adjudicación\)/)).toBeInTheDocument();
    expect(screen.getByText(/Cobertura parcial/)).toBeInTheDocument();
  });

  it("conserva el conflicto y no muestra un ganador artificial", () => {
    const cycle = data();
    const item = cycle.products[0];
    if (!item) throw new Error("Falta fixture de producto");
    item.conflicts = ["quantity"];
    item.fields.quantity = { value: null, status: "conflicting", alternatives: [] };
    render(<EconomicCycle cycle={cycle} />);
    expect(screen.getByRole("note")).toHaveTextContent("Evidencia conflictiva: Cantidad");
    expect(screen.getByText(/Precio de compra: Desconocido/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("Cobertura documental por etapa"));
    expect(screen.getByText(/EVALUACION.pdf/)).toBeInTheDocument();
  });

  it("explica una reconstrucción vacía como pendiente de revisión manual", () => {
    render(<EconomicCycle cycle={{ document_coverage: [], products: [] }} />);
    expect(
      screen.getByText(/No se pudo reconstruir un ítem determinísticamente/),
    ).toBeInTheDocument();
  });
});
