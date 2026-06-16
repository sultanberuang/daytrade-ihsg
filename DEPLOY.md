# Deploy DayTrade Pro — Tanpa Kartu Kredit

Render Blueprint sering meminta kartu kredit. Gunakan **Hugging Face Spaces** (gratis, tanpa kartu).

```
https://USERNAME-daytrade-ihsg.hf.space
├── /          → React UI
└── /api/*     → FastAPI
```

---

## Hugging Face Spaces (Recommended)

### 1. Buat akun Hugging Face

Daftar gratis: [huggingface.co/join](https://huggingface.co/join) — **tanpa kartu kredit**.

### 2. Buat Space baru

1. Buka [huggingface.co/new-space](https://huggingface.co/new-space)
2. Isi:
   | Field | Value |
   |-------|-------|
   | Space name | `daytrade-ihsg` |
   | SDK | **Docker** |
   | Visibility | Public |
3. Klik **Create Space**

### 3. Push kode ke Space

Di PowerShell (ganti `USERNAME` dengan username Hugging Face Anda):

```powershell
cd d:\projeg\testing
git remote add space https://huggingface.co/spaces/USERNAME/daytrade-ihsg
git push space main
```

Saat diminta login, gunakan **Access Token** Hugging Face:
- [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- Create token → permission **Write**
- Username: `USERNAME`
- Password: paste token

### 4. Tunggu build

Space → tab **Logs** → tunggu `Application startup complete` (~5–10 menit).

App live di:
```
https://USERNAME-daytrade-ihsg.hf.space
```

Tes: `https://USERNAME-daytrade-ihsg.hf.space/api/health`

---

## Update Aplikasi

```powershell
git push origin main    # GitHub
git push space main     # Hugging Face (redeploy otomatis)
```

---

## Catatan Plan Gratis HF

| | |
|---|---|
| **Biaya** | Gratis, tanpa kartu kredit |
| **Sleep** | Tidur setelah ~1 jam idle |
| **Cold start** | ~30 detik saat bangun |
| **Scan 955 saham** | ~3–5 menit |

---

## Alternatif Lain (Tanpa Kartu)

| Platform | URL | Catatan |
|----------|-----|---------|
| **Hugging Face Spaces** | hf.space | ✅ Recommended, Docker |
| **PythonAnywhere** | pythonanywhere.com | Free tier, manual setup |
| **GitHub Pages** | github.io | Frontend saja, perlu backend terpisah |

---

## Render (Butuh Kartu Kredit)

Render free tier kadang bisa lewat **New → Web Service** (bukan Blueprint), tapi tetap sering minta verifikasi kartu.

Jika punya kartu nanti:
1. [dashboard.render.com](https://dashboard.render.com) → **New → Web Service**
2. Connect repo `sultanberuang/daytrade-ihsg`
3. Runtime: **Docker**

---

## Dev Lokal

```powershell
cd backend && venv\Scripts\uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

Buka http://localhost:5173
