import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { mockApi } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { MarketBenchmarkCard, MarketBenchmarks, EvidenceQualityBadge } from "./MarketBenchmark";
import { samsungMarket } from "./fixtures/samsungMarket";
import { ResearchPage } from "./ResearchPage";

afterEach(() => vi.unstubAllGlobals());
const clone = () => structuredClone(samsungMarket);

it("presenta oferta, precio, cantidad, proveedor, documento, página, IVA y conflicto exacto", () => {
  renderWithProviders(<MarketBenchmarkCard report={clone()} />);
  const publicCard = within(screen.getByRole("region", { name: "Evidencia pública" }));
  expect(publicCard.getByText("$3.767.123")).toBeInTheDocument();
  expect(publicCard.getByText("1")).toBeInTheDocument();
  expect(publicCard.getByText("TEAM IT")).toBeInTheDocument();
  expect(
    publicCard.getByText(/Oferta documentada — aceptación\/adjudicación no confirmada/),
  ).toBeInTheDocument();
  expect(publicCard.getByText("Precio antes de IVA")).toBeInTheDocument();
  expect(publicCard.getByText("PDF p. 339 de 340")).toBeInTheDocument();
  expect(
    publicCard.getByText(/referencia MC-028-2026 aunque está asociado al proceso MC-070-2026/),
  ).toBeInTheDocument();
  expect(publicCard.getByRole("link", { name: /OFERTA ECONOMICA/ })).toHaveAttribute(
    "rel",
    "noreferrer",
  );
});

it("dos precios son estadísticas parciales, no benchmark definitivo ni diferencia calculada", () => {
  renderWithProviders(<MarketBenchmarkCard report={clone()} />);
  expect(screen.getByText("Evidencia de mercado insuficiente")).toBeInTheDocument();
  expect(screen.getByText("2 de 3 observaciones mínimas requeridas")).toBeInTheDocument();
  expect(screen.getByText("Estadísticas parciales")).toBeInTheDocument();
  expect(screen.getByText("$2.569.900")).toBeInTheDocument();
  expect(screen.getByText("Comparación monetaria no generada")).toBeInTheDocument();
  expect(screen.getByText("Sin señal definitiva")).toBeInTheDocument();
  expect(screen.queryByText("Diferencia absoluta")).not.toBeInTheDocument();
  expect(screen.queryByText(/PUBLIC_VS_PRIVATE_PRICE_DIFFERENCE/)).not.toBeInTheDocument();
  expect(screen.getByText(/Base tributaria no alineada/)).toBeInTheDocument();
  expect(screen.getByText(/no representa necesariamente el precio/)).toBeInTheDocument();
});

it("muestra ofertas válidas, referencia, moneda inferida, captura Bogotá y enlaces", () => {
  renderWithProviders(<MarketBenchmarkCard report={clone()} />);
  expect(screen.getAllByText("Aceptada monetariamente")).toHaveLength(2);
  expect(screen.getByRole("link", { name: /Abrir oferta de Éxito/ })).toHaveAttribute(
    "href",
    samsungMarket.benchmark.observations[0]?.url,
  );
  expect(screen.getAllByText(/04\/11\/2026 20:58:51/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/COP inferido/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/tienda y checkout sin verificar/).length).toBeGreaterThan(0);
  expect(screen.getByText(/Envío: \+ \$ 7.500/)).toBeInTheDocument();
});

it("conserva Addi ambigua expandible sin aceptarla monetariamente", async () => {
  renderWithProviders(<MarketBenchmarkCard report={clone()} />);
  expect(screen.getByText("Addi")).not.toBeVisible();
  await userEvent.click(screen.getByText("Observaciones ambiguas o rechazadas (1)"));
  expect(screen.getByText("Addi")).toBeVisible();
  expect(screen.getByText("Ambigua · excluida")).toBeVisible();
  expect(screen.getByText("$2.270.000")).toBeVisible();
  expect(screen.getAllByText("Aceptada monetariamente")).toHaveLength(2);
});

it("traduce razón de rechazo sin reemplazar el motivo recibido", async () => {
  const r = clone();
  Object.assign(r.benchmark.observations[2]!, {
    match_level: "reject",
    rejection_reason: "wrong_model",
  });
  renderWithProviders(<MarketBenchmarkCard report={r} />);
  await userEvent.click(screen.getByText(/Observaciones ambiguas o rechazadas/));
  expect(screen.getByText("Modelo diferente")).toBeVisible();
  expect(screen.getByText("Rechazada")).toBeVisible();
});

it.each([
  ["api_verified_price", "API verificada"],
  ["page_verified_price", "Página verificada"],
  ["shopping_provider_price", "Proveedor de shopping"],
  ["snippet_price", "Snippet / evidencia débil"],
])("badge %s", (quality, label) => {
  renderWithProviders(<EvidenceQualityBadge quality={quality} />);
  expect(screen.getByText(label)).toBeInTheDocument();
});

it("fuente degradada conserva precios y diagnóstico seguro", () => {
  const r = clone();
  r.errors = [{ code: "rate_limited", http_status: 429 }];
  renderWithProviders(<MarketBenchmarkCard report={r} />);
  expect(screen.getByRole("status")).toHaveTextContent(/el benchmark continúa/);
  expect(screen.getByText(/SerpApi: degraded/)).toBeInTheDocument();
  expect(screen.getByText(/rate_limited \(HTTP 429\)/)).toBeInTheDocument();
  expect(screen.getByText("$2.569.900")).toBeInTheDocument();
});

