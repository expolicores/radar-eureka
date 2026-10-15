import { useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { api, unwrap } from "../../api/client";
import { arr, obj } from "./types";
import { EvidenceDocuments } from "./EvidenceDocuments";
import { evidenceSummary, groupEvidence } from "./evidencePresentation";

export function EvidencePanel({
  id,
  label,
  references,
  countSources = false,
}: {
  id: string;
  label: string;
  references: unknown;
  countSources?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [technical, setTechnical] = useState(false);
  const ids = [
    ...new Set(
      arr(references)
        .map((value) => obj(value).canonical_fact_id)
        .filter((value): value is string => typeof value === "string"),
    ),
  ];
  const queries = useQueries({
    queries: ids.map((canonicalId) => ({
      queryKey: ["eureka-evidence", id, canonicalId],
      enabled: open || countSources,
      queryFn: async () =>
        unwrap(
          await api.GET("/api/eureka/opportunities/{opportunity_id}/evidence", {
            params: { path: { opportunity_id: id }, query: { canonical_fact_id: canonicalId } },
          }),
        ),
    })),
  });
  if (!ids.length) return null;
  const facts = queries.flatMap((query) => query.data ?? []);
  const documents = groupEvidence(facts);
  const sourceCount = documents.reduce((count, doc) => count + doc.entries.length, 0);
  const loaded = queries.every((query) => query.isSuccess);
  return (
    <>
      <p className="small">
        {evidenceSummary(references, countSources && loaded ? sourceCount : undefined)}
      </p>
      <details
        className="eureka-evidence-panel"
        onToggle={(event) => setOpen(event.currentTarget.open)}
      >
        <summary>Ver evidencia de {label}</summary>
        {open && (
          <>
            {!countSources && loaded && !!documents.length && (
              <p className="small">{sourceCount} fuentes útiles · agrupadas sin repeticiones</p>
            )}
            {queries.some((query) => query.isPending) && <p role="status">Cargando evidencia…</p>}
            {queries.some((query) => query.isError) && (
              <div role="alert">
                No fue posible recuperar la evidencia.{" "}
                <button
                  className="btn"
                  onClick={() =>
                    queries.forEach((query) => {
                      void query.refetch();
                    })
                  }
                >
                  Reintentar
                </button>
              </div>
            )}
            <EvidenceDocuments documents={documents} />
            {queries.every((query) => query.isSuccess) && !facts.length && (
              <p>No hay evidencia disponible.</p>
            )}
            {!!facts.length && (
              <details onToggle={(event) => setTechnical(event.currentTarget.open)}>
                <summary>Ver evidencia técnica completa</summary>
                {technical && (
                  <>
                    <p>Referencias internas</p>
                    <pre>{JSON.stringify(references, null, 2)}</pre>
                    {facts.map((fact, index) => (
                      <pre key={index}>{JSON.stringify(fact, null, 2)}</pre>
                    ))}
                  </>
                )}
              </details>
            )}
          </>
        )}
      </details>
    </>
  );
}
