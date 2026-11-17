import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { formatBogotaEventDateTime, formatDate } from "../../lib/format";
import "./ResearchRuns.css";

type Run = {
  run_id: string;
  run_type?: string;
  status: string;
  start_date: string;
  end_date: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  stage: string;
  warnings: string[];
  errors: string[];
  counts: Record<string, number>;
  result_url: string | null;
};
const terminal = new Set(["completed", "completed_with_warnings", "failed"]);
const labels: Record<string, string> = {
  queued: "Pendiente",
  running: "En ejecución",
  completed: "Completada",
  completed_with_warnings: "Completada con advertencias",
  failed: "Fallida",
};
const stages: Record<string, string> = {
  queued: "En espera",
  discovery: "Descubrimiento e inventarios",
  documents_extraction: "Documentos y extracción",
  research_report: "Informe de investigación",
  economic_cycle: "Reconstrucción económica",
  product_identification: "Identificación y elegibilidad de productos",
  private_market_discovery: "Búsqueda y verificación de mercado privado",
  benchmark: "Benchmark privado",
  comparison: "Comparación pública vs privada",
  finished: "Finalizada",
  interrupted: "Interrumpida",
};
const counts: Record<string, string> = {
  processes_discovered: "Procesos descubiertos",
  processes_selected: "Procesos seleccionados",
  products_identified: "Productos identificados",
  private_market_candidates: "Productos elegibles para mercado privado",
  private_market_products_processed: "Productos con benchmark procesado",
  private_market_products_failed: "Productos con consulta privada fallida",
  private_market_observations_valid: "Observaciones privadas válidas",
  benchmarks_sufficient: "Benchmarks suficientes",
  benchmarks_insufficient: "Benchmarks insuficientes",
  comparisons_generated: "Comparaciones generadas",
  processes_found: "Procesos encontrados",
  document_candidates: "Documentos candidatos",
  documents_downloaded: "Documentos descargados",
  processes_with_documented_tv: "Procesos con TV documentado",
  tv_observations: "Observaciones TV",
  reliable_purchase_unit_prices: "Precios de compra sustentados",
  comparisons_possible: "Comparaciones posibles",
  signals_generated: "Señales generadas",
  documents_failed: "Documentos fallidos",
  extraction_failed: "Extracciones fallidas",
  partial_coverage_documents: "Documentos con cobertura parcial",
};
const reasons: Record<string, string> = {
  no_eligible_private_market_products:
    "La evidencia pública de esta ventana no permitió identificar productos elegibles. No se consultó mercado privado.",
  private_provider_limitations:
    "Una fuente privada tuvo limitaciones; se conservó la evidencia disponible.",
  insufficient_market_evidence:
    "No se alcanzó evidencia privada suficiente para todos los productos.",
  private_market_product_failed:
    "Falló la consulta privada de un producto. Su evidencia pública permanece disponible.",
  backend_restarted:
    "El backend se reinició o apagó durante la corrida. No se reintentó automáticamente.",
  pipeline_failed:
    "El pipeline no pudo finalizar. Se conservaron sus artefactos locales y el último resultado publicado.",
  process_warnings_or_errors:
    "Hay procesos con advertencias o errores parciales; revise sus evidencias.",
  inventory_errors:
    "Algunos inventarios documentales no estuvieron disponibles; el resultado conserva esa cobertura parcial.",
  worker_start_failed: "La corrida quedó registrada, pero el worker no pudo iniciarse.",
};

async function read<T>(path: string, signal?: AbortSignal): Promise<T> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal?.aborted) abort();
  signal?.addEventListener("abort", abort, { once: true });
  const timeout = setTimeout(abort, 20000);
  try {
    const response = await fetch(
      new Request(new URL(path, location.origin), { signal: controller.signal }),
    );
    if (!response.ok) throw new Error(response.status === 404 ? "not_found" : "unavailable");
    return (await response.json()) as T;
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener("abort", abort);
  }
}

