import { useState, useEffect, useCallback } from "react";
import { 
  Activity, Terminal, AlertTriangle, ShieldAlert, Cpu, Layers, Database, Sparkles, RefreshCw, ChevronRight, Code
} from "lucide-react";

interface Trace {
  trace_id: string;
  module: string;
  input: string;
  final_output: string;
  total_latency_ms: number;
  status: string;
  created_at: string;
}

interface Step {
  id: string;
  trace_id: string;
  step_name: string;
  status: string;
  latency_ms: number;
  metadata: any;
  created_at: string;
}

interface RAGMetric {
  id: string;
  trace_id: string;
  query: string;
  top_k: number;
  similarity_scores: number[];
  context_relevance: number;
  hallucination_score: number;
  answer_confidence: number;
  retrieved_chunks: any[];
  created_at: string;
}

interface ToolCall {
  id: string;
  trace_id: string;
  tool_name: string;
  input: any;
  output: any;
  latency_ms: number;
  status: string;
  created_at: string;
}

interface ErrorLog {
  id: string;
  trace_id: string | null;
  module: string;
  error_message: string;
  stack_trace: string;
  input_context: any;
  created_at: string;
}

interface StructuredLog {
  id: string;
  trace_id: string | null;
  module: string;
  severity: string;
  message: string;
  metadata: any;
  timestamp: string;
}

interface SystemMetrics {
  total_requests: number;
  success_requests: number;
  failed_requests: number;
  running_requests: number;
  error_rate: number;
  average_latency_ms: number;
  modules: Record<string, {
    count: number;
    avg_latency_ms: number;
    success_rate: number;
    failed_count: number;
  }>;
  rag: {
    context_relevance: number;
    hallucination_score: number;
    answer_confidence: number;
  };
  tools: Record<string, {
    invocations: number;
    avg_latency_ms: number;
    failures: number;
  }>;
  total_tokens_used: number;
}

interface ObservabilityDashboardProps {
  backendUrl: string;
}

