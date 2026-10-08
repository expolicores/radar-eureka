import { vi } from "vitest";

import type {
  CaseDetail,
  CaseSummary,
  FilterOptions,
  PurchaseList,
  PurchaseSummary,
  PurchaseDetail,
  Signal,
  SignalDetail,
  SignalList,
  SignalSummary,
} from "../api/client";

/** Builder de una compra resumida; por defecto, la compra de referencia del mockup. */
export function purchaseSummary(overrides: Partial<PurchaseSummary> = {}): PurchaseSummary {
  return {
    id: "031fd76d-19fa-4853-9eea-457326e6d679",
    reference: "CO1.PCCNTR.0000142",
    source: "secop_ii",
    entity_name: "Alcaldía Municipal de San Rafael del Valle",
    entity_department: "Valle del Cauca",
    supplier_name: "Tecnología Andina Demo S.A.S.",
    object_description: "Adquisición de televisores para las aulas",
    modality: "Mínima cuantía",
    total_value_cop: 39_600_000,
    signed_on: "2026-08-14",
    analysis_status: "pending_comparison",
    ...overrides,
  };
}

export function purchaseList(items: PurchaseSummary[], overrides: Partial<PurchaseList> = {}) {
  return { items, total: items.length, page: 1, page_size: 25, ...overrides };
}

export const FILTER_OPTIONS: FilterOptions = {
  sources: ["secop_ii", "tvec"],
  modalities: ["Mínima cuantía", "Tienda Virtual del Estado — Grandes superficies"],
  departments: ["Antioquia", "Valle del Cauca"],
  data_cutoff_at: "2026-10-06T08:10:00Z",
};

/** Builder de una señal; por defecto, la del mockup. */
export function signal(overrides: Partial<Signal> = {}): Signal {
  return {
    code: "SG-2026-0142",
    purchase_id: "031fd76d-19fa-4853-9eea-457326e6d679",
    line_number: 1,
    purchase_reference: "CO1.PCCNTR.0000142",
    source: "secop_ii",
    entity_name: "Alcaldía Municipal de San Rafael del Valle",
    entity_department: "Valle del Cauca",
    supplier_name: "Tecnología Andina Demo S.A.S.",
    supplier_nit: "900.000.142-1",
    item_description: 'TV 65" 4K LED',
    quantity: 8,
    unit_price_cop: 4_950_000,
    median_cop: 2_718_200,
    deviation_pct: "82.1",
    match_type: "equivalent",
    confidence_level: "high",
    confidence_score: 80,
    signed_on: "2026-08-14",
    ...overrides,
  };
}

export function signalList(items: Signal[], overrides: Partial<SignalList> = {}): SignalList {
  return { items, total: items.length, page: 1, page_size: 25, ...overrides };
}

/** Detalle de la señal del mockup con 6 comparables y una observación de mercado. */
export function signalDetail(overrides: Partial<SignalDetail> = {}): SignalDetail {
  const prices = [2_350_000, 2_610_000, 2_750_000, 2_900_000, 3_150_000, 3_600_000];
  return {
    signal: signal(),
    modality: "Mínima cuantía",
    vat_basis: "included",
    config_version_id: "analitica-v1",
    threshold_rule: "iqr",
    window_months: 6,
    q1_cop: 2_616_450,
    q3_cop: 2_961_400,
    threshold_cop: 3_478_825,
    comparables: prices.map((price, index) => ({
      purchase_id: `00000000-0000-0000-0000-00000000000${index}`,
      source: index % 2 === 0 ? "tvec" : "secop_ii",
      reference: index % 2 === 0 ? `Orden 16600${index}` : `CO1.PCCNTR.000020${index}`,
      entity_name: `Entidad comparable ${index}`,
      signed_on: "2026-05-05",
      unit_price_cop: price,
      same_model: false,
    })),
    market_status: "limited",
    market_reference_cop: 3_299_900,
    market_deviation_pct: "50.0",
    market_observations: [
      {
        store: "alkosto",
        product_description: 'TV 65" 4K UHD LED Smart · Pantalix mod. PX65U7000',
        effective_price_cop: 3_299_900,
        list_price_cop: null,
        observed_on: "2026-07-17",
        method: "simulated",
      },
    ],
    penalties: [
      {
        code: "equivalent_match",
        label: "Emparejamiento por equivalencia (no mismo modelo)",
        points: 20,
      },
      { code: "market_limited", label: "Benchmark 2 con evidencia limitada", points: 10 },
    ],
    data_cutoff_at: "2026-10-06T08:10:00Z",
    ...overrides,
  };
}

