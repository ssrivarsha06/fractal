# 🔐 FractalAuth — Multi-Level Secure Authentication System

## 🐛 The Bug That Was Fixed

**Problem:** `st.components.v1.html()` is **one-way only** (Python → JS).  
JS cannot directly write back to `st.session_state`.

**Wrong approach (old code):** wrote to `sessionStorage` — Python never read it.

**Fix:** When the user places 3 markers, JS fires:
```js
window.parent.location.href = baseURL + "?markers=JSON&behavior=JSON"
```
This updates the **Streamlit app URL**. Streamlit detects the change, re-runs,
and Python reads `st.query_params["markers"]` → saved to `st.session_state`.

---

## 🗂 Project Structure

```
fractalauth/
├── backend/
│   ├── main.py           # FastAPI — all API endpoints, Level 3+4 risk logic
│   ├── db.py             # SQLite database (fractalauth.db)
│   └── requirements.txt
└── frontend/
    ├── app.py            # Streamlit entry point
    ├── config.py         # API_URL config
    ├── requirements.txt
    ├── pages/
    │   ├── level1_identity.py   # Step 1: username + password
    │   ├── level2_fractal.py    # Step 2: interactive fractal + FIXED bridge
    │   ├── level5_puzzle.py     # Step 3: risk panel + puzzle
    │   └── dashboard.py         # Post-auth dashboard
    └── utils/
        └── puzzle_gen.py        # Fractal coordinate → puzzle generator
```

---

## 🚀 Run Locally

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 2. Frontend
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
# Opens: http://localhost:8501
```

---

## ☁️ Deploy on Streamlit Cloud

### Step 1 — Deploy Backend (free options)

**Render.com** (recommended — free tier):
1. Create new Web Service → connect your GitHub repo → set root to `backend/`
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Note your URL e.g. `https://fractalauth-api.onrender.com`

**Railway.app** alternative:
```bash
cd backend
railway init && railway up
```

### Step 2 — Deploy Frontend on Streamlit Cloud

1. Push the `frontend/` folder to a **GitHub repo**
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. New app → select repo → main file: `app.py`
4. Click **Advanced settings → Secrets** and add:
```toml
FRACTALAUTH_API_URL = "https://fractalauth-api.onrender.com"
```
5. Deploy — done!

---

## 🔑 Auth Flow

### REGISTER (3 steps)
| Step | Description |
|------|-------------|
| 1 | Username, email, password (8+ chars, uppercase, symbol, number) |
| 2 | Choose fractal type, zoom, place **3 secret markers** on fractal canvas |
| 3 | Preview + complete registration |

**Background during registration:**
- Behavioral baseline saved (mouse speed, pauses, fractal time, clicks)
- Easy + Hard puzzles generated from coordinate math

### LOGIN (3 steps + 2 invisible)
| Step | Description |
|------|-------------|
| 1 | Username + password — **coordinates NEVER shown** |
| 2 | Navigate fractal from memory, re-mark your 3 points (±0.08 tolerance) |
| 3 | Risk-adaptive puzzle |

**Background (invisible to user):**
- **Level 3 Behavioral:** mouse speed, pauses, fractal time, click count vs baseline
- **Level 4 Contextual:** login hour, failed attempts, IP, device fingerprint

---

## 📊 Risk Score Logic

```
Composite = (Behavioral × 50%) + (Contextual × 50%)
< 40%  →  EASY puzzle
≥ 40%  →  HARD puzzle
```

### Level 3 — Behavioral Factors
| Factor | Weight |
|--------|--------|
| Mouse speed deviation | 25% |
| Pause duration pattern | 25% |
| Fractal traversal time | 30% |
| Click count pattern | 20% |

### Level 4 — Contextual Factors
| Factor | Score |
|--------|-------|
| Login before 5am or after 11pm | +20 |
| 3+ previous failed attempts | +35 |
| Device fingerprint changed | +20 |
| IP address changed | +15 |
| Subnet/geo region changed | +10 |

---

## 🔒 Security Notes
- Passwords: SHA-256 hashed in SQLite (upgrade to bcrypt/argon2 for production)
- Fractal coordinates **never sent to client** during login
- Puzzle answers verified server-side only
- Coordinate matching uses ±0.08 tolerance (lenient for usability)