export function ObservabilityDashboard({ backendUrl }: ObservabilityDashboardProps) {
  const [activeTab, setActiveTab] = useState<"traces" | "metrics" | "errors" | "logs">("traces");
  
  // Traces State
  const [traces, setTraces] = useState<Trace[]>([]);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [traceDetails, setTraceDetails] = useState<{
    trace: Trace;
    steps: Step[];
    rag: RAGMetric[];
    tools: ToolCall[];
    errors: ErrorLog[];
    logs: StructuredLog[];
  } | null>(null);
  const [moduleFilter, setModuleFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [loadingTraces, setLoadingTraces] = useState(false);

  // Metrics State
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  // Errors State
  const [errors, setErrors] = useState<ErrorLog[]>([]);
  const [selectedError, setSelectedError] = useState<ErrorLog | null>(null);
  const [loadingErrors, setLoadingErrors] = useState(false);

  // Logs State
  const [logs, setLogs] = useState<StructuredLog[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [loadingLogs, setLoadingLogs] = useState(false);

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Fetch traces
  const fetchTraces = useCallback(async () => {
    setLoadingTraces(true);
    try {
      let url = `${backendUrl}/api/v1/observability/traces?limit=40`;
      if (moduleFilter) url += `&module=${moduleFilter}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setTraces(data);
      }
    } catch (e) {
      console.error("Failed to load traces:", e);
    } finally {
      setLoadingTraces(false);
    }
  }, [backendUrl, moduleFilter, statusFilter]);

  // Fetch trace details
  const fetchTraceDetails = useCallback(async (traceId: string) => {
    try {
      const res = await fetch(`${backendUrl}/api/v1/observability/traces/${traceId}`);
      if (res.ok) {
        const data = await res.json();
        setTraceDetails(data);
      }
    } catch (e) {
      console.error("Failed to load trace details:", e);
    }
  }, [backendUrl]);

  // Fetch metrics
  const fetchMetrics = useCallback(async () => {
    setLoadingMetrics(true);
    try {
      const res = await fetch(`${backendUrl}/api/v1/observability/metrics/system`);
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (e) {
      console.error("Failed to load system metrics:", e);
    } finally {
      setLoadingMetrics(false);
    }
  }, [backendUrl]);

  // Fetch errors
  const fetchErrors = useCallback(async () => {
    setLoadingErrors(true);
    try {
      const res = await fetch(`${backendUrl}/api/v1/observability/errors?limit=30`);
      if (res.ok) {
        const data = await res.json();
        setErrors(data);
      }
    } catch (e) {
      console.error("Failed to load errors:", e);
    } finally {
      setLoadingErrors(false);
    }
  }, [backendUrl]);

  // Fetch logs
  const fetchLogs = useCallback(async () => {
    setLoadingLogs(true);
    try {
      let url = `${backendUrl}/api/v1/observability/logs?limit=100`;
      if (severityFilter) url += `&severity=${severityFilter}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (e) {
      console.error("Failed to load logs:", e);
    } finally {
      setLoadingLogs(false);
    }
  }, [backendUrl, severityFilter]);

  useEffect(() => {
    if (activeTab === "traces") {
      fetchTraces();
      if (selectedTraceId) {
        fetchTraceDetails(selectedTraceId);
      }
    } else if (activeTab === "metrics") {
      fetchMetrics();
    } else if (activeTab === "errors") {
      fetchErrors();
    } else if (activeTab === "logs") {
      fetchLogs();
    }
  }, [activeTab, fetchTraces, fetchTraceDetails, fetchMetrics, fetchErrors, fetchLogs, selectedTraceId, refreshTrigger]);

  const handleRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="space-y-6 animate-fadeIn text-gray-200">
      {/* Dashboard Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-darkBorder/40 pb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-200 flex items-center gap-2">
            <Activity className="w-5 h-5 text-neonIndigo animate-pulse" />
            AI Operations Control Center (Observability)
          </h2>
          <p className="text-xs text-darkMuted mt-0.5">
            Real-time execution tracing, RAG quality scoring, LLM token meters, and distributed call profiling.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-bold uppercase tracking-wider text-gray-300 bg-darkPanel border border-darkBorder hover:border-neonIndigo/50 rounded-lg transition-all cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs list */}
      <div className="flex border-b border-darkBorder/40">
        <button
          onClick={() => setActiveTab("traces")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeTab === "traces"
              ? "border-neonIndigo text-neonIndigo"
              : "border-transparent text-darkMuted hover:text-gray-300"
          }`}
        >
          🔍 Traces & Profiler
        </button>
        <button
          onClick={() => setActiveTab("metrics")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeTab === "metrics"
              ? "border-neonIndigo text-neonIndigo"
              : "border-transparent text-darkMuted hover:text-gray-300"
          }`}
        >
          📊 System Metrics
        </button>
        <button
          onClick={() => setActiveTab("errors")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeTab === "errors"
              ? "border-neonIndigo text-neonIndigo"
              : "border-transparent text-darkMuted hover:text-gray-300"
          }`}
        >
          🚨 Crash Log Tracker
        </button>
        <button
          onClick={() => setActiveTab("logs")}
          className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeTab === "logs"
              ? "border-neonIndigo text-neonIndigo"
              : "border-transparent text-darkMuted hover:text-gray-300"
          }`}
        >
          📋 Structured Logs
        </button>
      </div>

      {/* TAB CONTENT: TRACES */}
      {activeTab === "traces" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left panel - Recent Traces */}
          <div className="lg:col-span-5 space-y-4">
            <div className="p-4 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-3">
              <div className="flex gap-2">
                <select
                  value={moduleFilter}
                  onChange={(e) => setModuleFilter(e.target.value)}
                  className="bg-darkBg border border-darkBorder text-xs text-gray-300 px-2 py-1.5 rounded outline-none flex-1"
                >
                  <option value="">All Modules</option>
                  <option value="agent">Multi-Agent Swarm</option>
                  <option value="rag">RAG QA Chat</option>
                  <option value="workflow">Workflow Engine</option>
                  <option value="finance">Finance Automation</option>
                  <option value="crm">CRM Lead enrichment</option>
                </select>
                
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-darkBg border border-darkBorder text-xs text-gray-300 px-2 py-1.5 rounded outline-none flex-1"
                >
                  <option value="">All Statuses</option>
                  <option value="success">Success</option>
                  <option value="failed">Failed</option>
                  <option value="running">Running</option>
                </select>
              </div>

              {loadingTraces ? (
                <div className="py-20 text-center text-darkMuted flex flex-col items-center justify-center">
                  <RefreshCw className="w-6 h-6 animate-spin text-neonIndigo mb-2" />
                  <p className="text-xs">Loading execution traces...</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                  {traces.map((trace) => (
                    <div
                      key={trace.trace_id}
                      onClick={() => { setSelectedTraceId(trace.trace_id); fetchTraceDetails(trace.trace_id); }}
                      className={`p-3 bg-darkBg/30 border rounded-xl cursor-pointer transition-all flex items-center justify-between gap-3 ${
                        selectedTraceId === trace.trace_id ? "border-neonIndigo bg-darkBg/60" : "border-darkBorder"
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            trace.status === "success" 
                              ? "bg-emerald-400" 
                              : trace.status === "failed" 
                              ? "bg-rose-500 animate-pulse" 
                              : "bg-amber-400 animate-pulse"
                          }`} />
                          <code className="text-[10px] font-mono font-bold text-gray-300 uppercase">{trace.module}</code>
                        </div>
                        <p className="text-xs text-gray-200 truncate mt-1">{trace.input}</p>
                        <span className="text-[9px] text-darkMuted font-mono block mt-1">
                          {trace.trace_id.split("-")[0]}... | {new Date(trace.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-mono font-bold text-neonIndigo block">
                          {trace.total_latency_ms}ms
                        </span>
                        <ChevronRight className="w-4 h-4 text-darkMuted inline-block mt-1" />
                      </div>
                    </div>
                  ))}
                  {traces.length === 0 && (
                    <p className="text-xs text-darkMuted text-center py-10">No traces matching the criteria.</p>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right panel - Trace Details Profiler */}
          <div className="lg:col-span-7">
            {traceDetails ? (
              <div className="space-y-6">
                
                {/* Header detail */}
                <div className="p-5 bg-darkPanel/20 border border-darkBorder rounded-xl space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                          traceDetails.trace.status === "success" 
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25" 
                            : traceDetails.trace.status === "failed" 
                            ? "bg-rose-500/15 text-rose-400 border border-rose-500/25" 
                            : "bg-amber-500/15 text-amber-400 border border-amber-500/25"
                        }`}>
                          {traceDetails.trace.status}
                        </span>
                        <span className="text-xs font-semibold text-gray-300">
                          Module: <span className="font-mono text-neonIndigo uppercase">{traceDetails.trace.module}</span>
                        </span>
                      </div>
                      <code className="text-[9px] text-darkMuted font-mono block mt-1 select-all">
                        TRACE ID: {traceDetails.trace.trace_id}
                      </code>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-darkMuted block">Total Latency</span>
                      <span className="text-base font-mono font-bold text-neonIndigo">{traceDetails.trace.total_latency_ms}ms</span>
                    </div>
                  </div>

                  <div className="border-t border-darkBorder/30 pt-3 text-xs space-y-2 select-text">
                    <p className="text-darkMuted font-bold">Input Payload:</p>
                    <pre className="bg-darkBg/60 border border-darkBorder p-2.5 rounded font-mono text-[10.5px] max-h-[100px] overflow-y-auto text-gray-300 whitespace-pre-wrap">
                      {traceDetails.trace.input}
                    </pre>
                    
                    {traceDetails.trace.final_output && (
                      <>
                        <p className="text-darkMuted font-bold mt-2">Final Answer Output:</p>
                        <pre className="bg-darkBg/60 border border-darkBorder p-2.5 rounded font-mono text-[10.5px] max-h-[160px] overflow-y-auto text-gray-300 whitespace-pre-wrap">
                          {traceDetails.trace.final_output}
                        </pre>
                      </>
                    )}
                  </div>
                </div>

                {/* Sub-steps executions profile */}
                <div className="p-5 bg-darkPanel/20 border border-darkBorder rounded-xl space-y-4">
                  <h3 className="text-xs font-bold text-darkMuted uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="w-4 h-4 text-neonTeal" />
                    Sub-Step execution timeline
                  </h3>

                  <div className="space-y-3 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-darkBorder/40">
                    {traceDetails.steps.map((step) => (
                      <div key={step.id} className="flex gap-4 items-start pl-6 relative">
                        <div className={`absolute left-1.5 w-3.5 h-3.5 rounded-full flex items-center justify-center border ${
                          step.status === "success" 
                            ? "bg-emerald-500/25 border-emerald-400 text-emerald-400" 
                            : "bg-rose-500/25 border-rose-400 text-rose-400"
                        }`} />
                        
                        <div className="flex-1 bg-darkBg/30 border border-darkBorder p-3 rounded-lg flex items-center justify-between">
                          <div>
                            <p className="text-xs font-semibold text-gray-200">{step.step_name}</p>
                            {step.metadata && Object.keys(step.metadata).length > 0 && (
                              <pre className="text-[9px] font-mono text-darkMuted mt-1 bg-darkBg/40 px-1.5 py-0.5 rounded max-h-[60px] overflow-y-auto">
                                {JSON.stringify(step.metadata)}
                              </pre>
                            )}
                          </div>
                          <span className="text-xs font-mono font-semibold text-neonIndigo shrink-0 ml-2">
                            {step.latency_ms}ms
                          </span>
                        </div>
                      </div>
                    ))}
                    
                    {traceDetails.steps.length === 0 && (
                      <p className="text-xs text-darkMuted italic text-center py-4">No execution timeline steps registered.</p>
                    )}
                  </div>
                </div>

                {/* RAG Quality metrics details */}
                {traceDetails.rag.length > 0 && (
                  <div className="p-5 bg-darkPanel/20 border border-darkBorder rounded-xl space-y-4">
                    <h3 className="text-xs font-bold text-darkMuted uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-neonTeal" />
                      RAG Retrieval Quality Scoring
                    </h3>
                    
                    {traceDetails.rag.map((r) => (
                      <div key={r.id} className="space-y-4 text-xs">
                        <div className="grid grid-cols-3 gap-3.5 text-center">
                          <div className="p-2.5 bg-darkBg/40 border border-darkBorder rounded-lg">
                            <span className="block text-[9px] font-mono text-darkMuted uppercase">Context Relevance</span>
                            <span className="text-sm font-bold text-emerald-400">{(r.context_relevance * 100).toFixed(0)}%</span>
                          </div>
                          <div className="p-2.5 bg-darkBg/40 border border-darkBorder rounded-lg">
                            <span className="block text-[9px] font-mono text-darkMuted uppercase">Hallucination Risk</span>
                            <span className={`text-sm font-bold ${r.hallucination_score > 0.3 ? "text-rose-400" : "text-emerald-400"}`}>
                              {(r.hallucination_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="p-2.5 bg-darkBg/40 border border-darkBorder rounded-lg">
                            <span className="block text-[9px] font-mono text-darkMuted uppercase">Answer Confidence</span>
                            <span className="text-sm font-bold text-neonIndigo">{(r.answer_confidence * 100).toFixed(0)}%</span>
                          </div>
                        </div>

                        {/* Retrieved chunks */}
                        <div className="space-y-2 select-text">
                          <span className="text-[10px] font-bold text-darkMuted uppercase block">Retrieved Vector Chunks</span>
                          <div className="space-y-2 max-h-[220px] overflow-y-auto">
                            {r.retrieved_chunks && r.retrieved_chunks.map((c, i) => (
                              <div key={i} className="p-3 bg-darkBg/50 border border-darkBorder rounded-lg space-y-1.5 text-[10.5px]">
                                <div className="flex justify-between text-[9px] text-darkMuted">
                                  <span className="font-semibold text-gray-400">{c.filename || "Chunk"}</span>
                                  <span className="font-mono">Similarity: {(c.score * 100).toFixed(1)}%</span>
                                </div>
                                <p className="text-gray-300 leading-normal font-sans">{c.content}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Tool calls metrics details */}
                {traceDetails.tools.length > 0 && (
                  <div className="p-5 bg-darkPanel/20 border border-darkBorder rounded-xl space-y-4">
                    <h3 className="text-xs font-bold text-darkMuted uppercase tracking-wider flex items-center gap-1.5">
                      <Database className="w-4 h-4 text-neonIndigo" />
                      AI Tool Call Monitoring
                    </h3>
                    
                    <div className="space-y-3">
                      {traceDetails.tools.map((t) => (
                        <div key={t.id} className="p-3.5 bg-darkBg/50 border border-darkBorder rounded-xl space-y-2 select-text">
                          <div className="flex justify-between items-center border-b border-darkBorder/30 pb-1.5">
                            <code className="text-xs text-neonTeal font-bold">{t.tool_name}</code>
                            <div className="flex gap-2 items-center text-[10px] font-mono">
                              <span className={t.status === "success" ? "text-emerald-400" : "text-rose-400"}>
                                {t.status.toUpperCase()}
                              </span>
                              <span className="text-darkMuted">|</span>
                              <span className="text-neonIndigo">{t.latency_ms}ms</span>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[10px] font-mono pt-1">
                            <div className="space-y-1">
                              <span className="text-[9px] text-darkMuted block font-bold uppercase">Input Parameters:</span>
                              <pre className="p-2 bg-darkBg border border-darkBorder rounded max-h-[100px] overflow-y-auto text-gray-300 whitespace-pre-wrap">
                                {JSON.stringify(t.input, null, 2)}
                              </pre>
                            </div>
                            <div className="space-y-1">
                              <span className="text-[9px] text-darkMuted block font-bold uppercase">Output Result:</span>
                              <pre className="p-2 bg-darkBg border border-darkBorder rounded max-h-[100px] overflow-y-auto text-gray-300 whitespace-pre-wrap">
                                {JSON.stringify(t.output, null, 2)}
                              </pre>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Trace specific error logs */}
                {traceDetails.errors.length > 0 && (
                  <div className="p-5 bg-darkPanel/20 border border-rose-500/20 rounded-xl space-y-4">
                    <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldAlert className="w-4 h-4 text-rose-400" />
                      Trace Exception Crashes
                    </h3>

                    {traceDetails.errors.map((err) => (
                      <div key={err.id} className="p-3 bg-rose-950/10 border border-rose-500/25 rounded-lg space-y-2 select-text">
                        <p className="text-xs font-mono font-bold text-rose-300">{err.error_message}</p>
                        <pre className="p-2.5 bg-darkBg border border-darkBorder font-mono text-[9px] text-rose-300/80 max-h-[220px] overflow-y-auto leading-tight whitespace-pre">
                          {err.stack_trace}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-20 text-darkMuted border border-darkBorder border-dashed rounded-xl">
                <Terminal className="w-10 h-10 opacity-30 mb-3" />
                <p className="text-sm font-semibold">No Trace Selected</p>
                <p className="text-xs text-center mt-1 max-w-xs">
                  Select a workflow, RAG, or agent operation trace from the left panel to profile its timeline, latency breakdowns, and context relevance scores.
                </p>
              </div>
            )}
          </div>

        </div>
      )}

      {/* TAB CONTENT: METRICS */}
      {activeTab === "metrics" && (
        <div className="space-y-6">
          {loadingMetrics ? (
            <div className="py-40 text-center text-darkMuted flex flex-col items-center justify-center">
              <RefreshCw className="w-8 h-8 animate-spin text-neonIndigo mb-3" />
              <p className="text-xs">Aggregating system telemetry...</p>
            </div>
          ) : metrics ? (
            <div className="space-y-6">
              {/* Core summary numbers */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-2">
                  <span className="text-[10px] font-mono text-darkMuted block uppercase">Total Executions</span>
                  <span className="text-2xl font-bold text-gray-100">{metrics.total_requests}</span>
                  <div className="text-[9px] font-mono text-darkMuted flex gap-2 pt-1 border-t border-darkBorder/20">
                    <span className="text-emerald-400">Success: {metrics.success_requests}</span>
                    <span className="text-rose-400">Fail: {metrics.failed_requests}</span>
                  </div>
                </div>

                <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-2">
                  <span className="text-[10px] font-mono text-darkMuted block uppercase">Avg Total Latency</span>
                  <span className="text-2xl font-bold text-neonIndigo">{metrics.average_latency_ms}ms</span>
                  <span className="text-[9px] font-mono text-darkMuted block pt-1 border-t border-darkBorder/20">
                    Calculated over successful runs
                  </span>
                </div>

                <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-2">
                  <span className="text-[10px] font-mono text-darkMuted block uppercase">Swarm Error Rate</span>
                  <span className={`text-2xl font-bold ${metrics.error_rate > 0.05 ? "text-rose-400" : "text-emerald-400"}`}>
                    {(metrics.error_rate * 100).toFixed(2)}%
                  </span>
                  <span className="text-[9px] font-mono text-darkMuted block pt-1 border-t border-darkBorder/20">
                    Ratio of failed traces to total
                  </span>
                </div>

                <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-2">
                  <span className="text-[10px] font-mono text-darkMuted block uppercase">LLM Tokens Metered</span>
                  <span className="text-2xl font-bold text-neonTeal">{metrics.total_tokens_used.toLocaleString()}</span>
                  <span className="text-[9px] font-mono text-darkMuted block pt-1 border-t border-darkBorder/20">
                    Cumulated prompt & response tokens
                  </span>
                </div>
              </div>

              {/* RAG and Tools sections */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                
                {/* RAG Quality board */}
                <div className="lg:col-span-5 p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-4">
                  <h3 className="text-xs font-bold text-darkMuted uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-neonTeal" />
                    RAG Quality Diagnostics
                  </h3>

                  <div className="space-y-4 pt-1">
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-300">Top-K Context Relevance</span>
                        <span className="font-mono text-emerald-400">{(metrics.rag.context_relevance * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-darkBg/50 h-2 rounded-full overflow-hidden border border-darkBorder/40">
                        <div className="bg-emerald-400 h-full rounded-full" style={{ width: `${metrics.rag.context_relevance * 100}%` }} />
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-300">LLM Hallucination Index</span>
                        <span className={`font-mono ${metrics.rag.hallucination_score > 0.2 ? "text-rose-400" : "text-emerald-400"}`}>
                          {(metrics.rag.hallucination_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-darkBg/50 h-2 rounded-full overflow-hidden border border-darkBorder/40">
                        <div className="bg-rose-400 h-full rounded-full" style={{ width: `${metrics.rag.hallucination_score * 100}%` }} />
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-300">Answer Grounding Confidence</span>
                        <span className="font-mono text-neonIndigo">{(metrics.rag.answer_confidence * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-darkBg/50 h-2 rounded-full overflow-hidden border border-darkBorder/40">
                        <div className="bg-neonIndigo h-full rounded-full" style={{ width: `${metrics.rag.answer_confidence * 100}%` }} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tool calls table */}
                <div className="lg:col-span-7 p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-4">
                  <h3 className="text-xs font-bold text-darkMuted uppercase tracking-wider flex items-center gap-1.5">
                    <Database className="w-4 h-4 text-neonIndigo" />
                    Autonomous Tools Usage Summary
                  </h3>

                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left border-collapse">
                      <thead>
                        <tr className="border-b border-darkBorder text-darkMuted">
                          <th className="py-2.5 font-semibold">Tool Name</th>
                          <th className="py-2.5 font-semibold text-center">Invocations</th>
                          <th className="py-2.5 font-semibold text-center">Avg Latency</th>
                          <th className="py-2.5 font-semibold text-center">Failed Runs</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-darkBorder/30">
                        {Object.entries(metrics.tools).map(([t_name, stats]) => (
                          <tr key={t_name} className="hover:bg-darkBg/20">
                            <td className="py-3 font-mono text-neonTeal font-bold">{t_name}</td>
                            <td className="py-3 text-center">{stats.invocations}</td>
                            <td className="py-3 text-center font-mono text-neonIndigo">{stats.avg_latency_ms}ms</td>
                            <td className={`py-3 text-center font-bold ${stats.failures > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                              {stats.failures}
                            </td>
                          </tr>
                        ))}
                        {Object.keys(metrics.tools).length === 0 && (
                          <tr>
                            <td colSpan={4} className="py-4 text-center text-darkMuted italic">No tools have been called yet.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>

              {/* Module performance list */}
              <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-4">
                <h3 className="text-xs font-bold text-darkMuted uppercase tracking-wider flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-neonTeal" />
                  Module Performance Breakdown
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(metrics.modules).map(([mod_name, data]) => (
                    <div key={mod_name} className="p-4 bg-darkBg/40 border border-darkBorder rounded-xl space-y-2">
                      <span className="text-[10px] font-mono font-bold text-neonIndigo uppercase">{mod_name}</span>
                      <div className="flex justify-between text-xs pt-1">
                        <span className="text-darkMuted">Total Invocations:</span>
                        <span className="font-semibold">{data.count}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-darkMuted">Avg Latency:</span>
                        <span className="font-semibold font-mono">{data.avg_latency_ms}ms</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-darkMuted">Success Rate:</span>
                        <span className={`font-semibold ${(data.success_rate * 100) < 90 ? "text-rose-400" : "text-emerald-400"}`}>
                          {(data.success_rate * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-center text-darkMuted py-20">No system metrics loaded.</p>
          )}
        </div>
      )}

      {/* TAB CONTENT: ERRORS */}
      {activeTab === "errors" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left list */}
          <div className="lg:col-span-5 space-y-4">
            <div className="p-4 bg-darkPanel/25 border border-darkBorder rounded-xl space-y-4">
              <span className="text-xs font-bold text-darkMuted uppercase tracking-wider block">Recent Exceptions ({errors.length})</span>
              
              {loadingErrors ? (
                <div className="py-20 text-center text-darkMuted flex flex-col items-center justify-center">
                  <RefreshCw className="w-6 h-6 animate-spin text-neonIndigo mb-2" />
                  <p className="text-xs">Loading crash records...</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                  {errors.map((err) => (
                    <div
                      key={err.id}
                      onClick={() => setSelectedError(err)}
                      className={`p-3 bg-darkBg/30 border rounded-xl cursor-pointer transition-all ${
                        selectedError?.id === err.id ? "border-rose-500 bg-darkBg/60" : "border-darkBorder"
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="px-1.5 py-0.2 rounded text-[8px] font-bold uppercase bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          {err.module}
                        </span>
                        <span className="text-[9px] text-darkMuted font-mono">
                          {new Date(err.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-xs text-rose-300 font-mono mt-1.5 truncate leading-snug">{err.error_message}</p>
                    </div>
                  ))}
                  {errors.length === 0 && (
                    <p className="text-xs text-darkMuted text-center py-10">No exceptions captured.</p>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right inspector */}
          <div className="lg:col-span-7">
            {selectedError ? (
              <div className="space-y-5">
                <div className="p-5 bg-darkPanel/25 border border-rose-500/20 rounded-xl space-y-3 select-text">
                  <div>
                    <span className="text-[9px] text-rose-400 font-bold uppercase block">CRASH EXCEPTION REPORT</span>
                    <h3 className="text-sm font-mono font-bold text-rose-300 mt-1 leading-snug">{selectedError.error_message}</h3>
                    <code className="text-[9px] text-darkMuted font-mono block mt-1">
                      Module: {selectedError.module} | Timestamp: {new Date(selectedError.created_at).toLocaleString()}
                    </code>
                    {selectedError.trace_id && (
                      <code className="text-[9px] text-neonIndigo font-mono block mt-0.5">
                        Related Trace ID: {selectedError.trace_id}
                      </code>
                    )}
                  </div>

                  <div className="border-t border-darkBorder/30 pt-3 space-y-2 text-xs">
                    <span className="text-darkMuted font-bold block flex items-center gap-1">
                      <Code className="w-3.5 h-3.5 text-rose-400" />
                      Detailed Python Traceback Stack
                    </span>
                    <pre className="p-3 bg-darkBg border border-darkBorder font-mono text-[9.5px] text-rose-300/90 rounded-lg overflow-x-auto max-h-[350px] overflow-y-auto leading-normal whitespace-pre">
                      {selectedError.stack_trace}
                    </pre>
                  </div>

                  {selectedError.input_context && Object.keys(selectedError.input_context).length > 0 && (
                    <div className="border-t border-darkBorder/30 pt-3 space-y-1 text-xs">
                      <span className="text-darkMuted font-bold block">Input Context Parameters:</span>
                      <pre className="p-3 bg-darkBg border border-darkBorder font-mono text-[9px] text-gray-300 rounded-lg overflow-y-auto max-h-[120px]">
                        {JSON.stringify(selectedError.input_context, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-20 text-darkMuted border border-darkBorder border-dashed rounded-xl">
                <AlertTriangle className="w-10 h-10 opacity-30 text-rose-400 mb-3" />
                <p className="text-sm font-semibold">No Exception Selected</p>
                <p className="text-xs text-center mt-1">
                  Select a crash log from the left side panel to inspect its call stack traceback parameters and inputs.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: LOGS */}
      {activeTab === "logs" && (
        <div className="space-y-4">
          <div className="p-4 bg-darkPanel/25 border border-darkBorder rounded-xl flex flex-wrap justify-between items-center gap-3">
            <span className="text-xs font-bold text-darkMuted uppercase tracking-wider">Structured System Event Stream</span>
            
            <div className="flex gap-2">
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-darkBg border border-darkBorder text-xs text-gray-300 px-2 py-1 rounded outline-none"
              >
                <option value="">All Severities</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
                <option value="DEBUG">DEBUG</option>
              </select>
            </div>
          </div>

          <div className="p-5 bg-darkPanel/25 border border-darkBorder rounded-xl h-[580px] flex flex-col select-text">
            <div className="flex-1 overflow-y-auto font-mono text-[10.5px] leading-relaxed text-gray-300 space-y-2 pr-1">
              {loadingLogs ? (
                <div className="h-full flex flex-col items-center justify-center text-darkMuted text-center">
                  <RefreshCw className="w-6 h-6 animate-spin text-neonIndigo mb-2" />
                  <p className="text-xs">Loading structured logs...</p>
                </div>
              ) : logs.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-darkMuted text-center">
                  <Terminal className="w-8 h-8 opacity-25 mb-2" />
                  <p>Log stream is empty.</p>
                </div>
              ) : (
                logs.map((log) => {
                  const isErr = log.severity === "ERROR";
                  const isWarn = log.severity === "WARNING";
                  return (
                    <div 
                      key={log.id} 
                      className={`p-2 border ${
                        isErr 
                          ? "bg-rose-950/10 border-rose-500/20 text-rose-300" 
                          : isWarn 
                          ? "bg-amber-950/10 border-amber-500/20 text-amber-300"
                          : "bg-darkBg/30 border-darkBorder/40 text-gray-300"
                      }`}
                    >
                      <div className="flex justify-between items-center text-[9px] opacity-75 mb-1 border-b border-darkBorder/20 pb-0.5">
                        <span className="font-bold">
                          [{log.severity}] {log.module.toUpperCase()}
                        </span>
                        <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <p>{log.message}</p>
                      {log.trace_id && (
                        <span className="text-[8.5px] text-neonIndigo font-mono block mt-1">
                          Trace ID: {log.trace_id}
                        </span>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
