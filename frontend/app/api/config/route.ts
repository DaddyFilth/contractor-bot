/**
 * Next.js API route that proxies /config and /config/reload calls to the
 * Python backend, injecting the webhook secret server-side so it never
 * reaches the browser.
 */
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL ?? "";
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET ?? "";

function backendHeaders() {
  return {
    "x-webhook-secret": WEBHOOK_SECRET,
    "Content-Type": "application/json",
  };
}

export async function GET() {
  if (!API_URL) {
    return NextResponse.json({ error: "API_URL not configured" }, { status: 500 });
  }
  const res = await fetch(`${API_URL}/config`, { headers: backendHeaders() });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function POST(req: NextRequest) {
  if (!API_URL) {
    return NextResponse.json({ error: "API_URL not configured" }, { status: 500 });
  }
  // POST /config/reload on the backend does not require a body.
  const res = await fetch(`${API_URL}/config/reload`, {
    method: "POST",
    headers: backendHeaders(),
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
