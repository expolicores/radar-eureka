import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { caseDetail, caseSummary, lastBody, mockApi } from "../test/api";
import { renderWithProviders } from "../test/render";
import { SaveToCaseButton } from "./SaveToCaseButton";

const CASE = caseDetail();
const ITEMS_PATH = `/api/v1/cases/${CASE.id}/items`;

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Guardar en caso", () => {
  it("guarda la señal en el caso elegido y lo confirma", async () => {
    // Arrange
    const fetchMock = mockApi({
      "GET /api/v1/cases": () => ({ body: [caseSummary()] }),
      [`POST ${ITEMS_PATH}`]: () => ({ status: 201, body: CASE }),
    });
    const user = userEvent.setup();
    renderWithProviders(<SaveToCaseButton kind="signal" reference="SG-2026-0142" />);
    // Act
    await user.click(screen.getByRole("button", { name: "★ Guardar en caso" }));
    await user.click(
      await screen.findByRole("button", { name: /Televisores en sedes educativas/ }),
    );
    // Assert
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Guardado en el caso «Televisores en sedes educativas — Valle» como instantánea.",
    );
    await waitFor(async () =>
      expect(await lastBody(fetchMock, "POST", ITEMS_PATH)).toEqual({
        kind: "signal",
        reference: "SG-2026-0142",
      }),
    );
  });

  it("avisa cuando el elemento ya estaba guardado", async () => {
    // Arrange
    mockApi({
      "GET /api/v1/cases": () => ({ body: [caseSummary()] }),
      [`POST ${ITEMS_PATH}`]: () => ({
        status: 422,
        body: { title: "Regla de negocio no cumplida" },
      }),
    });
    const user = userEvent.setup();
    renderWithProviders(<SaveToCaseButton kind="signal" reference="SG-2026-0142" />);
    // Act
    await user.click(screen.getByRole("button", { name: "★ Guardar en caso" }));
    await user.click(
      await screen.findByRole("button", { name: /Televisores en sedes educativas/ }),
    );
    // Assert
    expect(await screen.findByRole("status")).toHaveTextContent(/Ya estaba guardado/);
  });
});
