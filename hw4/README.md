# Campus Customs: Yale Apparel Shop + AI Shopping Assistant

MGT 409 · Homework 4

A storefront for Campus Customs (Yale apparel, 57 Broadway, New Haven) with an AI shopping assistant. Shoppers can browse and filter 102 products, create an account and log in, and chat with a **PydanticAI** agent that looks up live prices and stock, puts matching products on the page as cards, remembers logged-in shoppers, and understands "this item" on a product page.

- **Front end:** React + Vite + TypeScript (`frontend/`)
- **Back end:** FastAPI + PydanticAI agent (`backend/`), model `gpt-5.6-luna` via Portkey
- **Data:** SQLite `data/campus_customs.db` + `data/products/` images (local-only, **not in this repo**)

Full system documentation is in [`output/harness.md`](output/harness.md).

---

## 1. Requirements
- Python 3.10+ (tested on 3.14)
- Node.js 20.19+ or 22.12+ and npm (required by Vite 8; tested on Node 26)
- A Portkey API key (for the chat agent)

## 2. Get the code
```bash
git clone https://github.com/talha1732/mgt409-hw4.git
cd mgt409-hw4          # the project is in the hw4/ folder inside the repo
```
All commands below start from `mgt409-hw4/`.

## 3. Place the data pack
The database and product images aren't committed. Copy the course data pack into `hw4/data/` so it looks like this:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/          # 102 product images referenced by the catalogue
```

On first start the backend adds a `sessions` table for logins and converts the demo account's password hash to the current format, so `test@campuscustoms.yale.edu` / `password` works out of the box. No other setup is needed.

## 4. Add your API key
```bash
cd hw4
cp .env.example .env
# edit .env and set PORTKEY_API_KEY=...
```
The backend looks for `.env` in `hw4/` or any parent folder.

## 5. Run the back end (terminal 1)
```bash
cd hw4
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd backend
uvicorn main:app --reload --port 8000
```
API: `http://localhost:8000` (docs at `/docs`).

## 6. Run the front end (terminal 2)
```bash
cd hw4/frontend
npm install
npm run dev
```
Open **http://localhost:5173**. Vite forwards `/api/*` and `/images/*` to the back end on port 8000, so start the back end first.

**Test login:** `test@campuscustoms.yale.edu` / `password`, or create a new account.

## 7. Things to try
- **Products page:** search "hockey", tap the *Hoodies* chip, choose *In stock in M*.
- **Chat** (bottom right): "What hoodies do you have?" puts product cards on the page.
- On a product page, click **Ask about this item**, then "Is this in stock in M?". If it's sold out you'll get in-stock alternatives.
- Log in, chat, log out, log back in: the assistant remembers the conversation.

---

## Repository layout
```
hw4/
├── AI_prompts.md            # prompts used with the AI coding assistant
├── README.md
├── requirements.txt         # Python deps for the back end
├── .env.example             # placeholder keys only
├── .gitignore               # keeps .env, data/, node_modules/, .venv/ out of git
├── frontend/                # Vite + React + TypeScript app
├── backend/
│   ├── main.py              # FastAPI app: run with `uvicorn main:app --reload --port 8000`
│   ├── agent.py             # agent wiring: model, prompt, tools, validation, audit logging
│   ├── models.py            # Pydantic / PydanticAI structured types
│   ├── tools.py             # read-only tools the agent can call
│   ├── prompts/prompt.md    # system prompt: voice, tool guide, safety rules
│   ├── auth.py              # password hashing (PBKDF2) + sessions
│   ├── guard.py             # masks card numbers / SSNs / passwords before the model sees them
│   └── audit.py             # append-only agent audit trail
└── output/
    ├── harness.md           # how the whole system works
    ├── design.md            # visual design write-up
    ├── usability.md         # usability improvements write-up
    ├── app_check.html       # live-site test report (open in a browser)
    ├── app_check_images/    # screenshots linked from app_check.html
    └── audit_trail.json     # append-only log of agent runs
```

The agent itself is the four files `backend/prompts/prompt.md`, `backend/agent.py`, `backend/tools.py` and `backend/models.py`. `main.py` exposes it through the `/api/chat` route.

## Notes
- **Never commit** `.env`, `data/campus_customs.db` or product images. `.gitignore` already excludes them.
- `output/audit_trail.json` is append-only and grows with every chat turn.
- Only the demo account is converted at startup. The other two seed accounts keep their original hashes (see `output/harness.md` §2).
