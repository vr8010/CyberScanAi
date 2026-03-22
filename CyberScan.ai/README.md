# 🛡 SecureScout — AI Website Security Scanner

> **Production-ready SaaS** | FastAPI · React · LangChain · PostgreSQL · Razorpay · Docker

---

## 📁 Complete Project Structure

```
securescout/
├── backend/
│   ├── main.py                         # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic.ini                     # DB migration config
│   ├── alembic/
│   │   └── env.py                      # Alembic async env
│   ├── tests/
│   │   └── test_api.py                 # pytest test suite
│   └── app/
│       ├── __init__.py
│       ├── core/
│       │   ├── config.py               # Pydantic settings (all env vars)
│       │   └── database.py             # Async SQLAlchemy engine + session
│       ├── models/
│       │   ├── models.py               # SQLAlchemy ORM models
│       │   └── schemas.py              # Pydantic request/response schemas
│       ├── auth/
│       │   └── jwt_handler.py          # JWT create/verify + FastAPI deps
│       ├── middleware/
│       │   └── rate_limit.py           # Rate limiting middleware
│       ├── services/
│       │   ├── scanner.py              # Core security scanner engine
│       │   ├── ai_reporter.py          # LangChain + OpenAI report generator
│       │   ├── scan_service.py         # Scan orchestrator (scanner + AI + DB)
│       │   ├── pdf_generator.py        # ReportLab PDF generation
│       │   └── email_service.py        # SMTP email delivery
│       └── routes/
│           ├── auth.py                 # POST /register, /login, GET /me
│           ├── scan.py                 # POST /scan, GET /scan/:id, /history
│           ├── payment.py              # Razorpay subscribe, verify, webhook
│           ├── user.py                 # GET /user/profile, /user/stats
│           └── admin.py                # Admin stats and user management
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── Dockerfile
│   ├── nginx.conf                      # SPA nginx config (inside container)
│   └── src/
│       ├── main.jsx                    # React entry point
│       ├── App.jsx                     # Router + routes
│       ├── index.css                   # Tailwind + global styles
│       ├── store/
│       │   └── authStore.js            # Zustand auth state (persisted)
│       ├── utils/
│       │   └── api.js                  # Axios instance + API helpers
│       ├── pages/
│       │   ├── Landing.jsx             # Public landing page
│       │   ├── Login.jsx               # Login page
│       │   ├── Register.jsx            # Register page
│       │   ├── Dashboard.jsx           # Main dashboard with stats + history
│       │   ├── ScanPage.jsx            # New scan interface
│       │   ├── ScanResult.jsx          # Full scan report viewer
│       │   ├── Pricing.jsx             # Plans + Razorpay checkout
│       │   └── Profile.jsx             # User profile management
│       └── components/
│           ├── dashboard/
│           │   └── DashboardLayout.jsx # Sidebar + layout shell
│           ├── scanner/
│           │   ├── ScanForm.jsx        # URL input + scan trigger
│           │   ├── RiskScoreRing.jsx   # Animated SVG risk score ring
│           │   ├── VulnerabilityCard.jsx # Collapsible vuln details
│           │   ├── FindingsChecklist.jsx # Pass/fail check list
│           │   ├── CheckResultsTable.jsx # Raw findings table
│           │   └── ScanHistoryTable.jsx  # Scan history list
│           └── common/
│               └── StatCard.jsx        # Dashboard stat widget
│
├── nginx/
│   └── nginx.conf                      # Production reverse proxy config
│
├── scripts/
│   └── init.sql                        # DB initialization SQL
│
├── docker-compose.yml                  # Production Docker Compose
├── docker-compose.dev.yml              # Development overrides
├── .env.example                        # All environment variables documented
└── .gitignore
```

---

## 🗄️ Database Schema

