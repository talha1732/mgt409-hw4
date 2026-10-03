// Thin scrolling ticker above the nav, like a campus shop's window banner.
const ITEMS = [
  'Officially licensed Yale apparel',
  'Visit us at 57 Broadway, New Haven',
  'Residential college, school & varsity collections',
  'Questions? Ask our assistant, bottom right',
  'Boola Boola',
]

export default function AnnouncementBar() {
  // The list is rendered twice so the CSS marquee can loop seamlessly.
  const row = [...ITEMS, ...ITEMS]
  return (
    <div className="announce" aria-label="Store announcements">
      <div className="announce-track">
        {row.map((t, i) => (
          <span key={i} aria-hidden={i >= ITEMS.length}>
            {t} <em>✦</em>
          </span>
        ))}
      </div>
    </div>
  )
}
