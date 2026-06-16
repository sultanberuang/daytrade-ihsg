# DayTrade Pro — Rekomendasi Saham Day Trading IHSG

Aplikasi web untuk menganalisis **seluruh saham terdaftar IHSG** (~955 emiten) berdasarkan indikator teknikal day trading.

## Fitur

- **955 saham IHSG** — seluruh emiten terdaftar di Bursa Efek Indonesia
- **Scan paralel** — analisis teknikal otomatis dengan progress bar
- **Indikator** — RSI, MACD, EMA 9/21, Bollinger Bands, ATR, Relative Volume
- **Scoring 0–100** — sinyal BUY / HOLD / SELL per saham
- **Rencana trading** — Entry, Stop Loss (SL), Take Profit (TP1/TP2), rasio Risk:Reward
- **Analisis berita** — sentimen dari Yahoo Finance & Google News, mempengaruhi skor prediksi
- **Header tabel klik** — sort ascending/descending per kolom
- **Tabel + paginasi** — navigasi 50 saham per halaman
- **Filter & sort** — by sinyal, skor, perubahan %, volume, kode
- **Pencarian** — cari berdasarkan kode atau nama emiten

## Tech Stack

- **Backend:** Python, FastAPI, httpx (Yahoo Finance API)
- **Frontend:** React, Vite, Tailwind CSS

## Cara Menjalankan

### Backend

```powershell
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm run dev
```

Buka http://localhost:5173

## Deploy Online

**Recommended:** Full deploy di [Render.com](https://render.com) — frontend + backend satu URL.

Lihat **[DEPLOY.md](DEPLOY.md)** (gratis, deploy otomatis dari GitHub push).

**Catatan:** Scan pertama kali ~955 saham membutuhkan waktu 2–5 menit. Hasil di-cache selama 15 menit.

## API Endpoints

| Endpoint | Method | Deskripsi |
|----------|--------|-----------|
| `/api/stocks` | GET | Daftar seluruh saham IHSG (955 ticker) |
| `/api/scan` | GET | Hasil analisis dengan paginasi |
| `/api/scan/status` | GET | Progress scan |
| `/api/scan/refresh` | POST | Paksa scan ulang |
| `/api/analyze/{ticker}` | GET | Analisis saham individual |

### Parameter `/api/scan`

- `page` — halaman (default: 1)
- `limit` — per halaman (default: 50, max: 200)
- `action` — filter: BUY, SELL, HOLD
- `q` — cari kode/nama
- `sort` — score, change_pct, volume, code, price, rsi, news_sentiment, name, action
- `order` — asc atau desc
- `refresh` — true untuk scan ulang

## Sumber Data Saham

Daftar ticker IHSG disimpan di `backend/data/ihsg_tickers.json` (955 emiten).
Data harga dari Yahoo Finance (format `.JK`).

Perbarui daftar emiten:
```
POST /api/stocks/refresh-list
```

## Rencana Entry, SL & TP

| Sinyal | Entry | Stop Loss | Take Profit |
|--------|-------|-----------|-------------|
| BUY | Harga / EMA9 | Swing low 5 hari atau 1.5×ATR | TP1: 1.5×ATR, TP2: 2.5×ATR |
| SELL | Harga / EMA9 | Swing high 5 hari atau 1.5×ATR | TP1: 1.5×ATR, TP2: 2.5×ATR |
| HOLD | Harga saat ini | 1×ATR (referensi) | 1×ATR (referensi) |

Setiap saham menampilkan rasio Risk:Reward. Klik baris saham untuk detail lengkap.

## Disclaimer

Aplikasi ini **bukan saran investasi**. Day trading memiliki risiko tinggi.
