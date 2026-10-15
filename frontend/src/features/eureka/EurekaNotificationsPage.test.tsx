import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "../../App";
import { lastQuery, mockApi } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import type { components } from "../../api/schema";

afterEach(() => vi.unstubAllGlobals());
const ID = "11111111-1111-4111-8111-111111111111";
const ALERT = "22222222-2222-4222-8222-222222222222";
const base = "/api/eureka/notifications";
const notification: components["schemas"]["NotificationSummary"] = {
  id: ID,
  alert_id: ALERT,
  alert_ids: [ALERT],
  channel: "email",
  recipient: "r@example.invalid",
  notification_type: "immediate",
  delivery_scope: "capture",
  delivery_mode: "file",
  provider: "file",
  status: "captured",
  created_at: "2026-10-14T15:00:00Z",
  updated_at: "2026-10-14T15:00:00Z",
  sent_at: null,
  captured_at: "2026-10-14T15:00:00Z",
  failed_at: null,
  processing_started_at: null,
  next_retry_at: null,
  provider_idempotency_until: null,
  delivery_ambiguous: false,
  attempt_count: 1,
  retry_count: 0,
  provider_message_id: "file:id",
  error_code: null,
  error_message: null,
  idempotency_key: "key",
  digest_from: null,
  digest_to: null,
};
const page = (items: (typeof notification)[], total = items.length) => ({
  items,
  total,
  page: 1,
  page_size: 25,
  counts: {},
});

it("distinguishes local capture and provider acceptance without sending controls", async () => {
  const fetch = mockApi({
    [base]: () => ({
      body: page([
        notification,
        { ...notification, id: ALERT, status: "sent", delivery_scope: "real", provider: "resend" },
      ]),
    }),
  });
  renderWithProviders(<App />, { route: "/eureka/notifications" });
  expect(await screen.findByText(/Capturado localmente · Alerta/)).toBeInTheDocument();
  expect(screen.getByText(/Aceptado por proveedor · Alerta/)).toBeInTheDocument();
  expect(
    screen.getByText(/no confirma entrega en bandeja, apertura ni lectura/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Enviar/ })).not.toBeInTheDocument();
  expect(screen.getAllByRole("link", { name: /Ver alerta/ })[0]).toHaveAttribute(
    "href",
    `/eureka/alerts/${ALERT}`,
  );
  expect(fetch.mock.calls.every(([r]) => r.method === "GET")).toBe(true);
});

it("loads frozen text and attempts lazily, rendering HTML as text", async () => {
  mockApi({
    [base]: () => ({ body: page([notification]) }),
    [`${base}/${ID}`]: () => ({
      body: {
        ...notification,
        payload_snapshot: {
          subject: "Covarachía",
          text: '<script>alert("x")</script> · Jugo Hit · Score 65',
        },
        attempt_history: [
          {
            attempt_number: 1,
            provider: "file",
            result: "captured",
            timestamp: "2026-10-14",
            duration_ms: 5,
          },
        ],
      },
    }),
  });
  renderWithProviders(<App />, { route: "/eureka/notifications" });
  await screen.findByText(/Capturado localmente · Alerta/);
  await userEvent.click(screen.getByText("Ver mensaje e intentos"));
  expect(await screen.findByText("Covarachía")).toBeInTheDocument();
  expect(await screen.findByText(/Jugo Hit · Score 65/)).toBeInTheDocument();
  expect(document.querySelector("script")).toBeNull();
});

it("filters and keeps filters on pagination", async () => {
  const fetch = mockApi({ [base]: () => ({ body: page([notification], 30) }) });
  renderWithProviders(<App />, { route: "/eureka/notifications" });
  await screen.findByText(/Capturado localmente · Alerta/);
  await userEvent.selectOptions(screen.getByLabelText("Estado"), "captured");
  await userEvent.click(screen.getByRole("button", { name: "Filtrar" }));
  await userEvent.click(await screen.findByRole("button", { name: /Siguiente/ }));
  await screen.findByText(/Página 2 de 2/);
  expect(lastQuery(fetch, base).get("status")).toBe("captured");
  expect(lastQuery(fetch, base).get("page")).toBe("2");
});

it("shows empty and schema-pending states", async () => {
  mockApi({ [base]: () => ({ body: page([]) }) });
  const view = renderWithProviders(<App />, { route: "/eureka/notifications" });
  expect(await screen.findByText("No hay notificaciones para esta consulta.")).toBeInTheDocument();
  view.unmount();
  mockApi({ [base]: () => ({ status: 503, body: { title: "Servicio no disponible" } }) });
  renderWithProviders(<App />, { route: "/eureka/notifications" });
  expect(await screen.findByRole("alert")).toHaveTextContent("Servicio no disponible");
});

it("notification alert deep link uses the existing single-alert API", async () => {
  const fetch = mockApi({
    [`/api/eureka/alerts/${ALERT}`]: () => ({
      body: {
        id: ALERT,
        opportunity_id: ID,
        run_id: ID,
        alert_type: "new_opportunity",
        rule_version: "fixture",
        created_at: "2026-10-14T15:00:00Z",
        priority: "high",
        review_required: true,
        reasons: [],
        snapshot: {
          entity: "Escuela",
          municipality: "Covarachía",
          department: "Boyacá",
          budget: 2080000,
          score: 65,
        },
      },
    }),
    "/api/eureka/radar-runs": () => ({ body: { items: [], total: 0, page: 1, page_size: 5 } }),
  });
  renderWithProviders(<App />, { route: `/eureka/alerts/${ALERT}` });
  expect(await screen.findByText(/Nueva oportunidad Eureka/)).toBeInTheDocument();
  expect(
    fetch.mock.calls.some(([r]) => new URL(r.url).pathname === `/api/eureka/alerts/${ALERT}`),
  ).toBe(true);
});
