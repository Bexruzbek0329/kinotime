#!/usr/bin/env bash
# ==============================================================================
# KinoBot & Admin Panel — 1-Click Server Deployment Script (Ubuntu / Debian / Linux)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}  🎬 KINOBOT & ADMIN PANEL — SERVERGA O'RNATISH (DEPLOYMENT)    ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 1. Check Docker installation
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}[!] Docker topilmadi. Docker avtomatik o'rnatilmoqda...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}[✓] Docker muvaffaqiyatli o'rnatildi!${NC}"
else
    echo -e "${GREEN}[✓] Docker mavjud.${NC}"
fi

# 2. Check Docker Compose
DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        echo -e "${YELLOW}[!] Docker Compose plugin o'rnatilmoqda...${NC}"
        apt-get update && apt-get install -y docker-compose-plugin
    fi
fi
echo -e "${GREEN}[✓] Docker Compose buyrug'i: ${DOCKER_COMPOSE}${NC}"

# 3. Check .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}[!] .env fayli topilmadi. .env.example dan nusxalanmoqda...${NC}"
    cp .env.example .env

    # Generate random secret key
    RANDOM_SECRET=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32 ; echo '')
    sed -i "s/your_super_secret_jwt_key_min_32_chars/$RANDOM_SECRET/g" .env
    echo -e "${GREEN}[✓] Yangi xavfsiz JWT Secret Key yaratildi.${NC}"

    echo -e "${RED}[MUHIM!] Iltimos, .env faylini ochib BOT_TOKEN va BOT_USERNAME ni kiriting:${NC}"
    echo -e "  nano .env"
    echo -e "Keyin ushbu skriptni qayta ishga tushiring: ./deploy.sh"
    exit 1
fi

# 4. Verify BOT_TOKEN is configured
if grep -q "your_bot_token_here" .env; then
    echo -e "${RED}[XATO!] .env faylida BOT_TOKEN kiritilmagan!${NC}"
    echo -e "Iltimos, 'nano .env' buyrug'i orqali @BotFather dan olingan tokenni kiriting."
    exit 1
fi

# 5. Build and launch containers
echo -e "${BLUE}[*] Barcha konteynerlar yig'ilmoqda va ishga tushirilmoqda...${NC}"
$DOCKER_COMPOSE up -d --build

# 6. Determine Server IP
SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  🎉 KINOBOT VA ADMIN PANEL TAYYOR VA ISHGA TUSHDI!             ${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo -e "  🌐 ${BLUE}Admin Panel Havolasi:${NC} http://${SERVER_IP}"
echo -e "  👤 ${BLUE}Standart Login:${NC}       admin"
echo -e "  🔑 ${BLUE}Standart Parol:${NC}       admin123"
echo -e "  🤖 ${BLUE}Telegram Bot:${NC}         Ishlamoqda (Polling rejimida)"
echo ""
echo -e "${YELLOW}Maslahat:${NC} Admin panelga kirgach, 'Adminlar' bo'limidan 'admin123' parolini o'zgartiring!"
echo ""
echo -e "${BLUE}Foydali buyruqlar:${NC}"
echo -e "  - Bot loglarini ko'rish:          ${DOCKER_COMPOSE} logs -f bot"
echo -e "  - API loglarini ko'rish:          ${DOCKER_COMPOSE} logs -f admin_api"
echo -e "  - Hammasini to'xtatish:           ${DOCKER_COMPOSE} down"
echo -e "  - Qayta ishga tushirish:          ${DOCKER_COMPOSE} restart"
echo -e "${GREEN}================================================================${NC}"