/** Ficha de la compra del mockup: televisor con señal y soporte excluido. */
export function purchaseDetail(overrides: Partial<PurchaseDetail> = {}): PurchaseDetail {
  return {
    ...purchaseSummary({ analysis_status: "with_signal" }),
    proceso_de_compra: "CO1.REQ.0031026",
    entity_municipality: "San Rafael del Valle",
    supplier_nit: "900.000.142-1",
    supplier_is_natural_person: false,
    source_url: null,
    data_cutoff_at: "2026-10-06T08:10:00Z",
    items: [
      {
        line_number: 1,
        description: 'Televisor Smart TV 65", resolución 4K UHD, panel LED',
        classification: "included",
        quantity: 8,
        unit_price_cop: 4_950_000,
        unit_price_status: "explicit",
        vat_basis: "included",
        screen_size_inches: 65,
        resolution: "uhd_4k",
        panel: "led",
        brand: null,
        model: null,
        comparison_outcome: "signal",
        signal_code: "SG-2026-0142",
      },
      {
        line_number: 2,
        description: 'Soporte de pared para TV 55"–75"',
        classification: "excluded_accessory",
        quantity: 8,
        unit_price_cop: null,
        unit_price_status: "not_published",
        vat_basis: "included",
        screen_size_inches: null,
        resolution: null,
        panel: null,
        brand: null,
        model: null,
        comparison_outcome: null,
        signal_code: null,
      },
    ],
    ...overrides,
  };
}

/** Caso del mockup con la señal y una nota. */
export function caseDetail(overrides: Partial<CaseDetail> = {}): CaseDetail {
  return {
    id: "c0ffee00-0000-4000-8000-000000000001",
    title: "Televisores en sedes educativas — Valle",
    item_count: 1,
    note_count: 1,
    created_at: "2026-09-18T14:00:00Z",
    last_activity_at: "2026-10-06T14:30:00Z",
    items: [
      {
        kind: "signal",
        reference: "SG-2026-0142",
        saved_at: "2026-10-06T14:12:00Z",
        snapshot: {
          code: "SG-2026-0142",
          item_description: 'TV 65" 4K LED',
          quantity: 8,
          unit_price_cop: 4_950_000,
          median_cop: 2_860_000,
          deviation_pct: "73.1",
          confidence_level: "medium",
          entity_name: "Alcaldía Municipal de San Rafael del Valle",
          config_version_id: "analitica-v1",
        },
      },
    ],
    notes: [
      {
        body: "La invitación pide solo especificaciones básicas (LED, 4K, Smart).",
        created_at: "2026-10-06T14:12:00Z",
      },
    ],
    ...overrides,
  };
}

export function caseSummary(detail: CaseDetail = caseDetail()): CaseSummary {
  return {
    id: detail.id,
    title: detail.title,
    item_count: detail.item_count,
    note_count: detail.note_count,
    created_at: detail.created_at,
    last_activity_at: detail.last_activity_at,
  };
}

export const SIGNAL_SUMMARY: SignalSummary = {
  tv_purchases: 1280,
  tv_purchases_by_source: { secop_ii: 348, tvec: 932 },
  signals: 42,
  signals_by_confidence: { high: 16, medium: 26, low: 0 },
  incomplete_comparisons: 40,
  without_source_information: 112,
  config_version_id: "analitica-v1",
  data_cutoff_at: "2026-10-06T08:10:00Z",
};

type Responder = (url: URL, request: Request) => { status?: number; body: unknown };

/**
 * Simula `fetch` respondiendo por ruta. La clave puede llevar método (`"POST /api/v1/cases"`);
 * sin método responde a cualquiera. Devuelve el mock para revisar lo que se pidió.
 */
export function mockApi(routes: Record<string, Responder>) {
  const fetchMock = vi.fn((request: Request) => {
    const url = new URL(request.url);
    const responder = routes[`${request.method} ${url.pathname}`] ?? routes[url.pathname];
    const { status = 200, body } = responder
      ? responder(url, request)
      : { status: 404, body: { title: "No encontrado" } };
    const contentType = status >= 400 ? "application/problem+json" : "application/json";
    return Promise.resolve(
      new Response(JSON.stringify(body), { status, headers: { "Content-Type": contentType } }),
    );
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** Cuerpo JSON de la última petición con ese método y ruta. */
export async function lastBody(
  fetchMock: ReturnType<typeof mockApi>,
  method: string,
  pathname: string,
): Promise<unknown> {
  const request = fetchMock.mock.calls
    .map(([call]) => call)
    .filter((call) => call.method === method && new URL(call.url).pathname === pathname)
    .at(-1);
  if (!request) {
    throw new Error(`No hubo ${method} a ${pathname}`);
  }
  return (await request.clone().json()) as unknown;
}

/** Parámetros de la última consulta a una ruta. */
export function lastQuery(
  fetchMock: ReturnType<typeof mockApi>,
  pathname: string,
): URLSearchParams {
  const urls = fetchMock.mock.calls
    .map(([request]) => new URL(request.url))
    .filter((url) => url.pathname === pathname);
  const last = urls.at(-1);
  if (!last) {
    throw new Error(`No hubo consultas a ${pathname}`);
  }
  return last.searchParams;
}
