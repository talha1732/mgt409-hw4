# Campus Customs: Usability Improvements

Four improvements: two on the front end, two in the agent/backend. Each one says what was added, why it helps a Campus Customs shopper or the business, and how to see it in the running app (`http://localhost:5173`).

---

## Front end

### 1. Search, category filters and sorting on the Products page

**What I added**
- A search box that matches product names, descriptions, colors and tags (e.g. "hockey", "Morse", "navy", "The Game").
- Category chips: **All · T-shirts & tops · Hoodies · Crewnecks · Quarter-zips · Jackets & fleece**. The database's `garment_type` values are messy (22 variants like "pullover hoodie", "hoodie", "hooded sweatshirt"), so they're grouped into 5 shopper-friendly buckets. All 102 products land in one.
- An **"In stock in [size]"** filter that hides items sold out in the shopper's size.
- Sort by **Featured, Price low→high, Price high→low, Name A–Z**.
- A live "N of 102 items" count, a **Clear filters** link, and a friendly empty state when nothing matches.
- Filters are saved in the URL (e.g. `/products?cat=Hoodies&q=hockey&size=M`), so a filtered view can be bookmarked, shared or reopened with the back button.

**Why it helps**
- **Shoppers:** 102 products in one long grid is hard to browse. A parent looking for "a hoodie in M" can now get there in two clicks instead of scrolling past 75 shirts and crewnecks. The size filter stops shoppers from clicking into items they can't buy, which is frustrating since 145 of the 612 size/stock rows are 0.
- **Business:** faster discovery means more items viewed and more sales. Shareable filter links are handy for staff or social posts ("all our Morse College gear").

**Where to see it:** Products page. Try the Hoodies chip, type "hockey", and pick "In stock in M": 1 result, because the Ice Hockey hoodie is sold out in M.

### 2. Suggested questions in the chat + "Ask about this item"

**What I added**
- One-tap suggestion chips above the chat input:
  - On most pages: *What hoodies do you have? · Gift ideas under $40 · Show me Morse College gear*
  - On a product page: *Is this in stock in M? · What colors does this come in? · Show me similar items*. These use the page context from Problem 8, so "this" means the product being viewed.
- On every product page, two buttons under the sizes: **💬 Ask about this item** opens the chat, and **Find similar items** opens it and asks for alternatives.
- When the agent answers about the product that's already open, the page no longer pops up a duplicate one-card results panel.

**Why it helps**
- **Shoppers:** many people don't know what a shopping chatbot can do, or don't want to type. The chips show what to ask and answer it in one tap. The product-page buttons put help right where the buying decision happens.
- **Business:** more shoppers use the assistant, which answers stock and size questions that would otherwise become abandoned carts or calls to the store.

**Where to see it:** open any product page and click **Ask about this item**, then tap *What colors does this come in?*. Or open the chat on the home page to see the general chips.

---

## Agent / backend

### 3. New agent tool: `find_similar_products` (no dead ends on out of stock)

**What I added**
- A new tool in `backend/tools.py`: `find_similar_products(product_id, size?)` returns up to 4 **in-stock** alternatives (in the requested size, if given). It ranks by:
  - same kind of garment (same buckets as the Products page filter),
  - shared themes from the tags (sport, college, family, graphic), ignoring generic tags like "Yale",
  - similar price.
- A return type `SimilarProducts` in `backend/models.py`.
- A prompt rule in `backend/prompts/prompt.md`: when a size or item is out of stock, say so clearly, then call `find_similar_products` and show the alternatives as cards on the page.

**Why it helps**
- **Shoppers:** before, "Is the Ice Hockey hoodie in M?" got "No, it's out of stock in M." Now the agent says so and offers four $68 hoodies that *are* in stock in M, shown as clickable cards.
- **Business:** an out-of-stock answer is where sales are lost. Offering in-stock alternatives keeps the shopper buying. It's also more accurate than letting the model guess at alternatives, because every suggestion is checked against live inventory in code.

**Where to see it:** open the Ice Hockey Left Chest Hoodie page, open chat, tap *Is this in stock in M?*. Or on the Yale Mom Crewneck page, click **Find similar items** (suggests the Yale Cousin, Grandpa, Dad and Golf crewnecks).

### 4. Sensitive-data guard (card numbers, SSNs, passwords)

**What I added**
- `backend/guard.py`, which runs in plain Python **before** a chat message reaches the AI provider or the database:
  - **Card numbers:** 13–19 digits (spaces/dashes allowed) that pass the Luhn checksum all real cards use, so order numbers and phone numbers aren't flagged.
  - **US Social Security numbers:** `123-45-6789` format.
  - **Typed passwords:** "my password is …", "password: …", "pwd=…". A question like "what's your password policy?" is left alone.
- Masked text is what the agent sees and what's saved in `chat_messages`, e.g. "My card is [card number removed]". Guests' browser-sent history is masked too.
- The shopper's reply starts with a clear notice: "🔒 For your safety I removed a card number and a password from your message. It wasn't sent to our assistant or saved. Please never share payment details or passwords in chat."

**Why it helps**
- **Shoppers:** people do paste card numbers into chatbots ("can I just pay here?"). This keeps that data from being stored in our database or sent to a third-party AI provider, and teaches them not to do it.
- **Business:** storing card numbers would put the shop in scope for PCI compliance, and leaked SSNs or passwords are a serious liability. The guard is enforced in code, so it works even if the model ignores its prompt, unlike the "never ask for passwords" prompt rule alone. It also saves a little cost, since nothing is sent to the model that shouldn't be.

**Where to see it:** in the chat, type "Can I just pay here? My card is 4111 1111 1111 1111 and my password is Bulldog2026!". (4111 1111 1111 1111 is a standard test card number, not a real card.) The reply starts with the 🔒 notice. Logged in, the saved history shows the masked text.

---

## Testing summary

| # | Check | Result |
|---|---|---|
| 1 | Hoodies chip | 27 items |
| 1 | + search "hockey" | 2 |
| 1 | + "In stock in M" | 1 (Ice Hockey hoodie has M=0) |
| 1 | URL after filtering | `/products?cat=Hoodies&q=hockey&size=M` |
| 1 | Open `/products?cat=Crewnecks&sort=price-desc` | 29 crewnecks, sorted high→low |
| 1 | Search with no matches | Empty state shown |
| 1 | Clear filters | Back to 102, search box emptied |
| 1 | Category coverage | All 102 products in a category (27 tees, 29 crewnecks, 27 hoodies, 11 quarter-zips, 8 jackets) |
| 2 | "Ask about this item" on the Saybrook tee | Chat opens with the 3 product chips |
| 2 | Tap "What colors…?" | Answered for the Saybrook tee |
| 2 | Home page chat | Shows the 3 general chips |
| 3 | "Is this in stock in M?" on the Ice Hockey hoodie | "Out of stock in M", lists in-stock sizes, plus 4 similar hoodies in stock in M as cards |
| 3 | "Show me similar items" on Yale Mom crewneck | Yale Cousin, Grandpa, Golf and Dad crewnecks as cards |
| 4 | Unit tests | Card and SSN masked; password masked; order number, phone number and "password policy" left alone |
| 4 | Live, logged in, card + password in a message | 🔒 notice; DB stores only the masked text; original digits found 0 times in the DB and 0 times in the server log |

Two bugs found and fixed during testing:
- The Crewnecks filter was empty at first, because "sweat**shirt**" matched the T-shirt rule. Fixed by checking crewneck/sweatshirt before the generic "shirt" rule.
- Fast typing in the search box dropped characters. Fixed by keeping the box's own text in local state and updating the URL from the latest filters.
