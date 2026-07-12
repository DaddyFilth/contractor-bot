"""
Unified contractor bot: lead follow-up + missed call + universal webhook adapter.
One file. Config-driven. Switch businesses by editing business_config.json.
"""

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException
import os
import json
import time
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unified_bot")

app = FastAPI()

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "business_config.json")

def load_config() -> dict:
    with open(_CONFIG_PATH, "r") as f:
        return json.load(f)

CONFIG = load_config()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)

_cooldown = {}

def _validate_secret(request: Request, query_secret: str = None):
    header_secret = request.headers.get("x-webhook-secret")
    if header_secret != WEBHOOK_SECRET and query_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

class LeadPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., pattern=r"^+?[1-9]d{1,14}$")
    service: str = Field(default="", max_length=200)
    source: str = Field(default="website", max_length=50)

def _parse_generic(body: dict) -> dict:
    return {
        "name": body.get("name", ""),
        "phone": body.get("phone", ""),
        "service": body.get("service", ""),
        "source": body.get("source", "website"),
    }

def _parse_facebook(body: dict) -> dict:
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])
        lead_data = changes[0].get("value", {})
        field_data = {f["name"]: f["values"][0] for f in lead_data.get("field_data", [])}
        return {
            "name": field_data.get("full_name", field_data.get("name", "")),
            "phone": field_data.get("phone_number", field_data.get("phone", "")),
            "service": field_data.get("service", ""),
            "source": "facebook",
        }
    except Exception as e:
        logger.error(f"Facebook parse failed: {e}")
        raise HTTPException(status_code=422, detail="Invalid Facebook payload")

def _parse_google(body: dict) -> dict:
    try:
        messages = body.get("messageNotifications", [])
        msg = messages[0].get("message", {}) if messages else body
        return {
            "name": msg.get("displayName", "") or body.get("displayName", ""),
            "phone": msg.get("phoneNumber", "") or body.get("phoneNumber", ""),
            "service": (msg.get("text", "") or "")[:200],
            "source": "google",
        }
    except Exception as e:
        logger.error(f"Google parse failed: {e}")
        raise HTTPException(status_code=422, detail="Invalid Google Business payload")

def _parse_typeform(body: dict) -> dict:
    try:
        answers = body.get("form_response", {}).get("answers", [])
        field_map = {}
        for a in answers:
            ref = a.get("ref", "")
            typ = a.get("type", "")
            val = a.get(typ, "")
            if isinstance(val, dict):
                val = val.get("label", val.get("other", ""))
            field_map[ref] = val
        return {
            "name": field_map.get("name", field_map.get("full_name", "")),
            "phone": field_map.get("phone", field_map.get("phone_number", "")),
            "service": field_map.get("service", field_map.get("inquiry", "")),
            "source": "typeform",
        }
    except Exception as e:
        logger.error(f"Typeform parse failed: {e}")
        raise HTTPException(status_code=422, detail="Invalid Typeform payload")

def _auto_detect(body: dict) -> dict:
    if "entry" in body and "changes" in body.get("entry", [{}])[0]:
        return _parse_facebook(body)
    if "messageNotifications" in body or ("message" in body and "phoneNumber" in body):
        return _parse_google(body)
    if "form_response" in body:
        return _parse_typeform(body)
    if "name" in body and "phone" in body:
        return _parse_generic(body)
    raise HTTPException(status_code=422, detail="Could not auto-detect source format")

PARSERS = {
    "generic": _parse_generic,
    "facebook": _parse_facebook,
    "google": _parse_google,
    "typeform": _parse_typeform,
    "auto": _auto_detect,
}

def _normalize_phone(v: str) -> str:
    cleaned = v.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "").replace(".", "")
    if not cleaned.startswith("+"):
        if len(cleaned) == 10:
            cleaned = "+1" + cleaned
        elif len(cleaned) == 11 and cleaned.startswith("1"):
            cleaned = "+" + cleaned
        else:
            raise HTTPException(status_code=422, detail="Phone must be E.164 or 10-digit US/Canada")
    return cleaned

def _template(name: str, **kwargs) -> str:
    tpl = CONFIG["templates"].get(name, "Hi, this is {owner_name}. We received your request.")
    defaults = {
        "owner_name": CONFIG["owner_name"],
        "business_name": CONFIG["business_name"],
        "service": "our services",
    }
    defaults.update(kwargs)
    return tpl.format(**defaults)

def send_sms(to: str, body: str):
    try:
        twilio_client.messages.create(
            to=to,
            from_=CONFIG["twilio_phone"],
            body=body[:1600]
        )
    except TwilioRestException as e:
        logger.error(f"Twilio error: {e.code}")
    except Exception as e:
        logger.error(f"SMS send failed: {type(e).__name__}")

@app.post("/webhook/{source_type}")
async def webhook_by_source(source_type: str, request: Request, background_tasks: BackgroundTasks):
    if source_type not in PARSERS:
        raise HTTPException(status_code=400, detail=f"Unknown source. Use: {list(PARSERS.keys())}")
    _validate_secret(request)
    body = await request.json()
    parsed = PARSERS[source_type](body)
    return await _process_lead(parsed, background_tasks)

@app.post("/webhook/lead")
async def webhook_auto(request: Request, background_tasks: BackgroundTasks):
    _validate_secret(request)
    body = await request.json()
    parsed = _auto_detect(body)
    return await _process_lead(parsed, background_tasks)

