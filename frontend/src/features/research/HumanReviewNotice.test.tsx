import { screen } from "@testing-library/react";
import { render } from "@testing-library/react";
import { expect, it } from "vitest";
import { HumanReviewNotice } from "./HumanReviewNotice";

it("muestra recomendación y motivo sin presentar una señal confirmada", () => {
  render(
    <HumanReviewNotice
      review={{
        human_review_recommended: true,
        human_review_reasons: [
          "global_contract_value_without_item_breakdown",
          "conflicting_product_reference",
        ],
      }}
    />,
  );
  expect(screen.getByText("Revisión humana recomendada")).toBeInTheDocument();
  expect(screen.getByText(/El contrato publica un valor global/)).toBeInTheDocument();
  expect(screen.getByText(/55″ y 70″/)).toBeInTheDocument();
  expect(screen.getByText(/No es una señal confirmada/)).toBeInTheDocument();
});

it("no etiqueta procesos descartables ni casos listos sin recomendación", () => {
  const { container } = render(
    <HumanReviewNotice review={{ human_review_recommended: false, human_review_reasons: [] }} />,
  );
  expect(container).toBeEmptyDOMElement();
});
