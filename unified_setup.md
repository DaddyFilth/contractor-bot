# Unified Contractor Bot — Config-Driven, Source-Agnostic

**Goal:** One codebase. Any lead source. Swap `business_config.json` to onboard a new contractor in 5 minutes.

## What It Does

- Accepts leads from **Website**, **Facebook Lead Ads**, **Google Business Profile**, **Typeform**, or auto-detects format.
- Sends instant SMS via Twilio using templates from `business_config.json`.
- Runs 2-hour, 24-hour, and 72-hour follow-ups.
- Missed-call text-back with voicemail recording.
- All business logic (name, templates, phone) lives in **one JSON file**.

## Zero-Cost Stack

| Service | Free Tier |
|---------|-----------|
| Render | Web Service (free) |
| Supabase | 500 MB Postgres |
| Twilio | Client pays their own account |
| cron-job.org | Unlimited pings |

## Files

| File | Purpose |
|------|---------|
| `main.py` | Unified FastAPI app (lead bot + missed call + adapter) |
| `business_config.json` | Business name, templates, Twilio number |
| `.env` | Secrets (API keys, webhook secret) |
| `supabase_schema.sql` | Updated schema with `business_id` |
| `requirements.txt` | Dependencies |

## Quick Start

### 1. Clone / copy files

```bash
git init
git add .
git commit -m "init"
```

### 2. Create a Supabase project

1. Sign up at [supabase.com](https://supabase.com) (free tier).
2. Create a new project and note the **Project URL** and **service_role key** (Settings → API).
3. Open the SQL editor and paste the contents of `supabase_schema.sql`, then run it.

### 3. Set up Twilio

1. Sign up at [twilio.com](https://twilio.com) (client pays their own account).
2. Buy a phone number and note:
   - **Account SID**
   - **Auth Token**
   - **Phone number** (E.164 format, e.g. `+15551234567`)

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
# edit .env with your values
```

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Your Supabase `service_role` key |
| `TWILIO_SID` | Twilio Account SID |
| `TWILIO_TOKEN` | Twilio Auth Token |
| `WEBHOOK_SECRET` | Random secret string (min 32 chars) — guards all webhook endpoints |
| `APP_BASE_URL` | Full public URL of your deployed app (required for Twilio signature validation) |
| `CORS_ORIGINS` | Comma-separated list of allowed origins (e.g. `https://yourdomain.com`) |

### 5. Customise your business

Edit `business_config.json`:

```json
{
  "business_id": "your_unique_id",
  "business_name": "Your Business Name",
  "owner_name": "Your Name",
  "twilio_phone": "+15551234567",
  "templates": { ... },
  "sms_cooldown_minutes": 15
}
```

All SMS copy lives in `templates`. You never need to touch `main.py`.

### 6. Deploy to Render

1. Push the repo to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service** → connect your repo.
3. Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add every variable from `.env` in the **Environment** tab.
5. Note your Render URL (e.g. `https://your-app.onrender.com`) and set it as `APP_BASE_URL`.

### 7. Configure Twilio webhooks

In the Twilio console, for your phone number:

| Event | URL |
|-------|-----|
| Incoming Message (SMS) | `https://your-app.onrender.com/reply` |
| Incoming Call | `https://your-app.onrender.com/voice/inbound` |

Both should use **HTTP POST**.

### 8. Set up follow-up cron job

Use [cron-job.org](https://cron-job.org) (free):

- **URL:** `https://your-app.onrender.com/process-followups`
- **Method:** GET
- **Header:** `x-webhook-secret: <your WEBHOOK_SECRET>`
- **Schedule:** Every 15 minutes

### 9. Point your lead sources at the bot

| Source | Webhook URL |
|--------|-------------|
| Website / generic form | `POST /webhook/generic` |
| Facebook Lead Ads | `POST /webhook/facebook` |
| Google Business Profile | `POST /webhook/google` |
| Typeform | `POST /webhook/typeform` |
| Auto-detect | `POST /webhook/lead` |

All endpoints require the header `x-webhook-secret: <your WEBHOOK_SECRET>`.

---

## Testing Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start in test mode (no real SMS or DB writes)
TEST_MODE=true SUPABASE_URL=x SUPABASE_SERVICE_KEY=x TWILIO_SID=x TWILIO_TOKEN=x WEBHOOK_SECRET=secret \
  python -m uvicorn main:app --port 8000

# Run the test suite
python test_webhook.py --url http://localhost:8000 --secret secret
```

Add `--security-only` to run only the security checks, or `--test-rate-limit` to include the rate-limit test.

---

## Onboarding a New Contractor

1. Edit `business_config.json` (or keep a separate copy per client).
2. Set a new `business_id` so leads are segmented in the `leads` table.
3. Deploy — that's it.
