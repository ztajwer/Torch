# 5-minute presentation — no Render, no card

Render is **not** needed for a classroom demo. Use **your laptop** (or a USB copy of this folder).

## Best plan (recommended)

| When | What |
|------|------|
| **Tonight / before you leave** | On your PC, in this folder: `.\present-build.ps1` (5–10 min once) |
| **At the venue** | Plug **your laptop** into the projector → `.\present.ps1` → browser opens in **~30 seconds** |
| **During talk** | Open http://127.0.0.1:8010 — search `iphone` or `laptop`, show Top 3 + chat |

**Do not** set up Python on someone else’s laptop during a 5-minute slot — that will eat your whole presentation.

---

## At the venue (30 seconds)

```powershell
cd "D:\Zimal Tajwer\Aptech\Vision\Torch"
.\present.ps1
```

Browser opens **http://127.0.0.1:8010** — one address, UI + API together.

---

## If you must use another laptop

1. Copy the **whole Torch folder** to a USB (include `backend\.venv`, `backend\static`, `frontend\node_modules` after `present-build.ps1`).
2. On their PC: install **Python 3.12+** only if USB copy has no `.venv` (slow — avoid if possible).
3. Run `.\present.ps1` from the USB path.

Still faster: **present from your laptop** and only use theirs as a screen (HDMI / casting).

---

## Optional: public link (another device on internet)

After `.\present.ps1` is running, in a **second** terminal:

```powershell
.\present.ps1 -Tunnel
```

Or:

```powershell
npx --yes localtunnel --port 8010
```

Share the `https://....` URL. Needs internet; first load may take a few seconds.

---

## 5-minute talk script (suggestion)

| Time | Show |
|------|------|
| 0:00 | Home → type **iphone** → **Analyze Now** |
| 1:30 | Top 3 AI picks + **Browse all** |
| 3:00 | **Ask TORCH** chat — one product question |
| 4:00 | **Compare** or second search (**laptop**) |
| 4:45 | “Searches Daraz, PriceOye, Telemart, Mega.pk — PKR only” |

---

## If something breaks

- Blank page → run `.\present-build.ps1` again, then `.\present.ps1`
- Chat works but “AI unavailable” → normal without a fresh Gemini key; catalog answers still work
- Firewall → use http://127.0.0.1:8010 on the **same** machine that runs `present.ps1`
