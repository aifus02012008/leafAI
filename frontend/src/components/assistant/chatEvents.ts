/** Lets any page open the floating assistant without prop drilling. */
export const OPEN_CHAT_EVENT = 'leafai:open-chat';

/** A diagnosis the chat should talk about ("Hỏi bác sĩ AI" on the result screen). */
export interface ChatDiagnosisContext {
  diagnosisId: number;
  label: string; // e.g. "Thán thư măng cụt · 82%"
}

export function openChat(context?: ChatDiagnosisContext): void {
  window.dispatchEvent(new CustomEvent<ChatDiagnosisContext | undefined>(OPEN_CHAT_EVENT, { detail: context }));
}
