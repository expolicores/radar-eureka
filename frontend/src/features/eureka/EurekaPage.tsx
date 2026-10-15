import { Link, useSearchParams } from "react-router";
import { Pagination } from "../../components/Pagination";
import { SecopProcessInfo } from "./SecopProcessInfo";
import { categoryLabels, enrichmentLabels, money, priorityLabels } from "./types";
import { useEureka, type EurekaFilters } from "./useEureka";

export function EurekaPage() {
  const [params, setParams] = useSearchParams();
  const page = Math.max(1, Number(params.get("page")) || 1);
  const priority = params.get("priority");
  const filters: EurekaFilters = {
    page,
    page_size: 25,
    ...(priority === "high" || priority === "medium" || priority === "low" ? { priority } : {}),
    ...(params.get("department") ? { department: params.get("department")! } : {}),
    ...(params.get("category") ? { category: params.get("category")! } : {}),
    ...(params.has("review_required")
      ? { review_required: params.get("review_required") === "true" }
      : {}),
  };
  const query = useEureka(filters);
  const change = (key: string, value: string) =>
    setParams((current) => {
      const next = new URLSearchParams(current);
      if (value) next.set(key, value);
      else next.delete(key);
      next.delete("page");
      return next;
    });
  return (
    <section>
      <h1>Eureka · oportunidades comerciales</h1>
      <Link className="btn" to="/eureka/alerts">
        Ver alertas Eureka
      </Link>
      <p className="sub">
        Procesos SECOP y evidencia documental. La prioridad orienta la revisión; no confirma
        vigencia ni recomienda participar.
      </p>
      <div className="filters eureka-filters">
        <label>
          Prioridad
          <select
            value={params.get("priority") ?? ""}
            onChange={(e) => change("priority", e.target.value)}
          >
            <option value="">Todas</option>
            {Object.entries(priorityLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Departamento
          <input
            value={params.get("department") ?? ""}
            onChange={(e) => change("department", e.target.value)}
            placeholder="Ej. Boyacá"
          />
        </label>
        <label>
          Categoría
          <select
            value={params.get("category") ?? ""}
            onChange={(e) => change("category", e.target.value)}
          >
            <option value="">Todas</option>
            {Object.entries(categoryLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Revisión
          <select
            value={params.get("review_required") ?? ""}
            onChange={(e) => change("review_required", e.target.value)}
          >
            <option value="">Todas</option>
            <option value="true">Pendiente</option>
            <option value="false">Sin revisión pendiente</option>
          </select>
        </label>
      </div>
      {query.isPending ? (
        <p role="status">Cargando oportunidades…</p>
      ) : query.isError ? (
        <div role="alert">
          No fue posible cargar Eureka.{" "}
          <button className="btn" onClick={() => void query.refetch()}>
            Reintentar
          </button>
        </div>
      ) : !query.data.items.length ? (
        <p role="status">No hay oportunidades que coincidan con los filtros.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Entidad / objeto</th>
                <th>Ubicación</th>
                <th>Presupuesto</th>
                <th>Prioridad / score</th>
                <th>Categoría</th>
                <th>Documentos / revisión</th>
              </tr>
            </thead>
            <tbody>
              {query.data.items.map((opportunity) => (
                <tr key={opportunity.opportunity_id}>
                  <td>
                    <SecopProcessInfo
                      process={opportunity}
                      opportunityId={opportunity.opportunity_id}
                    />
                    <div className="small">{opportunity.entity || "Entidad no determinada"}</div>
                  </td>
                  <td>
                    {[opportunity.municipality, opportunity.department]
                      .filter(Boolean)
                      .join(" · ") || "No determinado"}
                  </td>
                  <td>{money(opportunity.budget)}</td>
                  <td>
                    {priorityLabels[opportunity.priority] ?? opportunity.priority} ·{" "}
                    {opportunity.score}
                  </td>
                  <td>
                    {opportunity.category.map((code) => categoryLabels[code] ?? code).join(", ") ||
                      "No determinada"}
                  </td>
                  <td>
                    {enrichmentLabels[opportunity.enrichment_status] ??
                      opportunity.enrichment_status}
                    <div>
                      {opportunity.review_required ? "Requiere revisión" : "Sin revisión pendiente"}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {query.data && query.data.total > 0 && (
        <Pagination
          page={page}
          pageSize={25}
          total={query.data.total}
          itemLabel="oportunidades"
          onPageChange={(next) =>
            setParams((current) => {
              const values = new URLSearchParams(current);
              values.set("page", String(next));
              return values;
            })
          }
        />
      )}
    </section>
  );
}
