import ProductTile from './ProductTile'
import { useChatResults } from '../chatResults'

// Renders the chat agent's product matches as cards at the top of the current page.
// Cards use the same /products/:id route as the Products page, so the single-item page still opens.
export default function ChatResultsPanel() {
  const { results, collapsed, setCollapsed, clear } = useChatResults()
  if (!results || results.products.length === 0) return null

  const count = results.products.length
  const label = `${count} item${count === 1 ? '' : 's'} from the assistant`

  if (collapsed) {
    return (
      <div className="chat-results collapsed">
        <span>
          🔎 {label} for “{results.query}”
        </span>
        <div>
          <button className="link-btn dark" onClick={() => setCollapsed(false)}>
            Show
          </button>
          <button className="link-btn dark" onClick={clear} aria-label="Dismiss results">
            ×
          </button>
        </div>
      </div>
    )
  }

  return (
    <section className="chat-results" aria-label="Chat search results">
      <div className="chat-results-head">
        <div>
          <h2>🔎 {label}</h2>
          <p className="muted">You asked: “{results.query}”</p>
        </div>
        <div>
          <button className="link-btn dark" onClick={() => setCollapsed(true)}>
            Hide
          </button>
          <button className="link-btn dark" onClick={clear} aria-label="Dismiss results">
            ×
          </button>
        </div>
      </div>
      <div className="grid">
        {results.products.map((p, i) => (
          <ProductTile
            key={p.product_id}
            product={p}
            index={i}
            // Collapse (not clear) so the shopper can come back to the results from the detail page.
            onClick={() => setCollapsed(true)}
          />
        ))}
      </div>
    </section>
  )
}