async def _process_lead(parsed: dict, background_tasks: BackgroundTasks):
    name = parsed["name"]
    phone = _normalize_phone(parsed["phone"])
    service = parsed.get("service", "") or "our services"
    source = parsed.get("source", "website")
    now = datetime.utcnow()

    lead_data = {
        "business_id": CONFIG["business_id"],
        "name": name,
        "phone": phone,
        "service": service,
        "source": source,
        "status": "new",
        "touch_count": 1,
        "created_at": now.isoformat(),
        "next_followup_at": (now + timedelta(hours=2)).isoformat(),
    }

    try:
        supabase.table("leads").insert(lead_data).execute()
    except Exception as e:
        logger.error(f"DB insert failed: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    body = _template("instant", name=name, service=service)
    background_tasks.add_task(send_sms, phone, body)
    logger.info("Lead accepted: phone=%s**** source=%s", phone[:4], source)
    return {"status": "accepted", "touch": 1, "source": source}

@app.get("/process-followups")
async def process_followups(request: Request, secret: str = Query(None)):
    _validate_secret(request, query_secret=secret)
    now = datetime.utcnow().isoformat()

    try:
        resp = supabase.table("leads").select("*").eq("status", "new").eq("business_id", CONFIG["business_id"]).lte("next_followup_at", now).execute()
        leads = resp.data or []
    except Exception as e:
        logger.error(f"DB query failed: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    processed = 0
    for lead in leads:
        touch = lead.get("touch_count", 1)
        phone = lead.get("phone")
        name = lead.get("name", "there")
        service = lead.get("service", "our services")
        lead_id = lead.get("id")

        if touch == 1:
            body = _template("followup_2h", name=name, service=service)
            next_delta = timedelta(hours=22)
        elif touch == 2:
            body = _template("followup_24h", name=name, service=service)
            next_delta = timedelta(hours=48)
        else:
            supabase.table("leads").update({"status": "closed", "next_followup_at": None}).eq("id", lead_id).execute()
            logger.info("Lead closed: id=%s...", str(lead_id)[:4])
            continue

        send_sms(phone, body)
        next_time = datetime.utcnow() + next_delta
        supabase.table("leads").update({
            "touch_count": touch + 1,
            "next_followup_at": next_time.isoformat()
        }).eq("id", lead_id).execute()
        processed += 1

    logger.info("Processed %s follow-ups", processed)
    return {"processed": processed}

@app.post("/reply")
async def handle_reply(request: Request):
    form = await request.form()
    from_phone = form.get("From", "")
    body = form.get("Body", "")

    if not from_phone:
        return {"status": "ignored"}

    try:
        resp = supabase.table("leads").select("id").eq("phone", from_phone).eq("status", "new").eq("business_id", CONFIG["business_id"]).order("created_at", desc=True).limit(1).execute()
        if resp.data:
            lead_id = resp.data[0]["id"]
            supabase.table("leads").update({"status": "responded"}).eq("id", lead_id).execute()
            logger.info("Lead responded: id=%s...", str(lead_id)[:4])
    except Exception as e:
        logger.error(f"Reply handling failed: {e}")

    return {"status": "ok"}

@app.post("/voice/inbound")
async def handle_inbound_call(request: Request):
    from twilio.twiml import VoiceResponse
    form = await request.form()
    from_phone = form.get("From", "")
    call_status = form.get("CallStatus", "")
    call_sid = form.get("CallSid", "")

    if not from_phone:
        return str(VoiceResponse())

    if call_status in ("completed", "no-answer", "busy", "failed", "canceled"):
        return _send_missed_text(from_phone, call_sid)

    resp = VoiceResponse()
    resp.say(
        f"Hi, you have reached {CONFIG['owner_name']} with {CONFIG['business_name']}. I'm on a job site right now and can't take your call. "
        "Please leave your name, number, and what you need help with, and I will call you back within the hour. "
        "You can also text me at this number."
    )
    resp.record(max_length=120, action="/voice/voicemail", method="POST")
    resp.say("We did not receive your recording. Please text us at this number and we will respond quickly.")
    return str(resp)

@app.post("/voice/voicemail")
async def handle_voicemail(request: Request):
    form = await request.form()
    from_phone = form.get("From", "")
    call_sid = form.get("CallSid", "")
    if from_phone:
        _send_missed_text(from_phone, call_sid)
    from twilio.twiml import VoiceResponse
    return str(VoiceResponse())

def _send_missed_text(phone: str, call_sid: str):
    from twilio.twiml import VoiceResponse
    cooldown_min = CONFIG.get("sms_cooldown_minutes", 15)
    now = time.time()
    last_sent = _cooldown.get(phone, 0)
    if (now - last_sent) < cooldown_min * 60:
        logger.info("SMS cooldown active for %s****", phone[:4])
        return str(VoiceResponse())

    body = _template("missed_call")
    try:
        twilio_client.messages.create(to=phone, from_=CONFIG["twilio_phone"], body=body)
        _cooldown[phone] = now
        logger.info("Missed-call SMS sent to %s****", phone[:4])
    except TwilioRestException as e:
        logger.error(f"Twilio SMS error: {e.code}")
    except Exception as e:
        logger.error(f"SMS send failed: {type(e).__name__}")
    return str(VoiceResponse())

@app.get("/health")
async def health():
    return {"status": "ok", "business": CONFIG["business_name"], "business_id": CONFIG["business_id"]}

@app.get("/config")
async def get_config(request: Request, secret: str = Query(None)):
    _validate_secret(request, query_secret=secret)
    return {"business": CONFIG, "sources": list(PARSERS.keys())}
