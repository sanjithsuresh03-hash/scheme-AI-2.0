# AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs — Production Deployment Guide
### Display Branding: AI Funding & Scheme Matcher
### Smart India Hackathon: AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs

This document provides complete, production-grade instructions for hosting and operating AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs (AI Funding & Scheme Matcher) across static frontend platforms, Python FastAPI backends, Supabase PostgreSQL, and Google Gemini AI.

---

## 🏗️ 1. Architecture Overview

AI Funding & Scheme Matcher operates under a decoupled, zero-trust affirmative architecture:
- **Frontend:** Semantic HTML5, Vanilla CSS3 (Navy & Teal Design System), Vanilla ES6+ JavaScript. Static assets can be hosted on any CDN or static hosting platform.
- **Backend:** Python 3.10+ FastAPI REST API enforcing Pydantic validations, Bearer token verification, grounded scheme matching, and request size limiting.
- **Database & Auth:** Supabase PostgreSQL with strict Row Level Security (RLS) and Supabase Auth (JWT).
- **AI Scheme Assistant:** Google Gemini API (invoked strictly from the FastAPI backend; keys never exposed to the client).

```
                     +---------------------------------------+
                     |         Web Browser Client            |
                     |  (HTML5 / Vanilla CSS / ES6+ JS)     |
                     +-------------------+-------------------+
                                         |
                       Bearer JWT        | CORS (Allowed Origins)
                                         v
                     +-------------------+-------------------+
                     |         FastAPI Backend Server        |
                     | - Request Body Limiter (1MB Max)      |
                     | - Token Verification (auth.users)     |
                     | - Deterministic Matching Engine       |
                     | - Roadmap & Checklist Persistence     |
                     +---------+-------------------+---------+
                               |                   |
            Private Server     |                   | Grounded Prompt
            PostgREST (RLS)    |                   | (Zero PII)
                               v                   v
                     +---------+---------+   +-----+-----------------+
                     |    Supabase       |   |    Google Gemini      |
                     | PostgreSQL & Auth |   |    Developer API      |
                     +-------------------+   +-----------------------+
```

---

## 🛡️ 2. Security Guarantees & Environmental Hardening

1. **Zero Secret Leakage:**
   - Supabase `service_role` key and `GEMINI_API_KEY` are configured **exclusively on the backend**.
   - Frontend `config.js` accepts only the public Supabase `anon` key.
2. **Environment Isolation for Demo Tokens:**
   - In `development` mode, `mock-demo-token-*` allows local hackathon evaluation without external cloud dependencies.
   - In `production` mode (`ENVIRONMENT=production`), mock tokens are **strictly rejected with HTTP 401 Unauthorized**.
3. **Payload Size Guard:**
   - Backend enforces `MAX_REQUEST_BODY_BYTES = 1048576` (1 MB) via HTTP middleware, mitigating Denial of Service (DoS) attacks via oversized payloads.
4. **Row Level Security (RLS):**
   - All database tables (`profiles`, `projects`, `project_stages`, `conversations`, `chat_messages`, `user_scheme_roadmap_progress`, `user_scheme_checklist_progress`) enforce `auth.uid() = user_id` on SELECT, INSERT, UPDATE, and DELETE.
5. **Zero Aadhaar Policy:**
   - No Aadhaar numbers, biometric data, or identity documents are collected or stored.

---

## ⚙️ 3. Environment Variables Configuration

### Backend Environment (`backend/.env`)

Create your `.env` file from `backend/.env.example`. **Never commit `.env` to Git.**

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `SUPABASE_URL` | Supabase project REST URL | `https://xyzcompany.supabase.co` |
| `SUPABASE_ANON_KEY` | Public Supabase anon key | `eyJhbGciOiJIUzI1Ni...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Administrative backend key (keep secret!) | `eyJhbGciOiJIUzI1Ni...` |
| `SUPABASE_JWT_SECRET` | Secret for offline token validation | *(from Supabase JWT settings)* |
| `FRONTEND_ORIGINS` | Comma-separated allowed CORS origins | `https://schemeai.yourdomain.com,https://your-app.vercel.app` |
| `ENVIRONMENT` | Runtime environment (`development`, `production`) | `production` |
| `HOST` | Bind address for API server | `0.0.0.0` (Production) / `127.0.0.1` (Local) |
| `PORT` | Listening port | `8000` |
| `GEMINI_API_KEY` | Google AI Studio Gemini API Key | *(from aistudio.google.com)* |
| `GEMINI_MODEL` | Grounded model name | `gemini-2.5-flash` |

