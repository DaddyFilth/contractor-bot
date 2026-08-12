"use client";

import { useMemo, useState } from "react";

type Status = "New" | "Contacted" | "Booked" | "Lost";
type Lead = {
  id: string;
  name: string;
  phone: string;
  service: string;
  source: string;
  time: string;
  urgency: "High" | "Normal" | "Low";
  status: Status;
};

const startingLeads: Lead[] = [
  { id: "L-1001", name: "Sarah Mitchell", phone: "(405) 555-0148", service: "Emergency AC repair", source: "After-hours call", time: "2 min ago", urgency: "High", status: "New" },
  { id: "L-1002", name: "David Wilson", phone: "(405) 555-0182", service: "Water heater quote", source: "Website form", time: "18 min ago", urgency: "Normal", status: "Contacted" },
  { id: "L-1003", name: "Amanda Lee", phone: "(405) 555-0127", service: "Roof inspection", source: "AI phone agent", time: "1 hr ago", urgency: "Normal", status: "Booked" },
  { id: "L-1004", name: "Robert King", phone: "(405) 555-0199", service: "Electrical panel issue", source: "Missed-call recovery", time: "2 hrs ago", urgency: "High", status: "New" }
];

export default function Dashboard() {
  const [leads, setLeads] = useState(startingLeads);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"All" | Status>("All");
  const [notice, setNotice] = useState("");

  const visibleLeads = useMemo(() => leads.filter((lead) => {
    const query = search.toLowerCase();
    return (filter === "All" || lead.status === filter) &&
      `${lead.name} ${lead.phone} ${lead.service}`.toLowerCase().includes(query);
  }), [leads, search, filter]);

  const updateStatus = (id: string, status: Status) => {
    setLeads((items) => items.map((lead) => lead.id === id ? { ...lead, status } : lead));
    setNotice(`Lead updated to ${status}.`);
  };

  const addTestLead = () => {
    const id = `L-${1001 + leads.length}`;
    setLeads((items) => [{
      id,
      name: "New incoming caller",
      phone: "(405) 555-0100",
      service: "Service request",
      source: "Manual test",
      time: "Just now",
      urgency: "Normal",
      status: "New"
    }, ...items]);
    setNotice("Test lead added.");
  };

  const count = (status: Status) => leads.filter((lead) => lead.status === status).length;

  return (
    <main>
      <header className="topbar">
        <div className="brand"><span className="brandMark">CB</span><span>Contractor Bot</span></div>
        <div className="online"><span className="pulse" /> Agent online</div>
      </header>

      <div className="shell">
        <section className="hero">
          <div>
            <p className="eyebrow">OPERATIONS DASHBOARD</p>
            <h1>Never miss another job.</h1>
            <p className="subhead">Capture every call, prioritize urgent work, and follow up before competitors do.</p>
          </div>
          <button className="primary" onClick={addTestLead}>+ Add test lead</button>
        </section>

        {notice && <div className="notice">{notice}<button onClick={() => setNotice("")}>×</button></div>}

        <section className="metrics">
          <article className="card"><span className="dot blue" /><p>New leads</p><strong>{count("New")}</strong><small>Need a response now</small></article>
          <article className="card"><span className="dot purple" /><p>Leads today</p><strong>{leads.length}</strong><small>Captured by your agent</small></article>
          <article className="card"><span className="dot green" /><p>Appointments</p><strong>{count("Booked")}</strong><small>Confirmed this week</small></article>
          <article className="card"><span className="dot orange" /><p>Pipeline value</p><strong>$4,850</strong><small>Open opportunities</small></article>
        </section>

        <section className="tableCard">
          <div className="tableHead">
            <div><h2>Incoming leads</h2><p>Calls and requests captured by your AI assistant.</p></div>
            <div className="controls">
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search leads" />
              <select value={filter} onChange={(e) => setFilter(e.target.value as "All" | Status)}>
                <option>All</option><option>New</option><option>Contacted</option><option>Booked</option><option>Lost</option>
              </select>
            </div>
          </div>
          <div className="scroll">
            <table>
              <thead><tr><th>Caller</th><th>Request</th><th>Urgency</th><th>Source</th><th>Status</th><th>Action</th></tr></thead>
              <tbody>
                {visibleLeads.map((lead) => <tr key={lead.id}>
                  <td><b>{lead.name}</b><span>{lead.phone} · {lead.time}</span></td>
                  <td>{lead.service}</td>
                  <td className={lead.urgency === "High" ? "urgent" : ""}>{lead.urgency}</td>
                  <td>{lead.source}</td>
                  <td><span className={`badge ${lead.status.toLowerCase()}`}>{lead.status}</span></td>
                  <td>{lead.status === "New"
                    ? <button className="action dark" onClick={() => updateStatus(lead.id, "Contacted")}>Mark contacted</button>
                    : <button className="action" onClick={() => updateStatus(lead.id, "Booked")}>Mark booked</button>}
                  </td>
                </tr>)}
                {visibleLeads.length === 0 && <tr><td colSpan={6} className="empty">No leads match your search.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>

        <section className="bottomGrid">
          <article className="agentCard"><p className="eyebrow">AI PHONE AGENT</p><h2>Ready for incoming calls</h2><p>Your Twilio-connected agent will capture caller details and alert you instantly.</p><button className="light">Configure agent</button></article>
          <article className="nextCard"><p className="eyebrow">NEXT MILESTONE</p><h2>Connect live backend data</h2><p>The dashboard is ready. Replace demo leads with leads from the deployed FastAPI service.</p><button className="linkButton">View integration guide →</button></article>
        </section>
      </div>
    </main>
  );
}
