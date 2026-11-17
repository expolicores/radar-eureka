import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { AssistantText } from "./AssistantText";
import { ChatFailure } from "./chatApi";
import {
  askInvestigationAssistant,
  investigationResultUrl,
  type InvestigationReply,
} from "./investigationChatApi";

const SUGGESTIONS = [
  "¿Qué encontró la última corrida investigativa?",
  "¿Qué procesos debería revisar primero?",
  "¿Por qué no hubo comparaciones?",
  "¿Qué productos tienen precio documentado pero identidad no resuelta?",
];
type Message = { id: number; role: "user" | "assistant"; text: string; reply?: InvestigationReply };

function InvestigationReferences({ reply }: { reply: InvestigationReply }) {
  const navigate = useNavigate();
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState(false);
  const urls = useRef(new Map<string, string>());
  async function open(runId: string, process?: string) {
    if (opening) return;
    setOpening(true);
    setError(false);
    try {
      const url = urls.current.get(runId) ?? (await investigationResultUrl(runId));
      urls.current.set(runId, url);
      const target = new URL(url, location.origin);
      if (process) target.searchParams.set("process", process);
      void navigate(target.pathname + target.search);
    } catch {
      setError(true);
    } finally {
      setOpening(false);
    }
  }
  const processes = [...new Set(reply.process_references)];
  return (
    <div className="investigation-chat-references">
      {!!reply.run_references.length && (
        <div aria-label="Corrida relacionada">
          <strong>Corrida relacionada</strong>
          {reply.run_references.map((id) => (
            <button
              className="investigation-reference-link"
              type="button"
              key={id}
              disabled={opening}
              onClick={() => void open(id)}
            >
              {id}
            </button>
          ))}
        </div>
      )}
      {!!processes.length && (
        <details>
          <summary>{processes.length} procesos relacionados</summary>
          <p>
            Primeros {Math.min(5, processes.length)} procesos referenciados; no representan un orden
            de prioridad.
          </p>
          <ul>
            {processes.slice(0, 5).map((id) => (
              <li key={id}>
                {id}{" "}
                {reply.run_references.length === 1 && (
                  <button
                    type="button"
                    disabled={opening}
                    onClick={() => void open(reply.run_references[0]!, id)}
                  >
                    Ver proceso
                  </button>
                )}
              </li>
            ))}
          </ul>
        </details>
      )}
      {opening && <p role="status">Abriendo resultado…</p>}
      {error && <p role="alert">No fue posible abrir el resultado de esta corrida.</p>}
    </div>
  );
}

export function InvestigationChat({ runId }: { runId: string | null }) {
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
      const reply = await askInvestigationAssistant(question, conversationId, runId);
      if (!mounted.current) return;
      setConversationId(reply.conversation_id);
      setMessages((old) => [
        ...old,
        { id: nextId.current++, role: "assistant", text: reply.response, reply },
      ]);
    } catch (failure) {
      if (!mounted.current) return;
      setError("No fue posible consultar el asistente investigativo.");
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
    setDraft("");
    setError(null);
    setContextReset(false);
  }
  return (
    <section
      className="assistant-page investigation-chat"
      aria-labelledby="investigation-assistant-title"
    >
      <div className="assistant-heading">
        <div>
          <span className="assistant-eyebrow">RADAR / INVESTIGACIÓN</span>
          <h1 id="investigation-assistant-title">Asistente investigativo</h1>
          <p>
            Consulta corridas, hallazgos, productos, comparaciones, señales y procesos que requieren
            revisión humana.
          </p>
        </div>
        <button type="button" onClick={startNew} disabled={pending || messages.length === 0}>
          Nueva conversación
        </button>
      </div>
      <p className="investigation-chat-context">
        {runId
          ? `Corrida seleccionada: ${runId}`
          : "Contexto: última corrida investigativa disponible."}{" "}
        Solo consulta resultados guardados.
      </p>
      {conversationId && (
        <details className="investigation-chat-context">
          <summary>Detalles de conversación</summary>
          <p>Conversación: {conversationId}</p>
        </details>
      )}
      {messages.length === 0 && (
        <div className="assistant-welcome">
          <span className="assistant-welcome-icon" aria-hidden="true">
            ⌕
          </span>
          <span className="assistant-eyebrow">EVIDENCIA PARA REVISIÓN HUMANA</span>
          <h2>Entiende qué encontró una corrida y dónde vale la pena revisar evidencia.</h2>
          <p>
            Consulta productos, precios documentados y limitaciones de los resultados
            investigativos.
          </p>
          <div className="assistant-suggestions" aria-label="Preguntas investigativas sugeridas">
            {SUGGESTIONS.map((question) => (
              <button
                type="button"
                key={question}
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
        aria-label="Conversación investigativa"
        aria-relevant="additions"
      >
        {messages.map((message) => (
          <article
            className={`assistant-message assistant-message-${message.role}`}
            key={message.id}
            aria-label={
              message.role === "user" ? "Tu mensaje investigativo" : "Respuesta investigativa"
            }
          >
            <b className="assistant-speaker">
              {message.role === "user" ? "Tú" : "Asistente investigativo"}
            </b>
            <AssistantText text={message.text} tables />
            {message.reply && <InvestigationReferences reply={message.reply} />}
          </article>
        ))}
        {pending && <p role="status">Consultando asistente investigativo…</p>}
        <div ref={end} />
      </div>
      {error && (
        <div className="assistant-error" role="alert">
          <p>{error}</p>
          {contextReset && (
            <p>
              La próxima consulta iniciará un contexto investigativo nuevo. El historial anterior
              sigue visible.
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
        <label htmlFor="investigation-question">Tu pregunta investigativa</label>
        <textarea
          id="investigation-question"
          value={draft}
          maxLength={4000}
          rows={3}
          disabled={pending}
          placeholder="¿Qué fue lo más importante de la última corrida?"
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
