import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { formatBogotaDateTime } from "../../lib/format";
import { CaseDetail } from "./CaseDetail";
import { useCase, useCaseMutations, useCases } from "./useCases";

export function CasesPage() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const cases = useCases();
  const selectedId = caseId ?? cases.data?.[0]?.id;
  const selected = useCase(selectedId);
  const { createCase } = useCaseMutations();
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  const create = async () => {
    const cleaned = title.trim();
    if (!cleaned) {
      setError("Escribe un título para el caso.");
      return;
    }
    try {
      const created = await createCase.mutateAsync(cleaned);
      setTitle("");
      setError(null);
      void navigate(`/casos/${created.id}`);
    } catch {
      setError("No fue posible crear el caso (máximo 120 caracteres).");
    }
  };

  return (
    <section>
      <h1>Mis casos de investigación</h1>
      <p className="sub">
        Tus casos son privados: solo tú puedes verlos. La evidencia guardada se conserva como
        instantánea aunque los benchmarks se recalculen.
      </p>
      <div className="grid g-main">
        <div>
          {cases.isPending ? (
            <p className="table-state" role="status">
              Cargando casos…
            </p>
          ) : cases.isError ? (
            <div className="table-state" role="alert">
              <p>No fue posible cargar tus casos. Intenta de nuevo.</p>
              <button type="button" className="btn" onClick={() => void cases.refetch()}>
                Reintentar
              </button>
            </div>
          ) : !selectedId ? (
            <div className="card table-state">
              Todavía no tienes casos. Crea uno a la derecha o guarda una señal con «★ Guardar en
              caso».
            </div>
          ) : selected.data ? (
            <CaseDetail data={selected.data} />
          ) : selected.isError ? (
            <div className="table-state" role="alert">
              Caso no encontrado.
            </div>
          ) : (
            <p className="table-state" role="status">
              Cargando caso…
            </p>
          )}
        </div>
        <div className="card" style={{ alignSelf: "start" }}>
          <h3>Todos mis casos</h3>
          <div className="case-list">
            {(cases.data ?? []).map((item) => (
              <button
                key={item.id}
                type="button"
                aria-current={item.id === selectedId}
                onClick={() => void navigate(`/casos/${item.id}`)}
              >
                <b>{item.title}</b>
                <div className="small muted">
                  {item.item_count} elementos · {formatBogotaDateTime(item.last_activity_at)}
                </div>
              </button>
            ))}
          </div>
          <label
            className="small muted"
            htmlFor="case-title"
            style={{ display: "block", marginTop: 10 }}
          >
            Nuevo caso
          </label>
          <input
            id="case-title"
            className="input"
            maxLength={120}
            placeholder="Título del caso"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
          {error ? (
            <div className="small" role="alert">
              {error}
            </div>
          ) : null}
          <button
            type="button"
            className="btn"
            style={{ marginTop: 8, width: "100%" }}
            onClick={() => void create()}
          >
            + Nuevo caso
          </button>
        </div>
      </div>
    </section>
  );
}
