# 🌐 Alwaysdata.com va GitHub orqali KinoBot'ni O'rnatish Qo'llanmasi

Ushbu qo'llanma orqali siz **KinoBot** Telegram boti va uning **Admin API / Frontendini** Alwaysdata bulut xizmatiga va GitHub'ga qadamma-qadam ulab ishga tushirishingiz mumkin.

---

## 🐙 1-BOSQICH: GitHub'ga Yuklash (Kodni bulutga joylash)

Lokal kompyuteringizdagi barcha kodlar allaqachon tayyorlangan va birinchi `commit` qilingan.

1. [github.com](https://github.com/) saytiga kiring va akkauntingizga kiring.
2. O'ng yuqoridagi **"+"** tugmasini bosib **"New repository"** ni tanlang:
   - **Repository name:** `kinobot`
   - **Private** (yopiq) ni tanlang (kodlaringiz va ma'lumotlaringiz xavfsiz bo'lishi uchun).
   - Pastdagi **"Create repository"** tugmasini bosing.
3. Ochilgan sahifadagi repozitoriy havolasini nusxalang (masalan: `https://github.com/SIZNING_USERNAME/kinobot.git`).
4. Kompyuteringizdagi terminalda quyidagi buyruqlarni kiriting:
   ```bash
   git remote add origin https://github.com/SIZNING_USERNAME/kinobot.git
   git push -u origin main
   ```
   *(GitHub login va parolingizni yoki Personal Access Token so'rasa kiriting)*.

---

## ☁️ 2-BOSQICH: Alwaysdata.com Sozlamalari

### 1. PostgreSQL Ma'lumotlar Bazasini Ochish
1. [alwaysdata.com](https://www.alwaysdata.com/) boshqaruv paneliga kiring.
2. Chap menyudan: **Databases > PostgreSQL** bo'limiga kiring.
3. Yangi baza yarating:
   - **Database name:** `kinobot_db` (yoki `USERNAME_kinobot`)
4. **Users** yorlig'iga o'ting va yangi foydalanuvchi qo'shing:
   - **Username:** `kinouser`
   - **Password:** Kuchli parol yozing (masalan: `MySuperPass2026`)
   - Barcha huquqlarni bering.
5. Ma'lumotlar bazasi host manzili odatda: `postgresql-USERNAME.alwaysdata.net` ko'rinishida bo'ladi.

---

### 2. SSH orqali Alwaysdata Serveriga Ulanish
1. Alwaysdata panelida: **Remote access > SSH** bo'limiga kiring va SSH yoqilganligini tekshiring.
2. Kompyuteringiz terminalida (PowerShell):
   ```bash
   ssh USERNAME@ssh-USERNAME.alwaysdata.net
   ```
   *(Alwaysdata hisobingiz parolini kiriting)*.

3. Serverda loyihani yuklab oling:
   ```bash
   git clone https://github.com/SIZNING_USERNAME/kinobot.git
   cd kinobot
   ```

4. Python virtual muhitini yaratib kutubxonalarni o'rnating:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. `.env` faylini yarating va sozlang:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Quyidagilarni o'z ma'lumotlaringiz bilan to'ldiring:
   ```env
   BOT_TOKEN=8982675694:AAExampleTokenHere...
   BOT_USERNAME=KINOMEDIA_RASMIY_bot
   DATABASE_URL=postgresql+asyncpg://kinouser:MySuperPass2026@postgresql-USERNAME.alwaysdata.net:5432/kinobot_db
   REDIS_URL=redis://localhost:6379/0
   ```
   *(Eslatma: Agar Redis o'rnatilmagan bo'lsa, bot avtomatik xotirada (MemoryStorage) xatosiz ishlayveradi!)*.
   *Saqlash uchun: `Ctrl + O` -> `Enter` -> `Ctrl + X`*.

6. Ma'lumotlar bazasini birinchi marta ishga tushirish (jadvallarni yaratish):
   ```bash
   python main_bot.py
   ```
   Konsolda `database_initialized` va `bot_starting` yozuvini ko'rsangiz, `Ctrl + C` bosib to'xtating (chunki uni fonda Alwaysdata servisi sifatida yoqamiz).

---

### 3. Telegram Botni 24/7 Fondagi Servis Qilib Yoqish
Bot server o'chib-yonsa ham to'xtamasligi uchun Alwaysdata'ning **Services** mexanizmi ishlatiladi:

1. Alwaysdata panelida chap menyudan: **Advanced > Services** bo'limiga o'ting.
2. **"Add a service"** tugmasini bosing:
   - **Name:** `kinobot`
   - **Command:** `/home/USERNAME/kinobot/venv/bin/python main_bot.py`
   - **Working directory:** `/home/USERNAME/kinobot`
   - **Enabled:** Ha (belgilang)
   - **Auto-restart:** Always (agar to'xtasa avtomatik qayta yoqilsin)
3. **"Submit"** bosing.
✅ **Bot 24/7 uzluksiz rejimda ishga tushdi!**

---

### 4. Admin Panel API (FastAPI) ni Alwaysdata'da Yoqish
1. Alwaysdata panelida chap menyudan: **Web > Sites** bo'limiga o'ting.
2. **"Add a site"** bosing:
   - **Name:** `KinoBot API`
   - **Domain:** `api.USERNAME.alwaysdata.net` (yoki `USERNAME.alwaysdata.net`)
   - **Type:** **User program**
   - **Command:** `/home/USERNAME/kinobot/venv/bin/uvicorn main_api:app --host 0.0.0.0 --port $PORT`
   - **Working directory:** `/home/USERNAME/kinobot`
3. **"Submit"** bosing.
✅ Endi sizning API manzilingiz: `https://USERNAME.alwaysdata.net` orqali ishlaydi!

---

### 5. Next.js Admin Panelini Joylash (Eng Tavsiya Etilgan Usul)

> [!TIP]
> Alwaysdata'ning bepul (Free) rejasida disk hajmi 100 MB bo'lib, Next.js `node_modules` (200MB+) ni bepul Alwaysdata'ga to'g'ridan-to'g'ri o'rnatganda xotira to'lib qolishi mumkin.
> Shu sababli, butun dunyo ishlab chiquvchilari Next.js frontendini **Vercel** (Next.js yaratuvchilarining 100% bepul hostingi) ga joylashtirishadi!

**Vercel'ga 1 daqiqada ulash:**
1. [vercel.com](https://vercel.com/) ga kiring va GitHub profilingiz orqali kiring.
2. **"Add New Project"** bosing va GitHub'dagi `kinobot` repozitoriyangizni tanlang.
3. Sozlamalarda:
   - **Root Directory:** `frontend` papkasini tanlang (`Edit` -> `frontend`).
   - **Environment Variables** bo'limiga:
     - Key: `NEXT_PUBLIC_API_URL`
     - Value: `https://USERNAME.alwaysdata.net` (Alwaysdata'dagi API manzilingiz)
4. **"Deploy"** tugmasini bosing!
5. 30 soniyada sizga `https://kinobot-admin.vercel.app` kabi chiroyli, bepul va xavfsiz domen beradi.

---

## 🏆 Natija
- 🤖 **Telegram Bot:** Alwaysdata'da 24/7 to'xtovsiz ishlaydi (`Services`).
- 🗄️ **Baza (PostgreSQL):** Alwaysdata'ning xavfsiz managed bazasida saqlanadi.
- ⚙️ **API (FastAPI):** Alwaysdata'ning `https://USERNAME.alwaysdata.net` manzilida ishlaydi.
- 💻 **Admin Panel (Next.js):** Vercel'da (yoki Alwaysdata'da) yuqori tezlikda ishlaydi.
