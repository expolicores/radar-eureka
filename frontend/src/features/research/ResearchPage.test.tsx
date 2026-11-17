import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { mockApi } from "../../test/api";
import { renderWithProviders } from "../../test/render";
import { ResearchPage } from "./ResearchPage";

afterEach(() => vi.unstubAllGlobals());

it("private result uses only its archived public evidence and candidate decisions", async () => {
  const id = "c15dd5d5-30cf-4d24-bb9e-c6a40d2c8983";
  const fetch = mockApi({
    "/api/v1/investigation/private-market": (url) => {
      expect(url.searchParams.get("run_id")).toBe(id);
      return { body: { reports: [] } };
    },
    "/api/v1/investigation/runs/policy": () => ({ body: { max_window_days: 60 } }),
    [`/api/v1/investigation/market-runs/${id}/research`]: () => ({
      body: {
        source: "socrata_secop",
        processes: [],
        comparisons: [],
        signals: [],
        signal_status: "insufficient_evidence",
        signal_reason: "Sin comparación",
        private_market_candidates: [
          {
            candidate_id: "new",
            process_identity: "CO1.REQ.NEW",
            process_code: "NEW-2026",
            description: "Televisor identificado durante esta ventana",
            brand: "LG",
            model: "55NANO80",
            status: "pending_review",
            reasons: ["missing_document_page_provenance"],
            public_evidence_status: "unresolved",
            market_status: "not_attempted",
            market_report_id: null,
            warnings: [],
          },
        ],
      },
    }),
  });
  renderWithProviders(<ResearchPage />, {
    route: `/explorar?private_run=${id}&market_run=${id}&run=unrelated`,
  });
  expect(await screen.findByText("NEW-2026")).toBeInTheDocument();
  expect(screen.getByText("Pendiente de revisión")).toBeInTheDocument();
  expect(screen.getByText("Falta documento, página o referencia de evidencia")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "NEW-2026" })).toHaveAttribute(
    "href",
    expect.stringContaining(`private_run=${id}`),
  );
  expect(
    fetch.mock.calls.some(([r]) => new URL(r.url).pathname === "/api/v1/investigation/research"),
  ).toBe(false);
});

it("abrir y cerrar un proceso conserva el run seleccionado", async () => {
  const runId = "c15dd5d5-30cf-4d24-bb9e-c6a40d2c8983";
  const windows: (string | null)[] = [];
  mockApi({
    "/api/v1/investigation/private-market": () => ({ body: { reports: [] } }),
    "/api/v1/investigation/runs/policy": () => ({ body: { max_window_days: 60 } }),
    [`/api/v1/investigation/runs/${runId}`]: () => ({
      body: {
        run_id: runId,
        status: "completed",
        start_date: "2026-10-01",
        end_date: "2026-10-31",
        created_at: "2026-11-05T15:00:00Z",
        started_at: null,
        finished_at: "2026-11-05T15:05:00Z",
        stage: "finished",
        warnings: [],
        errors: [],
        counts: {},
        result_url: `/explorar?run=${runId}`,
      },
    }),
    "/api/v1/investigation/research": (url) => {
      windows.push(url.searchParams.get("run_id"));
      return {
        body: {
          source: "socrata_secop",
          processes: [process],
          comparisons: [],
          signals: [],
          signal_status: "insufficient_evidence",
          signal_reason: "Sin comparación",
        },
      };
    },
  });
  renderWithProviders(<ResearchPage />, { route: `/explorar?run=${runId}` });
  await userEvent.click(await screen.findByRole("button", { name: "REAL-2026" }));
  expect(screen.getByLabelText("Detalle investigativo")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Ver señales" })).toHaveAttribute(
    "href",
    `/senales?run=${runId}`,
  );
  await userEvent.click(screen.getByRole("button", { name: "Cerrar detalle" }));
  expect(screen.queryByLabelText("Detalle investigativo")).not.toBeInTheDocument();
  expect(windows.every((value) => value === runId)).toBe(true);
});

const process = {
  id: "CO1.REQ.REAL",
  reference: "REAL-2026",
  entity: "Entidad de la muestra",
  department: "Boyacá",
  municipality: "Tunja",
  published_at: "2026-10-21",
  status: "Seleccionado",
  object: "Compra de televisores",
  base_price_cop: "5900000",
  source_url:
    "https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=original",
  facts_count: 2,
  canonicals_count: 1,
  conflicts: 0,
  contracts: [],
  documents: [],
  products: [],
  specification_evidence: [],
  lifecycle_covered: [],
  lifecycle_missing: ["contract"],
  warnings: [],
  errors: [],
};

