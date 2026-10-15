import { Link } from "react-router";

type Process = {
  secop_id: string;
  reference?: string | null;
  description?: string | null;
  source_url?: string | null;
};

export function SecopProcessInfo({
  process,
  opportunityId,
  showReference = true,
}: {
  process: Process;
  opportunityId?: string;
  showReference?: boolean;
}) {
  const reference = `Referencia del proceso: ${process.reference || "No disponible"}`;
  const sourceUrl = process.source_url;
  const usableUrl = sourceUrl && /^https?:\/\//i.test(sourceUrl);
  return (
    <div>
      {showReference &&
        (opportunityId ? (
          <Link to={`/eureka/${opportunityId}`}>{reference}</Link>
        ) : (
          <strong>{reference}</strong>
        ))}
      <p className="small">ID SECOP: {process.secop_id}</p>
      <p>Descripción:</p>
      <p style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
        {process.description || "Descripción no disponible"}
      </p>
      {usableUrl ? (
        <a href={sourceUrl} target="_blank" rel="noopener noreferrer">
          Abrir proceso en SECOP
        </a>
      ) : (
        <p className="small">Enlace SECOP no disponible</p>
      )}
    </div>
  );
}
