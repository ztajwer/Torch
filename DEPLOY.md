# Deploy TORCH live (free)

TORCH is one app: **React UI + FastAPI API** in a single Docker container. Your public URL serves both.

Hash routing (`#/search`) works on static hosts — no special server rules needed.

---

## Option A — Render.com (recommended, free tier)

1. Push this project to **GitHub** (do not commit `.env` — it is gitignored).

2. Sign up at [render.com](https://render.com) → **New** → **Blueprint** → connect the repo.

3. Render reads `render.yaml` and builds the `Dockerfile`.

4. In the Render dashboard, open your service → **Environment** → add:
   - `TORCH_GEMINI_API_KEY` = your key from [Google AI Studio](https://aistudio.google.com/apikey)

5. Click **Deploy**. When finished, open:
   `https://torch-xxxx.onrender.com`

6. First visit after idle sleep may take **30–60 seconds** (free tier cold start).

### Free tier notes

- Service **sleeps** after ~15 minutes without traffic.
- **Disk is ephemeral** — product catalog resets when the service redeploys or restarts. Use **Menu → refresh icon** or run a search to refill.
- Scraping Pakistani stores from Render usually works; if a store blocks cloud IPs, search may return fewer results.

---

## Option B — Railway.app

1. Push to GitHub.
2. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub** → select repo.
3. Railway detects `Dockerfile` automatically.
4. Add variables: `TORCH_GEMINI_API_KEY`, `TORCH_SERVE_STATIC=true`, `TORCH_ENVIRONMENT=production`.
5. Generate a public domain in **Settings → Networking**.

---

## Option C — Run production build on your PC (share on LAN)

```powershell
cd "d:\Zimal Tajwer\Aptech\Vision\TorchLight"
docker build -t torch .
docker run --rm -p 8010:8010 --env-file .env -e TORCH_SERVE_STATIC=true -e PORT=8010 torch
```

Open `http://localhost:8010` on your machine. Others on the same Wi‑Fi can use `http://YOUR-PC-IP:8010` if Windows Firewall allows port 8010.

---

## Option D — Split deploy (advanced)

| Part | Host | Build setting |
|------|------|----------------|
| Frontend | Vercel / Netlify | Root: `frontend`, build: `npm run build`, output: `dist` |
| Backend | Render / Railway | Docker or Python start command |

Set frontend env at build time:

```
VITE_API_BASE=https://your-backend.onrender.com
```

Set backend env:

```
TORCH_CORS_ORIGINS=https://your-frontend.vercel.app
TORCH_SERVE_STATIC=false
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TORCH_GEMINI_API_KEY` | Recommended | AI top-3 rankings |
| `TORCH_GEMINI_MODEL` | No | Default `gemini-2.0-flash` |
| `TORCH_SERVE_STATIC` | Production | `true` when UI is bundled in Docker |
| `TORCH_CORS_ORIGINS` | Split deploy | Comma-separated frontend URLs, or `*` |
| `TORCH_ENVIRONMENT` | No | `production` on live servers |
| `PORT` | Auto | Set by Render/Railway (default `8010`) |

---

## Health check

After deploy, open:

`https://YOUR-URL/health`

Should return `{"status":"ok","environment":"production"}`.

---

## Custom domain (optional)

On Render: **Settings → Custom Domains** → add your domain and follow DNS instructions.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Blank page | Check deploy logs; confirm `TORCH_SERVE_STATIC=true` and build succeeded |
| API errors | Open `/health`; verify `TORCH_GEMINI_API_KEY` if AI fails |
| Slow first load | Free tier cold start — wait and retry |
| Empty catalog | Tap refresh in header or run a product search |
