# Contractor Bot

A config-driven, source-agnostic lead-response bot for contractors. Swap `business_config.json` to onboard a new client in minutes — no code changes needed.

## What It Does

- Accepts leads from **Website**, **Facebook Lead Ads**, **Google Business Profile**, **Typeform**, or auto-detects the format.
- Sends instant SMS via Twilio using templates defined in `business_config.json`.
- Runs automated 2-hour, 24-hour, and 72-hour follow-ups.
- Handles missed-call text-back with voicemail recording.

## Stack

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [Render](https://render.com) | Hosting | Web Service (free) |
| [Supabase](https://supabase.com) | Postgres database | 500 MB |
| [Twilio](https://twilio.com) | SMS & voice | Client's own account |
| [cron-job.org](https://cron-job.org) | Follow-up scheduler | Unlimited pings |

## Repository Structure

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app — lead ingestion, missed-call handler, follow-ups |
| `business_config.json` | Business name, SMS templates, Twilio number |
| `.env` / `.env.example` | Secrets and runtime configuration |
| `supabase_schema.sql` | Database schema |
| `requirements.txt` | Python dependencies |
| `test_webhook.py` | Integration test suite |

---

## Local Development

### Prerequisites

- Python 3.11+
- `pip`

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your values (see Environment Variables below)
```

### 3. Run in test mode

`TEST_MODE=true` skips real SMS sends and database writes so you can iterate locally without external services.

```bash
TEST_MODE=true SUPABASE_URL=x SUPABASE_SERVICE_KEY=x TWILIO_SID=x TWILIO_TOKEN=x WEBHOOK_SECRET=secret \
  python -m uvicorn main:app --port 8000
```

### 4. Run the test suite

In a second terminal (while the server is running):

```bash
python test_webhook.py --url http://localhost:8000 --secret secret
```

Additional flags:

| Flag | Description |
|------|-------------|
| `--security-only` | Run only the security checks |
| `--test-rate-limit` | Include the rate-limit test |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase `service_role` key (Settings → API) |
| `TWILIO_SID` | Twilio Account SID |
| `TWILIO_TOKEN` | Twilio Auth Token |
| `WEBHOOK_SECRET` | Random string (min 32 chars) — authenticates all webhook endpoints |
| `APP_BASE_URL` | Full public URL of the deployed app (required for Twilio signature validation) |
| `CORS_ORIGINS` | Comma-separated allowed origins (e.g. `https://yourdomain.com`) |
| `TEST_MODE` | Set to `true` to disable real SMS/DB writes during local testing |

---

## Deployment

### Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. Note the **Project URL** and **service_role key** (Settings → API).
3. Open the SQL editor, paste `supabase_schema.sql`, and run it.

### Render

1. Push the repo to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service** → connect the repo.
3. Set **Start Command**:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. Add all variables from `.env` in the **Environment** tab.
5. Copy the Render URL and set it as `APP_BASE_URL`.

### Twilio webhooks

In the Twilio console, configure your phone number:

| Event | URL |
|-------|-----|
| Incoming Message (SMS) | `https://your-app.onrender.com/reply` |
| Incoming Call | `https://your-app.onrender.com/voice/inbound` |

Both should use **HTTP POST**.

### Follow-up cron job

Use [cron-job.org](https://cron-job.org) (free):

- **URL:** `https://your-app.onrender.com/process-followups`
- **Method:** GET
- **Header:** `x-webhook-secret: <your WEBHOOK_SECRET>`
- **Schedule:** Every 15 minutes

---

## Lead Source Webhooks

All endpoints require the header `x-webhook-secret: <your WEBHOOK_SECRET>`.

| Source | Endpoint |
|--------|----------|
| Website / generic form | `POST /webhook/generic` |
| Facebook Lead Ads | `POST /webhook/facebook` |
| Google Business Profile | `POST /webhook/google` |
| Typeform | `POST /webhook/typeform` |
| Auto-detect | `POST /webhook/lead` |

---

## Business Configuration

Edit `business_config.json` to customise SMS copy and business details:

```json
{
  "business_id": "your_unique_id",
  "business_name": "Your Business Name",
  "owner_name": "Your Name",
  "twilio_phone": "+15551234567",
  "templates": { "...": "..." },
  "sms_cooldown_minutes": 15
}
```

All SMS copy lives in `templates`. You never need to edit `main.py`.

To onboard a new contractor: update `business_config.json` (or keep a separate copy per client), set a unique `business_id`, and redeploy.
