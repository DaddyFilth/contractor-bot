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
-- Only one 'open' lead per phone/business is allowed; a new lead can be
-- inserted once the previous one has been closed or responded to.
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_unique_active
    ON leads(business_id, phone) WHERE status = 'open';

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_configs ENABLE ROW LEVEL SECURITY;

-- Migration: apply new columns to existing databases
ALTER TABLE leads ADD COLUMN IF NOT EXISTS consent_source TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS opted_out BOOLEAN NOT NULL DEFAULT FALSE;

-- Rate limiting table — replaces in-memory store for serverless deployments (e.g. Vercel).
-- One row per client IP; tracks the start of the current 60-second window and the
-- number of requests recorded within it.
CREATE TABLE IF NOT EXISTS rate_limits (
    ip TEXT PRIMARY KEY,
    window_start TIMESTAMPTZ NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 1
);

-- Atomic rate-limit check-and-increment.
-- Inserts a fresh window row on first request or after expiry; otherwise
-- increments the counter in one statement using INSERT … ON CONFLICT DO UPDATE.
-- Returns TRUE if the request is within the allowed limit, FALSE if it should
-- be rejected.  Because the entire operation is a single SQL statement it is
-- free of the read-then-write race condition that a separate SELECT + UPDATE
-- would introduce.
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_ip             TEXT,
    p_limit          INTEGER DEFAULT 100,
    p_window_seconds INTEGER DEFAULT 60
) RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    v_count INTEGER;
BEGIN
    INSERT INTO rate_limits (ip, window_start, request_count)
    VALUES (p_ip, NOW(), 1)
    ON CONFLICT (ip) DO UPDATE SET
        window_start   = CASE
                             WHEN rate_limits.window_start < NOW() - (p_window_seconds || ' seconds')::INTERVAL
                             THEN NOW()
                             ELSE rate_limits.window_start
                         END,
        request_count  = CASE
                             WHEN rate_limits.window_start < NOW() - (p_window_seconds || ' seconds')::INTERVAL
                             THEN 1
                             ELSE rate_limits.request_count + 1
                         END
    RETURNING request_count INTO v_count;

    RETURN v_count <= p_limit;
END;
$$;
