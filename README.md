# AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs
### Official Display Name: AI Funding & Scheme Matcher
### Smart India Hackathon (SIH) Project • SIH 2024 Finalist Solution

---

## 🚀 Official Project Overview

**AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs** (compact branding: **AI Funding & Scheme Matcher**) is an affirmative entrepreneurship platform designed to empower marginalized founders across India (**Scheduled Castes [SC], Scheduled Tribes [ST], Backward Classes [BC], Most Backward Classes [MBC], Women, and First-Generation Founders**) by eliminating information asymmetry in accessing Central & State Government funding, grants, and subsidies.

### Tech Stack (Strictly Followed)
- **Frontend:** Semantic HTML5, Vanilla CSS3 (custom Navy-Blue & Teal design system), Vanilla JavaScript (ES6+).
- **Backend:** Python FastAPI with Pydantic validation, httpx, and PyJWT.
- **Database:** Supabase PostgreSQL with Row Level Security (RLS).
- **Authentication:** Supabase Auth (Email & Password, Session management, Password Reset).
- **Future Chatbot (Phase 2):** Google Gemini API (strictly invoked from Python backend only; never exposed to browser).
- **IDE:** Antigravity IDE.

> **Zero-Leakage Security Guarantee:** No backend secrets, Supabase `service_role` keys, or Gemini API keys are exposed to the browser. Only the public Supabase `anon` key is permitted in frontend config.

---

## 📁 Project Structure

```
SchemeAI/
├── frontend/
│   ├── index.html              # Landing page with scheme catalog & SIH intro
│   ├── login.html              # Sign-in and password reset
│   ├── register.html           # 3-step registration form with demo OTP
│   ├── dashboard.html          # Authenticated entrepreneur dashboard
│   ├── css/
│   │   └── style.css           # Bespoke Navy & Teal modern design system
│   └── js/
│       ├── config.js           # Supabase URL & Anon Key config with guards
│       ├── supabase-client.js  # Supabase JS SDK client + mock demo fallback
│       ├── auth.js             # Supabase Auth wrapper with route guards & toasts
│       ├── register.js         # Form validation & profile persistence logic
│       ├── login.js            # Sign-in controller with demo account prefill
│       └── dashboard.js        # Protected route, FastAPI Bearer auth & profile
├── backend/
│   ├── __init__.py             # Python package marker
│   ├── main.py                 # FastAPI backend with /api/health & /api/profile/me
│   ├── requirements.txt        # Python dependency specifications
│   └── .env.example            # Environment variables template
├── supabase/
│   └── schema.sql              # PostgreSQL schema, RLS policies & triggers
├── .gitignore                  # Git exclusions for Python, secrets, and IDEs
└── README.md                   # Complete Windows setup and operating guide
```

---

## 🛡️ Security & Regulatory Compliance

1. **Row Level Security (RLS):**
   - The `public.profiles` PostgreSQL table is protected by four strict RLS policies (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).
   - Every policy enforces `auth.uid() = id`. A user can only access and modify their own record.
2. **Cryptographic Token Verification:**
   - The FastAPI backend endpoint `GET /api/profile/me` requires `Authorization: Bearer <access_token>`.
   - The backend directly derives the entrepreneur's `user_id` from Supabase Auth verification. It **never** trusts arbitrary user IDs supplied in query parameters or request bodies.
3. **Zero Aadhaar Policy:**
   - In accordance with UIDAI privacy guidelines, **no Aadhaar numbers or identity document files are requested or stored** in AI Funding & Scheme Matcher.
4. **Mock OTP Disclaimer:**
   - The mobile verification modal is explicitly labeled:
     `[DEMO ONLY] Mock SMS Verification for Hackathon Demonstration. Does not verify real mobile ownership.`

---

## 🛠️ Step-by-Step Setup Guide (Windows)

