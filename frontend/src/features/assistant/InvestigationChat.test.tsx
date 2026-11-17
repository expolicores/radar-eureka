import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useLocation } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import { mockApi, lastBody } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { AssistantPage } from "./AssistantPage";
import { AssistantText } from "./AssistantText";

const COMMERCIAL = "/api/eureka/assistant/chat";
const INVESTIGATION = "/api/v1/investigation/assistant/chat";
const COMMERCIAL_ID = "88cc44ee-43d2-49eb-b695-323d089aab50";
const INVESTIGATION_ID = "11111111-43d2-49eb-b695-323d089aab50";
const RUN_ID = "aea6ad3f-d458-48c5-9f47-f56f919182ca";
const commercial = {
  conversation_id: COMMERCIAL_ID,
  message: "Respuesta comercial",
  process_references: [],
};
const investigative = {
  conversation_id: INVESTIGATION_ID,
  response: "Hallazgo investigativo con evidencia pendiente.",
  run_references: [RUN_ID],
  process_references: Array.from({ length: 32 }, (_, i) => `CO1.REQ.${1000 + i}`),
};
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});
const change = () =>
  userEvent.click(screen.getByRole("button", { name: "Asistente investigativo" }));
const back = () => userEvent.click(screen.getByRole("button", { name: "Asistente comercial" }));

