import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import { AssistantText } from "./AssistantText";
import {
  askAssistant,
  ChatFailure,
  externalUrl,
  type ExternalReference,
  type ProcessReference,
} from "./chatApi";

const SUGGESTIONS = [
  "¿Qué salió en la última corrida CDP?",
  "¿Viste alguna oportunidad interesante para mí?",
  "¿Qué procesos debería revisar primero?",
];

type Message = {
  id: number;
  role: "user" | "assistant";
  text: string;
  references?: ProcessReference[];
  externalReferences?: ExternalReference[];
};

function ProcessCards({ references }: { references: ProcessReference[] }) {
  return (
    <div className="assistant-processes" aria-label="Procesos consultados">
      <h3>Procesos consultados en Eureka</h3>
      {references.map((process) => (
        <article className="assistant-process" key={process.identity}>
          <strong>{process.process_code || process.identity}</strong>
          {process.entity && <p>{process.entity}</p>}
          <p>{[process.municipality, process.department].filter(Boolean).join(", ")}</p>
          <Link to={`/eureka/revision/${encodeURIComponent(process.identity)}`}>Ver proceso</Link>
        </article>
      ))}
    </div>
  );
}

function ExternalSources({ references }: { references: ExternalReference[] }) {
  return (
    <section className="assistant-external-sources" aria-label="Fuentes externas de Web Search">
      <h3>Fuentes externas · Web Search</h3>
      <p>Los hallazgos web no han sido incorporados ni validados por el pipeline de Eureka.</p>
      <div className="assistant-processes">
        {references.map((ref) => {
          const url = externalUrl(ref.url);
          return (
            url && (
              <article className="assistant-process" key={ref.url}>
                <a href={url} target="_blank" rel="noopener noreferrer">
                  [{ref.citation_number}] {ref.title}
                </a>
                <p>{ref.source}</p>
                {ref.published_at && <p>Publicación: {ref.published_at}</p>}
                {ref.entity && <p>{ref.entity}</p>}
                {ref.location && <p>{ref.location}</p>}
                <small>Referencia externa · verificación preliminar</small>
              </article>
            )
          );
        })}
      </div>
    </section>
  );
}

export function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contextReset, setContextReset] = useState(false);
  const inFlight = useRef(false);
  const mounted = useRef(true);
  const nextId = useRef(0);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    end.current?.scrollIntoView?.({ behavior: "smooth", block: "nearest" });
  }, [messages, pending, error]);

  async function send(text = draft) {
    const question = text.trim();
    if (inFlight.current || !question || question.length > 4000) return;
    inFlight.current = true;
    setPending(true);
    setError(null);
    setContextReset(false);
    setDraft("");
    setMessages((old) => [...old, { id: nextId.current++, role: "user", text: question }]);
    try {
      const reply = await askAssistant(question, conversationId);
      if (!mounted.current) return;
      setConversationId(reply.conversation_id);
      setMessages((old) => [
        ...old,
        {
          id: nextId.current++,
          role: "assistant",
          text: reply.message,
          references: reply.process_references,
          externalReferences: reply.external_references,
        },
      ]);
    } catch (failure) {
      if (!mounted.current) return;
      setError(
        failure instanceof ChatFailure
          ? failure.message
          : "No pude consultar Eureka en este momento. Intenta nuevamente.",
      );
      setDraft(question);
      if (!(failure instanceof ChatFailure) || failure.resetConversation) {
        setConversationId(null);
        setContextReset(true);
      }
    } finally {
      inFlight.current = false;
      if (mounted.current) setPending(false);
    }
  }

  function startNew() {
    if (inFlight.current) return;
    setMessages([]);
    setConversationId(null);
    setError(null);
    setDraft("");
    setContextReset(false);
  }

  return (
    <section className="assistant-page" aria-labelledby="assistant-title">
      <div className="assistant-heading">
        <div>
          <span className="assistant-eyebrow">RADAR / ASISTENTE COMERCIAL</span>
          <h1 id="assistant-title">Asistente Eureka</h1>
          <p>Consulta corridas, oportunidades y evidencia para decidir qué revisar.</p>
        </div>
        <button type="button" onClick={startNew} disabled={pending || messages.length === 0}>
          Nueva conversación
        </button>
      </div>

      {messages.length === 0 && (
        <div className="assistant-welcome">
          <span className="assistant-welcome-icon" aria-hidden="true">
            ✧
          </span>
          <span className="assistant-eyebrow">MENOS BÚSQUEDA. MÁS CRITERIO.</span>
          <h2>Tu próxima oportunidad empieza con una pregunta.</h2>
          <p>
            Explora los hallazgos de Radar, contrasta la evidencia y decide qué merece tu atención.
          </p>
          <div className="assistant-suggestions" aria-label="Preguntas sugeridas">
            {SUGGESTIONS.map((question) => (
              <button
                key={question}
                type="button"
                disabled={pending}
                onClick={() => void send(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      <div
        className="assistant-history"
        role="log"
        aria-label="Conversación con Eureka"
        aria-relevant="additions"
      >
        {messages.map((message) => (
          <article
            key={message.id}
            className={`assistant-message assistant-message-${message.role}`}
            aria-label={message.role === "user" ? "Tu mensaje" : "Respuesta de Eureka"}
          >
            <b className="assistant-speaker">{message.role === "user" ? "Tú" : "Eureka"}</b>
            <AssistantText text={message.text} externalReferences={message.externalReferences} />
            {!!message.references?.length && <ProcessCards references={message.references} />}
            {!!message.externalReferences?.length && (
              <ExternalSources references={message.externalReferences} />
            )}
          </article>
        ))}
        {pending && <p role="status">Consultando Eureka…</p>}
        <div ref={end} />
      </div>

      {error && (
        <div className="assistant-error" role="alert">
          <p>{error}</p>
          {contextReset && (
            <p>
              La próxima consulta iniciará un contexto nuevo. El historial anterior sigue visible.
            </p>
          )}
          <button type="button" onClick={() => void send()} disabled={pending}>
            Reintentar
          </button>
        </div>
      )}

      <form
        className="assistant-composer"
        onSubmit={(event) => {
          event.preventDefault();
          void send();
        }}
      >
        <label htmlFor="assistant-question">Tu pregunta</label>
        <textarea
          id="assistant-question"
          value={draft}
          maxLength={4000}
          rows={3}
          placeholder="¿Qué debería revisar primero?"
          disabled={pending}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              void send();
            }
          }}
        />
        <div className="assistant-composer-actions">
          <small>Enter para enviar · Shift+Enter para una nueva línea</small>
          <button type="submit" className="btn primary" disabled={pending || !draft.trim()}>
            Enviar
          </button>
        </div>
      </form>
    </section>
  );
}
