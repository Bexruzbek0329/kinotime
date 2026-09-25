# 🎬 KinoBot — Premium Telegram Movie Bot

Premium Telegram kino bot — zamonaviy UX, to'liq admin panel, PostgreSQL va Redis bilan.

## 📋 Tarkib

```
kinobot/
├── bot/                    # Telegram bot (aiogram 3.x)
│   ├── handlers/           # Message & callback handlers
│   ├── keyboards/          # Reply & Inline keyboards
│   ├── middlewares/        # DB, User, Subscription, RateLimit
│   ├── services/           # Business logic
│   ├── states/             # FSM states
│   └── utils/              # Formatting, stickers, deep links
├── database/               # SQLAlchemy models & repositories
│   ├── models/             # 13 ORM modeli
│   ├── repositories/       # Async CRUD layers
│   └── migrations/         # Alembic async migrations
├── admin/                  # FastAPI admin backend
│   ├── api/routes/         # 9 ta REST endpoint gruhi
│   ├── services/           # JWT auth service
│   └── schemas/            # Pydantic schemas
├── frontend/               # Next.js 14 admin panel
│   └── src/
│       ├── app/            # Page components (App Router)
│       ├── components/     # UI & Layout components
│       ├── services/       # API client
│       └── types/          # TypeScript types
├── scripts/                # Setup & utility scripts
├── docker-compose.yml      # Full stack orchestration
├── Dockerfile.bot          # Bot container
├── Dockerfile.api          # API container
├── .env.example            # Environment template
└── requirements.txt        # Python dependencies
```

---

## 🚀 Tez Ishga Tushirish

### 1. Muhit sozlash

```bash
cd kinobot
cp .env.example .env
# .env faylini o'zingizning ma'lumotlaringiz bilan to'ldiring
```

### 2. `.env` faylini to'ldirish

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
BOT_USERNAME=your_bot_username
ADMIN_IDS=your_telegram_id

POSTGRES_PASSWORD=strong_password_here
REDIS_PASSWORD=redis_password_here
ADMIN_SECRET_KEY=min_32_chars_secret_key_here_change_this
```

### 3. Docker bilan ishga tushirish

```bash
docker-compose up -d
```

### 4. Superadmin yaratish

```bash
docker-compose exec bot python scripts/create_superadmin.py
```

Yoki local:
```bash
python scripts/create_superadmin.py
```

### 5. Botni sozlash

1. `@BotFather` da bot yarating va `BOT_TOKEN` ni oling
2. Bot `@YourChannel` ga admin qilib qo'shing (kanal obunasi uchun)
3. Admin panelga kiring: http://localhost:3000/login

---

## 🌐 Servislar

| Servis | URL |
|--------|-----|
| 🤖 Telegram Bot | Telegram'da ishlaydi |
| ⚙️ Admin Panel | http://localhost:3000 |
| 📡 API Docs | http://localhost:8000/api/docs (debug=True) |
| 🐘 PostgreSQL | localhost:5432 |
| 🔴 Redis | localhost:6379 |

---

## 🤖 Bot Funksiyalari

### Foydalanuvchi uchun:
- **🎬 Kino** — Katalog (Premyeralar, Top)
- **🔎 Qidirish** — Nom yoki kod bo'yicha qidirish
- **🔥 Premyeralar** — Yangi kinolar
- **⭐ Top kinolar** — Eng yuqori reytingli
- **👤 Profil** — Ko'rishlar, baholar, sevimlilar
- **ℹ️ Yordam** — Qo'llanma

### Kino card funksiyalari:
- 🎥 Sifat tanlash (360p → 4K)
- ❤️ Sevimlilarga qo'shish/olib tashlash
- ⭐ 1-5 yulduz baho berish
- 📤 Ulashish (deep link)

---

## 🛡️ Admin Panel

### Sahifalar:
- **Dashboard** — Real-time statistika + grafiklar
- **Kinolar** — CRUD, qidirish, filter, status boshqaruv
- **Kino qo'shish** — Wizard: ma'lumotlar + video qo'shish
- **Foydalanuvchilar** — Ko'rish, bloklash/blokdan chiqarish
- **Reklama** — Barcha userlarga xabar + progress tracker
- **Kanallar** — Majburiy obuna kanallarini boshqarish
- **Statistika** — Grafiklar, top kinolar, qidiruvlar
- **Sozlamalar** — Bot matnlari + sticker file_id lari
- **Adminlar** — Admin CRUD (superadmin only)
- **Loglar** — Audit log tarixi

---

## 📦 Kino qo'shish jarayoni

1. Admin panelda **"Kino qo'shish"** bosing
2. Ma'lumotlarni to'ldiring (nom, yil, janr, tavsif, IMDb)
3. Poster uchun — Telegram botga rasm yuboring, `file_id` ni nusxa oling
4. Video qo'shish — Telegram botga video yuboring, `file_id` ni nusxa oling
5. Sifat (360p/480p/720p/1080p/4K) bilan belgilang
6. **"Saqlash"** → Status: `Qoralama` → `Nashr`

---

## 🔧 Local Development

```bash
# Python virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# PostgreSQL va Redis ni ishga tushiring (Docker):
docker-compose up postgres redis -d

