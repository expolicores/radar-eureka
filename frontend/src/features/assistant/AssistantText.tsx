import type { ReactNode } from "react";
import { externalUrl, type ExternalReference } from "./chatApi";

/** Restricted formatting only. React escapes all text; model HTML is never executed. */
function inline(text: string, references: ExternalReference[]): ReactNode {
  return text.split(/(\*\*[^*\n]+\*\*|\[\d+\])/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{inline(part.slice(2, -2), references)}</strong>;
    }
    const citation = /^\[(\d+)\]$/.exec(part);
    const ref = citation && references.find((r) => r.citation_number === Number(citation[1]));
    const url = ref && externalUrl(ref.url);
    return ref && url ? (
      <a
        key={index}
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Fuente ${ref.citation_number}: ${ref.title}`}
      >
        {part}
      </a>
    ) : (
      part
    );
  });
}

export function AssistantText({
  text,
  externalReferences = [],
  tables = false,
}: {
  text: string;
  externalReferences?: ExternalReference[];
  tables?: boolean;
}) {
  const blocks: ReactNode[] = [];
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  for (let i = 0; i < lines.length;) {
    const line = lines[i] ?? "";
    if (!line.trim()) {
      i++;
      continue;
    }
    if (tables && line.trim().startsWith("|") && /^\s*\|\s*:?-{3,}/.test(lines[i + 1] ?? "")) {
      const cells = (value: string) =>
        value
          .trim()
          .replace(/^\||\|$/g, "")
          .split("|")
          .map((cell) => cell.trim());
      const headers = cells(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && (lines[i] ?? "").trim().startsWith("|")) {
        rows.push(cells(lines[i++]!));
      }
      blocks.push(
        <div
          key={i}
          className="assistant-table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Tabla de evidencia investigativa"
        >
          <table>
            <thead>
              <tr>
                {headers.map((cell, col) => (
                  <th scope="col" key={col}>
                    {inline(cell, externalReferences)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index}>
                  {headers.map((_, col) => (
                    <td key={col}>{inline(row[col] ?? "", externalReferences)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }
    const list = /^\s*(?:[-*]|\d+\.)\s+/.test(line);
    if (list) {
      const ordered = /^\s*\d+\./.test(line);
      const start = ordered ? Number.parseInt(line, 10) : undefined;
      const items: ReactNode[] = [];
      while (i < lines.length && (ordered ? /^\s*\d+\.\s+/ : /^\s*[-*]\s+/).test(lines[i] ?? "")) {
        items.push(
          <li key={i}>
            {inline((lines[i] ?? "").replace(/^\s*(?:[-*]|\d+\.)\s+/, ""), externalReferences)}
          </li>,
        );
        i++;
      }
      blocks.push(
        ordered ? (
          <ol key={i} start={start}>
            {items}
          </ol>
        ) : (
          <ul key={i}>{items}</ul>
        ),
      );
    } else {
      const paragraph: string[] = [];
      while (
        i < lines.length &&
        (lines[i] ?? "").trim() &&
        !/^\s*(?:[-*]|\d+\.)\s+/.test(lines[i] ?? "")
      ) {
        paragraph.push((lines[i] ?? "").replace(/^#{1,6}\s+/, ""));
        i++;
      }
      blocks.push(<p key={i}>{inline(paragraph.join("\n"), externalReferences)}</p>);
    }
  }
  return <div className="assistant-text">{blocks}</div>;
}
