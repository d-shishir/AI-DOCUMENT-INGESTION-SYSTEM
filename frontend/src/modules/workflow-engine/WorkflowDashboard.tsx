import React, { useEffect, useState, useCallback } from "react";
import { 
  Play, Plus, CheckCircle2, XCircle, RefreshCw, 
  Loader2, Sparkles, Send, FileText, 
  Clock, Database, Mail, ShieldAlert
} from "lucide-react";

interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: string[];
  created_at: string;
}

interface StepLog {
  id: string;
  step_name: string;
  status: "success" | "failed" | "running" | "pending";
  execution_time_ms: number;
  retry_count: number;
  error?: string;
  input_data?: unknown;
  output_data?: unknown;
  created_at: string;
}

interface WorkflowRun {
  id: string;
  workflow_id?: string;
  workflow_name: string;
  status: "success" | "failed" | "running" | "pending";
  input_context: unknown;
  output_context: unknown;
  started_at: string;
  completed_at?: string;
  error?: string;
  steps?: StepLog[];
}

interface DocumentInfo {
  id: string;
  filename: string;
  document_type?: string;
}

interface WorkflowDashboardProps {
  backendUrl: string;
}

export function WorkflowDashboard({ backendUrl }: WorkflowDashboardProps) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<WorkflowRun | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  
  // Forms & State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState("");
  const [newWorkflowDesc, setNewWorkflowDesc] = useState("");
  const [selectedSteps, setSelectedSteps] = useState<string[]>([]);
  
  const [goalPrompt, setGoalPrompt] = useState("");
  const [planningAndRunning, setPlanningAndRunning] = useState(false);
  const [selectedRunDocId, setSelectedRunDocId] = useState("");
  
  const [loading, setLoading] = useState(true);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [customInputContext, setCustomInputContext] = useState<string>("{\n  \"document_id\": \"\"\n}");

  const handleSelectDocumentForCustomRun = (docId: string) => {
    setCustomInputContext(JSON.stringify({ document_id: docId }, null, 2));
  };

  const availableSteps = [
    { name: "extract_document", desc: "Structured Invoice/Payroll Schema Parsing", icon: FileText },
    { name: "detect_anomalies", desc: "Compliance Auditing & Fraud Verification", icon: ShieldAlert },
    { name: "summarize_document", desc: "AI Document Digest Summarization", icon: Clock },
    { name: "search_vector_db", desc: "RAG Semantic Context Querying", icon: Database },
    { name: "send_email", desc: "Mock Notification Alert Relay", icon: Mail },
    { name: "generate_report", desc: "Findings Document Assembly", icon: FileText }
  ];

  const fetchWorkflows = useCallback(async () => {
    try {
      const res = await fetch(`${backendUrl}/api/v1/workflows`);
      if (res.ok) {
        const data = await res.json();
        setWorkflows(data);
      }
    } catch (e) {
      console.error("Error loading workflows", e);
    }
  }, [backendUrl]);

  const fetchRuns = useCallback(async () => {
    try {
      const res = await fetch(`${backendUrl}/api/v1/workflows/runs`);
      if (res.ok) {
        const data = await res.json();
        setRuns(data);
      }
    } catch (e) {
      console.error("Error loading workflow runs", e);
    }
  }, [backendUrl]);

  const fetchRunDetails = useCallback(async (runId: string) => {
    try {
      const res = await fetch(`${backendUrl}/api/v1/workflows/runs/${runId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedRun(data);
      }
    } catch (e) {
      console.error("Error loading run details", e);
    }
  }, [backendUrl]);

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch(`${backendUrl}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (e) {
      console.error("Error loading documents", e);
    }
  }, [backendUrl]);

  useEffect(() => {
    let active = true;
    const run = async () => {
      await Promise.resolve();
      if (active) {
        setLoading(true);
        Promise.all([fetchWorkflows(), fetchRuns(), fetchDocuments()]).finally(() => {
          if (active) setLoading(false);
        });
      }
    };
    run();
    return () => {
      active = false;
    };
  }, [fetchWorkflows, fetchRuns, fetchDocuments]);

  // Poll active runs if any are running
  useEffect(() => {
    const hasRunning = runs.some(r => r.status === "running");
    if (!hasRunning) return;

    const timer = setInterval(() => {
      fetchRuns();
      if (selectedRun && selectedRun.status === "running") {
        fetchRunDetails(selectedRun.id);
      }
    }, 2000);

    return () => clearInterval(timer);
  }, [runs, selectedRun, fetchRuns, fetchRunDetails]);

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWorkflowName.trim() || selectedSteps.length === 0) return;

    try {
      const res = await fetch(`${backendUrl}/api/v1/workflows/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newWorkflowName,
          description: newWorkflowDesc,
          steps: selectedSteps
        })
      });

      if (res.ok) {
        fetchWorkflows();
        setShowCreateModal(false);
        setNewWorkflowName("");
        setNewWorkflowDesc("");
        setSelectedSteps([]);
      }
    } catch (e) {
      console.error("Failed to create workflow", e);
    }
  };

  const handleRunWorkflow = async (workflowId: string) => {
    let parsedInput: Record<string, unknown>;
    try {
      parsedInput = JSON.parse(customInputContext) as Record<string, unknown>;
    } catch {
      alert("Invalid JSON configuration in context input.");
      return;
    }

    try {
      const res = await fetch(`${backendUrl}/api/v1/workflows/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow_id: workflowId,
          input_context: parsedInput
        })
      });

      if (res.ok) {
        const runData = await res.json();
        fetchRuns();
        setSelectedRun(runData);
      }
    } catch (e) {
      console.error("Failed to execute workflow", e);
    }
  };

  const handlePlanAndRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goalPrompt.trim()) return;

    setPlanningAndRunning(true);
    const inputContext: Record<string, unknown> = {};
    if (selectedRunDocId.trim()) {
      inputContext["document_id"] = selectedRunDocId.trim();
    }

    try {
      const res = await fetch(`${backendUrl}/api/v1/workflows/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_goal: goalPrompt,
          input_context: inputContext
        })
      });

      if (res.ok) {
        const runData = await res.json();
        setGoalPrompt("");
        fetchWorkflows();
        fetchRuns();
        setSelectedRun(runData);
      }
    } catch (e) {
      console.error("Failed planning workflow", e);
    } finally {
      setPlanningAndRunning(false);
    }
  };

  const toggleStep = (stepName: string) => {
    if (selectedSteps.includes(stepName)) {
      setSelectedSteps(prev => prev.filter(s => s !== stepName));
    } else {
      setSelectedSteps(prev => [...prev, stepName]);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Overview Heading */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-200 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-neonTeal" />
            Workflow & Agent Orchestration
          </h2>
          <p className="text-xs text-darkMuted mt-0.5">
            Orchestrate multi-step task chains, model tool execution, and track reliability metrics.
          </p>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-neonTeal hover:bg-neonTeal/85 rounded-lg shadow-lg shadow-neonTeal/10 transition-all cursor-pointer self-start"
        >
          <Plus className="w-4 h-4" />
          Define Custom Workflow
        </button>
      </div>

      {/* Grid split: Workflows / Goal Planner (Left) and Run Details Graph (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left pane: Definition & Execution Tools */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* AI Task Planner console */}
          <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-4">
            <div>
              <h3 className="text-xs font-bold text-neonTeal uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                AI Agent Task Planner
              </h3>
              <p className="text-[10px] text-darkMuted mt-0.5">Translate natural goal statements into structured chained actions</p>
            </div>

            <form onSubmit={handlePlanAndRun} className="space-y-3">
              <div>
                <label className="block text-[10px] font-bold text-darkMuted uppercase mb-1">
                  Task Goal
                </label>
                <textarea
                  placeholder="e.g. Ingest new document, summarize findings, check for compliance anomalies, and notify team."
                  value={goalPrompt}
                  onChange={(e) => setGoalPrompt(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonTeal rounded-lg px-3 py-2 text-xs text-gray-200 placeholder:text-darkMuted outline-none min-h-[70px] resize-none transition-all"
                  required
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-darkMuted uppercase mb-1">
                  Document Context (Optional)
                </label>
                <select
                  value={selectedRunDocId}
                  onChange={(e) => setSelectedRunDocId(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonTeal rounded-lg px-3 py-2 text-xs text-gray-200 outline-none transition-all cursor-pointer"
                >
                  <option value="">-- No document context --</option>
                  {documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {doc.filename} ({doc.document_type || "generic"})
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                disabled={planningAndRunning || !goalPrompt.trim()}
                className="w-full py-2.5 text-xs font-mono font-bold uppercase tracking-wider text-white bg-neonIndigo hover:bg-neonIndigo/85 disabled:bg-neonIndigo/50 rounded-lg flex items-center justify-center gap-1.5 transition-all cursor-pointer"
              >
                {planningAndRunning ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Planning Chain...
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    Plan & Execute Workflow
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Workflow definitions list */}
          <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-4">
            <h3 className="text-xs font-bold text-darkMuted uppercase tracking-wider">
              Workflow Library
            </h3>

            {loading ? (
              <div className="py-6 flex justify-center"><Loader2 className="w-6 h-6 text-neonTeal animate-spin" /></div>
            ) : workflows.length === 0 ? (
              <p className="text-xs text-darkMuted italic text-center py-4">No custom workflows defined yet.</p>
            ) : (
              <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1">
                {workflows.map(wf => (
                  <div
                    key={wf.id}
                    className={`p-3 bg-darkBg/40 border rounded-lg transition-colors flex flex-col justify-between gap-2.5 ${
                      selectedWorkflowId === wf.id ? "border-neonTeal bg-darkBg/65" : "border-darkBorder"
                    }`}
                  >
                    <div onClick={() => setSelectedWorkflowId(wf.id === selectedWorkflowId ? null : wf.id)} className="cursor-pointer">
                      <div className="flex justify-between items-start">
                        <span className="font-semibold text-xs text-gray-200 hover:text-neonTeal transition-colors">{wf.name}</span>
                        <span className="text-[9px] font-mono text-darkMuted">[{wf.steps.length} steps]</span>
                      </div>
                      <p className="text-[10px] text-darkMuted mt-0.5 truncate">{wf.description || "No description"}</p>
                    </div>

                    {selectedWorkflowId === wf.id && (
                      <div className="space-y-3 pt-2 border-t border-darkBorder/30 animate-fadeIn">
                        <div>
                          <label className="block text-[8px] font-mono uppercase text-darkMuted mb-1">
                            Select Document context
                          </label>
                          <select
                            onChange={(e) => handleSelectDocumentForCustomRun(e.target.value)}
                            className="w-full bg-darkBg/80 border border-darkBorder focus:border-neonTeal rounded p-1 text-[10px] text-gray-300 outline-none cursor-pointer mb-2"
                          >
                            <option value="">-- Choose Document --</option>
                            {documents.map((doc) => (
                              <option key={doc.id} value={doc.id}>
                                {doc.filename}
                              </option>
                            ))}
                          </select>

                          <label className="block text-[8px] font-mono uppercase text-darkMuted mb-1">
                            Execution Parameters (JSON Context)
                          </label>
                          <textarea
                            value={customInputContext}
                            onChange={(e) => setCustomInputContext(e.target.value)}
                            className="w-full bg-darkBg/80 border border-darkBorder focus:border-neonTeal rounded p-1.5 text-[9px] font-mono text-gray-300 outline-none min-h-[55px] resize-none"
                          />
                        </div>
                        <button
                          onClick={() => handleRunWorkflow(wf.id)}
                          className="w-full py-1.5 text-[10px] font-mono font-bold uppercase tracking-wider text-darkBg bg-neonTeal hover:bg-neonTeal/85 rounded flex items-center justify-center gap-1 transition-all cursor-pointer"
                        >
                          <Play className="w-3 h-3 fill-current" />
                          Execute Run
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Workflow Run History */}
          <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-4">
            <h3 className="text-xs font-bold text-darkMuted uppercase tracking-wider">
              Execution Run History
            </h3>

            {loading ? (
              <div className="py-6 flex justify-center"><Loader2 className="w-6 h-6 text-neonTeal animate-spin" /></div>
            ) : runs.length === 0 ? (
              <p className="text-xs text-darkMuted italic text-center py-4">No executions logged.</p>
            ) : (
              <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                {runs.map(r => (
                  <div
                    key={r.id}
                    onClick={() => fetchRunDetails(r.id)}
                    className={`p-3 bg-darkBg/40 border hover:border-darkBorder/100 rounded-lg cursor-pointer transition-colors flex items-center justify-between gap-3 ${
                      selectedRun && selectedRun.id === r.id ? "border-neonIndigo bg-darkBg/65" : "border-darkBorder"
                    }`}
                  >
                    <div className="truncate">
                      <p className="font-semibold text-xs text-gray-200 truncate">{r.workflow_name}</p>
                      <p className="text-[9px] font-mono text-darkMuted mt-0.5 truncate">{r.id.split("-")[0]}... | {new Date(r.started_at).toLocaleTimeString()}</p>
                    </div>

                    <div className="shrink-0 flex items-center gap-1">
                      {r.status === "success" && <CheckCircle2 className="w-4.5 h-4.5 text-emerald-400" />}
                      {r.status === "failed" && <XCircle className="w-4.5 h-4.5 text-rose-500" />}
                      {r.status === "running" && <Loader2 className="w-4.5 h-4.5 text-neonTeal animate-spin" />}
                      {r.status === "pending" && <Clock className="w-4.5 h-4.5 text-darkMuted" />}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Right pane: Visual Execution Flow & Step Details */}
        <div className="lg:col-span-2 space-y-6">
          {selectedRun ? (
            <div className="p-6 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-6 select-text animate-fadeIn">
              
              {/* Run overview header */}
              <div className="flex justify-between items-start gap-4 border-b border-darkBorder/50 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-gray-200 text-sm">{selectedRun.workflow_name}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono uppercase font-bold border ${
                      selectedRun.status === "success"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : selectedRun.status === "failed"
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        : "bg-neonTeal/10 text-neonTeal border-neonTeal/20 animate-pulse"
                    }`}>
                      {selectedRun.status}
                    </span>
                  </div>
                  <p className="text-[10px] text-darkMuted font-mono mt-1">Run UUID: {selectedRun.id}</p>
                </div>

                <div className="text-right text-[10px] text-darkMuted space-y-0.5">
                  <p>Started: {new Date(selectedRun.started_at).toLocaleString()}</p>
                  {selectedRun.completed_at && (
                    <p>Duration: {Math.max(0, Math.round((new Date(selectedRun.completed_at).getTime() - new Date(selectedRun.started_at).getTime())))} ms</p>
                  )}
                </div>
              </div>

              {/* Visual graph / node flow */}
              <div>
                <span className="text-[10px] font-bold text-darkMuted uppercase tracking-wider block mb-4">
                  Visual Execution Graph (Pipeline View)
                </span>
                
                {/* Visual pipeline layout */}
                <div className="flex flex-col space-y-6 relative pl-6">
                  {/* Vertical connector line */}
                  <div className="absolute left-[33px] top-4 bottom-4 w-0.5 bg-darkBorder/60" />

                  {selectedRun.steps && selectedRun.steps.map((step) => {
                    const isSuccess = step.status === "success";
                    const isFailed = step.status === "failed";
                    const isRetried = step.retry_count > 0;
                    
                    return (
                      <div key={step.id} className="relative flex gap-4 items-start animate-fadeIn">
                        {/* Node bubble */}
                        <div className={`relative z-10 w-9 h-9 rounded-full flex items-center justify-center border transition-all ${
                          isSuccess
                            ? "bg-emerald-950/20 border-emerald-500 text-emerald-400"
                            : isFailed
                            ? "bg-rose-950/20 border-rose-500 text-rose-400"
                            : "bg-darkPanel border-neonTeal text-neonTeal animate-pulse"
                        }`}>
                          {isSuccess && <CheckCircle2 className="w-4 h-4" />}
                          {isFailed && <XCircle className="w-4 h-4" />}
                          {!isSuccess && !isFailed && <Loader2 className="w-4 h-4 animate-spin" />}
                        </div>

                        {/* Step Details Card */}
                        <div className="flex-1 bg-darkBg/35 border border-darkBorder hover:border-darkBorder/100 rounded-xl p-4 space-y-2">
                          <div className="flex justify-between items-center gap-2">
                            <span className="font-semibold text-xs text-gray-200">{step.step_name}</span>
                            <div className="flex items-center gap-2 text-[10px]">
                              {isRetried && (
                                <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono text-[9px] flex items-center gap-0.5">
                                  <RefreshCw className="w-2.5 h-2.5 animate-spin" /> {step.retry_count} retries
                                </span>
                              )}
                              <span className="text-darkMuted font-mono">{step.execution_time_ms} ms</span>
                            </div>
                          </div>

                          {step.error && (
                            <p className="text-[10px] text-rose-400 bg-rose-950/20 p-2 rounded-lg border border-rose-900/30 font-mono">
                              [ERROR] {step.error}
                            </p>
                          )}

                          {!!step.output_data && (
                            <div className="space-y-1 pt-1 border-t border-darkBorder/20">
                              <p className="text-[8px] font-mono uppercase text-darkMuted">Output Context Payload</p>
                              <pre className="text-[10px] font-mono bg-darkBg/60 p-2 rounded max-h-[100px] overflow-y-auto text-gray-300 leading-normal">
                                {JSON.stringify(step.output_data, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Final combined context log */}
              <div className="space-y-2 border-t border-darkBorder/50 pt-4">
                <span className="text-[10px] font-bold text-darkMuted uppercase tracking-wider block">
                  Final Run Context Out
                </span>
                <pre className="text-[10px] font-mono bg-darkBg/40 p-4 rounded-xl border border-darkBorder text-gray-300 max-h-[180px] overflow-y-auto">
                  {JSON.stringify(selectedRun.output_context, null, 2)}
                </pre>
              </div>

            </div>
          ) : (
            <div className="p-8 border border-dashed border-darkBorder rounded-xl bg-darkPanel/10 min-h-[400px] flex flex-col items-center justify-center text-center text-darkMuted space-y-3 select-none">
              <Plus className="w-10 h-10 text-darkMuted animate-pulse stroke-1" />
              <p className="text-sm font-semibold text-gray-400">Execution Panel Ready</p>
              <p className="text-xs max-w-sm">Select an active run from the history log list or submit a planner goal to view visual workflows and step auditing outputs.</p>
            </div>
          )}
        </div>

      </div>

      {/* Modal - Create Workflow */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-darkBg/75 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-md bg-darkPanel border border-darkBorder rounded-2xl p-6 shadow-2xl space-y-5 animate-scaleIn">
            <div>
              <h3 className="text-base font-bold text-gray-200">Define Custom Workflow</h3>
              <p className="text-xs text-darkMuted mt-0.5">Configure reusable steps for ad-hoc tool calling execution.</p>
            </div>

            <form onSubmit={handleCreateWorkflow} className="space-y-4">
              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-darkMuted uppercase">
                  Workflow Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Audit & Report Pipeline"
                  value={newWorkflowName}
                  onChange={(e) => setNewWorkflowName(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonTeal rounded-lg px-3 py-2 text-xs text-gray-200 outline-none transition-all"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-bold text-darkMuted uppercase">
                  Description
                </label>
                <input
                  type="text"
                  placeholder="Summarize workflow goals..."
                  value={newWorkflowDesc}
                  onChange={(e) => setNewWorkflowDesc(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonTeal rounded-lg px-3 py-2 text-xs text-gray-200 outline-none transition-all"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-[10px] font-bold text-darkMuted uppercase">
                  Select Chain Steps (Ordered)
                </label>
                <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1">
                  {availableSteps.map(step => {
                    const isSelected = selectedSteps.includes(step.name);
                    const StepIcon = step.icon;
                    return (
                      <button
                        key={step.name}
                        type="button"
                        onClick={() => toggleStep(step.name)}
                        className={`w-full p-2.5 rounded-lg border text-left flex items-start gap-2.5 cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-neonTeal/5 border-neonTeal text-gray-200"
                            : "bg-darkBg/40 border-darkBorder text-darkMuted hover:border-darkBorder/100"
                        }`}
                      >
                        <StepIcon className={`w-4 h-4 shrink-0 mt-0.5 ${isSelected ? "text-neonTeal" : ""}`} />
                        <div>
                          <p className="font-semibold text-xs">{step.name}</p>
                          <p className="text-[9px] opacity-70">{step.desc}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewWorkflowName("");
                    setNewWorkflowDesc("");
                    setSelectedSteps([]);
                  }}
                  className="px-4 py-2 text-xs font-semibold bg-darkBorder/40 hover:bg-darkBorder text-gray-300 rounded-lg transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newWorkflowName.trim() || selectedSteps.length === 0}
                  className="px-4 py-2 text-xs font-semibold bg-neonTeal hover:bg-neonTeal/85 text-white rounded-lg shadow-lg shadow-neonTeal/10 transition-colors cursor-pointer"
                >
                  Save Definition
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