# Database yaratish:
python -c "import asyncio; from database.engine import engine; from database.models.base import Base; asyncio.run(engine.begin().__aenter__().__class__.run_sync.__func__(asyncio.run(engine.begin().__aenter__()), Base.metadata.create_all))"

# Bot ishga tushirish:
python main_bot.py

# API ishga tushirish (boshqa terminal):
uvicorn main_api:app --reload --port 8000

# Frontend (boshqa terminal):
cd frontend
npm install
npm run dev
```

---

## 📊 Database Sxemasi

| Jadval | Tavsif |
|--------|--------|
| `users` | Bot foydalanuvchilari |
| `movies` | Kinolar (kod, poster, ma'lumotlar) |
| `movie_videos` | Video fayllar (quality + file_id) |
| `genres` + `movie_genres` | Janrlar (M2M) |
| `favorites` | Sevimlilar (user ↔ movie) |
| `ratings` | Baholar 1-5 |
| `views` | Ko'rishlar logi |
| `searches` | Qidiruvlar logi |
| `channels` | Majburiy obuna kanallari |
| `settings` | Bot sozlamalari (texts, stickers) |
| `admins` | Admin paneli foydalanuvchilari |
| `audit_logs` | Admin amallar tarixi |

---

## 🔒 Xavfsizlik

- Bot token `.env` da saqlanadi — source code'da yo'q
- Admin panel JWT authentication (24h token)
- bcrypt password hashing
- Redis rate limiting (30 req/60s per user)
- SQL injection himoyasi (ORM)
- CORS sozlamalari
- Audit logging — barcha admin amallari saqlanadi

---

## 📝 Muhit o'zgaruvchilari

| O'zgaruvchi | Tavsif |
|-------------|--------|
| `BOT_TOKEN` | BotFather'dan olingan token |
| `BOT_USERNAME` | Bot username (@ siz) |
| `ADMIN_IDS` | Telegram admin ID lari (vergul bilan) |
| `DATABASE_URL` | PostgreSQL async URL |
| `REDIS_URL` | Redis URL |
| `ADMIN_SECRET_KEY` | JWT secret (min 32 char) |
| `CORS_ORIGINS` | Frontend URL lari |
| `DEBUG` | True/False |
| `MOVIES_PER_PAGE` | Bir sahifadagi kinolar soni |

---

## 🏗️ Texnologiyalar

**Backend:**
- Python 3.12 + aiogram 3.x
- FastAPI + uvicorn
- SQLAlchemy 2.x (async)
- Alembic (migrations)
- Redis (FSM + rate limiting + cache)
- PostgreSQL 16

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- TanStack Query
- Recharts (grafiklar)
- Lucide Icons

**Infrastructure:**
- Docker + Docker Compose
- Nginx (reverse proxy)

---

## 🤝 Yordam

Muammo yuzaga kelsa:
1. Log fayllarini tekshiring: `docker-compose logs bot`
2. Database ulanishini tekshiring: `docker-compose ps`
3. Admin loglarni ko'ring: Admin Panel → Loglar

---

*KinoBot v1.0.0 — Production Ready*
