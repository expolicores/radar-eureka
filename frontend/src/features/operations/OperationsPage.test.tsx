import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "../../App";
import { lastBody, mockApi } from "../../test/api";
import { renderWithProviders } from "../../test/render";

afterEach(() => vi.unstubAllGlobals());
const status = {
  execution_config: {
    start_date: "2026-10-17",
    before_date: "2026-10-20",
    before_exclusive: true,
    timezone: "America/Bogota",
    regions: ["Boyacá", "Casanare", "Distrito Capital de Bogotá"],
    max_processes: 2500,
  },
  db_connected: true,
  schema_ready: false,
  latest: null,
  latest_success: null,
  automation_enabled: false,
  notification_mode: "disabled",
  notification_enabled: false,
  scheduler: { status: "not_registered", next_run: null },
  next_theoretical: "2026-10-15T07:00:00-05:00",
  ocr: { available: true, language: "spa", engine_version: "Tesseract 5" },
};

it("shows the backend effective window and exact regions before any execution", async () => {
  const fetch = routes(() => runningCycle);
  renderWithProviders(<App />, { route: "/eureka/operations" });
  expect(await screen.findByText("Desde: 17/10/2026 · 00:00")).toBeInTheDocument();
  expect(screen.getByText(/Incluye el día actual hasta lo disponible/)).toBeInTheDocument();
  expect(screen.getByText("Límite operativo: 2500 procesos")).toBeInTheDocument();
  expect(
    screen.getByText(/Hasta: 20\/10\/2026 · 00:00.*límite superior exclusivo/),
  ).toBeInTheDocument();
  expect(
    screen.getByText("Regiones: Boyacá · Casanare · Distrito Capital de Bogotá"),
  ).toBeInTheDocument();
  expect(fetch.mock.calls.every(([r]) => r.method === "GET")).toBe(true);
});

it("distinguishes theoretical schedule from an unregistered real task and missing migration", async () => {
  const fetch = mockApi({ "/api/operations/status": () => ({ body: status }) });
  renderWithProviders(<App />, { route: "/eureka/operations" });
  expect(await screen.findByText(/Scheduler real: Sin tarea registrada/)).toBeInTheDocument();
  expect(screen.getByText(/Próxima real del scheduler: No disponible/)).toBeInTheDocument();
  expect(screen.getByText(/La hora teórica no confirma/)).toBeInTheDocument();
  expect(screen.getByRole("alert")).toHaveTextContent("Migración 0016 pendiente");
  expect(fetch.mock.calls.every(([r]) => r.method === "GET")).toBe(true);
});

const ID = "11111111-1111-4111-8111-111111111111";
const ID2 = "22222222-2222-4222-8222-222222222222";
const runningCycle = {
  id: ID,
  status: "running",
  coordinator_active: true,
  started_at: "2026-10-15T02:00:00Z",
  stage: "secop",
  failures: 0,
  metrics: { secop_records_fetched: 0, candidates: 0, enriched: 0, alert_created: 0 },
  source_summary: { zero_records_confirmed: false },
  errors: [],
};

function routes(detail: () => unknown, postStatus = 202) {
  return mockApi({
    "/api/operations/status": () => ({ body: { ...status, schema_ready: true } }),
    "/api/operations/cycles": () => ({ body: [] }),
    ["/api/operations/cycles/" + ID]: () => ({ body: detail() }),
    "POST /api/operations/cycles/manual": () => ({
      status: postStatus,
      body: {
        cycle_id: ID,
        status: postStatus === 409 ? "skipped" : "running",
        reason: postStatus === 409 ? "already_running" : null,
        active_cycle_id: ID,
      },
    }),
  });
}

async function confirmRun() {
  const user = userEvent.setup();
  await user.click(await screen.findByRole("button", { name: "Ejecutar corrida manual" }));
  await user.click(screen.getByRole("button", { name: "Ejecutar" }));
}

