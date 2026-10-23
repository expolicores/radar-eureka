import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "../../App";
import { mockApi } from "../../test/api";
import { renderWithProviders } from "../../test/render";

const opportunity = "6e94cc77-9f88-4f4c-bfb8-2e832976f4c0";
const alert = {
  id: "alert",
  opportunity_id: opportunity,
  run_id: "run",
  created_at: "2026-10-13T15:00:00Z",
  alert_type: "new_opportunity",
  rule_version: "v1",
  priority: "high",
  review_required: true,
  evidence_level: "document_confirmed",
  document_status: "available",
  process: {
    secop_id: "CO1.REQ.11172521",
    reference: "012-2026",
    description: "DESCRIPCIÓN ORIGINAL; refrigerios\nCOMUNIDAD EDUCATIVA",
    source_url: "https://community.secop.gov.co/Public/?noticeUID=original",
  },
  snapshot: {
    secop_id: "CO1.REQ.11172521",
    entity: "San Luis Beltrán",
    municipality: "Covarachía",
    department: "Boyacá",
    budget: 2080000,
    score: 65,
    execution_days: 5,
    payment_days: 30,
    guarantee_required: "not_required",
    products: [
      { name: "jugo hit", presentation_value: 200, presentation_unit: "ml" },
      { name: "chocorramo tradicional", presentation_value: 65, presentation_unit: "g" },
    ],
    confirmed_matches: [{ label: "Refrigerios y bebidas" }],
  },
  reasons: [
    { code: "candidate_match", concept: "50192703", method: "unspsc", origin: "metadata" },
    {
      code: "confirmed_commercial_match",
      concept: "Jugo Hit",
      method: "alias/normalization",
      origin: "canonical_fact",
    },
    { code: "score_reference", value: 65, threshold: 60, mandatory_gate: false },
  ],
};
afterEach(() => vi.unstubAllGlobals());
function routes(items = [alert]) {
  mockApi({
    "/api/eureka/alerts": () => ({ body: { items, total: items.length, page: 1, page_size: 25 } }),
    "/api/eureka/radar-runs": () => ({ body: { items: [], total: 0, page: 1, page_size: 5 } }),
  });
}

it("muestra golden case, tipos de coincidencia, revisión y enlace a oportunidad", async () => {
  routes();
  renderWithProviders(<App />, { route: "/eureka/alerts" });
  expect(await screen.findByText("Nueva oportunidad Eureka · Alta")).toBeInTheDocument();
  expect(screen.getByText("Referencia del proceso: 012-2026")).toBeInTheDocument();
  expect(screen.getByText(/ID SECOP: CO1.REQ.11172521/)).toBeInTheDocument();
  expect(screen.getByText(/DESCRIPCIÓN ORIGINAL; refrigerios/).textContent).toBe(
    alert.process.description,
  );
  expect(screen.getByRole("link", { name: "Abrir proceso en SECOP" })).toHaveAttribute(
    "href",
    alert.process.source_url,
  );
  expect(screen.getByText(/Covarachía, Boyacá.*2.080.000 COP/)).toBeInTheDocument();
  expect(screen.getByText("Jugo Hit · 200 ml")).toBeInTheDocument();
  expect(screen.getByText("Chocorramo tradicional · 65 g")).toBeInTheDocument();
  expect(screen.getByText("Coincidencia comercial confirmada")).toBeInTheDocument();
  expect(screen.getByText("Coincidencia preliminar: metadata")).toBeInTheDocument();
  expect(screen.getByText("Requiere revisión")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Ver oportunidad/ })).toHaveAttribute(
    "href",
    `/eureka/${opportunity}`,
  );
  await userEvent.setup().click(screen.getByText("Por qué se generó esta alerta"));
  expect(screen.getByText(/Score 65.*sin umbral obligatorio/)).toBeInTheDocument();
  expect(screen.getByText(/Coincidencia confirmada: Jugo Hit/)).toBeInTheDocument();
});

