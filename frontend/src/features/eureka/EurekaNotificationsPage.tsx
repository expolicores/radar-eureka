import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { api, unwrap } from "../../api/client";
import { Pagination } from "../../components/Pagination";
import { str } from "./types";
import type { components, paths } from "../../api/schema";

type Notification = components["schemas"]["NotificationSummary"];
type Filters = NonNullable<paths["/api/eureka/notifications"]["get"]["parameters"]["query"]>;
const notificationLabels: Record<Notification["status"], string> = {
  pending: "Pendiente",
  processing: "En proceso",
  captured: "Capturado localmente",
  sent: "Aceptado por proveedor",
  retryable: "Reintentable",
  failed: "Fallida · revisar",
  skipped: "Omitida",
};
const timestamp = (value: string | null) =>
  value ? new Date(value).toLocaleString("es-CO", { timeZone: "America/Bogota" }) : "—";

function NotificationContent({ id }: { id: string }) {
  const [open, setOpen] = useState(false);
  const query = useQuery({
    queryKey: ["notification-detail", id],
    enabled: open,
    queryFn: async () =>
      unwrap(
        await api.GET("/api/eureka/notifications/{notification_id}", {
          params: { path: { notification_id: id } },
        }),
      ),
  });
  return (
    <details onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary>Ver mensaje e intentos</summary>
      {open && (
        <>
          {query.isPending && <p role="status">Cargando notificación…</p>}
          {query.isError && (
            <p role="alert">
              No fue posible cargar el detalle.{" "}
              <button onClick={() => void query.refetch()}>Actualizar</button>
            </p>
          )}
          {query.data && (
            <>
              <h3>{str(query.data.payload_snapshot.subject)}</h3>
              <pre>{str(query.data.payload_snapshot.text)}</pre>
              <h3>Historial de intentos</h3>
              {!query.data.attempt_history.length && <p>Sin intentos registrados.</p>}
              {query.data.attempt_history.map((attempt, index) => (
                <div className="eureka-item" key={index}>
                  <p>
                    Intento {str(attempt.attempt_number)} · {str(attempt.provider)} ·{" "}
                    {str(attempt.result)}
                  </p>
                  <p>
                    {str(attempt.timestamp)} · Duración:{" "}
                    {attempt.duration_ms == null
                      ? "No disponible"
                      : `${str(attempt.duration_ms)} ms`}
                  </p>
                  {!!attempt.error_code && (
                    <p>
                      {str(attempt.error_code)} · {str(attempt.error_message)}
                    </p>
                  )}
                  {!!attempt.provider_message_id && (
                    <p>Referencia: {str(attempt.provider_message_id)}</p>
                  )}
                </div>
              ))}
            </>
          )}
        </>
      )}
    </details>
  );
}

export function EurekaNotificationsPage() {
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number(params.get("page")) || 1);
  const filters: Filters = { page, page_size: 25 };
  for (const [key, value] of params) {
    if (key === "created_from" || key === "created_before")
      Object.assign(filters, { [key]: `${value}T00:00:00-05:00` });
    else if (key !== "page") Object.assign(filters, { [key]: value });
  }
  const query = useQuery({
    queryKey: ["eureka-notifications", filters],
    queryFn: async () =>
      unwrap(await api.GET("/api/eureka/notifications", { params: { query: filters } })),
  });
  const submit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const next = new URLSearchParams();
    for (const [key, value] of new FormData(e.currentTarget))
      if (typeof value === "string" && value.trim()) next.set(key, value.trim());
    setParams(next);
  };
  return (
    <section className="eureka-detail">
      <Link to="/eureka/alerts">← Volver a alertas</Link>
      <h1>Eureka · notificaciones</h1>
      <p className="sub">
        Capturas locales y envíos del dispatcher manual. “Aceptado por proveedor” no confirma
        entrega en bandeja, apertura ni lectura.
      </p>
      <form key={params.toString()} onSubmit={submit} className="filters eureka-filters">
        <label>
          Estado
          <select name="status" defaultValue={params.get("status") ?? ""}>
            <option value="">Todos</option>
            {Object.entries(notificationLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Scope
          <select name="delivery_scope" defaultValue={params.get("delivery_scope") ?? ""}>
            <option value="">Todos</option>
            <option value="capture">Captura local</option>
            <option value="real">Correo real</option>
          </select>
        </label>
        <label>
          Destinatario
          <input name="recipient" defaultValue={params.get("recipient") ?? ""} type="email" />
        </label>
        <label>
          Canal
          <select name="channel" defaultValue={params.get("channel") ?? ""}>
            <option value="">Todos</option>
            <option value="email">Email</option>
          </select>
        </label>
        <label>
          Alerta
          <input name="alert_id" defaultValue={params.get("alert_id") ?? ""} />
        </label>
        <label>
          Desde (Colombia)
          <input name="created_from" type="date" defaultValue={params.get("created_from") ?? ""} />
        </label>
        <label>
          Hasta (exclusiva)
          <input
            name="created_before"
            type="date"
            defaultValue={params.get("created_before") ?? ""}
          />
        </label>
        <button className="btn" type="submit">
          Filtrar
        </button>
        <button className="btn" type="button" onClick={() => setParams({})}>
          Limpiar
        </button>
      </form>
      {query.isPending ? (
        <p role="status">Cargando notificaciones…</p>
      ) : query.isError ? (
        <div role="alert">
          <p>{query.error.message}</p>
          <button className="btn" onClick={() => void query.refetch()}>
            Actualizar listado
          </button>
        </div>
      ) : (
        <>
          <p>{query.data.total} notificaciones</p>
          {!query.data.items.length && <p>No hay notificaciones para esta consulta.</p>}
          {query.data.items.map((value) => (
            <article className="card" key={value.id}>
              <h2>
                {notificationLabels[value.status]} ·{" "}
                {value.notification_type === "digest" ? "Digest" : "Alerta individual"}
              </h2>
              <p>
                {timestamp(value.created_at)} · {value.recipient}
              </p>
              <p>
                {value.channel} ·{" "}
                {value.delivery_scope === "capture"
                  ? "Captura local · sin correo externo"
                  : "Correo real"}{" "}
                · {value.provider}
              </p>
              <p>
                Intentos: {value.attempt_count} · Reintentos: {value.retry_count}
              </p>
              {value.sent_at && <p>Aceptación: {timestamp(value.sent_at)}</p>}
              {value.captured_at && <p>Captura: {timestamp(value.captured_at)}</p>}
              {value.processing_started_at && (
                <p>En proceso desde {timestamp(value.processing_started_at)}.</p>
              )}
              {value.next_retry_at && (
                <p>
                  Reintento disponible desde {timestamp(value.next_retry_at)}, al invocar el
                  dispatcher.
                </p>
              )}
              {value.error_code && (
                <p role="note">
                  {value.error_code} · {value.error_message}
                </p>
              )}
              <div className="row">
                {value.alert_ids.map((id, index) => (
                  <Link key={id} to={`/eureka/alerts/${id}`}>
                    Ver alerta {value.alert_ids.length > 1 ? index + 1 : ""}
                  </Link>
                ))}
              </div>
              <NotificationContent id={value.id} />
            </article>
          ))}
          <Pagination
            page={page}
            pageSize={25}
            total={query.data.total}
            itemLabel="notificaciones"
            onPageChange={(value) =>
              setParams((current) => {
                const next = new URLSearchParams(current);
                next.set("page", String(value));
                return next;
              })
            }
          />
        </>
      )}
    </section>
  );
}
