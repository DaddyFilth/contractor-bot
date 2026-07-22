"use client";

import { useEffect, useState } from "react";
import { getSupabaseClient, type Lead } from "@/lib/supabase";
import LeadStatusBadge from "./LeadStatusBadge";

type SortKey = "created_at" | "name" | "touch_count";
type SortDir = "asc" | "desc";

const STATUS_FILTERS = ["all", "open", "responded", "closed"] as const;
type StatusFilter = (typeof STATUS_FILTERS)[number];

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function LeadsTable() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  async function loadLeads() {
    setLoading(true);
    setError(null);
    const db = getSupabaseClient();
    let query = db.from("leads").select("*");
    if (statusFilter !== "all") query = query.eq("status", statusFilter);
    query = query.order(sortKey, { ascending: sortDir === "asc" });

    const { data, error: err } = await query;
    if (err) {
      setError(err.message);
    } else {
      setLeads(data as Lead[]);
    }
    setLoading(false);
  }

  // Initial load + re-load when filters/sort change
  useEffect(() => {
    loadLeads();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, sortKey, sortDir]);

  // Real-time subscription
  useEffect(() => {
    const db = getSupabaseClient();
    const channel = db
      .channel("leads-realtime")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "leads" },
        () => loadLeads()
      )
      .subscribe();
    return () => {
      db.removeChannel(channel);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  function SortIndicator({ col }: { col: SortKey }) {
    if (sortKey !== col) return <span className="ml-1 text-gray-300">↕</span>;
    return <span className="ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>;
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-full px-3 py-1 text-sm font-medium capitalize transition-colors ${
              statusFilter === s
                ? "bg-indigo-600 text-white"
                : "bg-white text-gray-600 ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
            }`}
          >
            {s}
          </button>
        ))}
        <span className="ml-auto self-center text-sm text-gray-500">
          {leads.length} lead{leads.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th
                className="cursor-pointer px-4 py-3 text-left font-semibold text-gray-700 hover:bg-gray-100"
                onClick={() => toggleSort("name")}
              >
                Name <SortIndicator col="name" />
              </th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Phone</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Service</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Source</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Status</th>
              <th
                className="cursor-pointer px-4 py-3 text-left font-semibold text-gray-700 hover:bg-gray-100"
                onClick={() => toggleSort("touch_count")}
              >
                Touches <SortIndicator col="touch_count" />
              </th>
              <th
                className="cursor-pointer px-4 py-3 text-left font-semibold text-gray-700 hover:bg-gray-100"
                onClick={() => toggleSort("created_at")}
              >
                Created <SortIndicator col="created_at" />
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                  Loading…
                </td>
              </tr>
            ) : leads.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                  No leads found.
                </td>
              </tr>
            ) : (
              leads.map((lead) => (
                <tr key={lead.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{lead.name}</td>
                  <td className="px-4 py-3 text-gray-600">{lead.phone}</td>
                  <td className="px-4 py-3 text-gray-600">{lead.service ?? "—"}</td>
                  <td className="px-4 py-3 text-gray-600 capitalize">{lead.source ?? "—"}</td>
                  <td className="px-4 py-3">
                    <LeadStatusBadge status={lead.status} />
                    {lead.opted_out && (
                      <span className="ml-1 text-xs text-red-500">opted out</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{lead.touch_count}</td>
                  <td className="px-4 py-3 text-gray-600">{formatDate(lead.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