```sql
-- users table
CREATE TABLE users (
  id              VARCHAR PRIMARY KEY,        -- UUID
  email           VARCHAR UNIQUE NOT NULL,
  hashed_password VARCHAR NOT NULL,
  full_name       VARCHAR,
  plan            ENUM('free','pro') DEFAULT 'free',
  is_active       BOOLEAN DEFAULT true,
  is_admin        BOOLEAN DEFAULT false,
  is_verified     BOOLEAN DEFAULT false,
  scans_today     INTEGER DEFAULT 0,
  last_scan_date  TIMESTAMPTZ,
  total_scans     INTEGER DEFAULT 0,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ
);

-- scan_results table
CREATE TABLE scan_results (
  id               VARCHAR PRIMARY KEY,       -- UUID
  user_id          VARCHAR REFERENCES users(id) ON DELETE CASCADE,
  target_url       VARCHAR NOT NULL,
  status           ENUM('pending','running','completed','failed'),
  risk_score       FLOAT,                     -- 0–100
  overall_severity ENUM('low','medium','high','critical'),
  summary          TEXT,
  raw_findings     JSONB,                     -- [{check, status, detail}]
  vulnerabilities  JSONB,                     -- [{name, severity, description, recommendation}]
  ai_report        TEXT,                      -- Full markdown AI report
  ssl_valid        BOOLEAN,
  ssl_expiry_days  INTEGER,
  server_header    VARCHAR,
  response_time_ms INTEGER,
  critical_count   INTEGER DEFAULT 0,
  high_count       INTEGER DEFAULT 0,
  medium_count     INTEGER DEFAULT 0,
  low_count        INTEGER DEFAULT 0,
  error_message    TEXT,
  scan_duration_ms INTEGER,
  created_at       TIMESTAMPTZ DEFAULT now(),
  completed_at     TIMESTAMPTZ
);

-- subscriptions table
CREATE TABLE subscriptions (
  id                        VARCHAR PRIMARY KEY,
  user_id                   VARCHAR REFERENCES users(id) ON DELETE CASCADE,
  razorpay_subscription_id  VARCHAR UNIQUE,
  razorpay_plan_id          VARCHAR,
  status                    VARCHAR DEFAULT 'created',
  plan                      ENUM('free','pro'),
  starts_at                 TIMESTAMPTZ,
  ends_at                   TIMESTAMPTZ,
  created_at                TIMESTAMPTZ DEFAULT now()
);

-- payment_logs table
CREATE TABLE payment_logs (
  id                    VARCHAR PRIMARY KEY,
  user_id               VARCHAR REFERENCES users(id),
  razorpay_payment_id   VARCHAR,
  razorpay_order_id     VARCHAR,
  razorpay_signature    VARCHAR,
  amount                INTEGER,       -- In paise
  currency              VARCHAR DEFAULT 'INR',
  status                VARCHAR,
  event_type            VARCHAR,
  payload               JSONB,
  created_at            TIMESTAMPTZ DEFAULT now()
);
```

---

## 🔌 API Endpoints

### Authentication
| Method | Endpoint            | Auth | Description                    |
|--------|---------------------|------|--------------------------------|
| POST   | `/api/auth/register`| ✗    | Register new user              |
| POST   | `/api/auth/login`   | ✗    | Login (returns JWT)            |
| GET    | `/api/auth/me`      | ✓    | Get current user profile       |

### Scanner
| Method | Endpoint               | Auth | Description                        |
|--------|------------------------|------|------------------------------------|
| POST   | `/api/scan/`           | ✓    | Start a new scan (runs + returns)  |
| GET    | `/api/scan/history`    | ✓    | Paginated scan history             |
| GET    | `/api/scan/{id}`       | ✓    | Get full scan result               |
| GET    | `/api/scan/{id}/pdf`   | ✓    | Download PDF report                |
| DELETE | `/api/scan/{id}`       | ✓    | Delete a scan                      |

### Payments
| Method | Endpoint                  | Auth | Description                          |
|--------|---------------------------|------|--------------------------------------|
| GET    | `/api/payment/plans`      | ✗    | Get available plans                  |
| POST   | `/api/payment/subscribe`  | ✓    | Create Razorpay subscription         |
| POST   | `/api/payment/verify`     | ✓    | Verify payment + upgrade plan        |
| POST   | `/api/payment/webhook`    | ✗    | Razorpay webhook handler             |
| GET    | `/api/payment/status`     | ✓    | Get subscription status              |

### User
| Method | Endpoint             | Auth | Description               |
|--------|----------------------|------|---------------------------|
| GET    | `/api/user/profile`  | ✓    | Get user profile          |
| PATCH  | `/api/user/profile`  | ✓    | Update profile            |
| GET    | `/api/user/stats`    | ✓    | Get scan statistics       |

### Admin (admin role required)
| Method | Endpoint                      | Auth  | Description          |
|--------|-------------------------------|-------|----------------------|
| GET    | `/api/admin/stats`            | Admin | Platform statistics  |
| GET    | `/api/admin/users`            | Admin | List all users       |
| PATCH  | `/api/admin/users/{id}/plan`  | Admin | Change user plan     |

