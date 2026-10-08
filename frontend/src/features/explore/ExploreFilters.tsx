import { useEffect, useState } from "react";

import type { FilterOptions } from "../../api/client";
import { SOURCE_LABELS } from "../../lib/labels";

export interface ExploreFilterValues {
  q: string;
  source: string;
  modality: string;
  department: string;
  value_range: string;
  has_signal: string;
  sort: string;
}

const SEARCH_DELAY_MS = 300;

interface ExploreFiltersProps {
  values: ExploreFilterValues;
  options: FilterOptions | undefined;
  onChange: (changes: Partial<ExploreFilterValues>) => void;
}

export function ExploreFilters({ values, options, onChange }: ExploreFiltersProps) {
  const [search, setSearch] = useState(values.q);
  const [syncedQuery, setSyncedQuery] = useState(values.q);

  // La URL manda: si cambia desde fuera (atrás/adelante), el buscador se sincroniza.
  if (values.q !== syncedQuery) {
    setSyncedQuery(values.q);
    setSearch(values.q);
  }

  useEffect(() => {
    if (search === values.q) {
      return;
    }
    const timer = setTimeout(() => onChange({ q: search }), SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [search, values.q, onChange]);

  return (
    <div className="filters" role="search">
      <input
        className="search"
        type="search"
        aria-label="Buscar compras"
        placeholder="Entidad, proveedor (nombre o NIT), objeto o referencia…"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />
      <select
        aria-label="Fuente"
        value={values.source}
        onChange={(event) => onChange({ source: event.target.value })}
      >
        <option value="">Fuente: Todas</option>
        {(options?.sources ?? []).map((source) => (
          <option key={source} value={source}>
            {SOURCE_LABELS[source] ?? source}
          </option>
        ))}
      </select>
      <select
        aria-label="Modalidad"
        value={values.modality}
        onChange={(event) => onChange({ modality: event.target.value })}
      >
        <option value="">Modalidad: Todas</option>
        {(options?.modalities ?? []).map((modality) => (
          <option key={modality} value={modality}>
            {modality}
          </option>
        ))}
      </select>
      <select
        aria-label="Departamento"
        value={values.department}
        onChange={(event) => onChange({ department: event.target.value })}
      >
        <option value="">Departamento: Todos</option>
        {(options?.departments ?? []).map((department) => (
          <option key={department} value={department}>
            {department}
          </option>
        ))}
      </select>
      <select
        aria-label="Valor"
        value={values.value_range}
        onChange={(event) => onChange({ value_range: event.target.value })}
      >
        <option value="">Valor: cualquiera</option>
        <option value="lt_20m">&lt; $20 M</option>
        <option value="between_20m_100m">$20 M – $100 M</option>
        <option value="gt_100m">&gt; $100 M</option>
      </select>
      <select
        aria-label="Con señal"
        value={values.has_signal}
        onChange={(event) => onChange({ has_signal: event.target.value })}
      >
        <option value="">Con señal: todas</option>
        <option value="true">Solo con señal</option>
        <option value="false">Sin señal</option>
      </select>
      <select
        aria-label="Orden"
        value={values.sort}
        onChange={(event) => onChange({ sort: event.target.value })}
      >
        <option value="signed_desc">Ordenar: más recientes</option>
        <option value="signed_asc">Más antiguas</option>
        <option value="value_desc">Mayor valor</option>
        <option value="value_asc">Menor valor</option>
      </select>
    </div>
  );
}
