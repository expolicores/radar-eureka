import { describe, expect, it } from "vitest";

import {
  formatBogotaDateTime,
  formatCop,
  formatDate,
  formatInteger,
  formatBogotaEventDateTime,
  formatBogotaNumericDateTime,
} from "./format";

describe("formatos", () => {
  it("separates tray entry minutes and diagnostic event seconds in Bogota", () => {
    expect(formatBogotaNumericDateTime("2026-10-21T23:42:16Z")).toBe("21/10/2026 18:42");
    expect(formatBogotaEventDateTime("2026-10-21T23:42:16Z")).toBe("21/10/2026 18:42:16");
  });
  it("formatea pesos colombianos con separador de miles y sin decimales", () => {
    // Arrange
    const value = 39_600_000;
    // Act
    const formatted = formatCop(value);
    // Assert
    expect(formatted).toBe("$39.600.000");
  });

  it("muestra una raya cuando el monto no existe", () => {
    // Arrange
    const value = null;
    // Act
    const formatted = formatCop(value);
    // Assert
    expect(formatted).toBe("—");
  });

  it("formatea enteros con separador de miles", () => {
    // Arrange
    const value = 1280;
    // Act
    const formatted = formatInteger(value);
    // Assert
    expect(formatted).toBe("1.280");
  });

  it.each([
    ["2026-08-14", "14-ago-2026"],
    ["2023-01-01", "01-ene-2023"],
  ])("formatea la fecha de negocio %s como dd-mmm-aaaa sin cambiar el día", (isoDate, expected) => {
    // Arrange (parámetros) / Act
    const formatted = formatDate(isoDate);
    // Assert
    expect(formatted).toBe(expected);
  });

  it("muestra la fecha de corte en hora de Bogotá", () => {
    // Arrange
    const cutoff = "2026-10-06T08:10:00Z";
    // Act
    const formatted = formatBogotaDateTime(cutoff);
    // Assert
    expect(formatted).toBe("06-oct-2026 03:10");
  });
});
