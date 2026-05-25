import { useEffect, useState, useCallback } from "react";
import { FileUpload } from "./components/FileUpload";
import { DocumentList } from "./components/DocumentList";
import type { DocumentMetadata } from "./components/DocumentList";
import { DocumentViewer } from "./components/DocumentViewer";
import { Cpu, Server, Database, Sparkles, Search, Loader2, ArrowUpRight, HelpCircle } from "lucide-react";

const BACKEND_URL = "http://localhost:8000";

interface SearchResult {
  content: string;
  chunk_index: number;
  document_id: string;
  filename: string;
  similarity: number;
}

function App() {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  
  // Search state bindings
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/documents`);
      if (!response.ok) {
        throw new Error("Failed to fetch documents.");
      }
      const data = await response.json();
      setDocuments(data);
    } catch (error) {
      console.error("Error fetching documents:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery && !searchQuery.trim()) return;

    setSearching(true);
    setSearchError(null);
    setSearched(true);
    try {
      const res = await fetch(`${BACKEND_URL}/search?query=${encodeURIComponent(searchQuery)}`);
      if (!res.ok) {
        throw new Error("Semantic query request failed.");
      }
      const data = await res.json();
      setSearchResults(data);
    } catch (err: any) {
      setSearchError(err.message || "An error occurred during search.");
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="min-h-screen pb-16 flex flex-col">
      {/* Navbar / Header */}
      <header className="border-b border-darkBorder bg-darkPanel/20 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-neonTeal/10 flex items-center justify-center text-neonTeal border border-neonTeal/20">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h1 className="font-bold text-gray-200 tracking-wide flex items-center gap-1.5">
                IngestEngine
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-neonIndigo/20 text-neonIndigo border border-neonIndigo/30">
                  RAG Core
                </span>
              </h1>
              <p className="text-[10px] text-darkMuted">Enterprise AI Document Pipeline</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              API Connected
            </div>
          </div>
        </div>
      </header>

      {/* Main Grid Content */}
      <main className="max-w-6xl w-full mx-auto px-6 mt-8 flex-1 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Upload & System Stats */}
        <div className="space-y-6 lg:col-span-1">
          <div className="p-6 bg-darkPanel/30 border border-darkBorder rounded-xl space-y-4">
            <div>
              <h2 className="text-base font-semibold text-gray-200">Upload PDF Document</h2>
              <p className="text-xs text-darkMuted mt-0.5">Ingest files into the pipeline database</p>
            </div>
            
            <FileUpload 
              onUploadSuccess={fetchDocuments}
              backendUrl={BACKEND_URL}
            />
          </div>

          {/* System status details */}
          <div className="p-6 bg-darkPanel/30 border border-darkBorder rounded-xl space-y-4">
            <h3 className="text-xs font-semibold text-darkMuted uppercase tracking-wider">
              Pipeline Integration
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-darkBorder/40 flex items-center justify-center text-neonTeal">
                  <Server className="w-3.5 h-3.5" />
                </div>
                <div>
                  <p className="text-xs text-gray-300 font-medium">API Endpoint</p>
                  <p className="text-[10px] text-darkMuted">FastAPI running on localhost:8000</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-darkBorder/40 flex items-center justify-center text-neonIndigo">
                  <Database className="w-3.5 h-3.5" />
                </div>
                <div>
                  <p className="text-xs text-gray-300 font-medium">PostgreSQL Database</p>
                  <p className="text-[10px] text-darkMuted">DB: doc_ingest | Port: 5433</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-darkBorder/40 flex items-center justify-center text-yellow-400">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
                <div>
                  <p className="text-xs text-gray-300 font-medium">Vector Store Setup</p>
                  <p className="text-[10px] text-darkMuted">pgvector active (HNSW indexed)</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Document Table list & Semantic Search Workspace */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Document list */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-200">Ingested Library</h2>
                <p className="text-xs text-darkMuted mt-0.5">
                  Browse metadata and preview extracted text segments
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-darkBorder/40 text-gray-300">
                {documents.length} {documents.length === 1 ? "document" : "documents"}
              </span>
            </div>

            <DocumentList
              documents={documents}
              onSelectDocument={setSelectedDocId}
              isLoading={loading}
            />
          </div>

          {/* Semantic Search Panel */}
          <div className="p-6 bg-darkPanel/20 border border-darkBorder rounded-xl space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-neonIndigo" />
                Semantic Search Engine
              </h2>
              <p className="text-xs text-darkMuted mt-0.5">
                Query document segments by semantic meaning (powered by high-dimensional embeddings)
              </p>
            </div>

            {/* Search Input Bar */}
            <form onSubmit={handleSearch} className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="e.g., invoice payment details or document summary..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder focus:border-neonIndigo rounded-lg pl-10 pr-4 py-2.5 text-sm text-gray-200 placeholder:text-darkMuted outline-none transition-all"
                />
                <Search className="w-4 h-4 text-darkMuted absolute left-3.5 top-3.5" />
              </div>
              <button
                type="submit"
                disabled={searching}
                className="px-5 py-2.5 text-xs font-semibold text-white bg-neonIndigo hover:bg-neonIndigo/80 disabled:bg-neonIndigo/50 rounded-lg shadow-lg shadow-neonIndigo/10 flex items-center gap-1.5 transition-all shrink-0 cursor-pointer"
              >
                {searching ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-3.5 h-3.5" />
                    Search
                  </>
                )}
              </button>
            </form>

            {/* Search Result Snippets */}
            <div className="space-y-4">
              {searching ? (
                <div className="py-12 flex flex-col items-center justify-center gap-3">
                  <Loader2 className="w-8 h-8 text-neonIndigo animate-spin" />
                  <p className="text-xs text-darkMuted">Generating query embedding and querying pgvector indexes...</p>
                </div>
              ) : searchError ? (
                <div className="p-4 bg-rose-950/20 border border-rose-500/30 rounded-xl text-rose-300 text-xs font-medium">
                  {searchError}
                </div>
              ) : searchResults.length > 0 ? (
                <div className="space-y-3 animate-fadeIn">
                  <span className="text-[10px] font-bold text-darkMuted uppercase tracking-wider block">
                    Top Semantic Matches
                  </span>
                  
                  {searchResults.map((result, idx) => (
                    <div
                      key={idx}
                      className="p-5 bg-darkBg/30 border border-darkBorder hover:border-neonIndigo/40 rounded-xl space-y-3 transition-colors group relative"
                    >
                      {/* Card Header details */}
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-300">{result.filename}</span>
                          <span className="text-[10px] text-darkMuted">Chunk #{result.chunk_index}</span>
                        </div>
                        
                        <div className="flex items-center gap-1.5">
                          <span className="font-semibold text-neonTeal">
                            {(result.similarity * 100).toFixed(1)}% match
                          </span>
                          
                          <button
                            onClick={() => setSelectedDocId(result.document_id)}
                            className="p-1 rounded bg-darkBorder/60 hover:bg-neonIndigo hover:text-white text-gray-400 transition-colors"
                            title="Open document workspace"
                          >
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {/* Card Content Snippet */}
                      <p className="text-xs text-darkMuted leading-relaxed italic bg-darkPanel/20 p-3 rounded-lg border border-darkBorder/50 font-sans group-hover:text-gray-200 transition-colors whitespace-pre-wrap">
                        "{result.content}"
                      </p>
                    </div>
                  ))}
                </div>
              ) : searched ? (
                <div className="text-center py-12 border border-dashed border-darkBorder rounded-xl bg-darkPanel/10">
                  <HelpCircle className="w-8 h-8 text-darkMuted mx-auto mb-3 animate-pulse" />
                  <p className="text-gray-300 font-medium">No matches found</p>
                  <p className="text-xs text-darkMuted mt-1">Make sure you have indexed your ingested documents first.</p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </main>

      {/* Side preview Drawer */}
      <DocumentViewer
        documentId={selectedDocId}
        onClose={() => setSelectedDocId(null)}
        backendUrl={BACKEND_URL}
      />
    </div>
  );
}

export default App;
