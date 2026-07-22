CREATE TABLE IF NOT EXISTS business_configs (
    business_id TEXT PRIMARY KEY,
    business_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    twilio_phone TEXT NOT NULL,
    templates JSONB NOT NULL DEFAULT '{}',
    sources TEXT[] DEFAULT ARRAY['website'],
    sms_cooldown_minutes INTEGER DEFAULT 15,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    business_id TEXT DEFAULT 'yessian_sealing',
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    service TEXT,
    source TEXT DEFAULT 'website',
    consent_source TEXT,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'responded', 'closed')),
    opted_out BOOLEAN NOT NULL DEFAULT FALSE,
    touch_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    next_followup_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_status_next ON leads(status, next_followup_at);
CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);
CREATE INDEX IF NOT EXISTS idx_leads_business ON leads(business_id, status, next_followup_at);

-- Prevent duplicate active leads for the same phone number per business.
-- A lead can only be inserted once the previous one has been closed or responded to.
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_unique_active
    ON leads(business_id, phone) WHERE status = 'open';

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_configs ENABLE ROW LEVEL SECURITY;

-- Migration: apply new columns to existing databases
ALTER TABLE leads ADD COLUMN IF NOT EXISTS consent_source TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS opted_out BOOLEAN NOT NULL DEFAULT FALSE;
