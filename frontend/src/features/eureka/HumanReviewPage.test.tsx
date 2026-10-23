import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "../../App";
import { renderWithProviders } from "../../test/render";

afterEach(() => vi.unstubAllGlobals());

it("shows public origin and readable warning explanation without starting a run", async () => {
  const sample = {
    ...row,
    provider_source: "fao",
    review_explanations: ["Sin documentos disponibles; evaluación basada en metadata."],
  };
  const fetch = mock(sample);
  renderWithProviders(<App />, { route: "/eureka/revision/secop%3ACO1.NTC.11093676" });
  expect(await screen.findByText("Fuente de origen: fao")).toBeInTheDocument();
  expect(
    screen.getByText("Sin documentos disponibles; evaluación basada en metadata."),
  ).toBeInTheDocument();
  expect(fetch.mock.calls.every(([request]) => request.method === "GET")).toBe(true);
});
const row = {
  canonical_identity: "secop:CO1.NTC.11093676",
  codigo_proceso: "CMI-2026078",
  entity_name: "Municipio de Duitama",
  municipality: "Duitama",
  department: "Boyacá",
  object: "Papelería y mobiliario",
  amount: "44217000",
  published_at: "2026-10-20T17:39:48",
  deadline_at: "2026-10-23T09:00:00-05:00",
  validity_status: "open",
  sources: ["socrata", "licitaciones_info_cdp"],
  score: 35,
  stage_max: "completed",
  commercial_decision: "No elegible",
  no_alert_reason: "No se confirmaron productos del catálogo comercial",
  requires_manual_document_review: true,
  manual_review_reasons: ["suspicious_facts"],
  alert_ids: ["existing"],
  has_alert: true,
  last_run_at: "2026-10-21T18:00:00Z",
  last_run_id: "run-1",
  manual_rating: "medium",
  manual_note: "Nota anterior",
  reviewed_at: "2026-10-21T18:00:00Z",
  review_first_seen_at: "2026-10-21T23:42:00Z",
  review_first_seen_origin: "observed",
  history: [
    {
      run_id: "run-1",
      run_at: "2026-10-21T18:00:00Z",
      source: "licitaciones_info_cdp",
      result: {
        stage: "canonical_reused",
        document_review: {
          facts: [
            { id: "f1", suspicious: true, evidence_text: "120 kg", fact_type: "presentation" },
          ],
        },
      },
    },
  ],
  evidence: {
    facts: [{ id: "f1", fact_type: "presentation", evidence_text: "120 kg" }],
    documents: [],
    canonicals: null,
  },
};

function mock(initial = row) {
  let current = { ...initial };
  const fetch = vi.fn(async (req: Request) => {
    const url = new URL(req.url);
    if (req.method === "PUT") {
      const body = (await req.json()) as { manual_rating: string; manual_note: string };
      current = { ...current, ...body };
      return new Response(JSON.stringify(body));
    }
    return new Response(
      JSON.stringify(
        url.pathname.endsWith("/revision")
          ? {
              items: [current],
              total: 1,
              page: 1,
              page_size: 25,
              filter_options: { funnel_state: ["no_alert"] },
            }
          : current,
      ),
    );
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

it("keeps a metadata-excluded process visible with the readable alert reason", async () => {
  mock({ ...row, no_alert_reason: "Alerta provisional excluida por objeto: transporte" });
  renderWithProviders(<App />, { route: "/eureka/revision" });
  expect(
    await screen.findByText("Alerta provisional excluida por objeto: transporte"),
  ).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "CMI-2026078" })).toBeInTheDocument();
});

it("shows one unified process with distinct score and human evaluation", async () => {
  mock();
  renderWithProviders(<App />, { route: "/eureka/revision" });
  const link = await screen.findByRole("link", { name: "CMI-2026078" });
  const tr = link.closest("tr")!;
  expect(within(tr).getByText("35")).toBeInTheDocument();
  expect(within(tr).getByText("Media")).toBeInTheDocument();
  expect(within(tr).getByText("Socrata / Eureka · Licitaciones.info (CDP)")).toBeInTheDocument();
  expect(within(tr).getByRole("link", { name: "Alerta existente" })).toHaveAttribute(
    "href",
    "/eureka/alerts/existing",
  );
  expect(within(tr).getByText(row.no_alert_reason)).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "Entró a revisión" })).toBeInTheDocument();
  expect(within(tr).getByText("21/10/2026 18:42")).toBeInTheDocument();
  expect(screen.getAllByRole("link", { name: "CMI-2026078" })).toHaveLength(1);
});

it("applies filters without triggering any source run", async () => {
  const fetch = mock();
  renderWithProviders(<App />, { route: "/eureka/revision" });
  await screen.findByRole("link", { name: "CMI-2026078" });
  await userEvent.type(screen.getByLabelText("Buscar código, entidad u objeto"), "CMI");
  await userEvent.selectOptions(screen.getByLabelText("Fuente"), "licitaciones_info_cdp");
  await userEvent.click(screen.getByRole("button", { name: "Aplicar filtros" }));
  expect(fetch.mock.calls.some(([r]) => new URL(r.url).searchParams.get("q") === "CMI")).toBe(true);
  expect(fetch.mock.calls.every(([r]) => r.method === "GET")).toBe(true);
});

it("saves rating and note independently of score and displays persisted suspicious facts", async () => {
  const fetch = mock();
  renderWithProviders(<App />, { route: "/eureka/revision/secop%3ACO1.NTC.11093676" });
  expect(await screen.findByRole("heading", { name: "CMI-2026078" })).toBeInTheDocument();
  expect(screen.getByText("Score Eureka: 35")).toBeInTheDocument();
  expect(screen.getByText(/Entró a revisión:/)).toHaveTextContent("21/10/2026 18:42");
  expect(screen.getByText("120 kg · Presentación")).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText("Evaluación manual"), "discard");
  await userEvent.clear(screen.getByLabelText("Nota manual"));
  await userEvent.type(screen.getByLabelText("Nota manual"), "Presupuesto alto");
  await userEvent.click(screen.getByRole("button", { name: "Guardar evaluación" }));
  expect(await screen.findByText("Evaluación guardada")).toBeInTheDocument();
  expect(screen.getByText("Score Eureka: 35")).toBeInTheDocument();
  const put = fetch.mock.calls.find(([r]) => r.method === "PUT")![0];
  expect(new URL(put.url).pathname).toContain("secop%3ACO1.NTC.11093676");
  expect(fetch.mock.calls.some(([r]) => r.method === "POST")).toBe(false);
});

it("shows errors without generating a run", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(new Response("{}", { status: 500 }))),
  );
  renderWithProviders(<App />, { route: "/eureka/revision" });
  expect(await screen.findByRole("alert")).toHaveTextContent("No fue posible cargar");
});
