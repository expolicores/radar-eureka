import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { mockApi, signalDetail } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { SignalDetailPage } from "./SignalDetailPage";

const PROHIBITED_TERMS = ["sobreprecio", "corrupción", "fraude", "hallazgo fiscal"];

function renderDetail(code = "SG-2026-0142") {
  return renderWithProviders(
    <Routes>
      <Route path="/senales/:code" element={<SignalDetailPage />} />
    </Routes>,
    { route: `/senales/${code}` },
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Detalle de la señal", () => {
  it("muestra benchmarks, confianza, aviso y evidencia pendiente", async () => {
    // Arrange
    mockApi({ "/api/v1/signals/SG-2026-0142": () => ({ body: signalDetail() }) });
    // Act
    renderDetail();
    // Assert
    expect(
      await screen.findByRole("heading", { level: 1, name: 'TV 65" 4K LED — 8 unidades' }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "CO1.PCCNTR.0000142" })).toHaveAttribute(
      "href",
      "/compras/031fd76d-19fa-4853-9eea-457326e6d679",
    );
    expect(screen.getByText("Benchmark 1 · Compras públicas comparables")).toBeInTheDocument();
    expect(screen.getByText("$3.478.825")).toBeInTheDocument();
    expect(screen.getByText("Benchmark 2 · Mercado")).toBeInTheDocument();
    expect(screen.getByText("Simulado (demo)")).toBeInTheDocument();
    expect(
      screen.getByText("Emparejamiento por equivalencia (no mismo modelo)"),
    ).toBeInTheDocument();
    expect(screen.getByText(/no constituye una conclusión ni una acusación/)).toBeInTheDocument();
    expect(
      screen.getByText(/todavía no hay un documento de origen que mostrar/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: /Distribución de 6 precios unitarios/ }),
    ).toBeInTheDocument();
  });

  it("muestra la tabla de comparables con enlace a cada compra", async () => {
    // Arrange
    mockApi({ "/api/v1/signals/SG-2026-0142": () => ({ body: signalDetail() }) });
    const user = userEvent.setup();
    renderDetail();
    // Act
    await user.click(await screen.findByRole("button", { name: "Ver como tabla" }));
    // Assert
    expect(screen.getByRole("link", { name: "Orden 166000" })).toHaveAttribute(
      "href",
      "/compras/00000000-0000-0000-0000-000000000000",
    );
    expect(screen.getAllByRole("row")).toHaveLength(1 + 6 + 2);
  });

  it("dice que la señal no existe cuando la API responde 404", async () => {
    // Arrange
    mockApi({});
    // Act
    renderDetail("SG-2099-0001");
    // Assert
    expect(await screen.findByText(/Señal no encontrada/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "← Volver a la lista de señales" }),
    ).toBeInTheDocument();
  });

  it("muestra el Benchmark 2 como no disponible cuando no hay observaciones", async () => {
    // Arrange
    const detail = signalDetail({
      market_status: "unavailable",
      market_observations: [],
      market_reference_cop: null,
      market_deviation_pct: null,
    });
    mockApi({ "/api/v1/signals/SG-2026-0142": () => ({ body: detail }) });
    // Act
    renderDetail();
    // Assert
    expect(await screen.findByText("No disponible · evidencia insuficiente")).toBeInTheDocument();
    expect(screen.getByText("Benchmark 1 · Compras públicas comparables")).toBeInTheDocument();
  });

  it("no usa términos acusatorios", async () => {
    // Arrange
    mockApi({ "/api/v1/signals/SG-2026-0142": () => ({ body: signalDetail() }) });
    // Act
    const { container } = renderDetail();
    await screen.findByText("Benchmark 2 · Mercado");
    // Assert
    const text = (container.textContent ?? "").toLowerCase();
    expect(PROHIBITED_TERMS.filter((term) => text.includes(term))).toEqual([]);
  });
});