it("renders the persisted availability diagnostic in a completed empty cycle", async () => {
  routes(() => ({
    ...runningCycle,
    status: "completed",
    source_summary: {
      zero_records_confirmed: true,
      socrata_availability_diagnostic: {
        performed: true,
        status: "dataset_lag",
        query_window_start: "2026-10-21",
        query_window_before: "2026-10-24",
        latest_available_date: "2026-10-20",
      },
    },
  }));
  renderWithProviders(<App />, { route: "/eureka/operations" });
  await confirmRun();
  expect(await screen.findByText(/Es probable que el dataset/)).toBeInTheDocument();
  expect(screen.getByText(/Última fecha disponible en Socrata: 20-oct-2026/)).toBeInTheDocument();
});

it("shows provisional object exclusions in the funnel", async () => {
  routes(() => ({
    ...runningCycle,
    status: "completed",
    metrics: { ...runningCycle.metrics, metadata_alerts_excluded_by_object: 4 },
  }));
  renderWithProviders(<App />, { route: "/eureka/operations" });
  await confirmRun();
  const label = await screen.findByText("Alertas provisionales excluidas por objeto");
  expect(within(label.closest("tr")!).getByText("4")).toBeInTheDocument();
});

it("requires confirmation; cancel never posts", async () => {
  const fetch = routes(() => runningCycle);
  const user = userEvent.setup();
  renderWithProviders(<App />, { route: "/eureka/operations" });
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeEnabled(),
  );
  await user.click(screen.getByRole("button", { name: "Ejecutar corrida manual" }));
  expect(screen.getByRole("dialog")).toHaveTextContent("Se consultará SECOP");
  await user.click(screen.getByRole("button", { name: "Cancelar" }));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(fetch.mock.calls.every(([r]) => r.method === "GET")).toBe(true);
});

it("accepts 202, displays running cycle and disables execution while polling", async () => {
  const fetch = routes(() => runningCycle);
  renderWithProviders(<App />, { route: "/eureka/operations" });
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeEnabled(),
  );
  await confirmRun();
  expect(await screen.findByText("Ciclo " + ID)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeDisabled();
  expect(screen.getByText(/esto no confirma una respuesta vacía/)).toBeInTheDocument();
  expect(await lastBody(fetch, "POST", "/api/operations/cycles/manual")).toEqual({});
});

it("polls after four seconds and stops on completion with a confirmed empty SECOP response", async () => {
  let polls = 0;
  routes(() =>
    ++polls === 1
      ? runningCycle
      : {
          ...runningCycle,
          status: "completed",
          duration_ms: 4100,
          source_summary: { zero_records_confirmed: true },
          notification_summary: { disabled: true },
        },
  );
  renderWithProviders(<App />, { route: "/eureka/operations" });
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeEnabled(),
  );
  await confirmRun();
  expect(
    await screen.findByRole("heading", { name: "Corrida completada" }, { timeout: 7000 }),
  ).toBeInTheDocument();
  expect(screen.getByText(/SECOP devolvió 0 registros/)).toBeInTheDocument();
  expect(screen.getByText(/Notificaciones deshabilitadas: estado esperado/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeEnabled();
  expect(polls).toBe(2);
}, 10000);

it.each(["completed_with_warnings", "failed"])(
  "shows %s with visible operational stage/errors",
  async (finalStatus) => {
    routes(() => ({
      ...runningCycle,
      status: finalStatus,
      stage: "documents_sync",
      failures: 1,
      errors: [{ stage: "documents_sync", code: "process_failed", type: "ValueError" }],
      log_files: { log: "cycle.log", summary: "cycle.json" },
    }));
    renderWithProviders(<App />, { route: "/eureka/operations" });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeEnabled(),
    );
    await confirmRun();
    expect(await screen.findByText("Ciclo " + ID)).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("documents_sync");
    expect(screen.getByText(/Logs del ciclo: cycle.log/)).toBeInTheDocument();
  },
);

