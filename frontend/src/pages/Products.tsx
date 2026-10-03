import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import ProductTile from '../components/ProductTile'

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
const CATEGORIES = ['All', 'T-shirts & tops', 'Hoodies', 'Crewnecks', 'Quarter-zips', 'Jackets & fleece'] as const
type Category = (typeof CATEGORIES)[number]

// The DB's garment_type values are messy ("short-sleeve T-shirt", "pullover hoodie", "hoodie", ...),
// so group them into a few shopper-friendly categories. Order matters: "crew-neck t-shirt" is a T-shirt,
// "crewneck sweatshirt" is a crewneck.
function categoryOf(p: Product): Category | 'Other' {
  const t = `${p.garment_type} ${p.name}`.toLowerCase()
  if (t.includes('hood')) return 'Hoodies'
  if (t.includes('quarter') || t.includes('1 4 zip')) return 'Quarter-zips'
  if (t.includes('jacket') || t.includes('fleece')) return 'Jackets & fleece'
  if (t.includes('t-shirt') || t.includes('t shirt') || t.includes('tee')) return 'T-shirts & tops'
  // Checked before the generic "shirt" rule, since "sweatshirt" contains "shirt".
  if (t.includes('crew') || t.includes('sweatshirt') || t.includes('mockneck')) return 'Crewnecks'
  if (t.includes('shirt')) return 'T-shirts & tops' // e.g. long-sleeve performance shirt
  return 'Other'
}

const SORTS = {
  featured: 'Featured',
  'price-asc': 'Price: low to high',
  'price-desc': 'Price: high to low',
  name: 'Name A–Z',
} as const
type Sort = keyof typeof SORTS

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState('')
  // Filters live in the URL (?q=hockey&cat=Hoodies&size=M), so a filtered view can be shared or bookmarked.
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const cat = (params.get('cat') ?? 'All') as Category
  const size = params.get('size') ?? ''
  const sort = (params.get('sort') ?? 'featured') as Sort

  useEffect(() => {
    fetchProducts().then(setProducts).catch((e) => setError(String(e)))
  }, [])

  // Functional update: always builds on the latest URL, so quick successive changes don't overwrite each other.
  function update(key: string, value: string) {
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (value && !(key === 'cat' && value === 'All') && !(key === 'sort' && value === 'featured')) next.set(key, value)
        else next.delete(key)
        return next
      },
      { replace: true },
    )
  }

  // The search box keeps its own text (so typing never drops characters) and pushes it to the URL.
  const [searchText, setSearchText] = useState(q)

  const visible = useMemo(() => {
    if (!products) return []
    const words = q.toLowerCase().split(/\s+/).filter(Boolean)
    const list = products.filter((p) => {
      if (cat !== 'All' && categoryOf(p) !== cat) return false
      if (size && !p.inventory?.some((s) => s.size === size && s.in_stock)) return false
      const text = `${p.name} ${p.garment_type} ${p.description} ${p.colors.join(' ')} ${p.search_tags.join(' ')}`.toLowerCase()
      return words.every((w) => text.includes(w))
    })
    if (sort === 'price-asc') list.sort((a, b) => a.price - b.price)
    if (sort === 'price-desc') list.sort((a, b) => b.price - a.price)
    if (sort === 'name') list.sort((a, b) => a.name.localeCompare(b.name))
    return list
  }, [products, q, cat, size, sort])

  if (error) return <p className="status">Couldn't load products: {error}</p>
  if (!products) return <p className="status">Loading products…</p>

  const filtered = q || cat !== 'All' || size

  return (
    <>
      <header className="page-head">
        <span className="eyebrow">The shop</span>
        <h1>All Yale gear</h1>
        <p className="muted">Officially licensed apparel for students, alumni, families and fans.</p>
      </header>

      <div className="filters">
        <input
          type="search"
          className="search"
          placeholder="Search: hockey, Morse, navy, The Game…"
          value={searchText}
          onChange={(e) => {
            setSearchText(e.target.value)
            update('q', e.target.value)
          }}
          aria-label="Search products"
        />
        <select value={size} onChange={(e) => update('size', e.target.value)} aria-label="In stock in size">
          <option value="">Any size</option>
          {SIZES.map((s) => (
            <option key={s} value={s}>
              In stock in {s}
            </option>
          ))}
        </select>
        <select value={sort} onChange={(e) => update('sort', e.target.value)} aria-label="Sort">
          {Object.entries(SORTS).map(([k, label]) => (
            <option key={k} value={k}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <div className="chips" role="group" aria-label="Category">
        {CATEGORIES.map((c) => (
          <button key={c} className={`chip ${c === cat ? 'active' : ''}`} onClick={() => update('cat', c)}>
            {c}
          </button>
        ))}
      </div>

      <p className="muted">
        {visible.length} of {products.length} items
        {filtered && (
          <>
            {' · '}
            <button
              className="text-btn"
              onClick={() => {
                setSearchText('')
                setParams({}, { replace: true })
              }}
            >
              Clear filters
            </button>
          </>
        )}
      </p>

      {visible.length === 0 ? (
        <div className="empty">
          <p>No products match those filters.</p>
          <p className="muted">Try a different word or size, or ask the assistant in the corner for ideas.</p>
        </div>
      ) : (
        <div className="grid">
          {visible.map((p, i) => (
            <ProductTile key={p.product_id} product={p} index={i} />
          ))}
        </div>
      )}
    </>
  )
}
