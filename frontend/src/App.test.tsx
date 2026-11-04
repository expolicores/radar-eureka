import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { mockApi } from "./test/api";
import { renderWithProviders } from "./test/render";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Marco de la aplicación", () => {
  it("lleva la raíz a investigación real sin usar señales demo como fallback", async () => {
    // Arrange
    mockApi({
      "/api/v1/investigation/research": () => ({
        body: {
          source: "socrata_secop",
          processes: [],
          signals: [],
          comparisons: [],
          signal_status: "not_run",
          signal_reason: "Sin muestra",
        },
      }),
    });
    // Act
    renderWithProviders(<App />, { route: "/" });
    // Assert
    expect(
      await screen.findByRole("heading", { level: 1, name: "Señales investigativas" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Señales" })).toHaveClass("active");
    expect(screen.getAllByRole("note")[0]).toHaveTextContent("SECOP REAL");
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