it.each(["completed_with_warnings", "failed"])(
  "distinguishes limited radar from technical failure with cycle status %s",
  async (cycleStatus) => {
    routes(() => ({
      ...runningCycle,
      status: cycleStatus,
      radar_status: "limited",
      failures: 0,
      metrics: { limit_deferred: 1 },
      errors: [{ code: "radar_limited", severity: "warning" }],
    }));
    renderWithProviders(<App />, { route: "/eureka/operations" });
    await confirmRun();
    expect(await screen.findByRole("heading", { name: "Corrida limitada" })).toBeInTheDocument();
    expect(screen.getByText(/Estado: limited/)).toBeInTheDocument();
    expect(screen.getByText(/La cobertura está incompleta/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Falló la corrida" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeEnabled();
  },
);

it("does not hide a global technical failure behind limited radar", async () => {
  routes(() => ({
    ...runningCycle,
    status: "failed",
    radar_status: "limited",
    errors: [{ code: "radar_global_failure", type: "ValueError" }],
  }));
  renderWithProviders(<App />, { route: "/eureka/operations" });
  await confirmRun();
  expect(await screen.findByRole("heading", { name: "Falló la corrida" })).toBeInTheDocument();
});

it("shows already_running and follows the existing active cycle", async () => {
  routes(() => runningCycle, 409);
  renderWithProviders(<App />, { route: "/eureka/operations" });
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeEnabled(),
  );
  await confirmRun();
  expect(await screen.findByText("Ya hay una corrida en ejecución.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeDisabled();
});

it.each([0, 1])(
  "keeps a nonempty funnel with %i alerts and links when appropriate",
  async (alerts) => {
    routes(() => ({
      ...runningCycle,
      status: "completed",
      metrics: {
        secop_records_fetched: 10,
        candidates: 2,
        enriched: 2,
        alert_created: alerts,
        no_alert: 2 - alerts,
      },
    }));
    renderWithProviders(<App />, { route: "/eureka/operations" });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeEnabled(),
    );
    await confirmRun();
    expect(await screen.findByText(/SECOP sí devolvió registros/)).toBeInTheDocument();
    if (alerts)
      expect(screen.getByRole("link", { name: "Ver alertas" })).toHaveAttribute(
        "href",
        "/eureka/alerts",
      );
    else expect(screen.queryByRole("link", { name: "Ver alertas" })).not.toBeInTheDocument();
  },
);

it("permits a new explicitly confirmed cycle after completion", async () => {
  let posts = 0;
  const fetch = mockApi({
    "/api/operations/status": () => ({ body: { ...status, schema_ready: true } }),
    "/api/operations/cycles": () => ({ body: [] }),
    "POST /api/operations/cycles/manual": () => ({
      status: 202,
      body: { cycle_id: ++posts === 1 ? ID : ID2, status: "running" },
    }),
    ["/api/operations/cycles/" + ID]: () => ({ body: { ...runningCycle, status: "completed" } }),
    ["/api/operations/cycles/" + ID2]: () => ({
      body: { ...runningCycle, id: ID2, status: "completed" },
    }),
  });
  renderWithProviders(<App />, { route: "/eureka/operations" });
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Ejecutar corrida manual" })).toBeEnabled(),
  );
  await confirmRun();
  await screen.findByText("Ciclo " + ID);
  await confirmRun();
  await screen.findByText("Ciclo " + ID2);
  expect(fetch.mock.calls.filter(([r]) => r.method === "POST")).toHaveLength(2);
});

it("shows persisted funnel, notification mode and cycle errors", async () => {
  mockApi({
    "/api/operations/status": () => ({ body: { ...status, schema_ready: true } }),
    "/api/operations/cycles": () => ({
      body: [
        {
          id: "cycle-1",
          status: "completed_with_warnings",
          duration_ms: 1200,
          metrics: { candidates: 2, extraction_ocr: 1, notification_captured: 0 },
          errors: [{ code: "ocr_unavailable" }],
        },
      ],
    }),
  });
  renderWithProviders(<App />, { route: "/eureka/operations" });
  expect(await screen.findByText("Ciclo cycle-1")).toBeInTheDocument();
  expect(screen.getByText("Páginas OCR procesadas")).toBeInTheDocument();
  expect(screen.getByText(/modo disabled/)).toBeInTheDocument();
});
