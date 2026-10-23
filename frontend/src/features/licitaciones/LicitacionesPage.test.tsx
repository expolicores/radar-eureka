import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "../../App";
import { renderWithProviders } from "../../test/render";

afterEach(() => vi.unstubAllGlobals());

it("separates discards warnings and technical errors without rejecting by origin", async () => {
  mock({
    ...run,
    metrics: {
      ...run.metrics,
      event_groups: {
        discard: [
          {
            code: "stale",
            message: "Histórico fuera de ventana",
            event_type: "discard",
            generated_at: "2026-10-22T14:00:00Z",
            run_id: run.id,
          },
        ],
        warning: [
          {
            code: "missing_documents",
            message: "Evaluación basada en metadata",
            event_type: "warning",
            source: "fao",
            run_id: run.id,
          },
        ],
        error: [
          {
            code: "extraction_failed",
            message: "Error técnico documental",
            event_type: "error",
            run_id: run.id,
          },
        ],
      },
    },
  });
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  const discard = await screen.findByText("Descartes del funnel (1)");
  expect(
    within(discard.parentElement!).getByText("Histórico fuera de ventana"),
  ).toBeInTheDocument();
  const warnings = screen.getByText("Advertencias (1)");
  expect(
    within(warnings.parentElement!).getByText("Evaluación basada en metadata"),
  ).toBeInTheDocument();
  expect(
    within(warnings.parentElement!).queryByText("Error técnico documental"),
  ).not.toBeInTheDocument();
  const errors = screen.getByText("Errores (1)");
  expect(within(errors.parentElement!).getByText("Error técnico documental")).toBeInTheDocument();
  expect(screen.queryByText(/Otra fuente SECOP/)).not.toBeInTheDocument();
});
type MockRun = {
  id: string;
  source: string;
  status: string;
  started_at: string;
  finished_at: string;
  metrics: Record<string, unknown>;
  errors: Record<string, unknown>[];
  items: Record<string, unknown>[];
};
const run: MockRun = {
  id: "manual-run",
  source: "licitaciones_info_cdp",
  status: "completed_with_warnings",
  started_at: "2026-10-21T10:00:00Z",
  finished_at: "2026-10-21T10:05:00Z",
  metrics: { alerts_created: 1, duplicate_alerts_skipped: 2, secop_ii_open: 3 },
  errors: [],
  items: [
    {
      secop_id: "source-process",
      stage: "completed",
      outcome: "duplicate",
      reason: "duplicate_canonical",
      requires_manual_document_review: true,
      metadata: {
        codigo_proceso: "CM-006-2026",
        entity_name: "Concejo de Duitama",
        object: "Papelería y oficina",
        validity_status: "open",
        amount: "8400000",
      },
    },
  ],
};
function mock(current = run) {
  const fetch = vi.fn(async (request: Request) => {
    await Promise.resolve();
    const path = new URL(request.url).pathname;
    if (request.method === "POST")
      return new Response(JSON.stringify({ id: current.id, status: "running" }), { status: 202 });
    return new Response(
      JSON.stringify(
        path.endsWith("/runs") ? { items: [current], total: 1, page: 1, page_size: 25 } : current,
      ),
    );
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

it("shows event generation time in Bogota with run and exact process identity", async () => {
  mock({
    ...run,
    metrics: {
      ...run.metrics,
      warnings: [
        {
          code: "provider_status_deadline_conflict",
          message: "El estado contradice el deadline",
          generated_at: "2026-10-21T23:42:16Z",
          run_id: run.id,
          process_identity: "secop:CO1.NTC.123",
          codigo_proceso: "CM-006-2026",
        },
      ],
    },
    errors: [
      {
        code: "extraction_failed",
        message: "Falló la extracción",
        generated_at: "2026-10-21T23:43:17Z",
        run_id: run.id,
      },
    ],
  });
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  await screen.findByText("El estado contradice el deadline");
  expect(screen.getAllByRole("columnheader", { name: "Fecha/Hora" })).toHaveLength(3);
  expect(screen.getByText("21/10/2026 18:42:16")).toBeInTheDocument();
  expect(screen.getByText("21/10/2026 18:43:17")).toBeInTheDocument();
  expect(screen.getByText(/secop:CO1.NTC.123/)).toBeInTheDocument();
});

it("does not invent generation time for historical warnings", async () => {
  mock({
    ...run,
    metrics: {
      ...run.metrics,
      warnings: [{ code: "legacy_warning", generated_at: null, run_id: run.id }],
    },
  });
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  expect(await screen.findByText("No registrada (histórico)")).toBeInTheDocument();
});
it("shows operational source, funnel, processes, duplicate and document review", async () => {
  mock();
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  expect(await screen.findByText("CM-006-2026")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Licitaciones.info (CDP)" })).toBeInTheDocument();
  expect(
    screen.getByText("Ya existe alerta para el proceso canónico", { exact: false }),
  ).toBeInTheDocument();
  expect(screen.getByText("Requiere revisión documental manual")).toBeInTheDocument();
  expect(screen.getByText("Alertas duplicadas omitidas")).toBeInTheDocument();
});
it("starts only from explicit user click", async () => {
  const fetch = mock();
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  await screen.findByText("CM-006-2026");
  expect(fetch.mock.calls.some(([r]) => r.method === "POST")).toBe(false);
  await userEvent.click(screen.getByRole("button", { name: "Ejecutar corrida Licitaciones.info" }));
  expect(fetch.mock.calls.filter(([r]) => r.method === "POST")).toHaveLength(1);
});
it("shows manual session instructions without automatic login", async () => {
  mock({ ...run, status: "session_unavailable" });
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  expect(await screen.findByRole("alert")).toHaveTextContent("inicia sesión");
  expect(screen.getByRole("alert")).toHaveTextContent("Vila Frontier");
});

it("distinguishes inconclusive SECOP sample without requesting another login", async () => {
  mock({
    ...run,
    status: "failed",
    metrics: {
      preflight: { preflight_status: "inconclusive", reason: "insufficient_secop_sample" },
    },
  });
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  expect(await screen.findByRole("alert")).toHaveTextContent("Preflight inconcluso");
  expect(screen.getByRole("alert")).toHaveTextContent("insufficient_secop_sample");
  expect(screen.getByRole("alert")).not.toHaveTextContent("inicia sesión");
});

it("distinguishes unhealthy response from expired session", async () => {
  mock({
    ...run,
    status: "failed",
    metrics: {
      preflight: { preflight_status: "unhealthy_response", reason: "insufficient_enriched_rows" },
    },
  });
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  expect(await screen.findByRole("alert")).toHaveTextContent("respuesta no saludable");
  expect(screen.getByRole("alert")).not.toHaveTextContent("inicia sesión");
});

it("shows healthy preflight without exposing quality metrics in the funnel", async () => {
  mock({ ...run, metrics: { preflight: { preflight_status: "healthy" } } });
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  expect(await screen.findByText("Preflight saludable.")).toBeInTheDocument();
});

it("shows separate extraction results and errors with manual review", async () => {
  mock({
    ...run,
    metrics: {
      ...run.metrics,
      extraction_metrics_version: 2,
      extraction_attempted: 2,
      extraction_succeeded: 0,
      extraction_failed: 2,
      process_errors: 1,
      process_warnings: 0,
      extracted: 0,
    },
    items: [
      {
        ...run.items[0],
        stage: "extraction_partial",
        outcome: "failed",
        reason: "extraction_failed",
        errors: [{ code: "unsupported_format" }],
      },
    ],
  });
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  await screen.findByText("Formato documental no compatible");
  for (const [label, value] of [
    ["Extracciones intentadas", "2"],
    ["Extracciones con texto útil", "0"],
    ["Extracciones fallidas", "2"],
    ["Procesos con errores", "1"],
  ] as const) {
    const term = screen.getByText(label);
    expect(within(term.parentElement!).getByText(value)).toBeInTheDocument();
  }
  expect(screen.getByText("Requiere revisión documental manual")).toBeInTheDocument();
  expect(screen.queryByText(/Corrida histórica:/)).not.toBeInTheDocument();
});

it("does not relabel historical extracted attempts as successful extractions", async () => {
  mock({ ...run, metrics: { ...run.metrics, extracted: 6 } });
  renderWithProviders(<App />, { route: "/eureka/licitaciones" });
  expect(await screen.findByText(/Corrida histórica:/)).toBeInTheDocument();
  const term = screen.getByText("Extracciones con texto útil");
  expect(within(term.parentElement!).getByText("—")).toBeInTheDocument();
});
