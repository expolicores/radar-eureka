import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "../../App";
import { lastQuery, mockApi } from "../../test/api";
import { renderWithProviders } from "../../test/render";

afterEach(() => vi.unstubAllGlobals());
const hit = {
  process_id: "d4bba041-acdf-4abd-b8d0-c94f51c5282c",
  secop_id: "CO1.REQ.11172521",
  title: "Refrigerios",
  entity: "Escuela",
  department: "Boyacá",
  municipality: "Covarachía",
  budget_cop: 2080000,
  score: 65,
  priority: "high",
  published_on: "2026-10-07",
  detail_url: "/eureka/existing",
  source_url: null,
  matches: [
    {
      type: "canonical_match",
      mode: "exact_normalized",
      field: "PRODUCT",
      value: { name: "jugo hit" },
      canonical_fact_id: "52a96910-7900-52d1-8cd7-be8072e15556",
    },
  ],
};
const page = (items: unknown[], total = items.length) => ({
  items,
  total,
  page: 1,
  page_size: 20,
  duration_ms: 12,
  ranking_version: "search-v1",
});

it("shows canonical explanation, score, Eureka link and shared OCR evidence", async () => {
  const fetch = mockApi({
    "/api/search": () => ({ body: page([hit]) }),
    [`/api/search/processes/${hit.process_id}/evidence`]: () => ({
      body: [
        {
          evidence_text: "JUGO HIT",
          source_locator: {
            sources: [
              {
                text: "JUGO HIT",
                locator: {
                  original_name: "Documento.pdf",
                  page_number: 3,
                  extraction_method: "ocr_text",
                },
              },
            ],
          },
        },
      ],
    }),
  });
  renderWithProviders(<App />, { route: "/search?q=jugo%20hit" });
  expect(await screen.findByText("Hecho canónico vigente")).toBeInTheDocument();
  expect(screen.getByText(/Score Eureka 65/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Ver detalle Eureka" })).toHaveAttribute(
    "href",
    "/eureka/existing",
  );
  await userEvent.click(screen.getByText("Ver evidencia"));
  expect(await screen.findByText("Documento.pdf")).toBeInTheDocument();
  expect(await screen.findByText(/OCR/)).toBeInTheDocument();
  expect(lastQuery(fetch, "/api/search").get("q")).toBe("jugo hit");
});

it("combines filters on submit and resets pagination", async () => {
  const fetch = mockApi({ "/api/search": () => ({ body: page([]) }) });
  renderWithProviders(<App />, { route: "/search?page=3" });
  await screen.findByText("No hay resultados en esta página.");
  await userEvent.click(screen.getByText("Filtros"));
  await userEvent.type(screen.getByLabelText("Departamento"), "Boyacá");
  await userEvent.type(screen.getByLabelText("Presupuesto mínimo"), "2000000");
  await userEvent.type(screen.getByLabelText("Buscar"), "jugo hit");
  await userEvent.click(screen.getByRole("button", { name: "Buscar" }));
  await screen.findByText("Sin coincidencias para esta búsqueda.");
  expect(lastQuery(fetch, "/api/search").get("department")).toBe("Boyacá");
  expect(lastQuery(fetch, "/api/search").get("budget_min")).toBe("2000000");
  expect(lastQuery(fetch, "/api/search").get("page")).toBe("1");
});

it("allows metadata-only processes without creating an opportunity", async () => {
  const fetch = mockApi({
    "/api/search": () => ({
      body: page([
        {
          ...hit,
          detail_url: null,
          score: null,
          matches: [
            { type: "metadata_match", mode: "phrase", field: "title", value: "Refrigerios" },
          ],
        },
      ]),
    }),
  });
  renderWithProviders(<App />, { route: "/search" });
  expect(await screen.findByText(/Sin oportunidad Eureka/)).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "Ver detalle Eureka" })).not.toBeInTheDocument();
  expect(fetch.mock.calls.every(([request]) => request.method === "GET")).toBe(true);
});

it("keeps filters on pagination", async () => {
  const fetch = mockApi({ "/api/search": () => ({ body: page([hit], 25) }) });
  renderWithProviders(<App />, { route: "/search?q=jugo&department=Boyac%C3%A1" });
  await screen.findByText("Hecho canónico vigente");
  await userEvent.click(screen.getByRole("button", { name: /Siguiente/ }));
  await screen.findByText(/Página 2 de 2/);
  expect(lastQuery(fetch, "/api/search").get("department")).toBe("Boyacá");
});

it("shows a controlled error while migration is pending", async () => {
  mockApi({
    "/api/search": () => ({
      status: 503,
      body: { title: "Búsqueda pendiente de la migración 0014" },
    }),
  });
  renderWithProviders(<App />, { route: "/search" });
  expect(await screen.findByRole("alert")).toHaveTextContent("0014");
});
