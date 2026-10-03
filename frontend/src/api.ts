export interface SizeStock {
  size: string
  quantity: number
  in_stock: boolean
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  price: number
  image_url: string
  total_stock: number
  inventory?: SizeStock[]
}

// One card the chat puts on the page. Built by the backend from the DB, keyed by the agent's product_ids.
export interface ProductCard {
  product_id: string
  name: string
  garment_type: string
  price: number
  image_url: string
  description: string
  colors: string[]
  total_stock: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: ProductCard[]
}

export interface ChatReply {
  reply: string
  products: ProductCard[]
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<Product[]>('/api/products')

export const fetchProduct = (id: string) =>
  getJson<Product>(`/api/products/${encodeURIComponent(id)}`)

// `page` tells the agent what the shopper is looking at (e.g. a product page), so "this" makes sense.
// For logged-in shoppers the server ignores `history` and uses the saved chat from the database.
export const sendChat = (message: string, history: ChatMessage[], pagePath: string) =>
  getJson<ChatReply>('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      history: history.slice(-20).map(({ role, content }) => ({ role, content })),
      page: { path: pagePath },
    }),
  })

// Logged-in shoppers' saved conversation; empty for guests.
export const fetchChatHistory = () => getJson<ChatMessage[]>('/api/chat/history')

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

export function shortDescription(text: string, max = 110): string {
  if (text.length <= max) return text
  return text.slice(0, text.lastIndexOf(' ', max)) + '…'
}

// ---------- Auth (session lives in an HttpOnly cookie set by the backend) ----------

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
}

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Something went wrong.')
  return data as T
}

export const signup = (body: { first_name: string; last_name: string; email: string; password: string }) =>
  postJson<User>('/api/auth/signup', body)

export const login = (email: string, password: string) =>
  postJson<User>('/api/auth/login', { email, password })

export const logout = () => postJson<{ ok: boolean }>('/api/auth/logout')

export async function fetchMe(): Promise<User | null> {
  const res = await fetch('/api/auth/me')
  return res.ok ? ((await res.json()) as User) : null
}