### Frontend Configuration (`frontend/js/config.js`)

In production, you can configure frontend settings without editing source files via:
1. **Window Runtime Object (Recommended for CDN/HTML injection):**
   ```html
   <script>
     window.SCHEMEAI_BACKEND_URL = "https://api.schemeai.yourdomain.com";
     window.SCHEMEAI_SUPABASE_URL = "https://xyzcompany.supabase.co";
     window.SCHEMEAI_SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1Ni...";
   </script>
   ```
2. **Reverse Proxy (Nginx / Vercel rewrites):**
   Route `/api/*` requests directly to the FastAPI server. In this setup, `DEFAULT_BACKEND_API_URL` defaults to `window.location.origin`.
3. **Local Storage Override:**
   Developers can customize backend URLs directly from browser devtools:
   ```javascript
   localStorage.setItem('schemeai_backend_url', 'https://api.yourdomain.com');
   ```

---

## 🗄️ 4. Supabase Database & Auth Production Setup

1. **Create Supabase Production Project:**
   - Log in to [Supabase Console](https://supabase.com).
   - Create a project (e.g., `schemeai-prod-db`) in the desired region (e.g., `ap-south-1` Mumbai).
2. **Execute Database Schema:**
   - In Supabase SQL Editor, run `supabase/schema.sql`.
   - This sets up:
     - `public.profiles`
     - `public.projects` and `public.project_stages`
     - `public.conversations` and `public.chat_messages`
     - `public.user_scheme_roadmap_progress`
     - `public.user_scheme_checklist_progress`
     - All Row Level Security (RLS) policies and `handle_updated_at` triggers.
3. **Configure Authentication Settings in Supabase:**
   - **Site URL:** Set to your production frontend domain (e.g. `https://schemeai.yourdomain.com`).
   - **Redirect URLs:** Add:
     - `https://schemeai.yourdomain.com/dashboard.html`
     - `https://schemeai.yourdomain.com/login.html`
   - **Email Confirmations:** Enable or disable email confirmation based on deployment requirements. (When disabled, users can immediately log in upon registration).

---

## 🚀 5. Deployment Instructions

### Option A: Static Frontend Hosting (Vercel / Netlify / Cloudflare Pages)

1. **Deploy Frontend Directory:**
   - Configure build settings:
     - Root directory: `frontend`
     - Build command: *(None / leave empty)*
     - Output directory: `.`
2. **Vercel Reverse Proxy Configuration (`vercel.json` in `frontend/`):**
   ```json
   {
     "rewrites": [
       { "source": "/api/:path*", "destination": "https://api.schemeai.yourdomain.com/api/:path*" }
     ]
   }
   ```

### Option B: FastAPI Backend Hosting (Render / Railway / Fly.io / VPS)

1. **Docker Container Deployment (Recommended):**
   Create a `Dockerfile` in `backend/`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt gunicorn uvicorn
   COPY . .
   EXPOSE 8000
   CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
   ```
2. **Direct Linux Systemd Service:**
   ```ini
   [Unit]
   Description=SchemeAI FastAPI Backend
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/schemeai/backend
   EnvironmentFile=/var/www/schemeai/backend/.env
   ExecStart=/var/www/schemeai/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. **Configure CORS:**
   Ensure `FRONTEND_ORIGINS` in `.env` includes your deployed frontend domain.

---

## 🧪 6. Testing & Operational Verification

### Automated Test Runner Commands (Local & CI/CD)

```powershell
# 1. Run Complete Integration & Security Test Suite (FastAPI TestClient)
pytest tests\test_phase7_integration_security.py -v

# 2. Run Deterministic Matching Engine Scenarios
python tests\test_phase4_matching.py

# 3. Run Frontend DOM Integrity Tests
node tests\test_phase4_dashboard_dom.js
node tests\test_phase5_chatbot_dom.js
node tests\test_phase6_roadmap_dom.js
```

### Live Server Integration Test Commands (With backend running on port 8000)

```powershell
# Start backend
python -m uvicorn backend.main:app --port 8000

# In another terminal, run end-to-end integration tests:
python tests\test_phase4_api.py
python tests\test_phase5_chat_api.py
python tests\test_phase6_roadmap_api.py
```
