# 🚀 KinoBot & Admin Panel — Serverga O'rnatish va Ishlatish Qo'llanmasi

Ushbu qo'llanma orqali siz **KinoBot** Telegram boti va uning **Next.js Admin Panelini** istalgan VPS serverga (Ubuntu / Debian) 5 daqiqa ichida 100% tayyor holatda o'rnatishingiz va ishlatishingiz mumkin.

---

## 📋 1. Server Talablari (VPS Requirments)

Bot va Admin Panel barcha xizmatlari (PostgreSQL, Redis, FastAPI, Next.js, Nginx, Aiogram 3) bilan Docker konteynerlarida ishlaydi.

* **Operatsion tizim:** Ubuntu 22.04 LTS yoki Ubuntu 24.04 LTS (yoki Debian 11/12)
* **Operativ xotira (RAM):** Kamida 1 GB (Tavsiya etiladi: 2 GB)
* **Protsessor (CPU):** 1 yoki 2 vCPU
* **Disk:** Kamida 15–20 GB SSD
* **Tavsiya etilgan hostinglar:** 
  - [Hetzner](https://www.hetzner.com/) (eng arzon va kuchli, oyiga ~€3.8 - €5)
  - [VDSina](https://vdsina.ru/)
  - [DigitalOcean](https://www.digitalocean.com/)
  - [Timeweb Cloud](https://timeweb.cloud/)

---

## 🛠️ 2. Bosqichma-bosqich O'rnatish (5 Daqiqada)

### 1-qadam: Serverga SSH orqali ulaning
Windows kompyuteringizda **PowerShell** yoki **Terminal**ni oching va serveringizga ulaning:
```bash
ssh root@SERVER_IP_MANZILI
```
*(Server provayderingiz bergan parolni kiriting)*

---

### 2-qadam: Bot fayllarini serverga nusxalang

Fayllarni serverga o'tkazishning 2 xil oson usuli bor:

#### A-usul (FileZilla yoki WinSCP dasturi orqali - Eng osoni):
1. [FileZilla](https://filezilla-project.org/) yoki [WinSCP](https://winscp.net/) dasturini oching.
2. `Host:` serveringiz IP manzili, `Username:` root, `Password:` server paroli, `Port:` 22.
3. Kompyuteringizdagi `kinobot` papkasini serveringizdagi `/root/kinobot` manziliga tashlang.
4. Server konsolida papkaga kiring:
   ```bash
   cd /root/kinobot
   ```

#### B-usul (Git orqali):
Agar kodingiz GitHub/GitLab'da bo'lsa:
```bash
git clone SIZNING_REPOZITORIY_LINKINGIZ kinobot
cd kinobot
```

---

### 3-qadam: .env faylini sozlang
Serverda loyiha papkasi ichida:
```bash
cp .env.example .env
nano .env
```
Faqat quyidagi 2 ta qatorni o'zingizning botingiz ma'lumotlari bilan to'ldiring:
```env
BOT_TOKEN=8982675694:AAExampleTokenHere...
BOT_USERNAME=KINOMEDIA_RASMIY_bot
```
*Saqlash uchun: `Ctrl + O`, tasdiqlash uchun `Enter`, chiqish uchun `Ctrl + X` bosing.*

---

### 4-qadam: 1-Bosish bilan avtomatik o'rnatish (1-Click Deploy)

Loyiha ichidagi tayyor avtomatik skriptga ruxsat bering va ishga tushiring:
```bash
chmod +x deploy.sh
./deploy.sh
```

**Ushbu skript nimalarni avtomatik bajaradi?**
1. Docker va Docker Compose o'rnatilganini tekshiradi (bo'lmasa avtomatik o'rnatadi).
2. Xavfsiz JWT Secret Key yaratadi.
3. PostgreSQL, Redis, FastAPI backend, Next.js Admin Panel va Nginx konteynerlarini yig'adi.
4. Ma'lumotlar bazasini va jadvallarni avtomatik yaratadi.
5. Standart **Superadmin** hisobini yaratadi.
6. Serveringiz IP manzilini aniqlab, ekranga tayyor havolani chiqaradi!

---

## 🖥️ 3. Admin Panelni Serverda Qanday Ishlatasiz?

Skript ishini yakunlagach, brauzeringizni oching:

1. Brauzer qidiruv qatoriga serveringiz IP manzilini yozing:
   ```
   http://SERVER_IP
   ```
   *(Masalan: `http://194.163.150.25`)*
2. Login oynasi ochiladi:
   - **Foydalanuvchi nomi (Username):** `admin`
   - **Parol (Password):** `admin123`
3. Tizimga muvaffaqiyatli kirasiz!

> [!IMPORTANT]
> Admin panelga kirganingizdan so'ng, xavfsizlik uchun darhol **Adminlar** bo'limiga o'ting va `admin123` parolini o'zingizning shaxsiy kuchli parolingizga o'zgartiring!

---

## 📱 4. Telefondan Admin Panelga Kirish

Admin panel to'liq mobil moslashuvchan (Responsive Web App).
Siz istalgan vaqtda o'z smartfoningiz (iPhone / Android) brauzeridan `http://SERVER_IP` manziliga kirib:
* Yangi premyera filmlar yoki serial epizodlarini yuklashingiz;
* Barcha a'zolarga reklama yoki xabarnoma yuborishingiz;
* Statistika va ko'rishlar sonini kuzatishingiz mumkin.

---

## 📢 5. Reklama Tizimidan Foydalanish

Admin panelning **"Reklama Markazi"** (`/broadcast`) bo'limi orqali:
1. **Ommaviy Xabarnoma (Broadcast):**
   - **Targeting tanlang:** Barcha a'zolar, oxirgi 30 kunda faol bo'lganlar, yoki **Adminga sinov** (xabar avval sizning shaxsiy Telegramingizga keladi).
   - **Rasm yoki Video** file_id sini qo'ying.
   - **🔘 Inline URL tugmalar:** Masalan: `[🔥 Kanalimizga ulanish | https://t.me/kanal]` tugmasini qo'shing.
   - **📌 Chatga qadash (Pin):** Foydalanuvchi chatiga xabarni qadab qo'yadi.
   - **Avtomatik Bloklanganlarni tozalash:** Agar a'zo botni bloklagan bo'lsa, tizim uni avtomatik aniqlab bazada belgilab qo'yadi.
2. **Doimiy Homiy (Kino va Serial ostidagi Reklama):**
   - "Doimiy Homiy" bo'limida homiylikni yoqing.
   - Har safar botdan kino yoki serial qismi yuklanganda, video ostiga avtomatik homiy havolasi va tugmasi joylanadi.

---

## 🌐 6. O'z Domeningizni Ulash va Bepul SSL (HTTPS) O'rnatish (Ixtiyoriy)

Agar IP o'rniga o'z domeningizdan (masalan: `admin.kinolarolami.uz`) foydalanmoqchi bo'lsangiz:

1. Domen sozlamalaringizda (DNS) yangi **A-record** ochib, serveringiz `SERVER_IP` sini ko'rsating.
2. Serverda Certbot orqali bepul SSL sertifikat oling:
   ```bash
   apt-get install -y certbot
   certbot certonly --standalone -d admin.kinolarolami.uz
   ```
3. Endi admin panelingizga xavfsiz `https://admin.kinolarolami.uz` orqali kirishingiz mumkin bo'ladi.

---

## ⚙️ 7. Serverdagi Foydali Buyruqlar

Serverda bot holatini tekshirish va boshqarish:

| Amal | Buyruq |
| :--- | :--- |
| **Bot loglarini jonli kuzatish** | `docker compose logs -f bot` |
| **Admin API loglarini ko'rish** | `docker compose logs -f admin_api` |
| **Konteynerlar holatini tekshirish** | `docker compose ps` |
| **Barcha xizmatlarni qayta yoqish** | `docker compose restart` |
| **Barcha xizmatlarni to'xtatish** | `docker compose down` |
| **Kodni yangilab qayta ishga tushirish** | `docker compose up -d --build` |

---

✅ **Bot va Admin Panelingiz serverda 24/7 uzluksiz ishlashga to'liq tayyor!**
