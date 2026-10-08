import { useMemo } from "react";
import { useSearchParams } from "react-router";

import { Pagination } from "../../components/Pagination";
import { formatBogotaDateTime, formatInteger } from "../../lib/format";
import { SOURCE_LABELS } from "../../lib/labels";
import { usePurchaseFilters } from "../explore/usePurchases";
import { SignalsKpis } from "./SignalsKpis";
import { SignalsTable } from "./SignalsTable";
import { useSignalSummary, useSignals } from "./useSignals";

const PAGE_SIZE = 25;
const FILTER_KEYS = ["q", "department", "year", "source", "confidence", "sort"] as const;
const YEARS = ["2026", "2025", "2024", "2023"];

type SignalFilterKey = (typeof FILTER_KEYS)[number];

export function SignalsPage() {
  const [params, setParams] = useSearchParams();
  const filters = useMemo(
    () => Object.fromEntries(FILTER_KEYS.map((key) => [key, params.get(key) ?? ""])),
    [params],
  ) as Record<SignalFilterKey, string>;
  const page = Math.max(1, Number(params.get("page") ?? "1") || 1);

  const query: Record<string, string | number> = { page, page_size: PAGE_SIZE };
  for (const key of FILTER_KEYS) {
    if (filters[key]) {
      query[key] = filters[key];
    }
  }
  const signals = useSignals(query);
  const summary = useSignalSummary();
  const options = usePurchaseFilters();

  const update = (key: SignalFilterKey | "page", value: string) =>
    setParams((current) => {
      const next = new URLSearchParams(current);
      if (value) {
        next.set(key, value);
      } else {
        next.delete(key);
      }
      if (key !== "page") {
        next.delete("page");
      }
      return next;
    });

  const cutoff = summary.data?.data_cutoff_at;
  return (
    <section>
      <h1>Señales que merecen revisión</h1>
      <p className="sub">
        Compras de televisores cuyo precio unitario se desvía de compras públicas comparables o de
        referencias de mercado.
        {cutoff ? (
          <>
            {" "}
            Datos actualizados al <b>{formatBogotaDateTime(cutoff)}</b>
          </>
        ) : null}{" "}
        · SECOP II y Tienda Virtual del Estado (TVEC).
      </p>

      <div className="notice" role="note" style={{ marginBottom: 16 }}>
        <span aria-hidden="true">ⓘ</span>
        <div>
          <b>Una señal no es una conclusión.</b> Indica que una compra merece revisión humana. No
          implica irregularidad ni responsabilidad de ninguna persona o entidad. Revisa siempre la
          evidencia de origen antes de sacar conclusiones.
        </div>
      </div>

      <SignalsKpis summary={summary.data} />

      <div className="filters" role="search">
        <input
          className="search"
          type="search"
          aria-label="Buscar señales"
          placeholder="Buscar por entidad, proveedor (nombre o NIT), ítem o código…"
          defaultValue={filters.q}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              update("q", event.currentTarget.value.trim());
            }
          }}
          onBlur={(event) => update("q", event.currentTarget.value.trim())}
        />
        <select
          aria-label="Departamento"
          value={filters.department}
          onChange={(event) => update("department", event.target.value)}
        >
          <option value="">Departamento: Todos</option>
          {(options.data?.departments ?? []).map((department) => (
            <option key={department} value={department}>
              {department}
            </option>
          ))}
        </select>
        <select
          aria-label="Año"
          value={filters.year}
          onChange={(event) => update("year", event.target.value)}
        >
          <option value="">Fecha: todos los años</option>
          {YEARS.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
        <select
          aria-label="Fuente"
          value={filters.source}
          onChange={(event) => update("source", event.target.value)}
        >
          <option value="">Fuente: Todas</option>
          {Object.entries(SOURCE_LABELS).map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
        <select
          aria-label="Confianza"
          value={filters.confidence}
          onChange={(event) => update("confidence", event.target.value)}
        >
          <option value="">Confianza: Todas</option>
          <option value="high">Alta</option>
          <option value="medium">Media</option>
          <option value="low">Baja</option>
        </select>
        <select
          aria-label="Orden"
          value={filters.sort}
          onChange={(event) => update("sort", event.target.value)}
        >
          <option value="">Ordenar: prioridad (confianza → desviación)</option>
          <option value="deviation">Desviación</option>
          <option value="value">Valor unitario</option>
          <option value="date">Fecha</option>
        </select>
        <span className="spacer" />
        {signals.data ? (
          <span className="chip">{formatInteger(signals.data.total)} resultados</span>
        ) : null}
      </div>

      <div className="table-wrap" aria-busy={signals.isFetching}>
        {signals.isPending ? (
          <p className="table-state" role="status">
            Cargando señales…
          </p>
        ) : signals.isError ? (
          <div className="table-state" role="alert">
            <p>No fue posible cargar las señales. Intenta de nuevo.</p>
            <button type="button" className="btn" onClick={() => void signals.refetch()}>
              Reintentar
            </button>
          </div>
        ) : signals.data.items.length === 0 ? (
          <p className="table-state" role="status">
            No hay señales que coincidan con los filtros.
          </p>
        ) : (
          <SignalsTable signals={signals.data.items} />
        )}
      </div>

      {signals.data && signals.data.total > 0 ? (
        <Pagination
          page={signals.data.page}
          pageSize={signals.data.page_size}
          total={signals.data.total}
          itemLabel="señales"
          onPageChange={(next) => update("page", String(next))}
        />
      ) : null}
      <p className="small muted" style={{ marginTop: 8 }}>
        Solo las desviaciones por encima de la referencia generan señal; los precios anormalmente
        bajos van a revisión de calidad.
      </p>
    </section>
  );
}
