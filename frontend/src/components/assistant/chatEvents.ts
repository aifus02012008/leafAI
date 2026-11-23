/** Lets any page open the floating assistant without prop drilling. */
export const OPEN_CHAT_EVENT = 'leafai:open-chat';

export function openChat(): void {
  window.dispatchEvent(new Event(OPEN_CHAT_EVENT));
}
