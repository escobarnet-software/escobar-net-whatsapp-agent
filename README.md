<div align="center">

# 🤖 Escobar NET — AI WhatsApp Sales & Booking Agent

### *Tu fuerza de ventas en WhatsApp, 24/7. Sin dormir. Sin olvidar. Sin perder clientes.*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-LLM_Fast-F55036?style=for-the-badge)](https://groq.com)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud_API-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://developers.facebook.com/docs/whatsapp/cloud-api)
[![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlalchemy.org)

**Agente comercial con IA que atiende por WhatsApp, entiende la intención del cliente,
agenda citas automáticamente y guarda todo en base de datos — respuestas en < 1 segundo.**

[🚀 Inicio rápido](#-inicio-rápido-5-minutos) • [⚙️ Cómo funciona](#️-cómo-funciona-el-sistema) •
[🔑 Llaves API](#-dónde-conseguir-tus-llaves-api) • [🏛️ Arquitectura](#️-arquitectura-del-sistema)

</div>

---

## ✨ ¿Qué hace este proyecto?

Un cliente escribe *"hola, quiero una web para mi negocio"* a las 11 PM. Nadie está despierto. **El bot sí:**

| Paso | Qué pasa | Ejemplo |
|------|----------|---------|
| 📩 **1. Recibe** | Meta envía el mensaje a tu webhook | `"hola, quiero una web"` |
| 🧠 **2. Piensa** | Groq analiza intención + extrae datos | `intent=booking, service="Desarrollo web"` |
| 💬 **3. Responde** | Pregunta solo lo que falta | `"¿Me confirmas tu nombre y fecha ideal?"` |
| ✅ **4. Confirma** | Cliente dice "SI" → cita guardada en SQLite | `appointments(id=1, ...)` |
| 📲 **5. Entrega** | La respuesta llega al WhatsApp del cliente | En menos de 2 segundos |

**Capacidades:**
- 🗣️ Conversación natural en español (Groq, < 1s)
- 📅 **Booking automático**: extrae `nombre + servicio + fecha/hora` y persiste la cita
- 🧠 **Memoria por cliente**: últimas 12 mensajes de cada número
- 🔄 Fallback inteligente: si Groq falla, responde con heurísticas (nunca se queda mudo)
- 🧪 **Modo simulación**: pruébalo sin Meta ni WhatsApp real

---

## 🏛️ Arquitectura del sistema

```
┌──────────┐  POST /webhook  ┌─────────────────────────────────────────┐
│ Meta /   │───────────────▶ │ FastAPI (app/main.py)                   │
│ WhatsApp │  ◀──────────────│ routers/webhook.py → services/          │
└──────────┘  send_text      │ orchestrator.py ─┬─ memory.py → SQLite  │
                             │                  ├─ groq_agent.py → Groq │
                             │                  ├─ booking.py → citas  │
                             │                  └─ whatsapp.py → Meta  │
                             └─────────────────────────────────────────┘
```

### 📁 Estructura de carpetas

```
escobar-net-whatsapp-agent/
├── requirements.txt   → dependencias pineadas (fastapi, groq, sqlalchemy, httpx…)
├── .env.example       → plantilla documentada de configuración
├── .env               → TUS llaves reales (nunca se sube a git)
├── escobar_net.db     → SQLite (se crea solo al arrancar)
└── app/
    ├── config.py      → settings tipados con pydantic-settings (lee el .env)
    ├── database.py    → engine + SessionLocal + init_db() (SQLite robusto)
    ├── models.py      → tablas ORM: Contact | Message | Appointment
    ├── schemas.py     → AgentDecision (JSON estricto de la IA) + payloads
    ├── prompts.py     → system prompt enterprise (rol, reglas, servicios)
    ├── main.py        → factory FastAPI + lifespan + routers
    ├── routers/
    │   ├── webhook.py  → GET /webhook (verificación Meta) + POST /webhook (ingesta)
    │   └── simulate.py → GET /health + POST /simulate (testing sin Meta)
    └── services/
        ├── orchestrator.py → CEREBRO: extrae msgs → memoria → Groq → booking → reply
        ├── groq_agent.py   → Groq con response_format=json_object + fallback
        ├── memory.py       → get_or_create_contact + save + load_history
        ├── booking.py      → valida slot y crea Appointment
        └── whatsapp.py     → envío vía Graph API (modo DRY_RUN para dev)
```

### 🗄️ Modelo de datos

- **contacts**: `id, phone (único, ej 15551234567), name, created_at`
- **messages**: `id, contact_id, role (user|assistant), content, wa_message_id`
- **appointments**: `id, contact_id, customer_name, service, scheduled_at (ISO), status (pending|confirmed|cancelled|done)`

---

## ⚙️ Cómo funciona el sistema (flujo de un mensaje)

1. **Meta → `POST /webhook`**: llega el payload `whatsapp_business_account.entry[].changes[].value.messages[]`.
2. **`extract_messages()`** (`services/orchestrator.py`): parsea TODOS los textos, ignora `statuses` (ticks azules), imágenes y audios.
3. **`memory.py`**: busca/crea el `Contact` por teléfono, guarda el mensaje `user`, carga los últimos `MEMORY_WINDOW` (12) mensajes.
4. **`groq_agent.py`**: envía `system prompt (rol Escobar NET) + historial` a Groq con `response_format={"type":"json_object"}`. La IA devuelve SIEMPRE JSON estricto con `intent (greeting|question|booking|cancel_booking|handoff|other) + reply + booking{nombre,servicio,fecha} + wants_confirmation`.
5. **`booking.py`**: si el slot está completo y el usuario dijo "SI", crea el `Appointment`. Si falta un dato, pide solo ese.
6. **`whatsapp.py`**: envía el `reply` por Graph API (`POST /{phone-id}/messages`). Con `WHATSAPP_DRY_RUN=True` solo lo loguea.
7. Todo queda guardado: ambos mensajes en `messages` + la cita en `appointments`.

---

## 🔑 Dónde conseguir tus llaves API

Necesitas **2 llaves gratuitas**. Sin ellas el bot corre en fallback (respuestas básicas, sin IA real ni envío).

### 1️⃣ GROQ_API_KEY — el cerebro 🧠 (gratis, 2 min, sin tarjeta)

1. Entra a **https://console.groq.com** → crea cuenta (Google/GitHub).
2. Menú → **API Keys** → **Create API Key** → cópiala (`gsk_...`).
3. Modelos vivos cambian seguido: revisa **https://console.groq.com/docs/models**. Este proyecto usa `openai/gpt-oss-20b`.
4. Pégala en tu `.env` → `GROQ_API_KEY=gsk_...`
5. Ver qué modelos acepta TU key:
   ```powershell
   python -c "from groq import Groq; c=Groq(api_key='TU_KEY'); print([m.id for m in c.models.list().data])"
   ```

### 2️⃣ WhatsApp Cloud API — boca y oídos 📲 (gratis, 10 min)

> Meta regala un **número de prueba** (`+1 555-xxx`) + 1000 conversaciones/mes.

1. Ve a **https://developers.facebook.com** → **Mis apps** → **Crear app** (Empresa) → producto **WhatsApp**.
2. En **API Setup** copia `Phone number ID` → `WHATSAPP_PHONE_NUMBER_ID` y el **Access token temporal** (~24h) → `WHATSAPP_ACCESS_TOKEN`.
### 📞 Cómo obtener tu número (2 números distintos, no los confundas)

| # | Número | Qué es | Dónde sale | Para qué sirve |
|---|--------|--------|------------|----------------|
| 1 | **Número de prueba** (`+1 555-xxx`) | El BOT (remitente). Meta te lo regala | **API Setup**, arriba, junto al `Phone number ID` | Es quien *envía* los mensajes. Lo configuras en `WHATSAPP_PHONE_NUMBER_ID`. No lo eliges tú, Meta lo asigna |
| 2 | **Tu WhatsApp real** (ej. `+52 1 55...`) | El CLIENTE (destinatario). Es tu celular | **API Setup → campo "To" → Manage/Add** | Es quien *recibe* y responde. El número de prueba SOLO puede escribir a números verificados aquí |

**Paso a paso para registrar tu número (destinatario):**
1. En **API Setup**, ubica la sección de envío de prueba (campo **"To"** con un dropdown).
2. Clic en **Manage/Add phone number** → escribe tu número en formato internacional (ej. `5215512345678`, sin `+`, sin espacios).
3. Te llega un **código por SMS/WhatsApp** a ese celular → ingrésalo en el panel para verificarlo.
4. Listo: ese número ya puede recibir mensajes del bot y responderle.
5. Puedes agregar hasta **5 destinatarios** en modo prueba (equipo, socios, clientes piloto).

> 💡 **Número propio permanente (producción):** el de prueba es temporal y con límites. Para un número real tuyo verificado con tu empresa: **WhatsApp → API Setup → Add phone number** (requiere cuenta de WhatsApp Business + verificación de empresa en Meta Business Suite). Recién ahí migras `WHATSAPP_PHONE_NUMBER_ID` y el token permanente.
4. En **WhatsApp → Configuración → Webhooks**: Callback URL `https://TU-TUNEL.trycloudflare.com/webhook` + Verify token igual al `.env` → **Verificar y guardar** → **Suscribirse** a `messages`.
5. ⚠️ En modo **Desarrollo** Meta NO entrega mensajes reales del celular (solo botón "Probar"). Para real: publica la app (**Desarrollo → En vivo**) o usa simulación.

### 3️⃣ Túnel: exponer tu localhost a Meta 🌐

Meta no llama a `localhost`. Cloudflare Tunnel (gratis, sin cuenta):

```powershell
winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
cloudflared tunnel --url http://127.0.0.1:8000
```

> ⚠️ La URL cambia al reiniciar el túnel → actualízala en Meta + Verificar y guardar.

---

## 🚀 Inicio rápido (5 minutos)

```powershell
cd escobar-net-whatsapp-agent
Copy-Item .env.example .env
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
start http://127.0.0.1:8000/docs
```

La DB `escobar_net.db` se crea sola al arrancar. Para borrar todo: detén el servidor y elimina `escobar_net.db`.

> ⚠️ NO subas httpx de 0.27.2: `groq==0.11.0` se rompe con httpx 0.28 (error `proxies`).

---

## 🧪 Probar el bot (3 formas)

**A. Simulación local — sin Meta, con Groq + envío real ✅ (recomendado):**

```powershell
$b = @{phone='15551234567'; text='hola, quiero una web para mi negocio, soy Juan'} | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/simulate -Method Post -Body $b -ContentType 'application/json'
```

**B. Webhook real de Meta (payload exacto):** usa `POST /webhook` con el objeto `whatsapp_business_account` (ver `/docs`).

**C. Desde tu celular** (app publicada + túnel + webhook verificado): escríbele al número de prueba. Verás `POST /webhook 200 → Groq 200 → POST .../messages 200`.

**Ver qué se guardó:**

```powershell
python -c "import sqlite3; c=sqlite3.connect('escobar_net.db'); print(c.execute('select phone,name from contacts').fetchall()); print(c.execute('select customer_name,service,scheduled_at,status from appointments').fetchall())"
```

---

## ⚠️ Errores que ya nos pasaron (y su fix)

| Síntoma | Causa | Fix |
|---|---|---|
| `401 Unauthorized` en `/messages` | Token Meta expiró (~24h) | Nuevo token → `.env` → **reinicia uvicorn** (`--reload` no recarga el `.env`) |
| `400 Bad Request` en `/messages` | `to` no verificado | Agrega el número en API Setup → To |
| `model does not exist / decommissioned` | Groq dio de baja el modelo | Lista modelos y actualiza `GROQ_MODEL` |
| `Client.__init__() ... 'proxies'` | httpx 0.28 vs groq 0.11 | `pip install httpx==0.27.2` (ya pineado) |
| Nada cae en `/webhook` | `messages` no suscrito / URL vieja / app en desarrollo | Suscribe `messages`, actualiza URL o publica la app |
| `403 Forbidden` en verify | Tokens distintos | `hub.verify_token` = `WHATSAPP_VERIFY_TOKEN`, sin espacios |

---

## 🔒 Seguridad

- `.env` con secretos → **jamás** se commitea (ver `.gitignore`).
- Rota `GROQ_API_KEY` y `WHATSAPP_ACCESS_TOKEN` si se exponen en un chat/log.
- En producción: token permanente de Meta, HTTPS real, `WHATSAPP_DRY_RUN=False`, migra SQLite → Postgres con `DATABASE_URL`.

---

<div align="center">

**Hecho con 💙 por Escobar NET — Software que vende mientras duermes.**

`FastAPI` · `Groq` · `WhatsApp Cloud API` · `SQLAlchemy`

</div>


