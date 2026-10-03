import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type Product } from '../api'
import { askAssistant } from '../chatEvents'
import { categoryLabel, stockBadge, swatch } from '../style'

const CATEGORY_FILTER: Record<string, string> = {
  Hoodie: 'Hoodies',
  Crewneck: 'Crewnecks',
  Tee: 'T-shirts & tops',
  'Quarter-zip': 'Quarter-zips',
  Jacket: 'Jackets & fleece',
}

export default function ProductDetail() {
  const { id = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setProduct(null)
    setError('')
    fetchProduct(id).then(setProduct).catch((e) => setError(String(e)))
  }, [id])

  if (error) return <p className="status">Couldn't load this product: {error}</p>
  if (!product) return <div className="detail skeleton" aria-label="Loading" />

  const category = categoryLabel(product.garment_type, product.name)
  const badge = stockBadge(product.total_stock)
  const inStock = product.inventory?.filter((s) => s.in_stock) ?? []
  const lowSizes = inStock.filter((s) => s.quantity <= 3)

  return (
    <>
      <nav className="crumbs" aria-label="Breadcrumb">
        <Link to="/">Home</Link>
        <span>/</span>
        <Link to="/products">Products</Link>
        {CATEGORY_FILTER[category] && (
          <>
            <span>/</span>
            <Link to={`/products?cat=${encodeURIComponent(CATEGORY_FILTER[category])}`}>
              {CATEGORY_FILTER[category]}
            </Link>
          </>
        )}
      </nav>

      <div className="detail">
        <div className="detail-media">
          <img src={product.image_url} alt={product.name} />
          {badge && <span className={`badge ${badge.kind}`}>{badge.label}</span>}
        </div>

        <div className="detail-info">
          <span className="eyebrow">{category} · Officially licensed</span>
          <h1>{product.name}</h1>
          <p className="price big">{formatPrice(product.price)}</p>
          <p className="lede">{product.description}</p>

          <h4>Colors</h4>
          <div className="color-list">
            {product.colors.map((c) => (
              <span key={c} className="color-pill">
                {swatch(c) && <span className="dot" style={{ background: swatch(c) }} />}
                {c}
              </span>
            ))}
          </div>

          <h4>
            Sizes <small className="muted">· {inStock.length} of 6 in stock</small>
          </h4>
          <div className="sizes">
            {product.inventory?.map((s) => (
              <span
                key={s.size}
                className={`size ${s.in_stock ? '' : 'out'} ${s.in_stock && s.quantity <= 3 ? 'low' : ''}`}
                title={s.in_stock ? `${s.quantity} in stock` : 'Out of stock'}
              >
                {s.size}
                <small>{s.in_stock ? `${s.quantity} left` : 'Sold out'}</small>
              </span>
            ))}
          </div>
          {product.total_stock === 0 && <p className="oos">Out of stock in all sizes</p>}
          {lowSizes.length > 0 && (
            <p className="hurry">⏳ Almost gone in {lowSizes.map((s) => s.size).join(', ')}</p>
          )}

          <div className="detail-actions">
            <button className="btn" onClick={() => askAssistant()}>
              💬 Ask about this item
            </button>
            <button className="btn secondary" onClick={() => askAssistant('Show me similar items')}>
              Find similar items
            </button>
          </div>

          <ul className="perks">
            <li>✦ Officially licensed Yale merchandise</li>
            <li>⌂ See it in person at 57 Broadway, New Haven</li>
            <li>💬 Not sure about fit? Our assistant can help pick a size</li>
          </ul>
        </div>
      </div>
    </>
  )
}