it("muestra datos reales y conserva precio unitario desconocido en el detalle", async () => {
  mockApi({
    "/api/v1/investigation/research": () => ({
      body: {
        source: "socrata_secop",
        processes: [process],
        signals: [],
        comparisons: [],
        signal_status: "insufficient_evidence",
        signal_reason: "Faltan comparables.",
      },
    }),
  });
  renderWithProviders(<ResearchPage />, { route: "/explorar" });
  const user = userEvent.setup();
  await user.click(await screen.findByRole("button", { name: "REAL-2026" }));
  expect(screen.getByLabelText("Detalle investigativo")).toBeInTheDocument();
  expect(screen.getByText(/No se dividió el valor global/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Abrir proceso oficial/ })).toHaveAttribute(
    "href",
    process.source_url,
  );
});

it("señales reales no usa la demo para rellenar una muestra insuficiente", async () => {
  mockApi({
    "/api/v1/investigation/research": () => ({
      body: {
        source: "socrata_secop",
        processes: [],
        signals: [],
        comparisons: [],
        signal_status: "insufficient_evidence",
        signal_reason: "No hay precios unitarios comparables.",
      },
    }),
  });
  renderWithProviders(<ResearchPage view="signals" />);
  expect(
    await screen.findByText("Evidencia insuficiente para publicar una señal"),
  ).toBeInTheDocument();
  expect(screen.getByText("No hay precios unitarios comparables.")).toBeInTheDocument();
});

it("un fallo del informe real se muestra sin sustituirlo con fixtures", async () => {
  mockApi({ "/api/v1/investigation/research": () => ({ status: 503, body: {} }) });
  renderWithProviders(<ResearchPage />);
  expect(await screen.findByText(/No fue posible cargar el informe real/)).toHaveTextContent(
    "No se sustituyó con datos de demostración",
  );
});

it("distingue el universo descubierto de la muestra documental y admite firma ausente", async () => {
  mockApi({
    "/api/v1/investigation/research": () => ({
      body: {
        source: "socrata_secop",
        processes: [
          {
            ...process,
            contracts: [
              {
                id_contrato: "PCCNTR-1",
                estado_contrato: "En aprobación",
                proveedor_adjudicado: "Proveedor",
                valor_del_contrato: "100",
                fecha_de_firma: null,
              },
            ],
          },
        ],
        signals: [],
        comparisons: [],
        signal_status: "insufficient_evidence",
        signal_reason: "Sin pares confiables",
        summary: {
          processes_found: 6329,
          document_candidates: 18,
          processes_with_documented_tv: 12,
          tv_observations: 31,
          reliable_purchase_unit_prices: 0,
          comparisons_possible: 0,
          documents_failed: 0,
          extraction_failed: 9,
          partial_coverage_documents: 16,
        },
      },
    }),
  });
  renderWithProviders(<ResearchPage />);
  expect(await screen.findByText("6.329 procesos encontrados")).toBeInTheDocument();
  expect(screen.getByText("18 candidatos documentales")).toBeInTheDocument();
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "REAL-2026" }));
  expect(screen.getByText(/Firma: No publicada/)).toBeInTheDocument();
});

it("muestra una señal sustentada recibida del backend sin inventarla cuando no existe", async () => {
  mockApi({
    "/api/v1/investigation/research": () => ({
      body: {
        source: "socrata_secop",
        processes: [],
        comparisons: [],
        signal_status: "signals_supported",
        signal_reason: "Dos compras documentadas",
        signals: [
          {
            id: "signal",
            title: "Diferencia sustentada de prueba",
            entities: ["Entidad A", "Entidad B"],
            processes: ["REQ-A", "REQ-B"],
            difference_pct: "50",
            absolute_difference_cop: "100",
            comparability: "same_model",
          },
        ],
      },
    }),
  });
  renderWithProviders(<ResearchPage view="signals" />);
  expect(await screen.findByText("Diferencia sustentada de prueba")).toBeInTheDocument();
  expect(screen.getByText("Señales documentadas para revisión humana")).toBeInTheDocument();
  expect(
    screen.queryByText("Evidencia insuficiente para publicar una señal"),
  ).not.toBeInTheDocument();
});
