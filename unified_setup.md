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
