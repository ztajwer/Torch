## TORCH — Shop smarter in Pakistan

Type a product name → TORCH searches **Pakistani e-commerce sites** → **Gemini AI** picks **1st, 2nd, 3rd** best buys (price + quality) → **Browse all** to compare every listing.

### Quick start (Windows)

1. **One-time setup**
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   cd ..
   copy .env.example .env
   # Edit .env and add your TORCH_GEMINI_API_KEY from https://aistudio.google.com/apikey
   cd frontend
   npm install
   ```

2. **Run everything**
   ```powershell
   cd ..
   .\start.ps1
   ```

3. Open **http://127.0.0.1:5173** → search e.g. `iphone`, `samsung`, `laptop` → see **Top 3 recommendations** and **Browse all**.

### Pakistani stores searched

| Store | Site |
|-------|------|
| PriceOye | [priceoye.pk](https://priceoye.pk/) |
| Daraz | [daraz.pk](https://www.daraz.pk/) |
| Telemart | [telemart.pk](https://www.telemart.pk/) |
| Mega.pk | [mega.pk](https://www.mega.pk/) |
| Shophive | [shophive.com](https://www.shophive.com/) |

Search results only show products from these Pakistani websites (no demo/fake stores).

### Gemini API key

Create `.env` in the project root (see `.env.example`):

```
TORCH_GEMINI_API_KEY=your_key_here
TORCH_GEMINI_MODEL=gemini-2.0-flash
```

Never commit `.env` or share your API key in chat. If a key was exposed, **rotate it** in Google AI Studio.

If Gemini quota is exceeded, TORCH falls back to smart rule-based rankings (still shows 1st / 2nd / 3rd).

### Manual start

**Backend** (port **8010**):
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

**Frontend**:
```powershell
cd frontend
npm run dev
```

### Project layout

- `backend/` — FastAPI, Pakistani scrapers, Gemini advisor
- `frontend/` — React UI (search + browse catalog)
- `data/` — `products.json` (auto-created)
- `start.ps1` — starts backend (8010) + frontend (5173)

### Tech stack

Python · FastAPI · httpx · Google Gemini · React · Vite · Tailwind

### Go live (free hosting)

See **[DEPLOY.md](DEPLOY.md)** for step-by-step instructions (Render, Railway, or Docker).

Quick path: push to GitHub → [Render Blueprint](https://render.com) → add `TORCH_GEMINI_API_KEY` → get a public `https://….onrender.com` URL.
