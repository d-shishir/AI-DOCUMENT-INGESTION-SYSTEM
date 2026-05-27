import React, { useState, useRef } from "react";
import { Upload, FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

interface FileUploadProps {
  onUploadSuccess: () => void;
  backendUrl: string;
  isAdvancedMode?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess, backendUrl, isAdvancedMode = false }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setStatusMsg(null);
    if (selectedFile.type !== "application/pdf" && !selectedFile.name.endsWith(".pdf")) {
      setStatusMsg({ type: "error", text: "Invalid file type. Only PDF documents are supported." });
      return;
    }
    // Limit to 20MB for safety
    if (selectedFile.size > 20 * 1024 * 1024) {
      setStatusMsg({ type: "error", text: "File size exceeds the 20MB limit." });
      return;
    }
    setFile(selectedFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const uploadFile = async () => {
    if (!file) return;

    setLoading(true);
    setStatusMsg(null);

    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch(`${backendUrl}/upload-document`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMsg = "Upload failed. Please check the PDF.";
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorMsg;
        } catch {
          errorMsg = `Server error ${response.status}: ${response.statusText || "Internal error occurred"}`;
        }
        throw new Error(errorMsg);
      }

      setStatusMsg({ type: "success", text: `Successfully processed and indexed "${file.name}"!` });
      setFile(null);
      onUploadSuccess();
    } catch (err) {
      const error = err as Error;
      setStatusMsg({ 
        type: "error", 
        text: error.message === "Failed to fetch" 
          ? "Cannot connect to Syntra OS backend. Please verify that the API server is active on port 8000." 
          : error.message || "An unexpected error occurred during document upload." 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full space-y-4">
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={file ? undefined : triggerFileInput}
        className={`relative border border-darkBorder/60 bg-darkPanel/20 p-8 transition-all duration-300 rounded-xl cursor-pointer flex flex-col items-center justify-center min-h-[220px] overflow-hidden ${
          isDragActive 
            ? "border-neonIndigo bg-darkPanel/40 shadow-[0_0_20px_rgba(99,102,241,0.15)]" 
            : file 
              ? "border-neonIndigo/40 bg-darkPanel/30 cursor-default" 
              : "hover:border-neonTeal/50 hover:bg-darkPanel/35 hover:shadow-[0_4px_20px_rgba(56,189,248,0.05)]"
        }`}
      >
        {/* Corner Telemetry crosshairs (Advanced Mode Only) */}
        {isAdvancedMode && (
          <>
            <span className="absolute top-2 left-3 font-mono text-[9px] text-neonTeal/30 select-none">[SYS_DRAG]</span>
            <span className="absolute top-2.5 right-3 font-mono text-[9px] text-neonTeal/40 select-none">+</span>
            <span className="absolute bottom-2.5 left-3 font-mono text-[9px] text-neonTeal/40 select-none">+</span>
            <span className="absolute bottom-2.5 right-3 font-mono text-[9px] text-neonTeal/40 select-none">+</span>
          </>
        )}

        {/* Radar Ring Sweeper Animations (visible during drag or upload loading) */}
        {(isDragActive || loading) && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-48 h-48 rounded-full border border-neonIndigo/10 relative">
              <div className="radar-line" />
              <div className="absolute inset-4 rounded-full border border-neonIndigo/5 border-dashed" />
            </div>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileChange}
          disabled={loading}
        />

        {file ? (
          <div className="text-center space-y-4 w-full max-w-sm relative z-10 animate-fadeIn">
            <div className="mx-auto w-12 h-12 rounded-xl bg-neonIndigo/10 flex items-center justify-center text-neonIndigo border border-neonIndigo/20 animate-pulse">
              <FileText className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-gray-200 truncate px-2">{file.name}</p>
              <p className="text-[10px] font-mono text-darkMuted uppercase">
                {(file.size / (1024 * 1024)).toFixed(2)} MB {isAdvancedMode && " // TELEMETRY OK"}
              </p>
            </div>
            <div className="flex gap-2.5 justify-center pt-2">
              <button
                onClick={() => setFile(null)}
                disabled={loading}
                className="px-4 py-2 text-xs font-semibold rounded-lg text-gray-300 hover:text-white bg-darkBorder/40 hover:bg-darkBorder/80 border border-darkBorder transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={uploadFile}
                disabled={loading}
                className="px-4 py-2 text-xs font-semibold rounded-lg text-white bg-neonIndigo hover:bg-neonIndigo/90 disabled:bg-neonIndigo/40 shadow-lg shadow-neonIndigo/5 flex items-center gap-1.5 transition-all cursor-pointer"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  "Upload & Process"
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center space-y-4 pointer-events-none relative z-10 py-2">
            <div className="mx-auto w-12 h-12 rounded-xl border border-darkBorder/80 bg-darkBg/60 flex items-center justify-center text-darkMuted group-hover:text-neonTeal group-hover:border-neonTeal/30 transition-all duration-300">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <p className="font-semibold text-sm text-gray-200">
                Upload PDF Document
              </p>
              <p className="text-xs text-darkMuted mt-1.5">
                Drag and drop your file here, or <span className="text-neonTeal font-semibold">browse files</span>
              </p>
            </div>
          </div>
        )}
      </div>

      {statusMsg && (
        <div
          className={`flex items-start gap-3 p-3.5 rounded-xl border animate-fadeIn text-xs ${
            statusMsg.type === "success"
              ? "bg-emerald-500/5 border-emerald-500/20 text-emerald-400"
              : "bg-rose-500/5 border-rose-500/20 text-rose-400"
          }`}
        >
          {statusMsg.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          )}
          <span className="leading-relaxed break-words flex-1">
            {isAdvancedMode ? `[${statusMsg.type.toUpperCase()}] ` : ""}
            {statusMsg.text}
          </span>
        </div>
      )}
    </div>
  );
};

