import { act, fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { mockApi } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { ResearchRuns } from "./ResearchRuns";

const id = "c15dd5d5-30cf-4d24-bb9e-c6a40d2c8983";
const run = {
  run_id: id,
  status: "running",
  start_date: "2026-10-01",
  end_date: "2026-10-31",
  created_at: "2026-11-05T15:00:00Z",
  started_at: "2026-11-05T15:00:01Z",
  finished_at: null,
  stage: "discovery",
  warnings: [],
  errors: [],
  counts: {},
  result_url: null as string | null,
};
const policy = { "/api/v1/investigation/runs/policy": () => ({ body: { max_window_days: 60 } }) };
const route = `/explorar?research_run=${id}`;
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function openForm() {
  await userEvent.click(screen.getByRole("button", { name: "Nueva corrida Estado vs Estado" }));
  await screen.findByText(/Límite del pipeline actual: 60/);
}
function dates(start = "2026-10-01", end = "2026-10-31") {
  fireEvent.change(screen.getByLabelText("Fecha inicial"), { target: { value: start } });
  fireEvent.change(screen.getByLabelText("Fecha final"), { target: { value: end } });
}

it("abre y cancela un panel con solo dos filtros de fecha", async () => {
  mockApi(policy);
  renderWithProviders(<ResearchRuns />);
  await openForm();
  const form = screen.getByRole("form", { name: "Nueva corrida investigativa" });
  expect(form.querySelectorAll("input")).toHaveLength(2);
  expect(form.querySelectorAll("select")).toHaveLength(0);
  await userEvent.click(screen.getByRole("button", { name: "Cancelar" }));
  expect(screen.queryByRole("form")).not.toBeInTheDocument();
});

it.each([
  ["", "", "Indica fecha inicial y fecha final."],
  ["2026-10-01", "", "Indica fecha inicial y fecha final."],
  ["2026-11-01", "2026-10-31", "La fecha inicial debe ser anterior o igual a la fecha final."],
])("valida fechas %s a %s sin POST", async (start, end, message) => {
  const fetch = mockApi(policy);
  renderWithProviders(<ResearchRuns />);
  await openForm();
  dates(start, end);
  await userEvent.click(screen.getByRole("button", { name: "Iniciar corrida" }));
  expect(screen.getByRole("alert")).toHaveTextContent(message);
  expect(fetch.mock.calls.some(([r]) => r.method === "POST")).toBe(false);
});

it("POST envía solo fechas y no admite doble clic mientras registra", async () => {
  const base = mockApi({ ...policy, [`/api/v1/investigation/runs/${id}`]: () => ({ body: run }) });
  let resolvePost!: (r: Response) => void;
  const post = vi.fn<(request: Request) => Promise<Response>>(
    () =>
      new Promise<Response>((resolve) => {
        resolvePost = resolve;
      }),
  );
  vi.stubGlobal(
    "fetch",
    vi.fn((r: Request) => (r.method === "POST" ? post(r) : base(r))),
  );
  renderWithProviders(<ResearchRuns />);
  await openForm();
  dates();
  await userEvent.click(screen.getByRole("button", { name: "Iniciar corrida" }));
  const button = screen.getByRole("button", { name: "Registrando corrida…" });
  expect(button).toBeDisabled();
  await userEvent.click(button);
  expect(post).toHaveBeenCalledTimes(1);
  const request = post.mock.calls[0]?.[0];
  expect(await request?.clone().json()).toEqual({
    start_date: "2026-10-01",
    end_date: "2026-10-31",
  });
  act(() =>
    resolvePost(
      new Response(JSON.stringify({ ...run, status: "queued" }), {
        status: 202,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
  expect(await screen.findByText("En ejecución")).toBeInTheDocument();
  expect(screen.getByText(/01-oct-2026 → 31-oct-2026/)).toBeInTheDocument();
  expect(screen.getByText(/05\/11\/2026 10:00:00/)).toBeInTheDocument();
});

it.each([
  ["queued", "Pendiente"],
  ["running", "En ejecución"],
  ["completed", "Completada"],
  ["completed_with_warnings", "Completada con advertencias"],
  ["failed", "Fallida"],
])("recupera y muestra estado %s por run_id", async (status, label) => {
  mockApi({
    ...policy,
    [`/api/v1/investigation/runs/${id}`]: () => ({
      body: {
        ...run,
        status,
        finished_at: status.startsWith("completed") ? "2026-11-05T15:10:00Z" : null,
        counts: { processes_found: 4 },
        result_url: status.startsWith("completed") ? `/explorar?run=${id}` : null,
      },
    }),
  });
  renderWithProviders(<ResearchRuns />, { route });
  expect(await screen.findByText(label)).toBeInTheDocument();
  if (status.startsWith("completed")) {
    expect(screen.getByRole("link", { name: "Ver resultados de esta corrida" })).toHaveAttribute(
      "href",
      `/explorar?run=${id}`,
    );
    expect(screen.getByText("Procesos encontrados")).toBeInTheDocument();
  }
});

it("muestra reinicio de backend como fallo sin relanzar", async () => {
  const fetch = mockApi({
    ...policy,
    [`/api/v1/investigation/runs/${id}`]: () => ({
      body: { ...run, status: "failed", errors: ["backend_restarted"] },
    }),
  });
  renderWithProviders(<ResearchRuns />, { route });
  expect(await screen.findByText(/backend se reinició/)).toBeInTheDocument();
  expect(fetch.mock.calls.some(([r]) => r.method === "POST")).toBe(false);
});

it("run no encontrado y backend caído se muestran con reintento de lectura", async () => {
  mockApi({ ...policy, [`/api/v1/investigation/runs/${id}`]: () => ({ status: 404, body: {} }) });
  renderWithProviders(<ResearchRuns />, { route });
  expect(await screen.findByRole("alert")).toHaveTextContent("Corrida no encontrada");
  expect(screen.getByRole("button", { name: "Reintentar estado" })).toBeInTheDocument();
});

it("fallo de POST ofrece consultar activa y no reintenta crear automáticamente", async () => {
  const fetch = mockApi({
    ...policy,
    "POST /api/v1/investigation/runs": () => ({ status: 503, body: {} }),
    "/api/v1/investigation/runs/active": () => ({ body: run }),
    [`/api/v1/investigation/runs/${id}`]: () => ({ body: run }),
  });
  renderWithProviders(<ResearchRuns />);
  await openForm();
  dates();
  await userEvent.click(screen.getByRole("button", { name: "Iniciar corrida" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Puede haberse registrado");
  await userEvent.click(screen.getByRole("button", { name: "Consultar corrida activa" }));
  expect(await screen.findByText("En ejecución")).toBeInTheDocument();
  expect(fetch.mock.calls.filter(([r]) => r.method === "POST")).toHaveLength(1);
});

it("polling cada cinco segundos se detiene al completar y al desmontar", async () => {
  vi.useFakeTimers();
  let calls = 0;
  mockApi({
    ...policy,
    [`/api/v1/investigation/runs/${id}`]: () => ({
      body: {
        ...run,
        status: ++calls === 1 ? "running" : "completed",
        result_url: `/explorar?run=${id}`,
      },
    }),
  });
  const view = renderWithProviders(<ResearchRuns />, { route });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(100);
  });
  expect(screen.getByText("En ejecución")).toBeInTheDocument();
  expect(calls).toBe(1);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(5100);
  });
  expect(screen.getByText("Completada")).toBeInTheDocument();
  expect(calls).toBe(2);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(15000);
  });
  expect(calls).toBe(2);
  view.unmount();
  await vi.advanceTimersByTimeAsync(10000);
  expect(calls).toBe(2);
});

it("timeout de POST no repite la creación y permite recuperar estado", async () => {
  vi.useFakeTimers();
  let posts = 0;
  const base = mockApi(policy);
  vi.stubGlobal(
    "fetch",
    vi.fn((request: Request) => {
      if (request.method !== "POST") return base(request);
      posts++;
      return new Promise<Response>((_, reject) =>
        request.signal.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        ),
      );
    }),
  );
  renderWithProviders(<ResearchRuns />);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(100);
  });
  fireEvent.click(screen.getByRole("button", { name: "Nueva corrida Estado vs Estado" }));
  dates();
  fireEvent.submit(screen.getByRole("form", { name: "Nueva corrida investigativa" }));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(20100);
  });
  expect(screen.getByRole("alert")).toHaveTextContent("Puede haberse registrado");
  expect(posts).toBe(1);
  expect(screen.getByRole("button", { name: "Consultar corrida activa" })).toBeInTheDocument();
});

it("desmontar durante running elimina el polling activo", async () => {
  vi.useFakeTimers();
  let calls = 0;
  mockApi({
    ...policy,
    [`/api/v1/investigation/runs/${id}`]: () => {
      calls++;
      return { body: run };
    },
  });
  const view = renderWithProviders(<ResearchRuns />, { route });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(100);
  });
  expect(calls).toBe(1);
  view.unmount();
  await vi.advanceTimersByTimeAsync(15000);
  expect(calls).toBe(1);
});
