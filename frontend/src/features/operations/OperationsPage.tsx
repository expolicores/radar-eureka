import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router";
import { api, unwrap } from "../../api/client";
import { str } from "../eureka/types";

const timestamp = (value: unknown) =>
  typeof value === "string"
    ? new Date(value).toLocaleString("es-CO", { timeZone: "America/Bogota" })
    : "No disponible";
const schedulerLabels: Record<string, string> = {
  active: "Activo",
  disabled: "Deshabilitado",
  not_registered: "Sin tarea registrada",
  unknown: "No verificable",
};
const metricLabels: Record<string, string> = {
  secop_records_fetched: "SECOP recibidos",
  outside_window: "Fuera de ventana",
  outside_region: "Fuera de región",
  already_seen: "Ya vistos",
  limit_deferred: "Diferidos por límite operativo",
  prefilter_rejected: "Descartados por prefilter",
  candidates: "Candidatos",
  documents_processed: "Documentos inventariados",
  documents_available: "Documentos con binario disponible",
  document_download_failed: "Descargas documentales fallidas",
  document_sync_started: "Sincronizaciones documentales",
  document_sync_failed: "Sincronizaciones fallidas",
  document_errors: "Procesos con error documental",
  extraction_native: "Extracción nativa",
  extraction_reused: "Extracciones reutilizadas",
  extraction_ocr: "Páginas OCR procesadas",
  ocr_required: "Páginas OCR requeridas",
  ocr_unavailable: "OCR no disponible",
  extraction_failed: "Extracciones fallidas",
  consolidated: "Consolidados",
  canonical_reused: "Canónicos reutilizados",
  enriched: "Enriquecidos",
  alert_created: "Alertas nuevas",
  no_alert: "Sin alerta",
  metadata_alerts_excluded_by_object: "Alertas provisionales excluidas por objeto",
  metadata_exclusion_policy_errors: "Alertas provisionales bloqueadas por política inválida",
  notification_prepared: "Notificaciones preparadas",
  notification_sent: "Aceptadas por proveedor",
  notification_captured: "Capturas locales",
  notification_failed: "Notificaciones fallidas",
};

function displayedStatus(cycle: Record<string, unknown>) {
  const errors = cycle.errors as Array<Record<string, unknown>> | undefined;
  return cycle.radar_status === "limited" &&
    ["completed_with_warnings", "failed"].includes(str(cycle.status)) &&
    !errors?.some((error) =>
      ["cycle_stage_failed", "radar_global_failure"].includes(str(error.code)),
    )
    ? "limited"
    : str(cycle.status);
}

