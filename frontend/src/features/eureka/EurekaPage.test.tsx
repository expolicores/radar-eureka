import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "../../App";
import { mockApi, lastQuery } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import type { EurekaDetail, EurekaList, Evidence } from "./types";
import { EvidencePanel } from "./EvidencePanel";

const ID = "6e94cc77-9f88-4f4c-bfb8-2e832976f4c0";
const CANON = "52a96910-7900-52d1-8cd7-be8072e15556";
const base = "/api/eureka/opportunities";
const view = (value: unknown) => ({
  value,
  status: "confirmed",
  canonical_fact_id: CANON,
  confidence: "0.8",
});
const opportunity: EurekaList["items"][number] = {
  opportunity_id: ID,
  process_id: "d4bba041-acdf-4abd-b8d0-c94f51c5282c",
  secop_id: "CO1.REQ.11172521",
  title: "Suministro de refrigerios",
  reference: "012-2026",
  description: "DESCRIPCIÓN ORIGINAL; refrigerios\nCOMUNIDAD EDUCATIVA",
  source_url:
    "https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=original",
  entity: "I.E. San Luis Beltrán",
  department: "Boyacá",
  municipality: "Covarachía",
  budget: 2080000,
  category: ["packaged_food"],
  score: 65,
  priority: "high",
  review_required: true,
  enrichment_status: "consolidated",
  product_match: true,
  published_at: "2026-10-07",
};
function detail(): EurekaDetail {
  return {
    opportunity,
    details: {
      process_id: opportunity.process_id,
      opportunity_id: ID,
      secop_id: opportunity.secop_id,
      category: ["packaged_food"],
      score: 65,
      priority: "high",
      review_required: true,
      scoring_rule_version: "v1",
      enrichment_status: "consolidated",
      commercial: {
        products: [
          view({ name: "Jugo Hit", presentation_value: 200, presentation_unit: "ml" }),
          view({ name: "Chocorramo tradicional", presentation_value: 65, presentation_unit: "g" }),
        ],
        purchase_items: [
          view({
            description: "REFRIGERIOS PACK",
            quantity: 400,
            unit: "PACK",
            unit_price_cop: 5200,
            total_cop: 2080000,
          }),
        ],
        budget_cop: view({ value: 2080000, unit: "COP" }),
        unspsc: [view({ code: "50192703" })],
      },
      execution: {
        execution_term: view({ value: 5, kind: "calendar", trigger: "desde firma del contrato" }),
        delivery_location: view("Institución Educativa San Luis Beltrán, Covarachía"),
        delivery_count: null,
      },
      payment: {
        payment_method: view({ mode: "single_payment" }),
        payment_percentage: view({ value: 100 }),
        payment_term: view({ value: 30, kind: "calendar", trigger: "desde aprobación" }),
      },
      requirements: {
        guarantee_required: [view({ state: "not_required", subject: "policy" })],
        rup_required: null,
        experience_required: null,
        operational_observations: [],
      },
      commercial_profile: {},
      quality: {
        conflicts: [],
        canonical_fact_count: 18,
        structured_fact_count: 39,
        missing_fields: ["RUP_REQUIRED", "DELIVERY_COUNT", "EXPERIENCE_REQUIRED"],
        discovery_review_notes: ["Vigencia por confirmar: falta fecha de cierre"],
      },
      evidence: {
        "commercial.products": [
          {
            canonical_fact_id: CANON,
            structured_fact_ids: ["a", "b", "c", "d"],
            confidence: "0.8",
            corroborated: true,
          },
        ],
      },
    },
  };
}
const evidence: Evidence = {
  canonical_fact_id: CANON,
  structured_fact_id: "55c2c8da-10a9-443a-8abc-d19287614605",
  document_version_id: opportunity.process_id,
  content_fragment_id: null,
  evidence_text: "JUGO HIT TETRA X 200Ml",
  source_locator: {
    sources: [
      {
        original_name: "ESTUDIOS PREVIOS Firmados.pdf",
        locator: { page_number: 3 },
        text: "JUGO HIT TETRA X 200Ml",
      },
    ],
  },
  confidence: "0.8",
  corroborated: true,
  rule_name: "product",
  rule_version: "v1",
};
function routes(data = detail()) {
  return mockApi({
    [base]: () => ({ body: { items: [opportunity], total: 1, page: 1, page_size: 25 } }),
    [`${base}/${ID}`]: () => ({ body: data }),
    [`${base}/${ID}/evidence`]: () => ({ body: [evidence] }),
  });
}
afterEach(() => vi.unstubAllGlobals());