### System
| Method | Endpoint   | Auth | Description    |
|--------|------------|------|----------------|
| GET    | `/health`  | ✗    | Health check   |
| GET    | `/api/docs`| ✗    | Swagger UI     |

---

## 🚀 Step-by-Step: Run Locally (Without Docker)

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ running locally
- Redis running locally (optional — used for future Celery tasks)

### Step 1 — Clone and set up environment

```bash
git clone https://github.com/your-org/securescout.git
cd securescout

# Copy env file
cp .env.example .env
# Edit .env — fill in your OPENAI_API_KEY, database credentials, etc.
nano .env
```

### Step 2 — Set up the database

```bash
# Create database (PostgreSQL must be running)
createdb securescout

# Or via psql:
psql -U postgres -c "CREATE DATABASE securescout;"
psql -U postgres -c "CREATE USER securescout WITH PASSWORD 'yourpassword';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE securescout TO securescout;"
```

### Step 3 — Run the backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (tables created automatically on startup)
# Or manually with Alembic:
# alembic upgrade head

# Start the development server
uvicorn main:app --reload --port 8000
```

Backend is now at: http://localhost:8000
Swagger docs at:   http://localhost:8000/api/docs

### Step 4 — Run the frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

Frontend is now at: http://localhost:3000

---

## 🐳 Step-by-Step: Run with Docker (Recommended)

### Step 1 — Prepare environment

```bash
cp .env.example .env
# Edit .env with your values (minimum: OPENAI_API_KEY, SECRET_KEY)
nano .env

# Generate a strong secret key:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 2 — Build and start all services

```bash
# Build images and start everything
docker-compose up -d --build

# Watch logs
docker-compose logs -f

# Check all services are healthy
docker-compose ps
```

Services started:
- **postgres** on port 5432
- **redis** on port 6379
- **backend** on port 8000
- **frontend** (served by nginx inside container)
- **nginx** reverse proxy on port **80**

### Step 3 — Verify everything works

```bash
# Health check
curl http://localhost/health

# Should return:
# {"status":"healthy","version":"1.0.0","service":"SecureScout API"}

# Open in browser
open http://localhost
```

### Step 4 — Run database migrations (if needed)

```bash
# Alembic migrations (tables auto-created on startup, but for future migrations:)
docker-compose exec backend alembic upgrade head
```

### Step 5 — Create an admin user

```bash
# Connect to database
docker-compose exec postgres psql -U securescout securescout

# Update an existing user to admin:
UPDATE users SET is_admin = true, plan = 'pro' WHERE email = 'your@email.com';
\q
```

---

## ☁️ Production Deployment (Ubuntu VPS / DigitalOcean / AWS EC2)

### Step 1 — Provision server

```bash
# Minimum: 2 vCPU, 4GB RAM, 40GB SSD
# OS: Ubuntu 22.04 LTS

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin -y
```

### Step 2 — Clone and configure

```bash
cd /opt
sudo git clone https://github.com/your-org/securescout.git
cd securescout
sudo chown -R $USER:$USER .

# Create production .env
cp .env.example .env
nano .env
# Set: ENVIRONMENT=production, strong SECRET_KEY, real API keys, your domain
```

### Step 3 — Configure SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot -y

# Get certificate (replace yourdomain.com)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certs are at: /etc/letsencrypt/live/yourdomain.com/

# Copy certs to nginx ssl directory
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl/
```

### Step 4 — Update nginx.conf for production

Edit `nginx/nginx.conf`:
- Replace `server_name _;` with `server_name yourdomain.com www.yourdomain.com;`
- Uncomment the HTTP→HTTPS redirect block
- Uncomment and configure the HTTPS server block
- Add your SSL paths

### Step 5 — Deploy

```bash
# Build and start production stack
docker-compose up -d --build

# Run migrations
docker-compose exec backend alembic upgrade head

# Verify
curl https://yourdomain.com/health
```

### Step 6 — Set up auto-renewal for SSL

```bash
# Add crontab entry to renew cert and reload nginx
(crontab -l 2>/dev/null; echo "0 12 * * * certbot renew --quiet && docker-compose -f /opt/securescout/docker-compose.yml exec nginx nginx -s reload") | crontab -
```

### Step 7 — Set up log rotation

```bash
sudo nano /etc/logrotate.d/securescout
```
```
/opt/securescout/nginx_logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    sharedscripts
}
```

### Step 8 — Configure Razorpay Webhook

In Razorpay Dashboard → Settings → Webhooks:
- URL: `https://yourdomain.com/api/payment/webhook`
- Events: `subscription.activated`, `subscription.cancelled`, `subscription.expired`, `payment.captured`

