"use client";

import { useEffect, useState } from "react";
import { fetchConfig, reloadConfig, type BusinessConfig } from "@/lib/api";

const TEMPLATE_LABELS: Record<string, string> = {
  instant: "Instant reply",
  followup_2h: "2-hour follow-up",
  followup_24h: "24-hour follow-up",
  followup_72h: "72-hour follow-up",
  missed_call: "Missed call",
};

export default function ConfigEditor() {
  const [config, setConfig] = useState<BusinessConfig | null>(null);
  const [form, setForm] = useState<BusinessConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    fetchConfig()
      .then((c) => {
        setConfig(c);
        setForm(structuredClone(c));
      })
      .catch((e) => setMessage({ type: "error", text: e.message }))
      .finally(() => setLoading(false));
  }, []);

  function handleField(key: keyof BusinessConfig, value: string | number) {
    setForm((prev) => prev ? { ...prev, [key]: value } : prev);
  }

  function handleTemplate(key: string, value: string) {
    setForm((prev) =>
      prev ? { ...prev, templates: { ...prev.templates, [key]: value } } : prev
    );
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await reloadConfig();
      setConfig(form);
      setMessage({ type: "success", text: "Config reloaded on the server." });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setMessage({ type: "error", text: msg });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-gray-500">Loading config…</p>;
  }

  if (!form) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        {message?.text ?? "Failed to load config."}
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="space-y-8">
      {message && (
        <div
          className={`rounded-md p-4 text-sm ${
            message.type === "success"
              ? "bg-green-50 text-green-700"
              : "bg-red-50 text-red-700"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Business details */}
      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-gray-900">Business details</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            label="Business ID"
            value={form.business_id}
            onChange={(v) => handleField("business_id", v)}
          />
          <Field
            label="Business name"
            value={form.business_name}
            onChange={(v) => handleField("business_name", v)}
          />
          <Field
            label="Owner name"
            value={form.owner_name}
            onChange={(v) => handleField("owner_name", v)}
          />
          <Field
            label="Twilio phone"
            value={form.twilio_phone}
            onChange={(v) => handleField("twilio_phone", v)}
          />
          <Field
            label="SMS cooldown (minutes)"
            type="number"
            value={String(form.sms_cooldown_minutes)}
            onChange={(v) => handleField("sms_cooldown_minutes", Number(v))}
          />
        </div>
      </section>

      {/* SMS templates */}
      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-1 text-base font-semibold text-gray-900">SMS templates</h2>
        <p className="mb-4 text-sm text-gray-500">
          Variables: <code className="rounded bg-gray-100 px-1">{"{name}"}</code>{" "}
          <code className="rounded bg-gray-100 px-1">{"{owner_name}"}</code>{" "}
          <code className="rounded bg-gray-100 px-1">{"{business_name}"}</code>{" "}
          <code className="rounded bg-gray-100 px-1">{"{service}"}</code>
        </p>
        <div className="space-y-4">
          {Object.entries(form.templates).map(([key, value]) => (
            <div key={key}>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                {TEMPLATE_LABELS[key] ?? key}
              </label>
              <textarea
                rows={3}
                value={value}
                onChange={(e) => handleTemplate(key, e.target.value)}
                className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          ))}
        </div>
      </section>

      {/* Save */}
      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-60"
        >
          {saving ? "Saving…" : "Save & reload config"}
        </button>
        {config && JSON.stringify(config) !== JSON.stringify(form) && (
          <span className="text-sm text-amber-600">Unsaved changes</span>
        )}
      </div>
    </form>
  );
}

function Field({
  label,
  value,
  type = "text",
  onChange,
}: {
  label: string;
  value: string;
  type?: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-700">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      />
    </div>
  );
}
