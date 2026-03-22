#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
#  SecureScout — Local Development Setup Script
#  Usage: chmod +x scripts/setup.sh && ./scripts/setup.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}"
echo "  ███████╗███████╗ ██████╗██╗   ██╗██████╗ ███████╗"
echo "  ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔════╝"
echo "  ███████╗█████╗  ██║     ██║   ██║██████╔╝█████╗  "
echo "  ╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██╔══╝  "
echo "  ███████║███████╗╚██████╗╚██████╔╝██║  ██║███████╗"
echo "  ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝"
echo -e "${NC}"
echo -e "${BOLD}  AI Website Security Scanner — Setup${NC}"
echo ""

# ── Check prerequisites ────────────────────────────────────────────────────────
echo -e "${BLUE}▶ Checking prerequisites...${NC}"

check_cmd() {
  if command -v "$1" &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} $1 found ($(command -v $1))"
  else
    echo -e "  ${RED}✗${NC} $1 not found — please install it first"
    exit 1
  fi
}

check_cmd docker
check_cmd "docker compose" 2>/dev/null || check_cmd docker-compose

echo ""

# ── Copy .env if missing ───────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  echo -e "${BLUE}▶ Creating .env from .env.example...${NC}"
  cp .env.example .env
  
  # Generate a random SECRET_KEY
  SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
  sed -i "s/your-super-secret-jwt-key-change-this-in-production/$SECRET/" .env
  
  echo -e "  ${GREEN}✓${NC} .env created"
  echo -e "  ${YELLOW}⚠${NC}  Edit .env and add your OPENAI_API_KEY for AI reports"
else
  echo -e "${GREEN}✓${NC} .env already exists"
fi

echo ""

# ── Build and start ────────────────────────────────────────────────────────────
echo -e "${BLUE}▶ Building and starting Docker services...${NC}"
echo "  This may take a few minutes on first run."
echo ""

docker compose up -d --build

echo ""

# ── Wait for healthy ───────────────────────────────────────────────────────────
echo -e "${BLUE}▶ Waiting for services to be ready...${NC}"
MAX_WAIT=60
COUNT=0
until curl -sf http://localhost/health &>/dev/null; do
  COUNT=$((COUNT + 1))
  if [ $COUNT -gt $MAX_WAIT ]; then
    echo -e "  ${RED}✗${NC} Services did not start in time. Check: docker compose logs"
    exit 1
  fi
  echo -n "."
  sleep 1
done
echo ""

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}  ✓ SecureScout is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Application:${NC}  http://localhost"
echo -e "  ${BOLD}API Docs:${NC}     http://localhost/api/docs"
echo -e "  ${BOLD}Health:${NC}       http://localhost/health"
echo ""
echo -e "  ${YELLOW}Next steps:${NC}"
echo -e "  1. Open http://localhost and create an account"
echo -e "  2. Add OPENAI_API_KEY to .env for AI reports"
echo -e "  3. Add Razorpay keys to .env for payments"
echo -e "  4. Restart after .env changes: docker compose restart backend"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo -e "  docker compose logs -f backend   # Watch backend logs"
echo -e "  docker compose restart backend   # Restart after code changes"
echo -e "  docker compose down              # Stop everything"
echo ""
