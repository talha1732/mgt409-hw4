# Campus Customs: Design

**Direction: a collegiate-heritage shop.** The site should feel like walking into a Yale co-op on Broadway, not a generic template: Yale blue on warm ivory, a classic serif, and varsity details (pennants, felt patches, stitching). The goal is to make shoppers feel the pride they're buying into, then make buying easy.

## What I changed and why it helps shoppers stay and buy

| Area | What changed | Why it helps |
|---|---|---|
| **Color** | Yale blue `#00356b` + ivory background, crimson accent (pennant stripe, "Sold out"), gold highlight (main CTA, "Only N left", focus rings). | Feels instantly "Yale" and trustworthy. The accents are reserved for signals (stock, actions), so the eye goes to what matters. |
| **Type** | *Fraunces* serif for headings and prices, *Inter* for body text. Small uppercase "eyebrow" labels (HOODIE, THE SHOP). | Serif headings read heritage and premium, which supports $58–$98 prices. Inter keeps descriptions and forms easy to read. |
| **Brand marks** | A pennant logo in the nav, footer and favicon. The home hero has a felt pennant on a stick that sways gently, plus a "Boola Boola" stamp. | Gives the shop a memorable identity, so it doesn't look like a template. |
| **Announcement ticker** | A slim scrolling bar above the nav: officially licensed, visit 57 Broadway, ask the assistant. It pauses on hover. | Puts trust and service messages on every page without taking space. |
| **Home page** | Hero with two CTAs (Shop the collection / Ask our assistant). "Shop by category" tiles styled as chenille letter patches (H, C, T, Q, J). "Fan favorites" row. A trust strip (licensed · visit the shop · help in seconds). | Shoppers get from landing to products in one click. The patches turn categories into a fun, on-brand choice. Favorites give an easy starting point. |
| **Product cards** (one shared component on Products, Home and chat results) | Category label, serif name, price, **color swatch dots**, stock badges (**"Only 9 left"** in gold, **"Sold out"** in crimson with a grayed image). On hover: the card lifts, the image zooms 6%, and a "View details →" bar slides up. | Shoppers can compare colors and availability without clicking in. Scarcity badges are honest (straight from inventory) and encourage buying. Hover feedback makes the grid feel alive and clickable. |
| **Product page** | Breadcrumbs (Home / Products / Hoodies), a framed image that stays in view while scrolling, color pills with swatches, size tiles (sold-out sizes hatched, low sizes underlined in gold), an "Almost gone in S" note, Ask/Find-similar buttons, and a perks box. | Everything needed to decide is in one view. Sold-out sizes are obvious before anyone asks, and help is one tap away at the moment of decision. |
| **Products page** | Pill-shaped search with an icon, filter chips with an active state, and a page header ("All Yale gear"). | The search-and-filter tools from Problem 9 now look inviting, so shoppers use them. |
| **Chat** | Floating "🐶 Need a hand?" button that pops in after load. The panel slides up, with a bulldog avatar, a pulsing green "Checks live stock · replies in seconds" line and a crimson rule. Chat bubbles with tails, **animated typing dots**, and pill-shaped suggestion chips. Chat results on the page get a gold edge. | The assistant feels like a friendly shop employee, not a support widget. That builds trust in its answers and makes people more likely to ask, and every question it answers is a sale that isn't lost. |
| **Motion** | Page fade-in, staggered card and patch entrances, underline-slide nav links, button lift on hover. **Turned off automatically** for users with "reduce motion" enabled. | Makes the site feel polished and responsive without slowing anyone down, and stays accessible. |
| **Details** | Pinstripe page texture (like a jersey), gold focus rings for keyboard users, a drop cap on About Us, a shimmer skeleton while a product loads, and a styled footer with shop and visit links. Login and sign-up get a blue-topped card. | Small touches add up to "a real store." Keyboard and loading states don't feel broken. |
| **Responsive** | Under 860px: the hero stacks, the product page goes to one column, and the chat button shrinks. | Many students shop on their phones. |

## Fixes found while checking screenshots
- The first hero pennant was a narrow triangle, and "YALE" spilled outside it. I replaced it with a proper horizontal felt pennant with a stick and tassels.
- Guests triggered 12 console 401 errors from the login check. `/api/auth/me` now returns `null` for guests, so there are no false errors.

## How it was checked
Screenshots were taken in headless Chrome for Home, Products, a product page, About, Log in, card hover, the chat typing state, and chat results on the page. Login and logout were run through the restyled form, and the browser console showed no errors. Fonts load (Fraunces confirmed).
