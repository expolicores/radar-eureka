import { act, fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { mockApi, lastBody } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { MarketRuns } from "./MarketRuns";
import { ResearchRuns } from "./ResearchRuns";

const id = "c15dd5d5-30cf-4d24-bb9e-c6a40d2c8983";
const run = {
  run_id: id,
  run_type: "state_vs_private_market",
  status: "running",
  start_date: "2026-10-01",
  end_date: "2026-10-31",
  created_at: "2026-11-11T15:00:00Z",
  stage: "product_identification",
  counts: {},
  warnings: [],
  errors: [],
  result_url: null,
};
const policy = { "/api/v1/investigation/runs/policy": () => ({ body: { max_window_days: 60 } }) };
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

it("has two independent date actions and no product selector or startup POST", async () => {
  const fetch = mockApi(policy);
  renderWithProviders(
    <>
      <ResearchRuns />
      <MarketRuns />
    </>,
  );
  expect(
    screen.getByRole("button", { name: "Nueva corrida Estado vs Estado" }),
  ).toBeInTheDocument();
  await userEvent.click(
    screen.getByRole("button", { name: "Nueva corrida Estado vs mercado privado" }),
  );
  const form = screen.getByRole("form", { name: "Nueva corrida privada por fechas" });
  expect(form.querySelectorAll("input")).toHaveLength(2);
  expect(form.querySelectorAll("select")).toHaveLength(0);
  expect(within(form).getByLabelText("Fecha inicial")).toBeInTheDocument();
  expect(fetch.mock.calls.some(([r]) => r.method === "POST")).toBe(false);
  expect(fetch.mock.calls.some(([r]) => r.url.includes("market-products"))).toBe(false);
});

it("creates private date run independently without product or previous run", async () => {
  const fetch = mockApi({
    ...policy,
    "POST /api/v1/investigation/market-runs": () => ({ status: 202, body: run }),
    [`/api/v1/investigation/market-runs/${id}`]: () => ({ body: run }),
  });
  renderWithProviders(<MarketRuns />);
  await userEvent.click(
    screen.getByRole("button", { name: "Nueva corrida Estado vs mercado privado" }),
  );
  fireEvent.change(screen.getByLabelText("Fecha inicial"), { target: { value: "2026-10-01" } });
  fireEvent.change(screen.getByLabelText("Fecha final"), { target: { value: "2026-10-31" } });
  await screen.findByText(/60 d/);
  await userEvent.click(screen.getByRole("button", { name: "Iniciar corrida" }));
  expect(await lastBody(fetch, "POST", "/api/v1/investigation/market-runs")).toEqual({
    start_date: "2026-10-01",
    end_date: "2026-10-31",
  });
  expect(await screen.findByText(/Identificaci/)).toBeInTheDocument();
  expect(fetch.mock.calls.filter(([r]) => r.method === "POST")).toHaveLength(1);
});

it.each(["completed", "completed_with_warnings", "failed"])(
  "shows terminal private state %s and exact result",
  async (status) => {
    mockApi({
      ...policy,
      [`/api/v1/investigation/market-runs/${id}`]: () => ({
        body: {
          ...run,
          status,
          result_url: status === "failed" ? null : `/explorar?private_run=${id}&market_run=${id}`,
        },
      }),
    });
    renderWithProviders(<MarketRuns />, { route: `/explorar?market_job=${id}` });
    const panel = await screen.findByLabelText("Estado de corrida privada");
    expect(panel).toHaveTextContent("01-oct-2026");
    if (status !== "failed")
      expect(screen.getByRole("link", { name: "Ver resultados de esta corrida" })).toHaveAttribute(
        "href",
        `/explorar?private_run=${id}&market_run=${id}`,
      );
  },
);

it("private creation failure recovers active instead of repeating POST", async () => {
  const fetch = mockApi({
    ...policy,
    "POST /api/v1/investigation/market-runs": () => ({ status: 503, body: {} }),
    "/api/v1/investigation/market-runs/active": () => ({ body: run }),
    [`/api/v1/investigation/market-runs/${id}`]: () => ({ body: run }),
  });
  renderWithProviders(<MarketRuns />);
  await userEvent.click(
    screen.getByRole("button", { name: "Nueva corrida Estado vs mercado privado" }),
  );
  fireEvent.change(screen.getByLabelText("Fecha inicial"), { target: { value: "2026-10-01" } });
  fireEvent.change(screen.getByLabelText("Fecha final"), { target: { value: "2026-10-31" } });
  await screen.findByText(/60 d/);
  await userEvent.click(screen.getByRole("button", { name: "Iniciar corrida" }));
  await screen.findByRole("alert");
  await userEvent.click(screen.getByRole("button", { name: "Consultar corrida activa" }));
  await screen.findByLabelText("Estado de corrida privada");
  expect(fetch.mock.calls.filter(([r]) => r.method === "POST")).toHaveLength(1);
});

it("polling stops at terminal state", async () => {
  vi.useFakeTimers();
  let calls = 0;
  mockApi({
    ...policy,
    [`/api/v1/investigation/market-runs/${id}`]: () => ({
      body: { ...run, status: ++calls === 1 ? "running" : "completed" },
    }),
  });
  const view = renderWithProviders(<MarketRuns />, { route: `/explorar?market_job=${id}` });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(100);
  });
  expect(calls).toBe(1);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(5100);
  });
  expect(calls).toBe(2);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(15000);
  });
  expect(calls).toBe(2);
  view.unmount();
});
