import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { expect, it } from "vitest";
import { PublicPriceComparison, type PurchaseSide } from "./PublicPriceComparison";

function side(name: string): PurchaseSide {
  return {
    entity: `Entidad ${name}`,
    process_identity: `REQ-${name}`,
    process_code: `MC-${name}`,
    description: "Televisor 55 pulgadas",
    date: "2026-09-10",
    date_source: "socrata_jbjy-vk9h_fecha_de_firma",
    unit_price: "2000000",
    quantity: "2",
    unit: "UNIDAD",
    currency: "COP",
    tax_basis: "included",
    price_stage: "contract",
    characteristics: { screen_size_inches: 55, panel: "LED", resolution: "4k", smart: true },
    evidence: [
      {
        value_origin: "explicit",
        evidence: [
          {
            source_document: `Contrato ${name}.pdf`,
            source_page: 3,
            extraction_method: "native_pdf_text",
            evidence_text: "Tabla del ítem y precio",
          },
        ],
      },
    ],
  };
}

it("abre ambos lados con firma, precio, días y evidencia documental", () => {
  render(
    <MemoryRouter>
      <PublicPriceComparison
        sides={[side("A"), side("B")]}
        days={50}
        limitations={["no_inflation_or_fx_adjustment"]}
      />
    </MemoryRouter>,
  );
  expect(screen.getByText(/Días entre compras: 50/)).toBeInTheDocument();
  expect(screen.getByText("Entidad A")).toBeInTheDocument();
  expect(screen.getByText("Entidad B")).toBeInTheDocument();
  expect(screen.getByText(/Contrato A.pdf · página 3/)).toBeInTheDocument();
  expect(screen.getByText(/Contrato B.pdf · página 3/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "MC-A" })).toHaveAttribute(
    "href",
    "/explorar?process=REQ-A",
  );
});

it("mantiene desconocida la fecha y la base IVA cuando falta evidencia", () => {
  const a = side("A");
  a.date = null;
  a.date_source = null;
  a.tax_basis = "undetermined";
  render(
    <MemoryRouter>
      <PublicPriceComparison sides={[a, side("B")]} days={null} limitations={[]} />
    </MemoryRouter>,
  );
  expect(screen.getByText("Sin fecha de compra verificada")).toBeInTheDocument();
  expect(screen.getByText("Base no verificada; revisar")).toBeInTheDocument();
});
