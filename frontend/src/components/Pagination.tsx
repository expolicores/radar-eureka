import { formatInteger } from "../lib/format";

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  itemLabel: string;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, itemLabel, onPageChange }: PaginationProps) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <nav className="pagination small" aria-label="Paginación">
      <button
        type="button"
        className="btn sm"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
      >
        ← Anterior
      </button>
      <span className="muted">
        Página {formatInteger(page)} de {formatInteger(pages)} · {formatInteger(total)} {itemLabel}
      </span>
      <button
        type="button"
        className="btn sm"
        disabled={page >= pages}
        onClick={() => onPageChange(page + 1)}
      >
        Siguiente →
      </button>
    </nav>
  );
}
