import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";
import { renderWithProviders } from "../../test/render";
import { ComparisonReadiness, type ReadinessAudit } from "./ComparisonReadiness";

it("muestra el cierre de los 19 pares y diferencia observaciones sin inventar precios", async () => {
  const audit: ReadinessAudit = {
    summary: { initial_pairs: 19, unique_processes: 7, unique_observations: 20, pairs_ready: 0 },
    pairs: [
      {
        number: 1,
        id: "pair-1",
        processes: ["REQ-A", "REQ-B"],
        observation_ids: ["obs-a", "obs-b"],
        process_code_a: "MC-A",
        process_code_b: "MC-B",
        comparability_level: "exact",
        price_a: null,
        price_b: null,
        status: "missing_both_prices",
        blockers_a: ["verified_item_purchase_unit_price"],
        blockers_b: ["proof_of_winning_offer_acceptance"],
        requires_manual_review: true,
      },
    ],
  };
  renderWithProviders(<ComparisonReadiness audit={audit} />);
  expect(
    screen.getByText(/19 pares técnicamente comparables evaluados; ninguno/),
  ).toBeInTheDocument();
  expect(screen.getByText(/7 procesos únicos · 20 observaciones/)).toBeInTheDocument();
  await userEvent.click(screen.getByText("Ver matriz de bloqueo de los 19 pares"));
  const region = screen.getByRole("region", { name: "Cierre económico de pares técnicos" });
  expect(within(region).getByRole("link", { name: "MC-A" })).toHaveAttribute(
    "href",
    "/explorar?process=REQ-A",
  );
  expect(within(region).getByText("Falta precio de compra en ambos lados")).toBeInTheDocument();
  expect(within(region).getByText("No recuperado / No recuperado")).toBeInTheDocument();
  expect(
    within(region).getByText("Prueba de aceptación de esta oferta e ítem"),
  ).toBeInTheDocument();
});
