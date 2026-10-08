import { screen, within } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { mockApi, purchaseDetail } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { PurchaseDetailPage } from "./PurchaseDetailPage";

const PURCHASE_ID = "031fd76d-19fa-4853-9eea-457326e6d679";

function renderPurchase() {
  return renderWithProviders(
    <Routes>
      <Route path="/compras/:purchaseId" element={<PurchaseDetailPage />} />
    </Routes>,
    { route: `/compras/${PURCHASE_ID}` },
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Ficha de la compra", () => {
  it("muestra datos clave, ítems y la señal enlazada", async () => {
    // Arrange
    mockApi({ [`/api/v1/purchases/${PURCHASE_ID}`]: () => ({ body: purchaseDetail() }) });
    // Act
    renderPurchase();
    // Assert
    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "Ficha de la compra CO1.PCCNTR.0000142",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/no se usa como precio unitario/)).toBeInTheDocument();
    expect(
      screen.getByText("Tecnología Andina Demo S.A.S. · NIT 900.000.142-1"),
    ).toBeInTheDocument();
    const signalLink = screen.getByRole("link", { name: "⚑ Señal SG-2026-0142" });
    expect(signalLink).toHaveAttribute("href", "/senales/SG-2026-0142");
    const accessory = screen
      .getByText('Soporte de pared para TV 55"–75"')
      .closest("tr") as HTMLElement;
    expect(within(accessory).getByText("Excluido · accesorio")).toBeInTheDocument();
    expect(within(accessory).getByText("Fuera de categoría")).toBeInTheDocument();
  });

  it("no muestra el documento cuando el proveedor es persona natural", async () => {
    // Arrange
    const detail = purchaseDetail({
      supplier_name: "Persona natural — documento no visible",
      supplier_nit: null,
      supplier_is_natural_person: true,
    });
    mockApi({ [`/api/v1/purchases/${PURCHASE_ID}`]: () => ({ body: detail }) });
    // Act
    renderPurchase();
    // Assert
    expect(await screen.findByText("Persona natural — documento no visible")).toBeInTheDocument();
    expect(screen.queryByText(/NIT/)).not.toBeInTheDocument();
  });

  it("dice que la compra no existe cuando la API responde 404", async () => {
    // Arrange
    mockApi({});
    // Act
    renderPurchase();
    // Assert
    expect(await screen.findByText("Compra no encontrada.")).toBeInTheDocument();
  });
});