### Prerequisites
- **Python 3.10+** (Tested with Python 3.13)
- **Supabase Account** ([supabase.com](https://supabase.com))
- Any modern web browser (Edge, Chrome, Firefox)

---

### Step 1: Supabase Database & Auth Setup

1. Log in to [Supabase](https://supabase.com) and create a new project (e.g., `schemeai-db`).
2. Go to the **SQL Editor** in the left sidebar.
3. Open `supabase/schema.sql` from this repository, paste the contents into the SQL Editor, and click **Run**.
   - This creates `public.profiles` linked to `auth.users(id)`.
   - Enables Row Level Security (RLS).
   - Adds the `handle_updated_at()` trigger.
4. Retrieve your API credentials:
   - Navigate to **Project Settings** → **API**.
   - Copy **Project URL**.
   - Copy **Project API keys**:
     - `anon` / `public` (for frontend and backend).
     - `service_role` (optional, for backend server only — keep secret!).

---

### Step 2: Configure Backend (FastAPI)

1. Open PowerShell and navigate to the `backend/` directory:
   ```powershell
   cd "backend"
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(If script execution is restricted, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

3. Install required Python packages:
   ```powershell
   pip install -r requirements.txt
   ```

4. Create your `.env` file from `.env.example`:
   ```powershell
   Copy-Item .env.example .env
   ```

5. Edit `.env` with your Supabase values:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOi...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...
   FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000
   PORT=8000
   HOST=127.0.0.1
   ```

6. Start the FastAPI development server:
   ```powershell
   python -m uvicorn main:app --reload --port 8000
   ```
   The backend will be running at:
   - API Root: `http://127.0.0.1:8000/`
   - Health Check: `http://127.0.0.1:8000/api/health`
   - Interactive Swagger Docs: `http://127.0.0.1:8000/docs`

---

### Step 3: Configure Frontend

1. Open `frontend/js/config.js` in your editor.
2. Update `DEFAULT_SUPABASE_URL` and `DEFAULT_SUPABASE_ANON_KEY` with your project keys:
   ```javascript
   const DEFAULT_SUPABASE_URL = 'https://your-project-id.supabase.co';
   const DEFAULT_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
   ```
   *(Note: AI Funding & Scheme Matcher includes an instant in-memory Demo Fallback Mode so that judges can test registration and dashboard immediately even before adding remote Supabase keys!)*

---

### Step 4: Run the Web Application

In a new PowerShell window, serve the `frontend/` folder:

```powershell
cd "frontend"
python -m http.server 3000
```

Open your browser and navigate to:
👉 **`http://localhost:3000`**

---

## 🧪 Testing Phase 1 Functionality

| Test Case | How to Test | Expected Result |
| :--- | :--- | :--- |
| **API Health Check** | Navigate to `http://127.0.0.1:8000/api/health` | Returns HTTP 200 with JSON `status: ok` and version `1.0.0` |
| **Landing Page** | Open `http://localhost:3000/index.html` | Displays hero section, metrics strip, schemes catalog, and navigation |
| **Registration Form** | Open `register.html` and complete Steps 1–3 | Validates inputs, shows password checklist, pops up Mock OTP demo modal, saves profile into `public.profiles` |
| **Email Confirmation** | If enabled in Supabase Auth | Displays informational modal instructing user to check inbox before login |
| **Sign In** | Open `login.html` and submit credentials | Authenticates via Supabase Auth, handles errors cleanly, redirects to dashboard |
| **Demo Quick Fill** | Click `⚡ Quick-Fill Demo Account` on `login.html` | Fills test credentials for instant evaluation |
| **Protected Dashboard** | Open `dashboard.html` without signing in | Automatically redirects unauthenticated users to `login.html` |
| **Backend Profile Call** | Sign in and view `dashboard.html` | Calls `GET /api/profile/me` with Bearer token; displays profile, quota badges & eligible schemes |
| **Missing Profile Link** | Sign up without a profile record | Displays high-visibility alert banner with link to complete registration |
| **Profile Editing** | Click `Edit Profile` on dashboard | Updates profile via backend `PUT /api/profile/me` and refreshes dashboard live |
| **Sign Out** | Click `Sign Out` on dashboard | Clears session tokens and redirects back to `login.html` |

---

## 🏛️ Schemes Matched in Phase 1

1. **Stand-Up India Scheme:** Loans up to ₹1 Crore for SC/ST and women entrepreneurs.
2. **PMEGP:** Up to 35% margin money capital subsidy for micro-enterprises in special social categories.
3. **Pradhan Mantri MUDRA Yojana:** Collateral-free business credit up to ₹20 Lakhs (Shishu/Kishore/Tarun).
4. **Startup India Seed Fund Scheme (SISFS):** Up to ₹20L grant and ₹50L debt for early-stage ventures.
5. **PM-VISHWAKARMA:** Affirmative subsidized credit at 5% interest for traditional artisan communities.
6. **TREAD & WE Hub:** Direct 30% government grant assistance for women-led enterprises.

---

## 📊 PPT Content & Presentation Highlights
### Official Title: AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs (AI Funding & Scheme Matcher)
- **Affirmative Design:** Caters directly to marginalized communities with clear social category segmentation.
- **Privacy First:** Zero Aadhaar collection policy.
- **Zero-Trust Backend:** Token verification ensures private profile data is never exposed.
- **Modern Aesthetics:** Tailored Navy-Blue and Teal theme with glassmorphism, responsive cards, and micro-interactions.
#   s c h e m e - A I - 2 . 0  
 