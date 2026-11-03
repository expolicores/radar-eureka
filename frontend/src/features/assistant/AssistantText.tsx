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
}: {
  text: string;
  externalReferences?: ExternalReference[];
}) {
  const blocks: ReactNode[] = [];
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  for (let i = 0; i < lines.length;) {
    const line = lines[i] ?? "";
    if (!line.trim()) {
      i++;
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
