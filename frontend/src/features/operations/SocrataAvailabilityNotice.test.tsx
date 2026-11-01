import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { SocrataAvailabilityNotice } from "./SocrataAvailabilityNotice";

afterEach(cleanup);
it.each([
  ["dataset_lag", "Es probable que el dataset"],
  ["no_rows_in_window", "no parece explicarse por rezago"],
  ["diagnostic_failed", "No fue posible verificar"],
])("shows availability state %s with Bogotá timestamps", (status, message) => {
  render(
    <SocrataAvailabilityNotice
      diagnostic={{
        performed: true,
        status,
        query_window_start: "2026-10-21",
        query_window_before: "2026-10-24",
        latest_available_date: status === "diagnostic_failed" ? null : "2026-10-24T02:00:00Z",
      }}
    />,
  );
  expect(screen.getByText(new RegExp(message))).toBeInTheDocument();
  expect(screen.getByText(/21-oct-2026–23-oct-2026/)).toBeInTheDocument();
  expect(
    screen.getByText(status === "diagnostic_failed" ? /No disponible/ : /23\/10\/2026 21:00:00/),
  ).toBeInTheDocument();
});

it("does not invent availability or display a skipped diagnostic", () => {
  const { container } = render(<SocrataAvailabilityNotice diagnostic={{ performed: false }} />);
  expect(container).toBeEmptyDOMElement();
});

it("keeps date-only availability on the original calendar day", () => {
  render(
    <SocrataAvailabilityNotice
      diagnostic={{ performed: true, status: "dataset_lag", latest_available_date: "2026-10-20" }}
    />,
  );
  expect(screen.getByText(/Última fecha disponible en Socrata: 20-oct-2026/)).toBeInTheDocument();
});
