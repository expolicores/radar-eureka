import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router";

import type { PurchaseQuery } from "../../api/client";
import { Pagination } from "../../components/Pagination";
import { formatBogotaDateTime, formatInteger } from "../../lib/format";
import { ExploreFilters, type ExploreFilterValues } from "./ExploreFilters";
import { PurchasesTable } from "./PurchasesTable";
import { usePurchaseFilters, usePurchases } from "./usePurchases";

const PAGE_SIZE = 25;
const FILTER_KEYS = [
  "q",
  "source",
  "modality",
  "department",
  "value_range",
  "has_signal",
  "sort",
] as const;

function readFilters(params: URLSearchParams): ExploreFilterValues {
  return {
    q: params.get("q") ?? "",
    source: params.get("source") ?? "",
    modality: params.get("modality") ?? "",
    department: params.get("department") ?? "",
    value_range: params.get("value_range") ?? "",
    has_signal: params.get("has_signal") ?? "",
    sort: params.get("sort") ?? "signed_desc",
  };
}

function toQuery(filters: ExploreFilterValues, page: number): PurchaseQuery {
  // Solo se envían los filtros con valor; los valores los valida la API.
  const query: Record<string, string | number> = { page, page_size: PAGE_SIZE };
  for (const key of FILTER_KEYS) {
    if (filters[key]) {
      query[key] = filters[key];
    }
  }
  return query;
}

export function ExplorePage() {
  const [params, setParams] = useSearchParams();
  const filters = useMemo(() => readFilters(params), [params]);
  const page = Math.max(1, Number(params.get("page") ?? "1") || 1);
  const purchases = usePurchases(toQuery(filters, page));
  const options = usePurchaseFilters();

  const updateFilters = useCallback(
    (changes: Partial<ExploreFilterValues>) => {
      setParams((current) => {
        const next = new URLSearchParams(current);
        for (const [key, value] of Object.entries(changes)) {
          if (value) {
            next.set(key, value);
          } else {
            next.delete(key);
          }
        }
        next.delete("page"); // cualquier cambio de filtro vuelve a la página 1
        return next;
      });
    },
    [setParams],
  );

  const changePage = (nextPage: number) =>
    setParams((current) => {
      const next = new URLSearchParams(current);
      next.set("page", String(nextPage));
      return next;
    });

  const cutoff = options.data?.data_cutoff_at;
  const total = purchases.data?.total;

  return (
    <section>
      <h1>Explorar compras de televisores</h1>
      <p className="sub">
        Contratos SECOP II y órdenes de la Tienda Virtual del Estado identificados como compra de
        televisores (2023–2026).
        {cutoff ? <> Datos actualizados al {formatBogotaDateTime(cutoff)}.</> : null}
      </p>
      <div className="row">
        <div style={{ flex: 1 }}>
          <ExploreFilters values={filters} options={options.data} onChange={updateFilters} />
        </div>
        {total !== undefined ? <span className="chip">{formatInteger(total)} compras</span> : null}
      </div>

      <div className="table-wrap" aria-busy={purchases.isFetching}>
        {purchases.isPending ? (
          <p className="table-state" role="status">
            Cargando compras…
          </p>
        ) : purchases.isError ? (
          <div className="table-state" role="alert">
            <p>No fue posible cargar las compras. Intenta de nuevo.</p>
            <button type="button" className="btn" onClick={() => void purchases.refetch()}>
              Reintentar
            </button>
          </div>
        ) : purchases.data.items.length === 0 ? (
          <p className="table-state" role="status">
            No hay compras que coincidan con los filtros.
          </p>
        ) : (
          <PurchasesTable purchases={purchases.data.items} />
        )}
      </div>

      {purchases.data && purchases.data.total > 0 ? (
        <Pagination
          page={purchases.data.page}
          pageSize={purchases.data.page_size}
          total={purchases.data.total}
          itemLabel="compras"
          onPageChange={changePage}
        />
      ) : null}
      <p className="small muted" style={{ marginTop: 8 }}>
        Los estados distinguen «la fuente no publica el dato» de «el producto no logró compararlo».
      </p>
    </section>
  );
}
