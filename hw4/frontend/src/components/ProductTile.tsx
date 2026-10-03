import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, shortDescription } from '../api'
import { categoryLabel, stockBadge, swatch } from '../style'

export interface TileProduct {
  product_id: string
  name: string
  garment_type: string
  price: number
  image_url: string
  description: string
  total_stock: number
  colors?: string[]
}

// One product card, used on the Products page, the home page and the chat results panel.
export default function ProductTile({
  product: p,
  index = 0,
  onClick,
}: {
  product: TileProduct
  index?: number
  onClick?: () => void
}) {
  const badge = stockBadge(p.total_stock)
  const swatches = (p.colors ?? []).map((c) => ({ c, hex: swatch(c) })).filter((s) => s.hex)

  return (
    <Link
      to={`/products/${p.product_id}`}
      className={`card ${badge?.kind === 'sold' ? 'is-sold' : ''}`}
      style={{ '--i': Math.min(index, 12) } as CSSProperties}
      onClick={onClick}
    >
      <div className="card-media">
        <img src={p.image_url} alt={p.name} loading="lazy" />
        {badge && <span className={`badge ${badge.kind}`}>{badge.label}</span>}
        <span className="card-cta">View details →</span>
      </div>
      <div className="card-body">
        <span className="eyebrow">{categoryLabel(p.garment_type, p.name)}</span>
        <h3>{p.name}</h3>
        <p className="muted desc">{shortDescription(p.description, 90)}</p>
        <div className="card-foot">
          <span className="price">{formatPrice(p.price)}</span>
          {swatches.length > 0 && (
            <span className="swatches" aria-label={`Colors: ${p.colors!.join(', ')}`}>
              {swatches.slice(0, 4).map((s) => (
                <span key={s.c} className="dot" style={{ background: s.hex }} title={s.c} />
              ))}
              {swatches.length > 4 && <span className="more">+{swatches.length - 4}</span>}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
