# Deploy DayTrade Pro — Full Render

Satu URL untuk frontend + backend via Docker.

```
https://daytrade-ihsg.onrender.com
├── /          → React UI
└── /api/*     → FastAPI
```

---

## Langkah Deploy

### Opsi A — Script otomatis (Windows)

```powershell
cd d:\projeg\testing
.\scripts\setup-github.ps1 -Username USERNAME_GITHUB_ANDA
```

Atau double-click `scripts\setup-github.bat`

Script akan:
1. Buka browser ke halaman buat repo GitHub
2. Menunggu Anda klik **Create repository**
3. Push kode otomatis ke GitHub

### Opsi B — Manual

#### 1. Buat repo di GitHub

Buka: https://github.com/new?name=daytrade-ihsg

- **Repository name:** `daytrade-ihsg`
- **Public**
- **Jangan** centang "Add a README file"
- Klik **Create repository**

#### 2. Push kode

```powershell
cd d:\projeg\testing
git remote add origin https://github.com/USERNAME/daytrade-ihsg.git
git branch -M main
git push -u origin main
```

Ganti `USERNAME` dengan username GitHub Anda.

### 3. Deploy di Render

1. Buka [dashboard.render.com](https://dashboard.render.com)
2. **New → Blueprint**
3. Connect repo GitHub → pilih repo ini
4. Klik **Apply** — Render build Docker image (~5–10 menit)
5. App live di URL Render

Tes: `https://YOUR-APP.onrender.com/api/health`

---

## Update

Setiap `git push` ke `main` → Render otomatis redeploy.

---

## Catatan Plan Gratis

- Service **sleep** setelah ~15 menit idle
- Request pertama **~30–60 detik** (cold start)
- Scan 955 saham ~3–5 menit

---

## Dev Lokal

```powershell
# Dev mode (hot reload)
cd backend && venv\Scripts\uvicorn main:app --reload --port 8000
cd frontend && npm run dev

# Production lokal (Docker)
docker build -t daytrade .
docker run -p 8000:8000 daytrade
```

Buka http://localhost:8000
