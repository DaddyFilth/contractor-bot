/**
 * Thin wrapper for calls to the contractor-bot backend API routes.
 * All calls that require the webhook secret are proxied through
 * /api/config (a Next.js server route) so the secret never reaches
 * the browser.
 */

export type BusinessConfig = {
  business_id: string;
  business_name: string;
  owner_name: string;
  twilio_phone: string;
  templates: Record<string, string>;
  sources: string[];
  sms_cooldown_minutes: number;
};

/** Fetch the current business config via the Next.js proxy route. */
export async function fetchConfig(): Promise<BusinessConfig> {
  const res = await fetch("/api/config");
  if (!res.ok) {
    throw new Error(`Failed to fetch config: ${res.statusText}`);
  }
  const data = await res.json();
  return data.business as BusinessConfig;
}

/** Reload the backend config (triggers POST /config/reload on the Python API). */
export async function reloadConfig(): Promise<void> {
  const res = await fetch("/api/config", { method: "POST" });
  if (!res.ok) {
    throw new Error(`Config reload failed: ${res.statusText}`);
  }
}
