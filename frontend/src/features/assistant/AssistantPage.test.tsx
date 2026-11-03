import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { App } from "../../App";
import { lastBody, mockApi } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { AssistantPage } from "./AssistantPage";
import { AssistantText } from "./AssistantText";

const PATH = "/api/eureka/assistant/chat";
const CONVERSATION = "88cc44ee-43d2-49eb-b695-323d089aab50";
const scrollToLatest = vi.fn();
const reply = {
  conversation_id: CONVERSATION,
  message:
    "**Corrales** merece revisión.\n\n- Hay evidencia parcial.\n- Verifica la forma de pago.",
  process_references: [
    {
      identity: "secop:CO1.NTC.11147197",
      process_code: "MC-CMC-003-2026",
      entity: "Concejo Municipal Corrales",
      municipality: "Corrales",
      department: "Boyacá",
      source_url: "https://community.secop.gov.co/Public/Tendering",
    },
  ],
};

beforeEach(() => {
  scrollToLatest.mockClear();
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
    configurable: true,
    value: scrollToLatest,
  });
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

it("provides navigation and three suggestions without contacting Foundry on load", () => {
  const fetch = mockApi({});
  renderWithProviders(<App />, { route: "/eureka/asistente" });
  expect(screen.getByRole("heading", { name: "Asistente Eureka" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Asistente Eureka" })).toHaveClass("active");
  expect(within(screen.getByLabelText("Preguntas sugeridas")).getAllByRole("button")).toHaveLength(
    3,
  );
  expect(fetch).not.toHaveBeenCalled();
});

it("sends a question, displays user/agent formatting and structured process cards", async () => {
  const fetch = mockApi({ [PATH]: () => ({ body: reply }) });
  const user = userEvent.setup();
  renderWithProviders(<AssistantPage />);
  await user.type(screen.getByLabelText("Tu pregunta"), "Revisa la última corrida");
  await user.click(screen.getByRole("button", { name: "Enviar" }));
  expect(await screen.findByText("MC-CMC-003-2026")).toBeInTheDocument();
  expect(screen.getByLabelText("Tu mensaje")).toHaveTextContent("Revisa la última corrida");
  const response = screen.getByLabelText("Respuesta de Eureka");
  expect(response.querySelector("strong")).toHaveTextContent("Corrales");
  expect(within(response).getAllByRole("listitem")).toHaveLength(2);
  expect(screen.getByText("Concejo Municipal Corrales")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Ver proceso" })).toHaveAttribute(
    "href",
    "/eureka/revision/secop%3ACO1.NTC.11147197",
  );
  expect(await lastBody(fetch, "POST", PATH)).toEqual({
    message: "Revisa la última corrida",
    conversation_id: null,
  });
  expect(scrollToLatest).toHaveBeenCalled();
});

it("sends a suggested question immediately", async () => {
  const fetch = mockApi({ [PATH]: () => ({ body: reply }) });
  renderWithProviders(<AssistantPage />);
  await userEvent.click(
    screen.getByRole("button", { name: "¿Qué salió en la última corrida CDP?" }),
  );
  await screen.findByText("MC-CMC-003-2026");
  expect(await lastBody(fetch, "POST", PATH)).toMatchObject({
    message: "¿Qué salió en la última corrida CDP?",
  });
});

it("maintains the opaque backend conversation for consecutive messages", async () => {
  const fetch = mockApi({ [PATH]: () => ({ body: reply }) });
  const user = userEvent.setup();
  renderWithProviders(<AssistantPage />);
  await user.type(screen.getByLabelText("Tu pregunta"), "Resumen{Enter}");
  await screen.findByText("MC-CMC-003-2026");
  await user.type(screen.getByLabelText("Tu pregunta"), "¿Y sus documentos?{Enter}");
  await waitFor(() => expect(screen.getAllByLabelText("Respuesta de Eureka")).toHaveLength(2));
  expect(await lastBody(fetch, "POST", PATH)).toEqual({
    message: "¿Y sus documentos?",
    conversation_id: CONVERSATION,
  });
  expect(screen.getAllByLabelText("Tu mensaje")).toHaveLength(2);
});

it("shows loading and blocks double submit while the request is pending", async () => {
  let finish!: (value: Response) => void;
  const fetch = vi.fn(
    () =>
      new Promise<Response>((resolve) => {
        finish = resolve;
      }),
  );
  vi.stubGlobal("fetch", fetch);
  const user = userEvent.setup();
  renderWithProviders(<AssistantPage />);
  await user.type(screen.getByLabelText("Tu pregunta"), "Resumen{Enter}");
  expect(screen.getByRole("status")).toHaveTextContent("Consultando Eureka…");
  expect(screen.getByLabelText("Tu pregunta")).toBeDisabled();
  expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Enviar" }));
  expect(fetch).toHaveBeenCalledTimes(1);
  await act(async () => {
    finish(new Response(JSON.stringify(reply), { status: 200 }));
    await Promise.resolve();
  });
  await screen.findByText("MC-CMC-003-2026");
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
});

it("preserves Shift+Enter as a new line without submitting", async () => {
  const fetch = mockApi({});
  const user = userEvent.setup();
  renderWithProviders(<AssistantPage />);
  await user.type(screen.getByLabelText("Tu pregunta"), "Primera{Shift>}{Enter}{/Shift}Segunda");
  expect(screen.getByLabelText("Tu pregunta")).toHaveValue("Primera\nSegunda");
  expect(fetch).not.toHaveBeenCalled();
});

it("shows a safe recoverable error and retries without exposing diagnostics", async () => {
  let failed = true;
  mockApi({
    [PATH]: () =>
      failed
        ? {
            status: 503,
            body: {
              message: "Authorization private-secret azure-endpoint",
              reset_conversation: true,
            },
          }
        : { body: reply },
  });
  const user = userEvent.setup();
  renderWithProviders(<AssistantPage />);
  await user.type(screen.getByLabelText("Tu pregunta"), "Resumen{Enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent("No pude consultar Eureka");
  expect(document.body).not.toHaveTextContent("private-secret");
  expect(screen.getByLabelText("Tu pregunta")).toHaveValue("Resumen");
  failed = false;
  await user.click(screen.getByRole("button", { name: "Reintentar" }));
  await screen.findByText("MC-CMC-003-2026");
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

it("clears context for an expired conversation and keeps its visible history", async () => {
  let expired = false;
  const fetch = mockApi({
    [PATH]: () => (expired ? { status: 404, body: { reset_conversation: true } } : { body: reply }),
  });
  const user = userEvent.setup();
  renderWithProviders(<AssistantPage />);
  await user.type(screen.getByLabelText("Tu pregunta"), "Primero{Enter}");
  await screen.findByText("MC-CMC-003-2026");
  expired = true;
  await user.type(screen.getByLabelText("Tu pregunta"), "Segundo{Enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent("expiró");
  expect(screen.getByLabelText("Respuesta de Eureka")).toBeInTheDocument();
  expired = false;
  await user.click(screen.getByRole("button", { name: "Reintentar" }));
  await waitFor(() => expect(screen.getAllByLabelText("Respuesta de Eureka")).toHaveLength(2));
  expect(await lastBody(fetch, "POST", PATH)).toMatchObject({ conversation_id: null });
});

it("does not accept an empty answer or infer cards from free model text", async () => {
  let empty = true;
  mockApi({
    [PATH]: () => ({
      body: { ...reply, message: empty ? "" : "Recomiendo MC-INVENTADO", process_references: [] },
    }),
  });
  const user = userEvent.setup();
  renderWithProviders(<AssistantPage />);
  await user.type(screen.getByLabelText("Tu pregunta"), "Resumen{Enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent("no devolvió una respuesta");
  empty = false;
  await user.click(screen.getByRole("button", { name: "Reintentar" }));
  await screen.findByText("Recomiendo MC-INVENTADO");
  expect(screen.queryByLabelText("Procesos consultados")).not.toBeInTheDocument();
});

it("starts a new conversation without using persisted browser storage", async () => {
  const fetch = mockApi({ [PATH]: () => ({ body: reply }) });
  const user = userEvent.setup();
  renderWithProviders(<AssistantPage />);
  await user.type(screen.getByLabelText("Tu pregunta"), "Resumen{Enter}");
  await screen.findByText("MC-CMC-003-2026");
  await user.click(screen.getByRole("button", { name: "Nueva conversación" }));
  expect(screen.queryByLabelText("Tu mensaje")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Preguntas sugeridas")).toBeInTheDocument();
  await user.type(screen.getByLabelText("Tu pregunta"), "Nuevo{Enter}");
  await screen.findByText("MC-CMC-003-2026");
  expect(await lastBody(fetch, "POST", PATH)).toMatchObject({ conversation_id: null });
});

it("renders model HTML and script URLs as inert text", () => {
  const { container } = renderWithProviders(
    <AssistantText
      text={
        '**Seguro**\n\n<img src=x onerror="alert(1)">\n<script>alert(1)</script>\n[jump](javascript:alert(1))'
      }
    />,
  );
  expect(screen.getByText("Seguro")).toHaveProperty("tagName", "STRONG");
  expect(container.querySelector("script, img, a")).toBeNull();
  expect(container).toHaveTextContent("<script>alert(1)</script>");
});

it("preserves numbered-list positions across paragraphs", () => {
  const { container } = renderWithProviders(
    <AssistantText text={"2. Segundo caso\n\nDetalles\n\n3. Tercer caso"} />,
  );
  expect(container.querySelectorAll("ol")[0]).toHaveAttribute("start", "2");
  expect(container.querySelectorAll("ol")[1]).toHaveAttribute("start", "3");
});

it("describes an exhausted conversation as ended rather than busy", async () => {
  mockApi({
    [PATH]: () => ({ status: 409, body: { code: "conversation_limit", reset_conversation: true } }),
  });
  renderWithProviders(<AssistantPage />);
  await userEvent.type(screen.getByLabelText("Tu pregunta"), "Resumen{Enter}");
  expect(await screen.findByRole("alert")).toHaveTextContent("terminó o expiró");
});

it("renders structured web sources separately and links native citation markers", async () => {
  mockApi({
    [PATH]: () => ({
      body: {
        ...reply,
        message: "Hallazgo externo preliminar.[1] No confirmado en Eureka.",
        process_references: [],
        external_references: [
          {
            citation_number: 1,
            title: "Fuente oficial",
            source: "www.colombiacompra.gov.co",
            url: "https://www.colombiacompra.gov.co/proceso",
            published_at: null,
            entity: null,
            location: null,
            confidence: "preliminar",
          },
        ],
      },
    }),
  });
  renderWithProviders(<AssistantPage />);
  await userEvent.type(screen.getByLabelText("Tu pregunta"), "busca en la web{Enter}");
  expect(await screen.findByLabelText("Fuentes externas de Web Search")).toHaveTextContent(
    "no han sido incorporados ni validados",
  );
  expect(screen.getByRole("link", { name: "Fuente 1: Fuente oficial" })).toHaveAttribute(
    "href",
    "https://www.colombiacompra.gov.co/proceso",
  );
  expect(screen.getByRole("link", { name: "[1] Fuente oficial" })).toHaveAttribute(
    "rel",
    "noopener noreferrer",
  );
  expect(screen.queryByLabelText("Procesos consultados")).not.toBeInTheDocument();
  expect(screen.queryByText(/Publicación:/)).not.toBeInTheDocument();
});

it("does not create web references or clickable URLs from free model text", () => {
  const { container } = renderWithProviders(
    <AssistantText text="No verificado [1] https://inventado.example/proceso" />,
  );
  expect(container.querySelector("a")).toBeNull();
});

it("does not activate unsafe structured citation URLs", () => {
  const { container } = renderWithProviders(
    <AssistantText
      text="Hallazgo[1]"
      externalReferences={[
        {
          citation_number: 1,
          title: "Unsafe",
          source: "example",
          url: "javascript:alert(1)",
          confidence: "preliminar",
        },
      ]}
    />,
  );
  expect(container.querySelector("a")).toBeNull();
});
