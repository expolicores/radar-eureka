import { ChatFailure } from "./chatApi";

export type InvestigationReply = {
  response: string;
  conversation_id: string;
  run_references: string[];
  process_references: string[];
};

const FAILURE = "No fue posible consultar el asistente investigativo.";
const strings = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every((item) => typeof item === "string" && item.trim());

export async function askInvestigationAssistant(
  message: string,
  conversationId: string | null,
  runId: string | null,
): Promise<InvestigationReply> {
  const response = await fetch(
    new Request(new URL("/api/v1/investigation/assistant/chat", location.origin), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId, run_id: runId }),
    }),
  );
  if (!response.ok) {
    const problem = (await response.json().catch(() => ({}))) as { reset_conversation?: boolean };
    throw new ChatFailure(FAILURE, problem.reset_conversation === true || response.status >= 500);
  }
  const data = (await response.json()) as InvestigationReply;
  if (
    typeof data?.response !== "string" ||
    !data.response.trim() ||
    typeof data.conversation_id !== "string" ||
    !data.conversation_id.trim() ||
    !strings(data.run_references) ||
    !strings(data.process_references)
  ) {
    throw new ChatFailure(FAILURE, true);
  }
  return data;
}

/** Resolve the existing run type before navigating; a UUID alone has no type. */
export async function investigationResultUrl(runId: string): Promise<string> {
  for (const [resource, search] of [
    ["runs", `run=${encodeURIComponent(runId)}`],
    [
      "market-runs",
      `private_run=${encodeURIComponent(runId)}&market_run=${encodeURIComponent(runId)}`,
    ],
  ]) {
    const response = await fetch(
      new Request(
        new URL(`/api/v1/investigation/${resource}/${encodeURIComponent(runId)}`, location.origin),
      ),
    );
    if (response.status === 404) continue;
    if (!response.ok) throw new Error("run_unavailable");
    const data = (await response.json()) as { run_id?: string };
    if (data.run_id !== runId) throw new Error("run_mismatch");
    return `/explorar?${search}`;
  }
  throw new Error("run_unavailable");
}
