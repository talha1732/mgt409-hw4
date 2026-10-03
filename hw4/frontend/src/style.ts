// Small presentation helpers shared by product cards and the product page.

// Catalogue colors are names ("navy blue", "heather gray"); map them to swatch colors.
const SWATCHES: Record<string, string> = {
  'navy blue': '#1c2b4a', navy: '#1c2b4a', 'royal blue': '#2457b8', blue: '#286dc0', 'light blue': '#9cc3ea',
  white: '#ffffff', ivory: '#f8f3e6', cream: '#f3ead2',
  'heather gray': '#b9bdc3', 'light gray': '#d6d8db', gray: '#9aa0a6', 'dark heather gray': '#6f747a',
  'charcoal gray': '#4a4f55', 'heather charcoal gray': '#55595f', 'dark heather charcoal': '#3f4348',
  black: '#16181b', red: '#b31b1b', 'dusty coral': '#d98a7a', yellow: '#f2c230', gold: '#c99a2e', green: '#2f6b3b',
}

export function swatch(color: string): string | undefined {
  return SWATCHES[color.toLowerCase()]
}

export const LOW_STOCK = 20

export function stockBadge(totalStock: number): { label: string; kind: 'sold' | 'low' } | null {
  if (totalStock === 0) return { label: 'Sold out', kind: 'sold' }
  if (totalStock <= LOW_STOCK) return { label: `Only ${totalStock} left`, kind: 'low' }
  return null
}

// Same buckets as the Products page filter, used for the small category label on cards.
export function categoryLabel(garmentType: string, name: string): string {
  const t = `${garmentType} ${name}`.toLowerCase()
  if (t.includes('hood')) return 'Hoodie'
  if (t.includes('quarter') || t.includes('1 4 zip')) return 'Quarter-zip'
  if (t.includes('jacket') || t.includes('fleece')) return 'Jacket'
  if (t.includes('t-shirt') || t.includes('t shirt') || t.includes('tee')) return 'Tee'
  if (t.includes('crew') || t.includes('sweatshirt') || t.includes('mockneck')) return 'Crewneck'
  return t.includes('shirt') ? 'Tee' : 'Apparel'
}
