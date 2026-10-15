import type { EvidenceDocument } from "./evidencePresentation";

export function EvidenceDocuments({ documents }: { documents: EvidenceDocument[] }) {
  return documents.map((doc) => (
    <article className="eureka-evidence" key={doc.key}>
      <h4>{doc.name}</h4>
      {doc.entries.map((entry, index) => (
        <div key={index}>
          <p className="small">{entry.locations.join(" · ")}</p>
          {entry.cells ? (
            <dl>
              {entry.cells.map((cell, column) => (
                <div key={column}>
                  <dt>{cell.label}</dt>
                  <dd style={{ whiteSpace: "pre-wrap" }}>{cell.text.trim()}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <pre>{entry.text?.replace(/\n(?:[ \t]*\n)+/g, "\n").trim()}</pre>
          )}
        </div>
      ))}
    </article>
  ));
}