it("shows the metadata-only warning in opportunity detail with unchanged score", async () => {
  const data = detail();
  data.opportunity = {
    ...data.opportunity,
    evidence_level: "metadata_only",
    document_status: "unavailable",
  };
  routes(data);
  renderWithProviders(<App />, { route: `/eureka/${ID}` });
  expect(
    await screen.findByText(
      "No se pudo validar documentalmente, pero por metadatos parece viable. Revisar manualmente.",
    ),
  ).toBeInTheDocument();
  expect(screen.getByText("Score 65")).toBeInTheDocument();
});

it("lista oportunidades, filtra y abre el detalle desde la navegación", async () => {
  const mock = routes();
  const user = userEvent.setup();
  renderWithProviders(<App />, { route: "/eureka" });
  expect(
    await screen.findByRole("link", { name: "Referencia del proceso: 012-2026" }),
  ).toBeInTheDocument();
  expect(screen.getByRole("note")).toHaveTextContent("PROCESOS SECOP");
  expect(screen.getByRole("note")).not.toHaveTextContent("ficticios");
  await user.selectOptions(screen.getByLabelText("Prioridad"), "high");
  await screen.findByText("Alta · 65");
  expect(lastQuery(mock, base).get("priority")).toBe("high");
  expect(screen.getByText(/ID SECOP: CO1.REQ.11172521/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Abrir proceso en SECOP" })).toHaveAttribute(
    "href",
    opportunity.source_url,
  );
  await user.click(screen.getByRole("link", { name: "Referencia del proceso: 012-2026" }));
  expect(await screen.findByRole("heading", { name: "Qué se compra" })).toBeInTheDocument();
  expect(
    screen.getByRole("heading", { name: "Referencia del proceso: 012-2026" }),
  ).toBeInTheDocument();
  expect(screen.getByText(/DESCRIPCIÓN ORIGINAL; refrigerios/).textContent).toBe(
    opportunity.description,
  );
  expect(screen.getByRole("link", { name: "Abrir proceso en SECOP" })).toHaveAttribute(
    "href",
    opportunity.source_url,
  );
});

it("muestra productos, ítem, ejecución, pago, ausencias y evidencia diferida", async () => {
  const mock = routes();
  const user = userEvent.setup();
  renderWithProviders(<App />, { route: `/eureka/${ID}` });
  expect(await screen.findByText("Jugo Hit · 200 ml")).toBeInTheDocument();
  expect(screen.getByText("Chocorramo tradicional · 65 g")).toBeInTheDocument();
  expect(screen.getByText("Cantidad: 400 PACK")).toBeInTheDocument();
  expect(screen.getByText(/5.200 COP unitario/)).toBeInTheDocument();
  expect(screen.getByText(/2.080.000 COP total/)).toBeInTheDocument();
  expect(screen.getByText("Información consolidada")).toBeInTheDocument();
  expect(screen.getByText("Requiere revisión")).toBeInTheDocument();
  expect(screen.getAllByText("4 evidencias · confianza 0.8 · corroborado")).toHaveLength(2);
  expect(screen.getByText("50192703")).toBeInTheDocument();
  expect(screen.getByText("5 días calendario · desde firma del contrato")).toBeInTheDocument();
  expect(screen.getByText("30 días calendario · desde aprobación")).toBeInTheDocument();
  expect(screen.getByText("Pago único")).toBeInTheDocument();
  expect(screen.getByText("100%")).toBeInTheDocument();
  expect(screen.getByText("No requerida")).toBeInTheDocument();
  expect(
    within(screen.getByText("RUP", { exact: true }).parentElement!).getByText("No determinada"),
  ).toBeInTheDocument();
  expect(screen.getByText("RUP no determinado")).toBeInTheDocument();
  expect(screen.getByText(/0 conflictos · 18 canónicos · 39 hechos/)).toBeInTheDocument();
  expect(screen.getByText(/Vigencia por confirmar/)).toBeInTheDocument();
  expect(mock.mock.calls.some(([request]) => request.url.includes("/evidence"))).toBe(false);
  expect(screen.queryByText("JUGO HIT TETRA X 200Ml")).not.toBeInTheDocument();
  expect(screen.getByText("Ver evidencia de Jugo Hit").closest("details")).not.toHaveAttribute(
    "open",
  );
  await user.click(screen.getByText("Ver evidencia de Jugo Hit"));
  expect(await screen.findByText("ESTUDIOS PREVIOS Firmados.pdf")).toBeInTheDocument();
  expect(screen.getByText("página 3")).toBeInTheDocument();
  expect(screen.getByText("JUGO HIT TETRA X 200Ml")).toBeInTheDocument();
});

it("advierte cobertura OCR incompleta sin ocultar datos consolidados", async () => {
  const data = detail();
  Object.assign(data.details.quality, { extraction_coverage: { coverage_complete: false } });
  routes(data);
  renderWithProviders(<App />, { route: `/eureka/${ID}` });
  expect(await screen.findByText(/Cobertura documental parcial/)).toBeInTheDocument();
  expect(screen.getByText("Información consolidada")).toBeInTheDocument();
  expect(screen.getByText("Score 65")).toBeInTheDocument();
});

it("conserva datos parciales sin afirmar que los requisitos no existen", async () => {
  const data = detail();
  data.details.enrichment_status = "not_extracted";
  data.details.commercial = {};
  data.details.execution = {};
  data.details.payment = {};
  data.details.requirements = {};
  data.details.evidence = {};
  routes(data);
  renderWithProviders(<App />, { route: `/eureka/${ID}` });
  expect(await screen.findByText("Sin extracción")).toBeInTheDocument();
  expect(screen.queryByText("No requerida")).not.toBeInTheDocument();
  expect(screen.getAllByText("No determinada").length).toBeGreaterThan(1);
});

it("expone conflictos y candidatos en vez de escoger un valor", async () => {
  const data = detail();
  data.details.enrichment_status = "conflict";
  data.details.quality.conflicts = [
    { type: "QUANTITY", candidates: [{ value: 400 }, { value: 450 }] },
  ];
  data.details.commercial.purchase_items = [
    {
      value: { description: "REFRIGERIOS PACK", quantity: null, unit: "PACK" },
      status: "conflict",
    },
  ];
  routes(data);
  renderWithProviders(<App />, { route: `/eureka/${ID}` });
  expect(await screen.findByText("Conflicto documental")).toBeInTheDocument();
  expect(screen.getByText("Cantidad: No determinado PACK")).toBeInTheDocument();
  expect(screen.getByText("Revisar conflicto: QUANTITY")).toBeInTheDocument();
});

it("muestra error API y oportunidad inexistente con regreso al listado", async () => {
  mockApi({ [`${base}/${ID}`]: () => ({ status: 404, body: { title: "No encontrado" } }) });
  renderWithProviders(<App />, { route: `/eureka/${ID}` });
  expect(
    await screen.findByRole("heading", { name: "Oportunidad no encontrada" }),
  ).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Volver a Eureka" })).toBeInTheDocument();
});

it("muestra carga mientras espera la API", () => {
  vi.stubGlobal("fetch", () => new Promise(() => {}));
  renderWithProviders(<App />, { route: "/eureka" });
  expect(screen.getByRole("status")).toHaveTextContent("Cargando oportunidades");
});

it("maneja fallo de evidencia sin romper el detalle", async () => {
  mockApi({
    [`${base}/${ID}`]: () => ({ body: detail() }),
    [`${base}/${ID}/evidence`]: () => ({ status: 500, body: { title: "Error" } }),
  });
  const user = userEvent.setup();
  renderWithProviders(<App />, { route: `/eureka/${ID}` });
  await user.click(await screen.findByText("Ver evidencia de Jugo Hit"));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "No fue posible recuperar la evidencia",
  );
  expect(screen.getByText("Score 65")).toBeInTheDocument();
});