it("conserva alerta con score inferior al umbral de referencia y requisitos desconocidos", async () => {
  routes([
    {
      ...alert,
      priority: "low",
      snapshot: { ...alert.snapshot, score: 20, guarantee_required: "unknown" },
    },
  ]);
  renderWithProviders(<App />, { route: "/eureka/alerts" });
  expect(await screen.findByText("Nueva oportunidad Eureka · Baja")).toBeInTheDocument();
  expect(screen.getByText(/Score 20/)).toBeInTheDocument();
  expect(screen.getByText(/Póliza: No determinado/)).toBeInTheDocument();
});

it("shows metadata-only warning without claiming documentary confirmation", async () => {
  routes([
    {
      ...alert,
      evidence_level: "metadata_only",
      document_status: "unavailable",
      snapshot: { ...alert.snapshot, products: [], confirmed_matches: [] },
    },
  ]);
  renderWithProviders(<App />, { route: "/eureka/alerts" });
  expect(await screen.findByText("Alerta provisional · solo metadata")).toBeInTheDocument();
  expect(
    screen.getByText(
      "No se pudo validar documentalmente, pero por metadatos parece viable. Revisar manualmente.",
    ),
  ).toBeInTheDocument();
  expect(screen.queryByText("Coincidencia comercial confirmada")).not.toBeInTheDocument();
  expect(
    screen.queryByText("Afinidad confirmada en la descripción documental del ítem."),
  ).not.toBeInTheDocument();
  expect(screen.getByText("Productos pendientes de validación documental.")).toBeInTheDocument();
});

it("maneja listado vacío y errores API", async () => {
  routes([]);
  renderWithProviders(<App />, { route: "/eureka/alerts" });
  expect(await screen.findByText("No hay alertas para esta página.")).toBeInTheDocument();
  expect(screen.getByText("No hay corridas registradas.")).toBeInTheDocument();
});

it("muestra fallo de alertas sin afirmar que no existen", async () => {
  mockApi({
    "/api/eureka/alerts": () => ({ status: 500, body: { title: "Error" } }),
    "/api/eureka/radar-runs": () => ({ body: { items: [], total: 0, page: 1, page_size: 5 } }),
  });
  renderWithProviders(<App />, { route: "/eureka/alerts" });
  expect(await screen.findByRole("alert")).toHaveTextContent("No fue posible cargar las alertas");
  expect(screen.queryByText("No hay alertas para esta página.")).not.toBeInTheDocument();
});

it.each([
  ["socrata", "/eureka/alerts"],
  ["licitaciones_info_cdp", "/eureka/alerts"],
  ["socrata", "/eureka/alerts/alert"],
  ["licitaciones_info_cdp", "/eureka/alerts/alert"],
])("muestra created_at en Bogotá para %s en %s", async (source, route) => {
  const item = {
    ...alert,
    source,
    created_at: "2026-10-21T14:42:00Z",
    process: { ...alert.process, published_at: "2026-10-01T00:00:00Z" },
  };
  mockApi({
    "/api/eureka/alerts": () => ({ body: { items: [item], total: 1, page: 1, page_size: 25 } }),
    "/api/eureka/alerts/alert": () => ({ body: item }),
    "/api/eureka/radar-runs": () => ({ body: { items: [], total: 0, page: 1, page_size: 5 } }),
  });
  renderWithProviders(<App />, { route });
  const timestamp = await screen.findByText("21/10/2026 09:42");
  expect(timestamp.tagName).toBe("TIME");
  expect(timestamp).toHaveAttribute("datetime", item.created_at);
  expect(timestamp).toHaveAttribute("title", "America/Bogota");
  expect(timestamp.parentElement).toHaveTextContent("Fecha alerta:");
  expect(timestamp.parentElement).not.toHaveTextContent("01/10/2026");
});
