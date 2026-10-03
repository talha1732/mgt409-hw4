import { createContext, useContext, useState, type ReactNode } from 'react'
import type { ProductCard } from './api'

// Product cards the chat agent returned, shown on the page (not just inside the chat bubble).
export interface ChatResults {
  query: string
  products: ProductCard[]
}

interface ChatResultsState {
  results: ChatResults | null
  collapsed: boolean
  show: (results: ChatResults) => void
  setCollapsed: (collapsed: boolean) => void
  clear: () => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(null)
  const [collapsed, setCollapsed] = useState(false)

  function show(r: ChatResults) {
    setResults(r)
    setCollapsed(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <ChatResultsContext.Provider
      value={{ results, collapsed, show, setCollapsed, clear: () => setResults(null) }}
    >
      {children}
    </ChatResultsContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside ChatResultsProvider')
  return ctx
}
