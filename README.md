<div align="center">

# 🤖 Escobar NET — AI WhatsApp Sales & Booking Agent

### *Your sales force on WhatsApp, 24/7. No sleep. No forgetting. No lost customers.*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-LLM_Fast-F55036?style=for-the-badge)](https://groq.com)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud_API-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://developers.facebook.com/docs/whatsapp/cloud-api)
[![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlalchemy.org)

**AI-powered sales agent for WhatsApp: understands customer intent,
auto-books appointments and stores everything in a database — replies in < 1 second.**

[🚀 Quickstart](#-quickstart-5-minutes) • [⚙️ How it works](#️-how-the-system-works) •
[🔑 API keys](#-where-to-get-your-api-keys) • [🏛️ Architecture](#️-system-architecture)

</div>

---

## ✨ What does this project do?

A customer writes *"hola, quiero una web para mi negocio"* at 11 PM. Nobody is awake. **The bot is:**

| Step | What happens | Example |
|------|--------------|---------|
| 📩 **1. Receives** | Meta forwards the message to your webhook | `"hola, quiero una web"` |
| 🧠 **2. Thinks** | Groq analyzes intent + extracts data | `intent=booking, service="Web development"` |
| 💬 **3. Replies** | Asks only for what's missing | `"Can you confirm your name and ideal date?"` |
| ✅ **4. Confirms** | Customer says "SI" → appointment saved in SQLite | `appointments(id=1, ...)` |
| 📲 **5. Delivers** | The reply reaches the customer's WhatsApp | In under 2 seconds |

**Capabilities:**
- 🗣️ Natural Spanish conversation (Groq, < 1s)
- 📅 **Auto-booking**: extracts `name + service + date/time` and persists the appointment
- 🧠 **Per-customer memory**: last 12 messages of each phone number
- 🔄 Smart fallback: if Groq fails, answers with heuristics (never goes silent)
- 🧪 **Simulation mode**: try it without Meta or a real WhatsApp

---

## 🏛️ System architecture

```
┌──────────┐  POST /webhook  ┌─────────────────────────────────────────┐
│ Meta /   │───────────────▶ │ FastAPI (app/main.py)                   │
│ WhatsApp │  ◀──────────────│ routers/webhook.py → services/          │
└──────────┘  send_text      │ orchestrator.py ─┬─ memory.py → SQLite  │
                             │                  ├─ groq_agent.py → Groq │
                             │                  ├─ booking.py → appts  │
                             │                  └─ whatsapp.py → Meta  │
                             └─────────────────────────────────────────┘
```

### 📁 Folder structure

```
escobar-net-whatsapp-agent/
├── requirements.txt   → pinned deps (fastapi, groq, sqlalchemy, httpx…)
├── .env.example       → documented config template
├── .env               → YOUR real keys (never committed to git)
├── escobar_net.db     → SQLite (auto-created on boot)
└── app/
    ├── config.py      → typed settings via pydantic-settings (reads .env)
    ├── database.py    → engine + SessionLocal + init_db() (robust SQLite)
    ├── models.py      → ORM tables: Contact | Message | Appointment
    ├── schemas.py     → AgentDecision (strict AI JSON) + payloads
    ├── prompts.py     → enterprise system prompt (role, rules, services)
    ├── main.py        → FastAPI factory + lifespan + routers
    ├── routers/
    │   ├── webhook.py  → GET /webhook (Meta verification) + POST /webhook (ingest)
    │   └── simulate.py → GET /health + POST /simulate (testing without Meta)
    └── services/
        ├── orchestrator.py → BRAIN: extract msgs → memory → Groq → booking → reply
        ├── groq_agent.py   → Groq with response_format=json_object + fallback
        ├── memory.py       → get_or_create_contact + save + load_history
        ├── booking.py      → validates slot and creates Appointment
        └── whatsapp.py     → sends via Graph API (DRY_RUN mode for dev)
```

### 🗄️ Data model

- **contacts**: `id, phone (unique, e.g. 15551234567), name, created_at`
- **messages**: `id, contact_id, role (user|assistant), content, wa_message_id`
- **appointments**: `id, contact_id, customer_name, service, scheduled_at (ISO), status (pending|confirmed|cancelled|done)`

---

## ⚙️ How the system works (message flow)

1. **Meta → `POST /webhook`**: the `whatsapp_business_account.entry[].changes[].value.messages[]` payload arrives.
2. **`extract_messages()`** (`services/orchestrator.py`): parses ALL texts, ignores `statuses` (blue ticks), images and audio.
3. **`memory.py`**: finds/creates the `Contact` by phone, saves the `user` message, loads the last `MEMORY_WINDOW` (12) messages.
4. **`groq_agent.py`**: sends `system prompt (Escobar NET role) + history` to Groq with `response_format={"type":"json_object"}`. The AI ALWAYS returns strict JSON with `intent (greeting|question|booking|cancel_booking|handoff|other) + reply + booking{name,service,date} + wants_confirmation`.
5. **`booking.py`**: if the slot is complete and the user said "SI", creates the `Appointment`. If data is missing, asks only for that.
6. **`whatsapp.py`**: sends the `reply` via Graph API (`POST /{phone-id}/messages`). With `WHATSAPP_DRY_RUN=True` it only logs it.
7. Everything is stored: both messages in `messages` + the appointment in `appointments`.

---

## 🔑 Where to get your API keys

You need **2 free keys**. Without them the bot runs in fallback (basic replies, no real AI or sending).

### 1️⃣ GROQ_API_KEY — the brain 🧠 (free, 2 min, no card)

1. Go to **https://console.groq.com** → create an account (Google/GitHub).
2. Sidebar → **API Keys** → **Create API Key** → copy it (`gsk_...`).
3. Live models change often: check **https://console.groq.com/docs/models**. This project uses `openai/gpt-oss-20b`.
4. Paste it into your `.env` → `GROQ_API_KEY=gsk_...`
5. Check which models YOUR key accepts:
   ```powershell
   python -c "from groq import Groq; c=Groq(api_key='YOUR_KEY'); print([m.id for m in c.models.list().data])"
   ```

### 2️⃣ WhatsApp Cloud API — mouth and ears 📲 (free, 10 min)

> Meta gives you a free **test number** (`+1 555-xxx`) + 1000 conversations/month.

1. Go to **https://developers.facebook.com** → **My apps** → **Create app** (Business) → add the **WhatsApp** product.
2. In **API Setup** copy `Phone number ID` → `WHATSAPP_PHONE_NUMBER_ID` and the **temporary access token** (~24h) → `WHATSAPP_ACCESS_TOKEN`.
### 📞 How to get your number (2 different numbers — don't mix them up)

| # | Number | What it is | Where to find it | What it's for |
|---|--------|-----------|------------------|---------------|
| 1 | **Test number** (`+1 555-xxx`) | The BOT (sender). Gifted by Meta | **API Setup**, top, next to `Phone number ID` | It *sends* the messages. Set it in `WHATSAPP_PHONE_NUMBER_ID`. You don't choose it, Meta assigns it |
| 2 | **Your real WhatsApp** (e.g. `+52 1 55...`) | The CLIENT (recipient). Your phone | **API Setup → "To" field → Manage/Add** | It *receives* and replies. The test number can ONLY write to verified numbers here |

**Step by step to register your number (recipient):**
1. In **API Setup**, find the test-send section (the **"To"** dropdown field).
2. Click **Manage/Add phone number** → type your number in international format (e.g. `5215512345678`, no `+`, no spaces).
3. You'll get an **SMS/WhatsApp code** on that phone → enter it in the dashboard to verify.
4. Done: that number can now receive bot messages and reply to them.
5. You can add up to **5 recipients** in test mode (team, partners, pilot customers).

> 💡 **Permanent own number (production):** the test one is temporary and limited. For your own company-verified number: **WhatsApp → API Setup → Add phone number** (requires a WhatsApp Business account + company verification in Meta Business Suite). Only then migrate `WHATSAPP_PHONE_NUMBER_ID` and the permanent token.
4. In **WhatsApp → Settings → Webhooks**: Callback URL `https://YOUR-TUNNEL.trycloudflare.com/webhook` + Verify token matching `.env` → **Verify and save** → **Subscribe** to `messages`.
5. ⚠️ In **Development** mode Meta does NOT deliver real phone messages (only the "Test" button). For real ones: publish the app (**Development → Live**) or use simulation.

### 3️⃣ Tunnel: expose your localhost to Meta 🌐

Meta can't call `localhost`. Cloudflare Tunnel (free, no account):

```powershell
winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
cloudflared tunnel --url http://127.0.0.1:8000
```

> ⚠️ The URL changes on tunnel restart → update it in Meta + Verify and save.

---

## 🚀 Quickstart (5 minutes)

```powershell
cd escobar-net-whatsapp-agent
Copy-Item .env.example .env
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
start http://127.0.0.1:8000/docs
```

The `escobar_net.db` database is auto-created on boot. To wipe everything: stop the server and delete `escobar_net.db`.

> ⚠️ Do NOT upgrade httpx past 0.27.2: `groq==0.11.0` breaks with httpx 0.28 (`proxies` error).

---

## 🧪 Testing the bot (3 ways)

**A. Local simulation — no Meta, with real Groq + real sending ✅ (recommended):**

```powershell
$b = @{phone='15551234567'; text='hola, quiero una web para mi negocio, soy Juan'} | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/simulate -Method Post -Body $b -ContentType 'application/json'
```

**B. Real Meta webhook (exact payload):** use `POST /webhook` with the `whatsapp_business_account` object (see `/docs`).

**C. From your phone** (published app + tunnel + verified webhook): message the test number. You'll see `POST /webhook 200 → Groq 200 → POST .../messages 200`.

**Check what was stored:**

```powershell
python -c "import sqlite3; c=sqlite3.connect('escobar_net.db'); print(c.execute('select phone,name from contacts').fetchall()); print(c.execute('select customer_name,service,scheduled_at,status from appointments').fetchall())"
```

---

## ⚠️ Errors we already hit (and their fix)

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` on `/messages` | Meta token expired (~24h) | New token → `.env` → **restart uvicorn** (`--reload` doesn't reload `.env`) |
| `400 Bad Request` on `/messages` | `to` not verified | Add the number in API Setup → To |
| `model does not exist / decommissioned` | Groq retired the model | List models and update `GROQ_MODEL` |
| `Client.__init__() ... 'proxies'` | httpx 0.28 vs groq 0.11 | `pip install httpx==0.27.2` (already pinned) |
| Nothing hits `/webhook` | `messages` not subscribed / stale URL / dev-mode app | Subscribe `messages`, update URL or publish the app |
| `403 Forbidden` on verify | Mismatched tokens | `hub.verify_token` = `WHATSAPP_VERIFY_TOKEN`, no spaces |

---

## 🔒 Security

- `.env` with secrets → **never** committed (see `.gitignore`).
- Rotate `GROQ_API_KEY` and `WHATSAPP_ACCESS_TOKEN` if exposed in a chat/log.
- In production: permanent Meta token, real HTTPS, `WHATSAPP_DRY_RUN=False`, migrate SQLite → Postgres via `DATABASE_URL`.

---

<div align="center">

**Built with 💙 by Escobar NET — Software that sells while you sleep.**

`FastAPI` · `Groq` · `WhatsApp Cloud API` · `SQLAlchemy`

</div>