it("agrupa sin repetir bloques y mantiene evidencia técnica completa accesible", async () => {
  mockApi({
    [`${base}/${ID}/evidence`]: () => ({
      body: [evidence, { ...evidence, structured_fact_id: "second" }],
    }),
  });
  const user = userEvent.setup();
  renderWithProviders(
    <EvidencePanel id={ID} label="Jugo Hit" references={[{ canonical_fact_id: CANON }]} />,
  );
  await user.click(screen.getByText("Ver evidencia de Jugo Hit"));
  expect(await screen.findByText("JUGO HIT TETRA X 200Ml")).toBeInTheDocument();
  expect(screen.getAllByText("ESTUDIOS PREVIOS Firmados.pdf")).toHaveLength(1);
  expect(screen.getAllByText("JUGO HIT TETRA X 200Ml")).toHaveLength(1);
  expect(screen.queryByText(/"structured_fact_id"/)).not.toBeInTheDocument();
  await user.click(screen.getByText("Ver evidencia técnica completa"));
  expect(await screen.findAllByText(/"structured_fact_id"/)).toHaveLength(2);
  expect(screen.getAllByText(/"source_locator"/)).toHaveLength(2);
});

it("presenta DOCX como una fila legible y conserva las doce celdas en el nivel técnico", async () => {
  const headers = [
    "ITEM",
    "DESCRIPCION DEL BIEN O SERVICIO",
    "CANT",
    "UNIDAD DE MEDIDA",
    "VALOR UNITARIO",
    "VALOR TOTAL",
  ];
  const values = ["1", "REFRIGERIOS PACK", "400", "PACK", "XXXXX", "XXXXXX"];
  const sources = [headers, values].flatMap((row, rowIndex) =>
    row.map((text, index) => ({
      original_name: "Propuesta.docx",
      text,
      locator: {
        kind: "docx_table_cell",
        table_number: 1,
        row_number: rowIndex + 1,
        column_number: index + 1,
      },
    })),
  );
  mockApi({
    [`${base}/${ID}/evidence`]: () => ({
      body: [
        { ...evidence, source_locator: { sources } },
        { ...evidence, structured_fact_id: "duplicate", source_locator: { sources } },
      ],
    }),
  });
  const user = userEvent.setup();
  renderWithProviders(
    <EvidencePanel id={ID} label="Ítem 1" references={[{ canonical_fact_id: CANON }]} />,
  );
  await user.click(screen.getByText("Ver evidencia de Ítem 1"));
  expect(await screen.findByText("tabla 1 · fila 2")).toBeInTheDocument();
  expect(screen.queryByText("tabla 1 · fila 1")).not.toBeInTheDocument();
  expect(screen.queryByText("DESCRIPCION DEL BIEN O SERVICIO")).not.toBeInTheDocument();
  expect(screen.getAllByText("REFRIGERIOS PACK")).toHaveLength(1);
  expect(screen.getByText("Descripción")).toBeInTheDocument();
  expect(screen.getByText("Cantidad")).toBeInTheDocument();
  expect(screen.getByText("400")).toBeInTheDocument();
  expect(screen.getAllByText("PACK")).toHaveLength(1);
  await user.click(screen.getByText("Ver evidencia técnica completa"));
  expect(await screen.findAllByText(/DESCRIPCION DEL BIEN O SERVICIO/)).toHaveLength(2);
});

it("cuenta fuentes útiles del ítem sin abrir su evidencia", async () => {
  mockApi({
    [`${base}/${ID}/evidence`]: () => ({
      body: [evidence, { ...evidence, structured_fact_id: "duplicate" }],
    }),
  });
  renderWithProviders(
    <EvidencePanel
      id={ID}
      label="Ítem 1"
      countSources
      references={[{ canonical_fact_id: CANON, confidence: "1.0", corroborated: true }]}
    />,
  );
  expect(await screen.findByText("1 fuente concordante · confianza 1.0")).toBeInTheDocument();
  expect(screen.queryByText("JUGO HIT TETRA X 200Ml")).not.toBeInTheDocument();
  expect(screen.getByText("Ver evidencia de Ítem 1").closest("details")).not.toHaveAttribute(
    "open",
  );
});