function Cycle({ cycle }: { cycle: Record<string, unknown> }) {
  const status = displayedStatus(cycle);
  const metrics = cycle.metrics as Record<string, number> | undefined;
  const source = cycle.source_summary as Record<string, unknown> | undefined;
  const notifications = cycle.notification_summary as Record<string, unknown> | undefined;
  const errors = cycle.errors as Array<Record<string, unknown>> | undefined;
  const labels: Record<string, string> = {
    running: "Corrida en ejecución",
    completed: "Corrida completada",
    completed_with_warnings: "Corrida completada con advertencias",
    limited: "Corrida limitada",
    failed: "Falló la corrida",
    skipped: "Corrida omitida",
  };
  return (
    <article className="card">
      <h2>{labels[status] ?? status}</h2>
      <h2>Ciclo {String(cycle.id)}</h2>
      <p>
        Estado: {status} · Inicio: {timestamp(cycle.started_at)} · Duración:{" "}
        {str(cycle.duration_ms ?? "En curso")} ms
      </p>
      <p>Etapa: {str(cycle.stage ?? "No informada")}</p>
      {status === "limited" && (
        <p role="status">
          Radar alcanzó el límite operativo. La cobertura está incompleta; no equivale a un fallo
          técnico. Los procesos diferidos quedan pendientes para otra corrida.
        </p>
      )}
      <p>
        Procesos SECOP recibidos: {metrics?.secop_records_fetched ?? 0} · Candidatos:{" "}
        {metrics?.candidates ?? 0} · Enriquecidos: {metrics?.enriched ?? 0} · Alertas nuevas:{" "}
        {metrics?.alert_created ?? 0} · Errores: {str(cycle.failures ?? 0)}
      </p>
      {source?.zero_records_confirmed === true && (
        <p>
          SECOP devolvió 0 registros para la ventana y regiones consultadas, antes de los filtros
          locales.
        </p>
      )}
      {(metrics?.secop_records_fetched ?? 0) > 0 && (
        <p>
          SECOP sí devolvió registros. El embudo y las razones muestran cuáles avanzaron o se
          descartaron.
        </p>
      )}
      {source?.zero_records_confirmed !== true && (metrics?.secop_records_fetched ?? 0) === 0 && (
        <p>
          Sin registros recibidos hasta ahora. Si la consulta falló o sigue en curso, esto no
          confirma una respuesta vacía de SECOP.
        </p>
      )}
      <p>
        Los filtros aplicados en Socrata no permiten contar los registros excluidos antes de
        responder.
      </p>
      {notifications?.disabled === true && (
        <p>Notificaciones deshabilitadas: estado esperado, sin envío.</p>
      )}
      {(metrics?.alert_created ?? 0) > 0 && <Link to="/eureka/alerts">Ver alertas</Link>}
      {cycle.coordinator_active === false && cycle.status === "running" && (
        <p role="alert">
          El coordinador ya no conserva el lock. Una nueva corrida manual puede recuperar este ciclo
          interrumpido.
        </p>
      )}
      {!!errors?.length && (
        <div role="alert">
          <h3>Errores / advertencias del ciclo</h3>
          {errors.map((error, index) => (
            <p key={index}>
              Etapa: {str(error.stage ?? cycle.stage ?? "No informada")} · {str(error.code)} ·{" "}
              {str(error.type ?? "")}
            </p>
          ))}
        </div>
      )}
      {!!cycle.log_files && (
        <p>
          Logs del ciclo: {str((cycle.log_files as Record<string, unknown>).log)} ·{" "}
          {str((cycle.log_files as Record<string, unknown>).summary)}
        </p>
      )}
      {!!cycle.radar_run_id && !!cycle.radar_linked && (
        <a href={`/api/eureka/radar-runs/${str(cycle.radar_run_id)}`}>
          Ver detalle de corrida Radar (JSON)
        </a>
      )}
      <h3>Embudo</h3>
      <table>
        <thead>
          <tr>
            <th>Etapa</th>
            <th>Cantidad</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(metricLabels).map(([key, label]) => (
            <tr key={key}>
              <td>{label}</td>
              <td>{metrics?.[key] ?? 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <details>
        <summary>Razones, notificaciones, tiempos y errores</summary>
        <pre>
          {JSON.stringify(
            {
              reasons: cycle.reasons,
              notifications: cycle.notification_summary,
              durations_ms: cycle.durations_ms,
              errors: cycle.errors,
            },
            null,
            2,
          )}
        </pre>
      </details>
    </article>
  );
}

export function OperationsPage() {
  const client = useQueryClient();
  const [confirming, setConfirming] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [launchMessage, setLaunchMessage] = useState<string | null>(null);
  const query = useQuery({
    queryKey: ["operations-status"],
    queryFn: async () => unwrap(await api.GET("/api/operations/status")),
    refetchInterval: 60_000,
  });
  const history = useQuery({
    queryKey: ["operations-cycles"],
    enabled: query.data?.schema_ready === true,
    queryFn: async () =>
      unwrap(await api.GET("/api/operations/cycles", { params: { query: { limit: 5 } } })),
  });
  const data = query.data;
  const detectedId = typeof data?.active_cycle?.id === "string" ? data.active_cycle.id : null;
  const cycleId = selectedId ?? detectedId;
  const current = useQuery({
    queryKey: ["operation-cycle", cycleId],
    enabled: !!cycleId,
    queryFn: async () =>
      unwrap(
        await api.GET("/api/operations/cycles/{identifier}", {
          params: { path: { identifier: cycleId! } },
        }),
      ),
    refetchInterval: (q) =>
      q.state.data?.status === "running" && q.state.data?.coordinator_active !== false
        ? 4000
        : false,
  });
  const launch = useMutation({
    mutationFn: async () => {
      const response = await api.POST("/api/operations/cycles/manual", { body: {} });
      if (response.response.status === 409) {
        const conflict = response.error as { cycle_id?: string; active_cycle_id?: string };
        return { cycle_id: conflict.active_cycle_id ?? conflict.cycle_id ?? null, busy: true };
      }
      return { cycle_id: unwrap(response).cycle_id, busy: false };
    },
    onSuccess: (result) => {
      setConfirming(false);
      setSelectedId(result.cycle_id);
      setLaunchMessage(result.busy ? "Ya hay una corrida en ejecución." : null);
      void client.invalidateQueries({ queryKey: ["operations-status"] });
      void client.invalidateQueries({ queryKey: ["operations-cycles"] });
    },
  });
  const running =
    launch.isPending ||
    (!!cycleId && current.isPending) ||
    (current.data?.status === "running" && current.data?.coordinator_active !== false) ||
    (!!detectedId && detectedId !== cycleId);
  const terminal = current.data && current.data.status !== "running";
  useEffect(() => {
    if (terminal) {
      void client.invalidateQueries({ queryKey: ["operations-status"] });
      void client.invalidateQueries({ queryKey: ["operations-cycles"] });
    }
  }, [terminal, client]);
  const shownHistory = history.data?.filter((c) => c.id !== cycleId);
  return (
    <section>
      <h1>Eureka · operación local</h1>
      <p>
        <Link to="/eureka/alerts">Radar y alertas</Link> ·{" "}
        <Link to="/eureka/notifications">Notificaciones</Link>
      </p>
      {data?.execution_config && (
        <article className="card" aria-label="Configuración de la próxima corrida">
          <h2>Ventana de la próxima corrida manual</h2>
          <p>
            Ventana calendario desde anteayer en Bogotá. Incluye el día actual hasta lo disponible
            en Socrata al momento de ejecutar.
          </p>
          <p>
            Desde:{" "}
            {data.execution_config.start_date?.split("-").reverse().join("/") ??
              "Sin fecha configurada"}
            {" · 00:00"}
          </p>
          <p>
            Hasta: {data.execution_config.before_date.split("-").reverse().join("/")} · 00:00 —
            límite superior exclusivo ({data.execution_config.timezone})
          </p>
          <p>Regiones: {data.execution_config.regions.join(" · ")}</p>
          <p>Límite operativo: {data.execution_config.max_processes} procesos</p>
        </article>
      )}
      <button
        className="btn primary"
        disabled={running || !data?.schema_ready || !data.db_connected}
        onClick={() => {
          setConfirming(true);
          launch.reset();
          setLaunchMessage(null);
        }}
      >
        Ejecutar corrida manual
      </button>
      {confirming && (
        <div className="card" role="dialog" aria-modal="true" aria-label="Confirmar corrida manual">
          <p>
            Se consultará SECOP y se ejecutará el pipeline completo de Eureka. ¿Deseas continuar?
          </p>
          <button disabled={launch.isPending} onClick={() => setConfirming(false)}>
            Cancelar
          </button>
          <button disabled={running} onClick={() => launch.mutate()}>
            Ejecutar
          </button>
        </div>
      )}
      {launch.isError && (
        <div role="alert">
          No se pudo confirmar el inicio de la corrida. Etapa: preflight / persistencia. Revisa la
          configuración y la conexión a DB; consulta o actualiza el estado operacional antes de
          reintentar. No se confirmó que Radar haya iniciado.
        </div>
      )}
      {launchMessage && !terminal && <p role="status">{launchMessage}</p>}
      {running && (
        <p role="status">Corrida en ejecución · {cycleId ?? "Confirmando inicio persistido…"}</p>
      )}
      {current.isError && (
        <p role="alert">
          No se pudo consultar el ciclo {cycleId}.{" "}
          <button onClick={() => void current.refetch()}>Reintentar consulta</button>
        </p>
      )}
      {current.data && <Cycle cycle={current.data} />}
      {terminal && (
        <button
          onClick={() => {
            void history.refetch();
            void query.refetch();
          }}
        >
          Actualizar historial
        </button>
      )}
      <button
        onClick={() => {
          void query.refetch();
          void history.refetch();
        }}
      >
        Actualizar estado
      </button>
      {query.isPending && <p role="status">Consultando operación…</p>}
      {query.isError && <p role="alert">No fue posible consultar el estado operacional.</p>}
      {data && (
        <>
          <article className="card">
            <h2>Estado operacional</h2>
            <p>Base de datos: {data.db_connected ? "Disponible" : "No disponible"}</p>
            {!data.schema_ready && (
              <p role="alert">
                Migración 0016 pendiente o esquema no disponible. No hay historial operacional
                consultable.
              </p>
            )}
            <p>
              Automatización configurada: {data.automation_enabled ? "Habilitada" : "Deshabilitada"}
            </p>
            <p>
              Scheduler real: {schedulerLabels[String(data.scheduler.status)] ?? "No verificable"}
            </p>
            <p>Próxima real del scheduler: {timestamp(data.scheduler.next_run)}</p>
            <p>Próxima teórica según configuración: {timestamp(data.next_theoretical)}</p>
            <p>La hora teórica no confirma que exista una tarea registrada.</p>
            <p>
              Último ciclo: {timestamp(data.latest?.started_at)} · Último satisfactorio:{" "}
              {timestamp(data.latest_success?.finished_at)}
            </p>
            <p>
              Notificaciones: {data.notification_enabled ? "Habilitadas" : "Deshabilitadas"} · modo{" "}
              {data.notification_mode}
            </p>
            <p>
              OCR: {data.ocr.available ? "Disponible" : "No disponible"} ·{" "}
              {str(data.ocr.engine_version ?? "Sin versión")} ·{" "}
              {str(data.ocr.language ?? "Sin idioma")}
            </p>
          </article>
          {history.isError && <p role="alert">No fue posible cargar el historial de ciclos.</p>}
          {history.data?.length === 0 && !cycleId && <p>No hay ciclos registrados.</p>}
          {shownHistory?.map((c, index) =>
            index === 0 ? (
              <Cycle key={String(c.id)} cycle={c} />
            ) : (
              <details key={String(c.id)}>
                <summary>
                  {timestamp(c.started_at)} · {displayedStatus(c)}
                </summary>
                <Cycle cycle={c} />
              </details>
            ),
          )}
        </>
      )}
    </section>
  );
}
