import { useState } from "react";
import { Link } from "react-router";

import type { CaseDetail as CaseDetailData } from "../../api/client";
import { Badge } from "../../components/Badge";
import { formatBogotaDateTime, formatCop, formatPercent } from "../../lib/format";
import { useCaseMutations } from "./useCases";

const MAX_NOTE_LENGTH = 5_000;

type Snapshot = Record<string, string | number | null | undefined>;

function SnapshotItem({
  kind,
  snapshot,
  savedAt,
}: {
  kind: string;
  snapshot: Snapshot;
  savedAt: string;
}) {
  const saved = `Instantánea del ${formatBogotaDateTime(savedAt)}`;
  if (kind === "signal") {
    return (
      <div className="snap">
        <div className="row">
          <b>Señal {snapshot.code}</b>
          <Badge tone="review">⚑ Merece revisión</Badge>
          <span className="spacer" />
          <span className="small muted">{saved}</span>
        </div>
        <div className="small">
          {snapshot.item_description} ×{snapshot.quantity} ·{" "}
          {formatCop(Number(snapshot.unit_price_cop))} c/u ·{" "}
          {formatPercent(String(snapshot.deviation_pct))} vs. mediana pública ·{" "}
          {snapshot.entity_name} · configuración {snapshot.config_version_id} ·{" "}
          <Link to={`/senales/${String(snapshot.code)}`}>ver versión actual</Link>
        </div>
      </div>
    );
  }
  return (
    <div className="snap">
      <div className="row">
        <b>Compra {snapshot.reference}</b>
        <span className="spacer" />
        <span className="small muted">{saved}</span>
      </div>
      <div className="small">
        {snapshot.entity_name} · {snapshot.supplier_name} ·{" "}
        {formatCop(snapshot.total_value_cop === null ? null : Number(snapshot.total_value_cop))} ·{" "}
        <Link to={`/compras/${String(snapshot.purchase_id)}`}>ver ficha actual</Link>
      </div>
    </div>
  );
}

export function CaseDetail({ data }: { data: CaseDetailData }) {
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { addNote } = useCaseMutations();

  const submit = async () => {
    const body = note.trim();
    if (!body) {
      setError("La nota está vacía.");
      return;
    }
    try {
      await addNote.mutateAsync({ caseId: data.id, body });
      setNote("");
      setError(null);
    } catch {
      setError("No fue posible agregar la nota. Intenta de nuevo.");
    }
  };

  return (
    <div className="card">
      <div className="row">
        <h2 style={{ margin: 0 }}>{data.title}</h2>
        <span className="spacer" />
        <Badge tone="neutral">
          {data.item_count} elementos · {data.note_count} notas
        </Badge>
      </div>
      <p className="small muted">
        Creado el {formatBogotaDateTime(data.created_at)} · última actividad{" "}
        {formatBogotaDateTime(data.last_activity_at)}
      </p>
      <h3>Elementos guardados (instantáneas)</h3>
      {data.items.length === 0 ? (
        <p className="small muted">
          Guarda señales o compras con «★ Guardar en caso» desde su detalle.
        </p>
      ) : (
        data.items.map((item) => (
          <SnapshotItem
            key={`${item.kind}-${item.reference}`}
            kind={item.kind}
            snapshot={item.snapshot as Snapshot}
            savedAt={item.saved_at}
          />
        ))
      )}
      <h3 style={{ marginTop: 14 }}>Notas</h3>
      {data.notes.map((item) => (
        <div key={item.created_at} className="note">
          <div className="meta">{formatBogotaDateTime(item.created_at)}</div>
          {item.body}
        </div>
      ))}
      <label className="small muted" htmlFor="note-text">
        Nueva nota
      </label>
      <textarea
        id="note-text"
        maxLength={MAX_NOTE_LENGTH}
        placeholder="Escribe una nota (máx. 5.000 caracteres)…"
        value={note}
        onChange={(event) => setNote(event.target.value)}
      />
      <div className="row" style={{ marginTop: 8 }}>
        {error ? (
          <span className="small" role="alert">
            {error}
          </span>
        ) : null}
        <span className="spacer" />
        <button type="button" className="btn primary" onClick={() => void submit()}>
          Agregar nota
        </button>
      </div>
    </div>
  );
}
