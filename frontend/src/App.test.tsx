import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { FILTER_OPTIONS, SIGNAL_SUMMARY, mockApi, signalList } from "./test/api";
import { renderWithProviders } from "./test/render";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Marco de la aplicación", () => {
  it("lleva la ruta raíz a Señales y advierte que los datos son ficticios", async () => {
    // Arrange
    mockApi({
      "/api/v1/signals": () => ({ body: signalList([]) }),
      "/api/v1/signals/summary": () => ({ body: SIGNAL_SUMMARY }),
      "/api/v1/purchases/filters": () => ({ body: FILTER_OPTIONS }),
    });
    // Act
    renderWithProviders(<App />, { route: "/" });
    // Assert
    expect(
      await screen.findByRole("heading", { level: 1, name: "Señales que merecen revisión" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Señales" })).toHaveClass("active");
    expect(screen.getAllByRole("note")[0]).toHaveTextContent("ficticios");
  });

  it("muestra las secciones pendientes como próximos incrementos", async () => {
    // Arrange
    mockApi({});
    const user = userEvent.setup();
    renderWithProviders(<App />, { route: "/explorar" });
    // Act
    await user.click(screen.getByRole("link", { name: "Administración" }));
    // Assert
    expect(
      screen.getByRole("heading", { level: 1, name: "Administración y operación" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Disponible en un próximo incremento del MVP Beta."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Administración" })).toHaveClass("active");
  });
});
