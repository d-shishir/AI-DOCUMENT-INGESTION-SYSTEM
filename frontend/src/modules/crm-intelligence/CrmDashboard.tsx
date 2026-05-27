import React, { useEffect, useState, useCallback } from "react";
import { 
  Users, Plus, Search, Loader2, Sparkles, ShieldAlert,
  Mail, User, Globe,
  Eye, RefreshCw, Filter, List, LayoutGrid, Check, Copy
} from "lucide-react";

interface Lead {
  id: string;
  name: string;
  email: string;
  company: string;
  role: string | null;
  country: string | null;
  source: string | null;
  status: "new" | "contacted" | "qualified" | "converted";
  company_description: string | null;
  industry: string | null;
  estimated_size: string | null;
  relevance_score: number | null;
  lead_score: number;
  scoring_reasoning: string | null;
  outreach_templates: {
    email?: string;
    linkedin?: string;
    followup?: string;
  } | null;
  created_at: string;
}

interface CrmDashboardProps {
  backendUrl: string;
}

export function CrmDashboard({ backendUrl }: CrmDashboardProps) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  
  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [scoreFilter, setScoreFilter] = useState("all"); // all | high (>=80) | medium (50-79) | low (<50)
  const [viewMode, setViewMode] = useState<"kanban" | "table">("kanban");
  
  // Modal forms
  const [showAddLeadModal, setShowAddLeadModal] = useState(false);
  const [newLeadName, setNewLeadName] = useState("");
  const [newLeadEmail, setNewLeadEmail] = useState("");
  const [newLeadCompany, setNewLeadCompany] = useState("");
  const [newLeadRole, setNewLeadRole] = useState("");
  const [newLeadCountry, setNewLeadCountry] = useState("");
  const [newLeadSource, setNewLeadSource] = useState("");
  const [autoRunWorkflow, setAutoRunWorkflow] = useState(true);

  // Status Loaders
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [activeOutreachTab, setActiveOutreachTab] = useState<"email" | "linkedin" | "followup">("email");

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/api/v1/crm/leads`);
      if (res.ok) {
        const data = await res.json();
        setLeads(data);
      }
    } catch (e) {
      console.error("Failed to load leads", e);
    } finally {
      setLoading(false);
    }
  }, [backendUrl]);

  useEffect(() => {
    let active = true;
    const run = async () => {
      await Promise.resolve();
      if (active) {
        fetchLeads();
      }
    };
    run();
    return () => {
      active = false;
    };
  }, [fetchLeads]);

  // Search trigger
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      fetchLeads();
      return;
    }
    
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/api/v1/crm/leads/search?query=${encodeURIComponent(searchQuery)}`);
      if (res.ok) {
        const data = await res.json();
        setLeads(data);
      }
    } catch (e) {
      console.error("Failed search leads", e);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLeadName.trim() || !newLeadEmail.trim() || !newLeadCompany.trim()) return;

    setSubmitting(true);
    try {
      const res = await fetch(`${backendUrl}/api/v1/crm/leads/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newLeadName,
          email: newLeadEmail,
          company: newLeadCompany,
          role: newLeadRole || undefined,
          country: newLeadCountry || undefined,
          source: newLeadSource || undefined,
          trigger_workflow: autoRunWorkflow
        })
      });

      if (res.ok) {
        const data = await res.json();
        await fetchLeads();
        setShowAddLeadModal(false);
        // Reset form
        setNewLeadName("");
        setNewLeadEmail("");
        setNewLeadCompany("");
        setNewLeadRole("");
        setNewLeadCountry("");
        setNewLeadSource("");
        
        // Auto-select the newly created lead to show details
        setSelectedLead(data);
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to create lead.");
      }
    } catch (e) {
      console.error("Failed to add lead", e);
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusChange = async (leadId: string, newStatus: string) => {
    try {
      const res = await fetch(`${backendUrl}/api/v1/crm/leads/${leadId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        const updated = await res.json();
        setLeads(prev => prev.map(l => l.id === leadId ? updated : l));
        if (selectedLead && selectedLead.id === leadId) {
          setSelectedLead(updated);
        }
      }
    } catch (e) {
      console.error("Failed update status", e);
    }
  };

  const handleEnrich = async (leadId: string) => {
    setActionLoading("enrich");
    try {
      const res = await fetch(`${backendUrl}/api/v1/crm/leads/enrich/${leadId}`, { method: "POST" });
      if (res.ok) {
        const updated = await res.json();
        setLeads(prev => prev.map(l => l.id === leadId ? updated : l));
        setSelectedLead(updated);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(null);
    }
  };

  const handleScore = async (leadId: string) => {
    setActionLoading("score");
    try {
      const res = await fetch(`${backendUrl}/api/v1/crm/leads/score/${leadId}`, { method: "POST" });
      if (res.ok) {
        const updated = await res.json();
        setLeads(prev => prev.map(l => l.id === leadId ? updated : l));
        setSelectedLead(updated);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(null);
    }
  };

  const handleOutreach = async (leadId: string) => {
    setActionLoading("outreach");
    try {
      const res = await fetch(`${backendUrl}/api/v1/crm/leads/generate-outreach/${leadId}`, { method: "POST" });
      if (res.ok) {
        const updated = await res.json();
        setLeads(prev => prev.map(l => l.id === leadId ? updated : l));
        setSelectedLead(updated);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(null);
    }
  };

  // Run Onboarding Workflow (day 7 trigger)
  const handleOnboardingWorkflow = async (leadId: string) => {
    setActionLoading("workflow");
    try {
      // Trigger execution via day 7 workflow run endpoint directly using specific steps
      const res = await fetch(`${backendUrl}/api/v1/workflows/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          input_context: { lead_id: leadId },
          user_goal: "enrich this lead, calculate fit qualification scoring, and generate custom copywriting outreach"
        })
      });
      if (res.ok) {
        // Fetch refreshed details
        const leadRes = await fetch(`${backendUrl}/api/v1/crm/leads/${leadId}`);
        if (leadRes.ok) {
          const updated = await leadRes.json();
          setLeads(prev => prev.map(l => l.id === leadId ? updated : l));
          setSelectedLead(updated);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(null);
    }
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Filtered Leads
  const filteredLeads = leads.filter(l => {
    if (statusFilter !== "all" && l.status !== statusFilter) return false;
    if (scoreFilter !== "all") {
      if (scoreFilter === "high" && l.lead_score < 80) return false;
      if (scoreFilter === "medium" && (l.lead_score < 50 || l.lead_score >= 80)) return false;
      if (scoreFilter === "low" && l.lead_score >= 50) return false;
    }
    return true;
  });

  const kanbanColumns = [
    { id: "new", title: "New Prospects", accent: "border-sky-500 text-sky-400 bg-sky-500/5" },
    { id: "contacted", title: "Outreach Contacted", accent: "border-amber-500 text-amber-400 bg-amber-500/5" },
    { id: "qualified", title: "Sales Qualified", accent: "border-emerald-500 text-emerald-400 bg-emerald-500/5" },
    { id: "converted", title: "Converted Customers", accent: "border-neonTeal text-neonTeal bg-neonTeal/5" }
  ];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-200 flex items-center gap-2">
            <Users className="w-5 h-5 text-neonIndigo" />
            CRM Intelligence & Sales Automation
          </h2>
          <p className="text-xs text-darkMuted mt-0.5">
            AI enrichment, predictive lead fit scoring, personalized copywriter engine, and pipeline workflows.
          </p>
        </div>
        
        <button
          onClick={() => setShowAddLeadModal(true)}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-neonIndigo hover:bg-neonIndigo/85 rounded-lg shadow-lg shadow-neonIndigo/10 transition-all cursor-pointer self-start"
        >
          <Plus className="w-4 h-4" />
          Onboard New Lead
        </button>
      </div>

      {/* Control Bar (Search/Filters) */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between p-4 bg-darkPanel/25 border border-darkBorder rounded-xl">
        <form onSubmit={handleSearch} className="flex gap-2 w-full md:max-w-md">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search by Name, Company, Email, Industry..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonIndigo rounded-lg pl-9 pr-4 py-2 text-xs text-gray-200 outline-none transition-all"
            />
            <Search className="w-3.5 h-3.5 text-darkMuted absolute left-3 top-3" />
          </div>
          <button
            type="submit"
            className="px-4 py-2 text-xs font-semibold text-white bg-darkBorder/60 hover:bg-darkBorder border border-darkBorder rounded-lg transition-colors cursor-pointer"
          >
            Find
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto justify-end">
          {/* Status filter */}
          <div className="flex items-center gap-1.5 text-xs text-darkMuted">
            <Filter className="w-3.5 h-3.5" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-darkBg/60 border border-darkBorder rounded-lg px-2.5 py-1.5 text-xs text-gray-300 outline-none cursor-pointer"
            >
              <option value="all">ALL STAGES</option>
              <option value="new">NEW PROSPECTS</option>
              <option value="contacted">CONTACTED</option>
              <option value="qualified">QUALIFIED</option>
              <option value="converted">CONVERTED</option>
            </select>
          </div>

          {/* Score filter */}
          <div className="flex items-center gap-1.5 text-xs text-darkMuted">
            <select
              value={scoreFilter}
              onChange={(e) => setScoreFilter(e.target.value)}
              className="bg-darkBg/60 border border-darkBorder rounded-lg px-2.5 py-1.5 text-xs text-gray-300 outline-none cursor-pointer"
            >
              <option value="all">ALL SCORES</option>
              <option value="high">HIGH FIT (&gt;=80)</option>
              <option value="medium">MEDIUM FIT (50-79)</option>
              <option value="low">LOW FIT (&lt;50)</option>
            </select>
          </div>

          <div className="border-l border-darkBorder/50 h-5 mx-1" />

          {/* View toggle */}
          <div className="flex gap-1">
            <button
              onClick={() => setViewMode("kanban")}
              className={`p-1.5 rounded-lg border transition-all cursor-pointer ${
                viewMode === "kanban"
                  ? "bg-neonIndigo/15 text-neonIndigo border-neonIndigo/30"
                  : "bg-darkPanel/20 text-darkMuted border-darkBorder hover:text-gray-300"
              }`}
              title="Kanban Board"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode("table")}
              className={`p-1.5 rounded-lg border transition-all cursor-pointer ${
                viewMode === "table"
                  ? "bg-neonIndigo/15 text-neonIndigo border-neonIndigo/30"
                  : "bg-darkPanel/20 text-darkMuted border-darkBorder hover:text-gray-300"
              }`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Board view */}
      {loading ? (
        <div className="py-24 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-neonIndigo animate-spin" />
          <p className="text-xs font-mono text-darkMuted">Loading leads CRM database...</p>
        </div>
      ) : viewMode === "kanban" ? (
        /* Kanban pipeline board */
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 items-start">
          {kanbanColumns.map(col => {
            const colLeads = filteredLeads.filter(l => l.status === col.id);
            return (
              <div key={col.id} className="p-4 bg-darkPanel/15 border border-darkBorder rounded-xl space-y-4 min-h-[400px]">
                <div className={`border-l-2 pl-2.5 py-0.5 flex justify-between items-center text-xs font-bold uppercase tracking-wider ${col.accent.split(" ")[0]} ${col.accent.split(" ")[1]}`}>
                  <span>{col.title}</span>
                  <span className="px-1.5 py-0.5 rounded-md bg-darkBorder/40 text-gray-300 font-mono text-[10px]">
                    {colLeads.length}
                  </span>
                </div>

                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                  {colLeads.map(lead => (
                    <div
                      key={lead.id}
                      onClick={() => setSelectedLead(lead)}
                      className="p-3 bg-darkBg/40 border border-darkBorder hover:border-neonIndigo/40 hover:bg-darkBg/70 rounded-lg cursor-pointer transition-all space-y-2.5 group relative"
                    >
                      {/* Corner telemetry */}
                      <span className="absolute top-2 right-2 text-[8px] font-mono text-darkMuted opacity-25 group-hover:opacity-60 transition-opacity">
                        Score: {lead.lead_score}
                      </span>

                      <div>
                        <h4 className="font-semibold text-xs text-gray-200 group-hover:text-neonIndigo transition-colors truncate">
                          {lead.name}
                        </h4>
                        <p className="text-[10px] text-darkMuted truncate">{lead.role || "Role unspecified"}</p>
                      </div>

                      <div className="flex justify-between items-center gap-2 text-[10px]">
                        <span className="font-medium text-gray-300 truncate max-w-[100px]">{lead.company}</span>
                        {lead.lead_score >= 80 ? (
                          <span className="px-1 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[8px] font-mono font-bold animate-pulse">
                            HIGH FIT
                          </span>
                        ) : lead.lead_score >= 50 ? (
                          <span className="px-1 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[8px] font-mono font-bold">
                            MID FIT
                          </span>
                        ) : (
                          <span className="px-1 py-0.5 rounded bg-darkBorder/40 text-darkMuted text-[8px] font-mono font-bold">
                            LOW FIT
                          </span>
                        )}
                      </div>
                    </div>
                  ))}

                  {colLeads.length === 0 && (
                    <p className="text-[10px] text-darkMuted italic text-center py-8">No leads in stage.</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Dense Table View */
        <div className="overflow-hidden border border-darkBorder rounded-xl bg-darkPanel/20">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-darkBorder bg-darkPanel/40 text-xs font-semibold text-darkMuted uppercase tracking-wider">
                  <th className="py-3.5 px-6">Name</th>
                  <th className="py-3.5 px-6">Company</th>
                  <th className="py-3.5 px-6">Industry</th>
                  <th className="py-3.5 px-6">Lead Score</th>
                  <th className="py-3.5 px-6">Stage</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-darkBorder/30 text-xs">
                {filteredLeads.map(lead => (
                  <tr key={lead.id} className="hover:bg-darkPanel/40 transition-colors">
                    <td className="py-3 px-6 font-semibold text-gray-200">
                      <div>
                        <p>{lead.name}</p>
                        <p className="text-[10px] text-darkMuted font-mono">{lead.email}</p>
                      </div>
                    </td>
                    <td className="py-3 px-6 text-gray-300">
                      <p className="font-medium">{lead.company}</p>
                      <p className="text-[10px] text-darkMuted">{lead.role || "Role unspecified"}</p>
                    </td>
                    <td className="py-3 px-6 text-darkMuted font-medium">{lead.industry || "Pending Enrichment"}</td>
                    <td className="py-3 px-6">
                      <div className="flex items-center gap-2">
                        <span className={`font-mono font-bold ${
                          lead.lead_score >= 80 ? "text-emerald-400" : lead.lead_score >= 50 ? "text-amber-400" : "text-darkMuted"
                        }`}>
                          {lead.lead_score}/100
                        </span>
                        <div className="w-16 bg-darkBorder/50 h-1 rounded overflow-hidden">
                          <div 
                            className={`h-full ${
                              lead.lead_score >= 80 ? "bg-emerald-400" : lead.lead_score >= 50 ? "bg-amber-500" : "bg-darkBorder"
                            }`}
                            style={{ width: `${lead.lead_score}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-6">
                      <span className={`px-1.5 py-0.5 rounded-full text-[8px] uppercase font-bold border ${
                        lead.status === "qualified"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : lead.status === "converted"
                          ? "bg-neonTeal/10 text-neonTeal border-neonTeal/20"
                          : lead.status === "contacted"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : "bg-sky-500/10 text-sky-400 border-sky-500/20"
                      }`}>
                        {lead.status}
                      </span>
                    </td>
                    <td className="py-3 px-6 text-right">
                      <button
                        onClick={() => setSelectedLead(lead)}
                        className="px-2.5 py-1 text-[10px] font-bold text-neonIndigo hover:bg-neonIndigo/10 rounded-lg border border-neonIndigo/20 transition-all cursor-pointer inline-flex items-center gap-1"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Inspect Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal - Lead Details & AI Copywriter */}
      {selectedLead && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-darkBg/80 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-4xl bg-darkPanel border border-darkBorder rounded-2xl p-6 shadow-2xl space-y-6 select-text max-h-[90vh] overflow-y-auto animate-scaleIn">
            
            {/* Modal Header */}
            <div className="flex justify-between items-start border-b border-darkBorder/40 pb-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-base font-bold text-gray-200">{selectedLead.name}</h3>
                  <select
                    value={selectedLead.status}
                    onChange={(e) => handleStatusChange(selectedLead.id, e.target.value)}
                    className="bg-darkBg/60 border border-darkBorder/60 rounded px-2 py-0.5 text-[9px] font-mono text-gray-300 font-bold uppercase tracking-wider focus:border-neonIndigo outline-none cursor-pointer"
                  >
                    <option value="new">NEW PROSPECT</option>
                    <option value="contacted">CONTACTED</option>
                    <option value="qualified">QUALIFIED</option>
                    <option value="converted">CONVERTED</option>
                  </select>
                </div>
                <p className="text-[10px] text-darkMuted font-mono mt-1">Lead ID: {selectedLead.id}</p>
              </div>

              <button
                onClick={() => setSelectedLead(null)}
                className="px-2 py-1 text-xs text-darkMuted hover:text-white bg-darkBorder/30 hover:bg-darkBorder border border-darkBorder/50 rounded-lg cursor-pointer"
              >
                Close Portal
              </button>
            </div>

            {/* Split layout: Profile & Score (Left) and Outreach & Actions (Right) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Left pane (col-span-5) */}
              <div className="lg:col-span-5 space-y-5">
                {/* Contact data card */}
                <div className="p-4 bg-darkBg/40 border border-darkBorder rounded-xl space-y-3 text-xs leading-normal">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-neonTeal" />
                    <div>
                      <p className="text-[9px] font-mono uppercase text-darkMuted leading-none">Role at Company</p>
                      <p className="font-semibold text-gray-200 mt-0.5">{selectedLead.role || "Role unspecified"}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4 text-neonIndigo" />
                    <div>
                      <p className="text-[9px] font-mono uppercase text-darkMuted leading-none">Geography & Origin</p>
                      <p className="font-semibold text-gray-200 mt-0.5">{selectedLead.country || "Global"} | Source: {selectedLead.source || "Organic"}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-yellow-500" />
                    <div>
                      <p className="text-[9px] font-mono uppercase text-darkMuted leading-none">Corporate Email</p>
                      <p className="font-semibold text-gray-200 mt-0.5">{selectedLead.email}</p>
                    </div>
                  </div>
                </div>

                {/* Score radial gauge */}
                <div className="p-4 bg-darkBg/40 border border-darkBorder rounded-xl space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold text-darkMuted uppercase tracking-wider">Lead Fit Score</span>
                    <span className={`px-2 py-0.5 rounded text-[8px] font-mono font-bold uppercase border ${
                      selectedLead.lead_score >= 80
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 animate-pulse"
                        : selectedLead.lead_score >= 50
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-darkBorder/40 text-darkMuted"
                    }`}>
                      {selectedLead.lead_score >= 80 ? "Hot prospect" : selectedLead.lead_score >= 50 ? "Warm prospect" : "Cold fit"}
                    </span>
                  </div>

                  <div className="flex items-center gap-4">
                    {/* Ring gauge */}
                    {(() => {
                      const score = selectedLead.lead_score;
                      const radius = 25;
                      const circumference = 2 * Math.PI * radius;
                      const offset = circumference - (score / 100) * circumference;
                      return (
                        <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
                          <svg className="w-full h-full transform -rotate-90">
                            <circle cx="32" cy="32" r={radius} stroke="#1b1e28" strokeWidth="3.5" fill="transparent" />
                            <circle 
                              cx="32" 
                              cy="32" 
                              r={radius} 
                              stroke={score >= 80 ? "#10b981" : score >= 50 ? "#f59e0b" : "#4b5563"} 
                              strokeWidth="4.5" 
                              fill="transparent" 
                              strokeDasharray={circumference}
                              strokeDashoffset={offset}
                              strokeLinecap="round"
                            />
                          </svg>
                          <span className="absolute font-mono text-sm font-bold text-gray-100">{score}%</span>
                        </div>
                      );
                    })()}

                    <div className="text-xs text-darkMuted leading-relaxed">
                      <p className="font-semibold text-gray-300">Scoring Analysis</p>
                      <p className="text-[10px] mt-0.5 italic">"{selectedLead.scoring_reasoning || "Scoring engine pending execution."}"</p>
                    </div>
                  </div>
                </div>

                {/* Enrichment Card */}
                <div className="p-4 bg-darkBg/40 border border-darkBorder rounded-xl space-y-3 text-xs leading-normal">
                  <span className="text-[10px] font-bold text-darkMuted uppercase tracking-wider block">AI Enrichment Profile</span>
                  
                  <div className="grid grid-cols-2 gap-2 text-[10px]">
                    <div className="p-2 bg-darkPanel/25 border border-darkBorder/40 rounded-lg">
                      <span className="text-darkMuted block">Industry</span>
                      <span className="font-semibold text-gray-200 truncate block mt-0.5">{selectedLead.industry || "Pending"}</span>
                    </div>
                    <div className="p-2 bg-darkPanel/25 border border-darkBorder/40 rounded-lg">
                      <span className="text-darkMuted block">Company Size</span>
                      <span className="font-semibold text-gray-200 truncate block mt-0.5">{selectedLead.estimated_size || "Pending"}</span>
                    </div>
                  </div>

                  <div>
                    <span className="text-[9px] font-mono uppercase text-darkMuted block mb-0.5">Company Description</span>
                    <p className="text-[10px] text-gray-300 italic leading-relaxed bg-darkBg/40 p-2.5 rounded-lg border border-darkBorder/40">
                      {selectedLead.company_description || "Enrichment engine pending execution."}
                    </p>
                  </div>
                </div>

              </div>

              {/* Right pane (col-span-7) */}
              <div className="lg:col-span-7 space-y-5">
                
                {/* Sales Copywriter Templates Tabs */}
                <div className="p-5 bg-darkBg/40 border border-darkBorder rounded-xl space-y-4 flex flex-col justify-between">
                  <div className="flex justify-between items-center border-b border-darkBorder/30 pb-2">
                    <span className="text-[10px] font-bold text-darkMuted uppercase tracking-wider">AI Outreach copywriter</span>
                    <span className="text-[9px] text-neonIndigo font-mono font-bold animate-pulse">Personalized Copy</span>
                  </div>

                  {selectedLead.outreach_templates ? (
                    <div className="space-y-3 flex-1 flex flex-col justify-between">
                      {/* Copywriter tab buttons */}
                      <div className="flex border-b border-darkBorder/20">
                        {(["email", "linkedin", "followup"] as const).map(tab => (
                          <button
                            key={tab}
                            onClick={() => setActiveOutreachTab(tab)}
                            className={`px-3 py-1.5 text-[10px] font-mono font-bold uppercase border-b-2 transition-all cursor-pointer ${
                              activeOutreachTab === tab
                                ? "border-neonIndigo text-neonIndigo"
                                : "border-transparent text-darkMuted hover:text-gray-300"
                            }`}
                          >
                            {tab === "linkedin" ? "LinkedIn Connect" : tab === "followup" ? "Follow-Up Email" : "Cold Email"}
                          </button>
                        ))}
                      </div>

                      {/* Copied visual notification */}
                      <div className="relative">
                        <textarea
                          readOnly
                          value={selectedLead.outreach_templates[activeOutreachTab] || "Template not generated."}
                          className="w-full bg-darkBg/80 border border-darkBorder rounded-lg p-3 text-xs font-sans text-gray-300 leading-relaxed min-h-[160px] outline-none"
                        />
                        <button
                          onClick={() => handleCopy(selectedLead.outreach_templates![activeOutreachTab] || "", activeOutreachTab)}
                          className="absolute right-2 top-2 p-1.5 rounded-lg bg-darkPanel border border-darkBorder text-gray-400 hover:text-white hover:border-darkBorder/100 transition-colors cursor-pointer"
                          title="Copy text to clipboard"
                        >
                          {copiedKey === activeOutreachTab ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="py-12 border border-dashed border-darkBorder/40 rounded-xl bg-darkPanel/10 text-center select-none text-xs text-darkMuted">
                      <Mail className="w-7 h-7 mx-auto mb-2" />
                      <p className="font-semibold text-gray-400">Outreach Copy Pending</p>
                      <p className="text-[10px] mt-0.5">Click 'Generate Outreach' or trigger onboarding workflow to compile sales messaging.</p>
                    </div>
                  )}
                </div>

                {/* Automation & Diagnostics control suite */}
                <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-4">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-neonIndigo uppercase tracking-wider">
                    <ShieldAlert className="w-4 h-4" />
                    <span>Agent Automation & Intelligence triggers</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    {/* Individual Step buttons */}
                    <button
                      disabled={actionLoading !== null}
                      onClick={() => handleEnrich(selectedLead.id)}
                      className="py-2.5 text-[10px] font-mono font-bold uppercase border border-darkBorder bg-darkBg hover:bg-darkBorder/50 rounded-lg flex items-center justify-center gap-1.5 disabled:opacity-50 transition-all cursor-pointer"
                    >
                      {actionLoading === "enrich" ? <Loader2 className="w-3.5 h-3.5 animate-spin text-neonTeal" /> : <RefreshCw className="w-3.5 h-3.5" />}
                      Enrich lead (RAG)
                    </button>

                    <button
                      disabled={actionLoading !== null}
                      onClick={() => handleScore(selectedLead.id)}
                      className="py-2.5 text-[10px] font-mono font-bold uppercase border border-darkBorder bg-darkBg hover:bg-darkBorder/50 rounded-lg flex items-center justify-center gap-1.5 disabled:opacity-50 transition-all cursor-pointer"
                    >
                      {actionLoading === "score" ? <Loader2 className="w-3.5 h-3.5 animate-spin text-neonTeal" /> : <ShieldAlert className="w-3.5 h-3.5" />}
                      Re-Calculate score
                    </button>

                    <button
                      disabled={actionLoading !== null}
                      onClick={() => handleOutreach(selectedLead.id)}
                      className="py-2.5 text-[10px] font-mono font-bold uppercase border border-darkBorder bg-darkBg hover:bg-darkBorder/50 rounded-lg flex items-center justify-center gap-1.5 disabled:opacity-50 transition-all cursor-pointer"
                    >
                      {actionLoading === "outreach" ? <Loader2 className="w-3.5 h-3.5 animate-spin text-neonTeal" /> : <Mail className="w-3.5 h-3.5" />}
                      Regen outreach copy
                    </button>

                    {/* Integrated Workflow trigger (day 7 executor) */}
                    <button
                      disabled={actionLoading !== null}
                      onClick={() => handleOnboardingWorkflow(selectedLead.id)}
                      className="py-2.5 text-[10px] font-mono font-bold uppercase text-white bg-neonTeal hover:bg-neonTeal/85 disabled:bg-neonTeal/50 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-lg shadow-neonTeal/10"
                      title="Triggers full pipeline execution: Enrich -> Score -> Outreach via Workflow executor"
                    >
                      {actionLoading === "workflow" ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          Running Workflow...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5" />
                          Onboarding Pipeline (Day 7)
                        </>
                      )}
                    </button>
                  </div>
                </div>

              </div>

            </div>

          </div>
        </div>
      )}

      {/* Modal - Onboard Lead */}
      {showAddLeadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-darkBg/85 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-md bg-darkPanel border border-darkBorder rounded-2xl p-6 shadow-2xl space-y-5 animate-scaleIn">
            <div>
              <h3 className="text-base font-bold text-gray-200">Onboard CRM Prospect</h3>
              <p className="text-xs text-darkMuted mt-0.5">Input lead details to trigger AI validation, RAG enrichment, and outreach.</p>
            </div>

            <form onSubmit={handleAddLead} className="space-y-4">
              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-darkMuted uppercase">
                  Prospect Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Clara Oswald"
                  value={newLeadName}
                  onChange={(e) => setNewLeadName(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonIndigo rounded-lg px-3 py-2 text-xs text-gray-200 outline-none transition-all"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-darkMuted uppercase">
                  Corporate Email
                </label>
                <input
                  type="email"
                  placeholder="e.g. clara@skaro.co.uk"
                  value={newLeadEmail}
                  onChange={(e) => setNewLeadEmail(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonIndigo rounded-lg px-3 py-2 text-xs text-gray-200 outline-none transition-all"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-darkMuted uppercase">
                  Company Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Skaro Solutions Software Ltd"
                  value={newLeadCompany}
                  onChange={(e) => setNewLeadCompany(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonIndigo rounded-lg px-3 py-2 text-xs text-gray-200 outline-none transition-all"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-darkMuted uppercase">
                    Role / Title
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. VP of Ops"
                    value={newLeadRole}
                    onChange={(e) => setNewLeadRole(e.target.value)}
                    className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonIndigo rounded-lg px-3 py-2 text-xs text-gray-200 outline-none transition-all"
                  />
                </div>
                <div className="space-y-1">
                  <label className="block text-[10px] font-bold text-darkMuted uppercase">
                    Country
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. UK"
                    value={newLeadCountry}
                    onChange={(e) => setNewLeadCountry(e.target.value)}
                    className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonIndigo rounded-lg px-3 py-2 text-xs text-gray-200 outline-none transition-all"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-darkMuted uppercase">
                  Lead Origin / Source
                </label>
                <input
                  type="text"
                  placeholder="e.g. LinkedIn Referral"
                  value={newLeadSource}
                  onChange={(e) => setNewLeadSource(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonIndigo rounded-lg px-3 py-2 text-xs text-gray-200 outline-none transition-all"
                />
              </div>

              {/* Automatic Workflow Onboard Switch */}
              <div className="flex items-center justify-between p-2 bg-darkBg/40 border border-darkBorder rounded-lg">
                <div className="text-left">
                  <p className="text-[11px] font-semibold text-gray-200 flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-neonTeal" />
                    Auto-Run Onboarding Pipeline
                  </p>
                  <p className="text-[9px] text-darkMuted">Triggers RAG enrichment, scoring, and copywriting on save.</p>
                </div>
                <input
                  type="checkbox"
                  checked={autoRunWorkflow}
                  onChange={(e) => setAutoRunWorkflow(e.target.checked)}
                  className="w-4 h-4 text-neonTeal bg-darkBg/80 border-darkBorder rounded outline-none cursor-pointer"
                />
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddLeadModal(false);
                    setNewLeadName("");
                    setNewLeadEmail("");
                    setNewLeadCompany("");
                    setNewLeadRole("");
                    setNewLeadCountry("");
                    setNewLeadSource("");
                  }}
                  className="px-4 py-2 text-xs font-semibold bg-darkBorder/40 hover:bg-darkBorder text-gray-300 rounded-lg transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !newLeadName.trim() || !newLeadEmail.trim() || !newLeadCompany.trim()}
                  className="px-4 py-2 text-xs font-semibold bg-neonIndigo hover:bg-neonIndigo/85 text-white rounded-lg shadow-lg shadow-neonIndigo/10 transition-colors cursor-pointer flex items-center gap-1"
                >
                  {submitting && <Loader2 className="w-3 h-3 animate-spin" />}
                  Save Prospect
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
