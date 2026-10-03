// Lets any page open the chat panel, optionally sending a question right away
// (e.g. the "Ask about this item" button on a product page).
const EVENT = 'cc:ask-assistant'

export function askAssistant(message?: string) {
  window.dispatchEvent(new CustomEvent<string | undefined>(EVENT, { detail: message }))
}

export function onAskAssistant(handler: (message?: string) => void): () => void {
  const listener = (e: Event) => handler((e as CustomEvent<string | undefined>).detail)
  window.addEventListener(EVENT, listener)
  return () => window.removeEventListener(EVENT, listener)
}
