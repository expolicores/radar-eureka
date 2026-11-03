import type { components } from "../../api/schema";

export type ProcessReference = components["schemas"]["ProcessReference"];
export type ExternalReference = components["schemas"]["ExternalReference"];

export type ChatReply = components["schemas"]["ChatReply"];

export function externalUrl(value: string): string | null {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) && !url.username && !url.password
      ? url.href
      : null;
  } catch {
    return null;
  }
}

export class ChatFailure extends Error {
  constructor(
    message: string,
    readonly resetConversation: boolean,
  ) {
    super(message);
  }
}

export async function askAssistant(
  message: string,
  conversationId: string | null,
): Promise<ChatReply> {
  const response = await fetch(
    new Request(new URL("/api/eureka/assistant/chat", location.origin), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),
  );
  if (!response.ok) {
    // Never display arbitrary proxy/provider error bodies, HTML or technical diagnostics.
    const problem = (await response.json().catch(() => ({}))) as {
      code?: string;
      reset_conversation?: boolean;
    };
    const message =
      response.status === 404 || problem.code === "conversation_limit"
        ? "La conversación terminó o expiró. Puedes iniciar una nueva con tu pregunta."
        : response.status === 409 || response.status === 429
          ? "Eureka está ocupado. Espera un momento e intenta nuevamente."
          : "No pude consultar Eureka en este momento. Intenta nuevamente.";
    throw new ChatFailure(message, problem.reset_conversation ?? response.status >= 500);
  }
  const data = (await response.json()) as ChatReply;
  if (!data.message?.trim() || !data.conversation_id || !Array.isArray(data.process_references)) {
    throw new ChatFailure("Eureka no devolvió una respuesta. Intenta nuevamente.", true);
  }
  return data;
}
