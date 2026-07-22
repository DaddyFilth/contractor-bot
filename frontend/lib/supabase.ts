import { createClient, type SupabaseClient } from "@supabase/supabase-js";

export type Lead = {
  id: string;
  business_id: string;
  name: string;
  phone: string;
  service: string | null;
  source: string | null;
  status: "open" | "responded" | "closed";
  opted_out: boolean;
  touch_count: number;
  created_at: string;
  next_followup_at: string | null;
};

// Singleton client — created on first access inside a browser/server component,
// never at module-evaluation time (which would fail at build without env vars).
let _client: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (!_client) {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    if (!url || !key) {
      throw new Error(
        "NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set."
      );
    }
    _client = createClient(url, key);
  }
  return _client;
}
