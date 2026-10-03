import { useEffect, useRef, useState, type FormEvent } from 'react'
import Markdown from 'react-markdown'
import { useLocation } from 'react-router-dom'
import { fetchChatHistory, sendChat, type ChatMessage } from '../api'
import { useAuth } from '../auth'
import { useChatResults } from '../chatResults'
import { onAskAssistant } from '../chatEvents'

// One-tap starter questions. On a product page they're about that product ("this"),
// which the agent resolves through page context (Problem 8).
const GENERAL_SUGGESTIONS = ['What hoodies do you have?', 'Gift ideas under $40', 'Show me Morse College gear']
const PRODUCT_SUGGESTIONS = ['Is this in stock in M?', 'What colors does this come in?', 'Show me similar items']

function welcome(firstName?: string): ChatMessage {
  return {
    role: 'assistant',
    content: `Hi${firstName ? ` ${firstName}` : ''}! Looking for some Bulldog gear? Ask me about products, sizes or colors.`,
  }
}

export default function ChatWidget() {
  const { user } = useAuth()
  const { show } = useChatResults()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([welcome()])
  const bottomRef = useRef<HTMLDivElement>(null)

  // Logged in: restore this shopper's saved conversation. Logged out: start fresh.
  useEffect(() => {
    if (!user) {
      setMessages([welcome()])
      return
    }
    fetchChatHistory()
      .then((history) => setMessages([welcome(user.first_name), ...history]))
      .catch(() => setMessages([welcome(user.first_name)]))
  }, [user])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy, open])

  // Buttons elsewhere on the site can open the chat and ask a question.
  // No dependency list on purpose: re-subscribing each render keeps `send` fresh (current messages/page).
  useEffect(
    () =>
      onAskAssistant((message) => {
        setOpen(true)
        if (message) void send(message)
      }),
  )

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void send(input)
  }

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || busy) return
    // History excludes the canned welcome message, which the agent never said.
    const history = messages.slice(1)
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }])
    setBusy(true)
    try {
      const { reply, products } = await sendChat(text, history, location.pathname)
      setMessages((m) => [...m, { role: 'assistant', content: reply, products }])
      // The API contract: structured product matches -> cards rendered on the page.
      // Skip it when the only match is the product already open (it'd just repeat the page).
      const onlyCurrent = products.length === 1 && location.pathname === `/products/${products[0].product_id}`
      if (products.length > 0 && !onlyCurrent) show({ query: text, products })
    } catch {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: "Sorry, I can't reach the shop right now. Please try again." },
      ])
    } finally {
      setBusy(false)
    }
  }

  const onProductPage = /^\/products\/[^/]+$/.test(location.pathname)

  // The shopper's question that led to message i, used as the label on the page's results.
  function questionBefore(i: number): string {
    for (let j = i - 1; j >= 0; j--) if (messages[j].role === 'user') return messages[j].content
    return 'your chat'
  }

  if (!open) {
    return (
      <button className="chat-toggle" onClick={() => setOpen(true)} aria-label="Open chat">
        <span className="avatar">🐶</span>
        <span>
          <strong>Need a hand?</strong>
          <small>Ask the Campus Customs assistant</small>
        </span>
      </button>
    )
  }

  return (
    <div className="chat-panel" role="dialog" aria-label="Shopping assistant">
      <div className="chat-header">
        <span className="avatar">🐶</span>
        <div>
          <strong>Campus Customs Assistant</strong>
          <small>
            <span className="live-dot" /> Checks live stock · replies in seconds
          </small>
        </div>
        <button onClick={() => setOpen(false)} aria-label="Close chat">
          ×
        </button>
      </div>
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-row ${m.role}`}>
            <div className={`chat-msg ${m.role}`}>
              {m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : m.content}
            </div>
            {m.products && m.products.length > 0 && (
              <button
                className="chat-chip"
                onClick={() => show({ query: questionBefore(i), products: m.products! })}
              >
                🔎 {m.products.length} item{m.products.length === 1 ? '' : 's'}: show on the page
              </button>
            )}
          </div>
        ))}
        {busy && (
          <div className="chat-msg assistant typing" aria-label="Assistant is typing">
            <span />
            <span />
            <span />
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      {!busy && (
        <div className="chat-suggestions" aria-label="Suggested questions">
          {(onProductPage ? PRODUCT_SUGGESTIONS : GENERAL_SUGGESTIONS).map((q) => (
            <button key={q} className="chat-chip" onClick={() => send(q)}>
              {q}
            </button>
          ))}
        </div>
      )}
      <form className="chat-input" onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about products, sizes…"
          maxLength={2000}
        />
        <button type="submit" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