---

## 🧪 Sample Test Data

### Test user credentials
```
Email:    test@example.com
Password: testpass123
Plan:     Free
```

### Test URLs to scan
```
https://example.com          # Minimal headers — good test case
http://neverssl.com          # HTTP only — will show SSL issues
https://badssl.com           # Various SSL issues
https://google.com           # Well-configured — mostly passes
```

### Run the test suite

```bash
cd backend
pip install pytest pytest-asyncio aiosqlite

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --tb=short
```

---

## 💳 Razorpay Setup Guide

### 1. Create an account
- Sign up at https://razorpay.com
- Complete KYC for live payments

### 2. Get API Keys
- Dashboard → Settings → API Keys
- Copy Key ID and Key Secret to `.env`

### 3. Create a Subscription Plan
- Dashboard → Products → Subscriptions → Plans → Create Plan
- Name: `SecureScout Pro`
- Amount: `99900` (₹999 in paise)
- Period: `monthly`
- Copy Plan ID to `RAZORPAY_PLAN_ID_PRO` in `.env`

### 4. Test Mode
- Use `rzp_test_*` keys for testing
- Test card: `4111 1111 1111 1111`, any future date, any CVV

---

## 🤖 OpenAI / LangChain Setup

```bash
# Get API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...

# Recommended models (cost vs quality):
OPENAI_MODEL=gpt-3.5-turbo      # ~$0.001 per report (recommended)
OPENAI_MODEL=gpt-4o-mini        # Better quality, ~$0.002 per report
OPENAI_MODEL=gpt-4              # Best quality, ~$0.05 per report
```

If `OPENAI_API_KEY` is not set, SecureScout falls back to a template-based report — 
all scanning still works, just without AI narrative.

---

## 📊 Monitoring & Operations

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f nginx

# Restart a service
docker-compose restart backend

# Scale backend workers (if needed)
docker-compose up -d --scale backend=2

# Database backup
docker-compose exec postgres pg_dump -U securescout securescout > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T postgres psql -U securescout securescout < backup_20240101.sql

# Check disk usage
docker system df

# Clean up unused images/volumes
docker system prune -f
```

---

## 🔒 Security Hardening Checklist

Before going to production:
- [ ] Set a strong `SECRET_KEY` (32+ random bytes)
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure SSL/HTTPS
- [ ] Remove volume bind mount in production `docker-compose.yml`
- [ ] Disable `/api/docs` in production (comment out in main.py)
- [ ] Configure Razorpay webhook secret verification
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Set firewall rules (only ports 80 and 443 public)
- [ ] Create a non-root database user
- [ ] Enable rate limiting in Nginx

---

## ⚡ Bonus Features — Extension Points

### Scheduled Scans (with Celery)
```python
# Add to services/scheduler.py using APScheduler or Celery beat
# Users can schedule daily/weekly automatic re-scans
```

### Email Reports (already built)
```python
# In scan route, after scan completes:
from app.services.email_service import send_report_email
pdf = generate_pdf_report(scan)
await send_report_email(user.email, user.full_name, scan.target_url, scan.risk_score, pdf, scan.id)
```

### Admin Panel
```
GET  /api/admin/stats    → Platform-wide stats
GET  /api/admin/users    → All users list
PATCH /api/admin/users/{id}/plan → Change user plan
```

---

## 🏗️ Architecture Overview

```
                    ┌──────────────┐
  User Browser ───► │  Nginx :80   │ ◄── SSL termination, rate limiting
                    └──────┬───────┘
                           │
               ┌───────────┴────────────┐
               │                        │
        ┌──────▼──────┐         ┌───────▼──────┐
        │  Frontend   │         │   Backend    │
        │  React SPA  │         │  FastAPI :8000│
        │  (nginx:80) │         │  Gunicorn    │
        └─────────────┘         └──────┬───────┘
                                       │
                          ┌────────────┼───────────┐
                          │            │           │
                   ┌──────▼───┐  ┌─────▼──┐  ┌────▼────┐
                   │PostgreSQL│  │ Redis  │  │ OpenAI  │
                   │  :5432   │  │ :6379  │  │   API   │
                   └──────────┘  └────────┘  └─────────┘
```

---

*SecureScout v1.0.0 — Built with FastAPI, React, LangChain, PostgreSQL, Razorpay, Docker*
