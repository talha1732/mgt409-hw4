import { useEffect, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import { askAssistant } from '../chatEvents'
import HeroPennant from '../components/HeroPennant'
import ProductTile from '../components/ProductTile'

// Hand-picked crowd-pleasers; any that are missing are filled from the catalogue.
const FAVORITES = [
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'district-vit-crewneck-vintage-bulldog',
  'yale-mom-crewneck',
]

const CATEGORIES = [
  { cat: 'Hoodies', label: 'Hoodies', icon: 'H', note: 'Game-day warmth' },
  { cat: 'Crewnecks', label: 'Crewnecks', icon: 'C', note: 'Colleges & classics' },
  { cat: 'T-shirts & tops', label: 'Tees', icon: 'T', note: 'From $32' },
  { cat: 'Quarter-zips', label: 'Quarter-zips', icon: 'Q', note: 'Schools & colleges' },
  { cat: 'Jackets & fleece', label: 'Jackets', icon: 'J', note: 'Fleece & full-zips' },
]

export default function Home() {
  const [favorites, setFavorites] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then((all) => {
        const picked = FAVORITES.map((id) => all.find((p) => p.product_id === id)).filter(Boolean) as Product[]
        const rest = all.filter((p) => !picked.includes(p) && p.total_stock > 0)
        setFavorites([...picked, ...rest].slice(0, 4))
      })
      .catch(() => setFavorites([]))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow light">New Haven · 57 Broadway</span>
          <h1>
            Wear your <em>Bulldog</em> pride.
          </h1>
          <p>
            Officially licensed Yale gear for students, alumni, families and everyone who cheers for the Blue,
            from residential college crests to varsity hoodies.
          </p>
          <div className="hero-ctas">
            <Link to="/products" className="btn gold">
              Shop the collection
            </Link>
            <button className="btn ghost" onClick={() => askAssistant()}>
              💬 Ask our assistant
            </button>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="hero-pennant">
            <HeroPennant />
          </div>
          <span className="hero-stamp">Boola Boola</span>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Shop by category</h2>
          <Link to="/products" className="see-all">
            See everything →
          </Link>
        </div>
        <div className="patches">
          {CATEGORIES.map((c, i) => (
            <Link
              key={c.cat}
              to={`/products?cat=${encodeURIComponent(c.cat)}`}
              className="patch"
              style={{ '--i': i } as CSSProperties}
            >
              <span className="patch-letter">{c.icon}</span>
              <strong>{c.label}</strong>
              <small>{c.note}</small>
            </Link>
          ))}
        </div>
      </section>

      {favorites.length > 0 && (
        <section className="section">
          <div className="section-head">
            <h2>Fan favorites</h2>
            <Link to="/products" className="see-all">
              Shop all 102 →
            </Link>
          </div>
          <div className="grid">
            {favorites.map((p, i) => (
              <ProductTile key={p.product_id} product={p} index={i} />
            ))}
          </div>
        </section>
      )}

      <section className="trust">
        <div>
          <span className="trust-icon">✦</span>
          <strong>Officially licensed</strong>
          <p>Real Yale marks, from crests to the vintage bulldog.</p>
        </div>
        <div>
          <span className="trust-icon">⌂</span>
          <strong>Visit the shop</strong>
          <p>57 Broadway, steps from Old Campus.</p>
        </div>
        <div>
          <span className="trust-icon">💬</span>
          <strong>Help in seconds</strong>
          <p>Our assistant checks live stock, sizes and colors.</p>
        </div>
      </section>
    </>
  )
}
