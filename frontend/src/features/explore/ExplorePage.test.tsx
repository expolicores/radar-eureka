import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { AnalysisStatus } from "../../api/client";
import { FILTER_OPTIONS, lastQuery, mockApi, purchaseList, purchaseSummary } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { ExplorePage } from "./ExplorePage";

const PURCHASES = "/api/v1/purchases";
const FILTERS = "/api/v1/purchases/filters";

function mockExplore(list: unknown = purchaseList([purchaseSummary()], { total: 1280 })) {
  return mockApi({
    [PURCHASES]: () => ({ body: list }),
    [FILTERS]: () => ({ body: FILTER_OPTIONS }),
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Explorar compras", () => {
  it("muestra las compras con formatos colombianos, el contador y la fecha de corte", async () => {
    // Arrange
    mockExplore();
    // Act
    renderWithProviders(<ExplorePage />, { route: "/explorar" });
    // Assert
    const row = (await screen.findByText("CO1.PCCNTR.0000142")).closest("tr");
    expect(row).not.toBeNull();
    const cells = within(row as HTMLElement);
    expect(cells.getByText("SECOP II")).toBeInTheDocument();
    expect(cells.getByText("$39.600.000")).toBeInTheDocument();
    expect(cells.getByText("14-ago-2026")).toBeInTheDocument();
    expect(screen.getByText("1.280 compras")).toBeInTheDocument();
    expect(await screen.findByText(/Datos actualizados al 06-oct-2026 03:10/)).toBeInTheDocument();
  });

  it.each<[AnalysisStatus, string]>([
    ["with_signal", "⚑ Con señal"],
    ["compared_no_signal", "✓ Comparado · sin señal"],
    ["insufficient_comparables", "Comparables insuficientes"],
    ["pending_comparison", "Pendiente de comparación"],
    ["no_unit_price", "ⓘ Sin precio unitario · limitación de la fuente"],
    ["quality_review", "◐ En revisión de calidad"],
    ["vat_incomplete", "IVA no comparable · comparación incompleta"],
    ["excluded", "Excluido · no es compra de televisores"],
  ])("muestra la insignia del estado %s", async (status, label) => {
    // Arrange
    mockExplore(purchaseList([purchaseSummary({ analysis_status: status })]));
    // Act
    renderWithProviders(<ExplorePage />);
    // Assert
    expect(await screen.findByText(label)).toBeInTheDocument();
  });

  it("consulta la API con los filtros elegidos y vuelve a la página 1", async () => {
    // Arrange
    const fetchMock = mockExplore();
    const user = userEvent.setup();
    renderWithProviders(<ExplorePage />, { route: "/explorar?page=3" });
    await screen.findByText("CO1.PCCNTR.0000142");
    // Act
    await user.type(screen.getByRole("searchbox", { name: "Buscar compras" }), "san rafael");
    await user.selectOptions(await screen.findByRole("combobox", { name: "Fuente" }), "tvec");
    await user.selectOptions(screen.getByRole("combobox", { name: "Valor" }), "between_20m_100m");
    await user.selectOptions(screen.getByRole("combobox", { name: "Con señal" }), "true");
    await user.selectOptions(screen.getByRole("combobox", { name: "Orden" }), "value_desc");
    // Assert
    await waitFor(() => {
      const query = lastQuery(fetchMock, PURCHASES);
      expect(query.get("q")).toBe("san rafael");
      expect(query.get("source")).toBe("tvec");
      expect(query.get("value_range")).toBe("between_20m_100m");
      expect(query.get("sort")).toBe("value_desc");
      expect(query.get("has_signal")).toBe("true");
      expect(query.get("page")).toBe("1");
    });
  });

  it("restaura los filtros desde la URL", async () => {
    // Arrange
    const fetchMock = mockExplore();
    // Act
    renderWithProviders(<ExplorePage />, { route: "/explorar?source=tvec&page=2" });
    // Assert
    await waitFor(() =>
      expect(screen.getByRole("combobox", { name: "Fuente" })).toHaveValue("tvec"),
    );
    const query = lastQuery(fetchMock, PURCHASES);
    expect(query.get("source")).toBe("tvec");
    expect(query.get("page")).toBe("2");
  });

  it("muestra el estado vacío cuando no hay coincidencias", async () => {
    // Arrange
    mockExplore(purchaseList([]));
    // Act
    renderWithProviders(<ExplorePage />);
    // Assert
    expect(
      await screen.findByText("No hay compras que coincidan con los filtros."),
    ).toBeInTheDocument();
  });

  it("muestra el error y permite reintentar cuando la API falla", async () => {
    // Arrange
    let available = false;
    mockApi({
      [PURCHASES]: () =>
        available
          ? { body: purchaseList([purchaseSummary()]) }
          : { status: 503, body: { title: "Servicio no disponible" } },
      [FILTERS]: () => ({ body: FILTER_OPTIONS }),
    });
    const user = userEvent.setup();
    renderWithProviders(<ExplorePage />);
    expect(
      await screen.findByText("No fue posible cargar las compras. Intenta de nuevo."),
    ).toBeInTheDocument();
    // Act
    available = true;
    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    // Assert
    expect(await screen.findByText("CO1.PCCNTR.0000142")).toBeInTheDocument();
  });

  it("muestra el estado cargando mientras llega la respuesta", () => {
    // Arrange
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>(() => undefined)),
    );
    // Act
    renderWithProviders(<ExplorePage />);
    // Assert
    expect(screen.getByText("Cargando compras…")).toBeInTheDocument();
  });

  it("pagina y deshabilita Anterior en la primera página", async () => {
    // Arrange
    const fetchMock = mockExplore();
    const user = userEvent.setup();
    renderWithProviders(<ExplorePage />);
    expect(await screen.findByText("Página 1 de 52 · 1.280 compras")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "← Anterior" })).toBeDisabled();
    // Act
    await user.click(screen.getByRole("button", { name: "Siguiente →" }));
    // Assert
    await waitFor(() => expect(lastQuery(fetchMock, PURCHASES).get("page")).toBe("2"));
  });
});
