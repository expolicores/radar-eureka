import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { caseDetail, caseSummary, lastBody, mockApi } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { CasesPage } from "./CasesPage";

const CASE = caseDetail();
const CASE_PATH = `/api/v1/cases/${CASE.id}`;

function renderCases(route = "/casos") {
  return renderWithProviders(
    <Routes>
      <Route path="/casos" element={<CasesPage />} />
      <Route path="/casos/:caseId" element={<CasesPage />} />
    </Routes>,
    { route },
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Mis casos", () => {
  it("muestra el caso con su instantánea, notas y el aviso de privacidad", async () => {
    // Arrange
    mockApi({
      "GET /api/v1/cases": () => ({ body: [caseSummary()] }),
      [`GET ${CASE_PATH}`]: () => ({ body: CASE }),
    });
    // Act
    renderCases();
    // Assert
    expect(await screen.findByRole("heading", { level: 2, name: CASE.title })).toBeInTheDocument();
    expect(screen.getByText("Señal SG-2026-0142")).toBeInTheDocument();
    expect(screen.getByText(/Instantánea del 06-oct-2026 09:12/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ver versión actual" })).toHaveAttribute(
      "href",
      "/senales/SG-2026-0142",
    );
    expect(screen.getByText(/especificaciones básicas/)).toBeInTheDocument();
    expect(screen.getByText(/Tus casos son privados/)).toBeInTheDocument();
  });

  it("envía la nota escrita a la API", async () => {
    // Arrange
    const fetchMock = mockApi({
      "GET /api/v1/cases": () => ({ body: [caseSummary()] }),
      [`GET ${CASE_PATH}`]: () => ({ body: CASE }),
      [`POST ${CASE_PATH}/notes`]: () => ({ status: 201, body: CASE }),
    });
    const user = userEvent.setup();
    renderCases(`/casos/${CASE.id}`);
    await screen.findByRole("heading", { level: 2, name: CASE.title });
    // Act
    await user.type(screen.getByLabelText("Nueva nota"), "Pendiente: revisar otras sedes");
    await user.click(screen.getByRole("button", { name: "Agregar nota" }));
    // Assert
    await waitFor(async () =>
      expect(await lastBody(fetchMock, "POST", `${CASE_PATH}/notes`)).toEqual({
        body: "Pendiente: revisar otras sedes",
      }),
    );
  });

  it("no envía una nota vacía", async () => {
    // Arrange
    const fetchMock = mockApi({
      "GET /api/v1/cases": () => ({ body: [caseSummary()] }),
      [`GET ${CASE_PATH}`]: () => ({ body: CASE }),
    });
    const user = userEvent.setup();
    renderCases(`/casos/${CASE.id}`);
    await screen.findByRole("heading", { level: 2, name: CASE.title });
    // Act
    await user.click(screen.getByRole("button", { name: "Agregar nota" }));
    // Assert
    expect(await screen.findByText("La nota está vacía.")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([request]) => request.method === "POST")).toBe(false);
  });

  it("crea un caso nuevo con el título escrito", async () => {
    // Arrange
    const created = caseDetail({
      id: "c0ffee00-0000-4000-8000-000000000002",
      title: "Auditorios 75 pulgadas",
      items: [],
      notes: [],
    });
    const fetchMock = mockApi({
      "GET /api/v1/cases": () => ({ body: [] }),
      "POST /api/v1/cases": () => ({ status: 201, body: created }),
      [`GET /api/v1/cases/${created.id}`]: () => ({ body: created }),
    });
    const user = userEvent.setup();
    renderCases();
    expect(await screen.findByText(/Todavía no tienes casos/)).toBeInTheDocument();
    // Act
    await user.type(screen.getByLabelText("Nuevo caso"), "Auditorios 75 pulgadas");
    await user.click(screen.getByRole("button", { name: "+ Nuevo caso" }));
    // Assert
    await waitFor(async () =>
      expect(await lastBody(fetchMock, "POST", "/api/v1/cases")).toEqual({
        title: "Auditorios 75 pulgadas",
      }),
    );
  });
});