export function ResearchRuns({ privateMarket = false }: { privateMarket?: boolean }) {
  const base = privateMarket ? "/api/v1/investigation/market-runs" : "/api/v1/investigation/runs";
  const title = privateMarket
    ? "Nueva corrida Estado vs mercado privado"
    : "Nueva corrida Estado vs Estado";
  const [params, setParams] = useSearchParams();
  const id = privateMarket
    ? (params.get("market_job") ?? params.get("private_run"))
    : (params.get("research_run") ?? params.get("run"));
  const [open, setOpen] = useState(false);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [validation, setValidation] = useState("");
  const [recovery, setRecovery] = useState("");
  const postGuard = useRef(false);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const policy = useQuery<{ max_window_days: number }>({
    queryKey: ["investigation", "run-policy"],
    retry: false,
    queryFn: ({ signal }) => read("/api/v1/investigation/runs/policy", signal),
  });
  const run = useQuery<Run>({
    queryKey: ["investigation", privateMarket ? "market-run" : "run", id],
    enabled: !!id,
    retry: false,
    refetchOnWindowFocus: false,
    queryFn: ({ signal }) => read(`${base}/${encodeURIComponent(id!)}`, signal),
    refetchInterval: (q) =>
      !q.state.error && q.state.data && !terminal.has(q.state.data.status) ? 5000 : false,
  });
  function track(value: Run) {
    const next = new URLSearchParams(params);
    next.set(privateMarket ? "market_job" : "research_run", value.run_id);
    setParams(next);
    setOpen(false);
    setRecovery("");
  }
  const create = useMutation({
    retry: false,
    mutationFn: async () => {
      controller.current = new AbortController();
      const timeout = setTimeout(() => controller.current?.abort(), 20000);
      try {
        const response = await fetch(
          new Request(new URL(base, location.origin), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ start_date: start, end_date: end }),
            signal: controller.current.signal,
          }),
        );
        if (!response.ok)
          throw new Error(
            response.status === 409
              ? "busy"
              : response.status === 422
                ? "dates"
                : "creation_failed",
          );
        return (await response.json()) as Run;
      } finally {
        clearTimeout(timeout);
        postGuard.current = false;
      }
    },
    onSuccess: track,
  });
  async function recover() {
    try {
      const active = await read<Run | null>(`${base}/active`);
      if (active) track(active);
      else setRecovery("No hay una corrida activa registrada. No se ejecutó otro POST.");
    } catch {
      setRecovery(
        "No fue posible consultar la corrida activa. Reintente cuando el backend esté disponible.",
      );
    }
  }
  const active = run.data && !terminal.has(run.data.status);
  return (
    <section
      className="card"
      aria-label={privateMarket ? "Corridas de mercado privado" : "Corridas investigativas"}
      style={{ marginBlock: 18 }}
    >
      <div className="row">
        <div>
          <h2>{privateMarket ? "Comparar con mercado privado" : "Comparar compras públicas"}</h2>
          <p className="small muted">
            {privateMarket
              ? "Desde fechas: descubre procesos, reconstruye productos documentados y consulta precios privados solo para los elegibles. No requiere corridas previas."
              : "Flujo actual de televisores. Fechas inclusivas en Bogotá; no modifica filtros ni reglas de evidencia."}
          </p>
        </div>
        <span className="spacer" />
        <button
          className="btn primary"
          disabled={!!active || create.isPending}
          onClick={() => {
            setOpen(true);
            create.reset();
            setValidation("");
          }}
        >
          {title}
        </button>
      </div>
      {open && (
        <form
          aria-label={
            privateMarket ? "Nueva corrida privada por fechas" : "Nueva corrida investigativa"
          }
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            if (postGuard.current) return;
            if (!start || !end) {
              setValidation("Indica fecha inicial y fecha final.");
              return;
            }
            if (start > end) {
              setValidation("La fecha inicial debe ser anterior o igual a la fecha final.");
              return;
            }
            setValidation("");
            postGuard.current = true;
            create.mutate();
          }}
        >
          <div className="research-run-dates">
            <label>
              Fecha inicial
              <input
                type="date"
                required
                value={start}
                disabled={create.isPending}
                onChange={(e) => setStart(e.target.value)}
              />
            </label>
            <label>
              Fecha final
              <input
                type="date"
                required
                value={end}
                disabled={create.isPending}
                onChange={(e) => setEnd(e.target.value)}
              />
            </label>
          </div>
          {policy.data && (
            <p className="small muted">
              Límite del pipeline actual: {policy.data.max_window_days} días inclusivos. La
              validación definitiva se realiza en backend.
            </p>
          )}
          {policy.isError && (
            <p role="status">
              No se pudo leer la política del backend.{" "}
              <button type="button" className="btn" onClick={() => void policy.refetch()}>
                Reintentar política
              </button>
            </p>
          )}
          {validation && <p role="alert">{validation}</p>}
          <div className="row">
            <button
              type="button"
              className="btn"
              disabled={create.isPending}
              onClick={() => setOpen(false)}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn primary"
              disabled={create.isPending || !policy.data}
            >
              {create.isPending ? "Registrando corrida…" : "Iniciar corrida"}
            </button>
          </div>
        </form>
      )}
      {create.isError && (
        <div role="alert">
          <p>
            {create.error.message === "busy"
              ? "Ya existe una corrida activa o el backend está reiniciándose."
              : create.error.message === "dates"
                ? `Verifica las fechas: inicio no posterior al fin y máximo ${policy.data?.max_window_days ?? "según política"} días inclusivos.`
                : "No se pudo confirmar la creación de la corrida. Puede haberse registrado antes del error o timeout; consulte el estado antes de volver a iniciarla."}
          </p>
          <button className="btn" onClick={() => void recover()}>
            Consultar corrida activa
          </button>
        </div>
      )}
      {recovery && <p role="status">{recovery}</p>}
      {id && run.isPending && <p role="status">Consultando estado de la corrida…</p>}
      {id && run.isError && (
        <p role="alert">
          {run.error.message === "not_found"
            ? "Corrida no encontrada en este backend."
            : "No fue posible consultar el estado. La ejecución puede continuar en backend."}{" "}
          <button className="btn" onClick={() => void run.refetch()}>
            Reintentar estado
          </button>
        </p>
      )}
      {run.data && (
        <div aria-label={privateMarket ? "Estado de corrida privada" : "Estado de corrida"}>
          <p>
            <strong>{labels[run.data.status] ?? "Estado no registrado"}</strong> ·{" "}
            {formatDate(run.data.start_date)} → {formatDate(run.data.end_date)} (ambas fechas
            incluidas)
          </p>
          <p className="small">
            Corrida: {run.data.run_id} · {stages[run.data.stage] ?? "Procesando"}
          </p>
          <p className="small">
            Creada: {formatBogotaEventDateTime(run.data.created_at)} · Bogotá
            {run.data.finished_at && <> · Fin: {formatBogotaEventDateTime(run.data.finished_at)}</>}
          </p>
          {active && (
            <p className="small muted">
              Se actualiza cada 5 segundos. Los resultados visibles abajo pertenecen al informe
              consultado anteriormente hasta abrir el resultado nuevo.
            </p>
          )}
          {!!Object.keys(run.data.counts).length && (
            <dl className="research-run-counts">
              {Object.entries(run.data.counts)
                .filter(([k]) => counts[k])
                .map(([key, value]) => (
                  <div key={key}>
                    <dt>{counts[key]}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
            </dl>
          )}
          {[...run.data.warnings, ...run.data.errors].map((reason, i) => (
            <p className="small notice" key={`${reason}-${i}`}>
              {reasons[reason] ??
                counts[reason] ??
                "Advertencia de ejecución registrada; revise el resultado."}
            </p>
          ))}
          {run.data.result_url && (
            <Link
              className="btn"
              to={
                privateMarket
                  ? `/explorar?private_run=${encodeURIComponent(run.data.run_id)}&market_run=${encodeURIComponent(run.data.run_id)}`
                  : `/explorar?run=${encodeURIComponent(run.data.run_id)}`
              }
            >
              Ver resultados de esta corrida
            </Link>
          )}
        </div>
      )}
    </section>
  );
}
