import { useState } from "react";

import { ApiError, type CaseItemKind } from "../api/client";
import { useCaseMutations, useCases } from "../features/cases/useCases";

interface SaveToCaseButtonProps {
  kind: CaseItemKind;
  reference: string;
}

/** «★ Guardar en caso»: elige un caso existente o crea uno nuevo y guarda la instantánea. */
export function SaveToCaseButton({ kind, reference }: SaveToCaseButtonProps) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const cases = useCases();
  const { createCase, saveItem } = useCaseMutations();

  const save = async (caseId: string, caseTitle: string) => {
    try {
      await saveItem.mutateAsync({ caseId, kind, reference });
      setMessage(`Guardado en el caso «${caseTitle}» como instantánea.`);
    } catch (error) {
      setMessage(
        error instanceof ApiError && error.status === 422
          ? `Ya estaba guardado en el caso «${caseTitle}».`
          : "No fue posible guardar. Intenta de nuevo.",
      );
    }
    setOpen(false);
  };

  const createAndSave = async () => {
    const cleaned = title.trim();
    if (!cleaned) {
      return;
    }
    try {
      const created = await createCase.mutateAsync(cleaned);
      setTitle("");
      await save(created.id, created.title);
    } catch {
      setMessage("No fue posible crear el caso. Revisa el título (máximo 120 caracteres).");
    }
  };

  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        className="btn primary"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        ★ Guardar en caso
      </button>
      {message ? (
        <div className="status-message" role="status">
          {message}
        </div>
      ) : null}
      {open ? (
        <div className="popover" role="dialog" aria-label="Guardar en caso">
          <div className="small muted" style={{ marginBottom: 6 }}>
            Elige un caso (se guarda una instantánea):
          </div>
          <div className="case-list">
            {(cases.data ?? []).map((item) => (
              <button key={item.id} type="button" onClick={() => void save(item.id, item.title)}>
                <b>{item.title}</b>
                <div className="small muted">
                  {item.item_count} elementos · {item.note_count} notas
                </div>
              </button>
            ))}
            {cases.data?.length === 0 ? (
              <p className="small muted">Todavía no tienes casos.</p>
            ) : null}
          </div>
          <label
            className="small muted"
            htmlFor="new-case-title"
            style={{ display: "block", marginTop: 8 }}
          >
            Nuevo caso
          </label>
          <div className="row" style={{ flexWrap: "nowrap" }}>
            <input
              id="new-case-title"
              className="input"
              maxLength={120}
              placeholder="Título del caso"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
            <button type="button" className="btn" onClick={() => void createAndSave()}>
              Crear y guardar
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