it("defaults to commercial and switches copy and suggestions without fetching", async () => {
  const fetch = mockApi({});
  renderWithProviders(<AssistantPage />);
  expect(screen.getByRole("button", { name: "Asistente comercial" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await change();
  expect(screen.getByRole("heading", { name: "Asistente investigativo" })).toBeVisible();
  expect(screen.queryByRole("heading", { name: "Asistente Eureka" })).not.toBeInTheDocument();
  const suggestions = screen.getByLabelText("Preguntas investigativas sugeridas");
  expect(within(suggestions).getAllByRole("button")).toHaveLength(4);
  expect(suggestions).not.toHaveTextContent(/oportunidad|participación|vender|competir/i);
  expect(fetch).not.toHaveBeenCalled();
});

it("keeps endpoints, IDs, drafts and histories separate across mode changes", async () => {
  const fetch = mockApi({
    [COMMERCIAL]: () => ({ body: commercial }),
    [INVESTIGATION]: () => ({ body: investigative }),
  });
  renderWithProviders(<AssistantPage />);
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Tu pregunta"), "Comercial uno{Enter}");
  await screen.findByText("Respuesta comercial");
  await user.type(screen.getByLabelText("Tu pregunta"), "Borrador comercial");
  await change();
  await user.type(screen.getByLabelText("Tu pregunta investigativa"), "Investigar uno{Enter}");
  await screen.findByText(investigative.response);
  expect(await lastBody(fetch, "POST", INVESTIGATION)).toEqual({
    message: "Investigar uno",
    conversation_id: null,
    run_id: null,
  });
  await user.type(screen.getByLabelText("Tu pregunta investigativa"), "Investigar dos{Enter}");
  await waitFor(() => expect(screen.getAllByLabelText("Respuesta investigativa")).toHaveLength(2));
  expect(await lastBody(fetch, "POST", INVESTIGATION)).toMatchObject({
    conversation_id: INVESTIGATION_ID,
  });
  await back();
  expect(screen.getByLabelText("Tu pregunta")).toHaveValue("Borrador comercial");
  expect(screen.getByRole("log")).toHaveTextContent("Respuesta comercial");
  expect(screen.getByRole("log")).not.toHaveTextContent(investigative.response);
  await user.clear(screen.getByLabelText("Tu pregunta"));
  await user.type(screen.getByLabelText("Tu pregunta"), "Comercial dos{Enter}");
  await waitFor(() => expect(screen.getAllByLabelText("Respuesta de Eureka")).toHaveLength(2));
  expect(await lastBody(fetch, "POST", COMMERCIAL)).toEqual({
    message: "Comercial dos",
    conversation_id: COMMERCIAL_ID,
  });
  await change();
  expect(screen.getByRole("log")).toHaveTextContent("Investigar dos");
});

it("new conversation resets only the active assistant", async () => {
  const fetch = mockApi({
    [COMMERCIAL]: () => ({ body: commercial }),
    [INVESTIGATION]: () => ({ body: investigative }),
  });
  renderWithProviders(<AssistantPage />);
  await userEvent.type(screen.getByLabelText("Tu pregunta"), "Comercial{Enter}");
  await screen.findByText(commercial.message);
  await change();
  await userEvent.type(screen.getByLabelText("Tu pregunta investigativa"), "Primera{Enter}");
  await screen.findByText(investigative.response);
  await userEvent.click(screen.getByRole("button", { name: "Nueva conversación" }));
  expect(screen.getByRole("log")).not.toHaveTextContent(investigative.response);
  await userEvent.type(screen.getByLabelText("Tu pregunta investigativa"), "Nueva{Enter}");
  await screen.findByText(investigative.response);
  expect(await lastBody(fetch, "POST", INVESTIGATION)).toMatchObject({ conversation_id: null });
  await back();
  expect(screen.getByRole("log")).toHaveTextContent(commercial.message);
  await userEvent.type(screen.getByLabelText("Tu pregunta"), "Siguiente{Enter}");
  await waitFor(() => expect(screen.getAllByLabelText("Respuesta de Eureka")).toHaveLength(2));
  expect(await lastBody(fetch, "POST", COMMERCIAL)).toMatchObject({
    conversation_id: COMMERCIAL_ID,
  });
});

it("sends investigative suggestion and optional query run_id only to its endpoint", async () => {
  const fetch = mockApi({ [INVESTIGATION]: () => ({ body: investigative }) });
  renderWithProviders(<AssistantPage />, { route: `/eureka/asistente?run_id=${RUN_ID}` });
  await change();
  await userEvent.click(screen.getByRole("button", { name: "¿Por qué no hubo comparaciones?" }));
  await screen.findByText(investigative.response);
  expect(await lastBody(fetch, "POST", INVESTIGATION)).toEqual({
    message: "¿Por qué no hubo comparaciones?",
    conversation_id: null,
    run_id: RUN_ID,
  });
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("summarizes process references and expands at most five without automatic requests", async () => {
  const fetch = mockApi({ [INVESTIGATION]: () => ({ body: investigative }) });
  renderWithProviders(<AssistantPage />);
  await change();
  await userEvent.type(screen.getByLabelText("Tu pregunta investigativa"), "Resumen{Enter}");
  await screen.findByText(investigative.response);
  expect(screen.getByLabelText("Corrida relacionada")).toHaveTextContent(RUN_ID);
  expect(screen.getByText("32 procesos relacionados")).toBeVisible();
  expect(screen.queryByText("CO1.REQ.1031")).not.toBeInTheDocument();
  expect(fetch).toHaveBeenCalledTimes(1);
  await userEvent.click(screen.getByText("32 procesos relacionados"));
  expect(screen.getAllByRole("listitem")).toHaveLength(5);
});

function Location() {
  return <output aria-label="Ubicación">{useLocation().search}</output>;
}

it.each([false, true])(
  "opens the existing correct result route (private=%s)",
  async (privateMarket) => {
    mockApi({
      [INVESTIGATION]: () => ({ body: investigative }),
      [`/api/v1/investigation/runs/${RUN_ID}`]: () =>
        privateMarket ? { status: 404, body: {} } : { body: { run_id: RUN_ID } },
      [`/api/v1/investigation/market-runs/${RUN_ID}`]: () => ({ body: { run_id: RUN_ID } }),
    });
    renderWithProviders(
      <>
        <AssistantPage />
        <Location />
      </>,
    );
    await change();
    await userEvent.type(screen.getByLabelText("Tu pregunta investigativa"), "Resumen{Enter}");
    await screen.findByText(investigative.response);
    await userEvent.click(screen.getByRole("button", { name: RUN_ID }));
    await waitFor(() =>
      expect(screen.getByLabelText("Ubicación")).toHaveTextContent(
        privateMarket ? `private_run=${RUN_ID}` : `run=${RUN_ID}`,
      ),
    );
  },
);

it("keeps a pending response in its original mode when switching", async () => {
  let finish!: (response: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    ),
  );
  renderWithProviders(<AssistantPage />);
  await change();
  await userEvent.type(screen.getByLabelText("Tu pregunta investigativa"), "Resumen{Enter}");
  expect(screen.getByRole("status")).toHaveTextContent("Consultando asistente investigativo");
  expect(screen.getByLabelText("Tu pregunta investigativa")).toBeDisabled();
  await back();
  expect(screen.getByLabelText("Tu pregunta")).toBeEnabled();
  await act(async () => {
    finish(new Response(JSON.stringify(investigative)));
    await Promise.resolve();
  });
  expect(screen.getByRole("log")).not.toHaveTextContent(investigative.response);
  await change();
  expect(screen.getByRole("log")).toHaveTextContent(investigative.response);
});

it("shows a safe investigative error, retries, and rejects empty replies", async () => {
  let state = 0;
  mockApi({
    [INVESTIGATION]: () =>
      state === 0
        ? { status: 503, body: { message: "SECRET traceback", reset_conversation: true } }
        : { body: { ...investigative, response: state === 1 ? "" : investigative.response } },
  });
  renderWithProviders(<AssistantPage />);
  await change();
  await userEvent.type(screen.getByLabelText("Tu pregunta investigativa"), "Resumen{Enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "No fue posible consultar el asistente investigativo.",
  );
  expect(document.body).not.toHaveTextContent("SECRET");
  state = 1;
  await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));
  await waitFor(() => expect(screen.getByLabelText("Tu pregunta investigativa")).toBeEnabled());
  expect(screen.getByRole("alert")).toBeInTheDocument();
  state = 2;
  await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));
  await screen.findByText(investigative.response);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

it("renders investigative evidence tables as escaped, scrollable content", () => {
  const { container } = renderWithProviders(
    <AssistantText
      tables
      text={"| Proceso | Evidencia |\n| --- | --- |\n| MC-1 | <script>bad()</script> |"}
    />,
  );
  expect(screen.getByRole("columnheader", { name: "Proceso" })).toBeVisible();
  expect(screen.getByRole("cell", { name: "<script>bad()</script>" })).toBeVisible();
  expect(container.querySelector("script")).toBeNull();
});
