import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  FILTER_OPTIONS,
  SIGNAL_SUMMARY,
  lastQuery,
  mockApi,
  signal,
  signalList,
} from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { SignalsPage } from "./SignalsPage";

const SIGNALS = "/api/v1/signals";
const PROHIBITED_TERMS = ["sobreprecio", "corrupción", "fraude", "hallazgo fiscal"];

function mockSignals(list: unknown = signalList([signal()])) {
  return mockApi({
    [SIGNALS]: () => ({ body: list }),
    "/api/v1/signals/summary": () => ({ body: SIGNAL_SUMMARY }),
    "/api/v1/purchases/filters": () => ({ body: FILTER_OPTIONS }),
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Señales", () => {
  it("muestra indicadores, aviso y la señal con formatos", async () => {
    // Arrange
    mockSignals();
    // Act
    renderWithProviders(<SignalsPage />);
    // Assert
    const row = (await screen.findByText("⚑ SG-2026-0142")).closest("tr") as HTMLElement;
    const cells = within(row);
    expect(cells.getByText("$4.950.000")).toBeInTheDocument();
    expect(cells.getByText("+82,1 %")).toBeInTheDocument();
    expect(cells.getByText("Equivalente")).toBeInTheDocument();
    expect(cells.getByText("Alta")).toBeInTheDocument();
    expect(await screen.findByText("1.280")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText(/Una señal no es una conclusión/)).toBeInTheDocument();
  });

  it("consulta la API con la confianza y el orden elegidos", async () => {
    // Arrange
    const fetchMock = mockSignals();
    const user = userEvent.setup();
    renderWithProviders(<SignalsPage />, { route: "/senales?page=2" });
    await screen.findByText("⚑ SG-2026-0142");
    // Act
    await user.selectOptions(screen.getByRole("combobox", { name: "Confianza" }), "high");
    await user.selectOptions(screen.getByRole("combobox", { name: "Orden" }), "deviation");
    // Assert
    await waitFor(() => {
      const query = lastQuery(fetchMock, SIGNALS);
      expect(query.get("confidence")).toBe("high");
      expect(query.get("sort")).toBe("deviation");
      expect(query.get("page")).toBe("1");
    });
  });

  it("muestra el estado vacío cuando no hay señales", async () => {
    // Arrange
    mockSignals(signalList([]));
    // Act
    renderWithProviders(<SignalsPage />);
    // Assert
    expect(
      await screen.findByText("No hay señales que coincidan con los filtros."),
    ).toBeInTheDocument();
  });

  it("muestra el error con Reintentar cuando la API falla", async () => {
    // Arrange
    mockApi({
      [SIGNALS]: () => ({ status: 503, body: { title: "Servicio no disponible" } }),
      "/api/v1/signals/summary": () => ({ body: SIGNAL_SUMMARY }),
      "/api/v1/purchases/filters": () => ({ body: FILTER_OPTIONS }),
    });
    // Act
    renderWithProviders(<SignalsPage />);
    // Assert
    expect(
      await screen.findByText("No fue posible cargar las señales. Intenta de nuevo."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
  });

  it("no usa términos acusatorios en la pantalla", async () => {
    // Arrange
    mockSignals();
    // Act
    const { container } = renderWithProviders(<SignalsPage />);
    await screen.findByText("⚑ SG-2026-0142");
    // Assert
    const text = (container.textContent ?? "").toLowerCase();
    expect(PROHIBITED_TERMS.filter((term) => text.includes(term))).toEqual([]);
  });
});