it("usa diferencias backend literalmente, incluso signo negativo, sin calcular", () => {
  const r = clone();
  r.comparison = {
    public_entity: "Entidad",
    public_unit_price: "1000000",
    private_median_price: "2000000",
    absolute_difference: "-777",
    percentage_difference: "-0.12345",
    public_price_date: "2026-10-01T15:00:00Z",
    market_captured_at: "2026-11-04T15:00:00Z",
    time_gap_days: "34",
  };
  r.signal = {
    type: "PUBLIC_VS_PRIVATE_PRICE_DIFFERENCE",
    meaning: "Existe una diferencia cuantificada.",
  };
  renderWithProviders(<MarketBenchmarkCard report={r} signals />);
  expect(screen.getByText(/\$.*-777/)).toBeInTheDocument();
  expect(screen.getByText("-0.12345 %")).toBeInTheDocument();
  expect(screen.getByText("Existe una diferencia cuantificada.")).toBeInTheDocument();
});

it("no presenta vendedores de un marketplace como tiendas diversas y separa duplicados", async () => {
  const r = clone();
  r.benchmark.benchmark_status = "ready";
  r.benchmark.evidence_sufficiency = "marketplace_concentrated_evidence";
  r.benchmark.independent_sources_count = 1;
  r.benchmark.distinct_sellers_count = 3;
  r.benchmark.duplicates = [
    { ...r.benchmark.observations[0]!, duplicate_of: "MCO123", valid_for_benchmark: true },
  ];
  renderWithProviders(<MarketBenchmarkCard report={r} />);
  expect(screen.getByText("Evidencia concentrada en marketplace")).toBeInTheDocument();
  expect(screen.getByText("1 fuentes/retailers independientes")).toBeInTheDocument();
  await userEvent.click(screen.getByText("Duplicados no contados (1)"));
  expect(screen.getByText("Duplicada · no contada")).toBeVisible();
  expect(screen.getAllByText("Aceptada monetariamente")).toHaveLength(2);
});

it("sin evidencia pública no inventa precio ni señal", () => {
  const r = clone();
  r.public_product = null;
  renderWithProviders(<MarketBenchmarkCard report={r} />);
  expect(screen.getByText(/No se ha vinculado evidencia pública verificable/)).toBeInTheDocument();
});

it("recibo ausente no se sustituye con el fixture Samsung", async () => {
  mockApi({ "/api/v1/investigation/private-market": () => ({ body: { reports: [] } }) });
  renderWithProviders(<MarketBenchmarks />);
  expect(
    await screen.findByText(/Benchmark no ejecutado o recibo no disponible/),
  ).toBeInTheDocument();
  expect(screen.queryByText(/Samsung/)).not.toBeInTheDocument();
});

it("error de lectura permite reintentar sin stack trace", async () => {
  mockApi({ "/api/v1/investigation/private-market": () => ({ status: 503, body: {} }) });
  renderWithProviders(<MarketBenchmarks />);
  expect(await screen.findByRole("alert")).toHaveTextContent(/No fue posible cargar/);
  expect(screen.getByRole("button", { name: "Reintentar carga de mercado" })).toBeInTheDocument();
});

it("enlace de un recibo sustituido conserva contexto y muestra ausencia explícita", async () => {
  mockApi({ "/api/v1/investigation/private-market": () => ({ body: { reports: [] } }) });
  renderWithProviders(<MarketBenchmarks />, { route: "/explorar?process=REQ1&market=gone" });
  expect(
    await screen.findByText(/Recibo no disponible. Puede haber sido sustituido/),
  ).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Volver al contexto/ })).toHaveAttribute(
    "href",
    "/explorar?process=REQ1",
  );
});

it("navega desde explorar al detalle publicado sin ejecutar providers", async () => {
  const fetch = mockApi({
    "/api/v1/investigation/private-market": () => ({ body: { reports: [clone()] } }),
    "/api/v1/investigation/research": () => ({
      body: {
        source: "socrata_secop",
        processes: [],
        comparisons: [],
        signals: [],
        signal_status: "insufficient_evidence",
        signal_reason: "Sin comparaciones",
      },
    }),
  });
  renderWithProviders(<ResearchPage />, { route: "/explorar" });
  const link = await screen.findByRole("link", { name: "Ver comparación de mercado" });
  expect(link).toHaveAttribute("href", "/explorar?market=samsung-fixture&process=CO1.REQ.11253117");
  await userEvent.click(link);
  expect(screen.getByRole("region", { name: "Evidencia pública" })).toBeInTheDocument();
  expect(screen.getByText("Sin señal definitiva")).toBeInTheDocument();
  expect(fetch.mock.calls.every(([r]) => r.method === "GET")).toBe(true);
  expect(
    fetch.mock.calls.every(([r]) => new URL(r.url).pathname.startsWith("/api/v1/investigation/")),
  ).toBe(true);
});

it("no mezcla recibos de otro proceso cuando se selecciona un contexto", async () => {
  mockApi({ "/api/v1/investigation/private-market": () => ({ body: { reports: [clone()] } }) });
  renderWithProviders(<MarketBenchmarks />, { route: "/explorar?process=OTRO" });
  expect(await screen.findByText(/recibo no disponible para este proceso/)).toBeInTheDocument();
  expect(
    screen.queryByRole("link", { name: "Ver comparación de mercado" }),
  ).not.toBeInTheDocument();
});
