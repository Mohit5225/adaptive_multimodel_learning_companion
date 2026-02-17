"use client";

import React from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { ChevronLeft, ChevronRight, X, Upload, Trash2, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { uploadPDF, listChatPDFs, deletePDF, createChat, type PDFInfo } from "@/lib/api";

// Configure worker locally (standard for Next.js to avoid issues)
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PDFSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeChatId: string | null;
  onChatCreated?: (chatId: string) => void; // Called when a new chat is created for PDF upload
  onPDFChange?: (hasPDFs: boolean) => void; // Notify parent when PDFs change
  className?: string;
}

export function PDFSidebar({ isOpen, onClose, activeChatId, onChatCreated, onPDFChange, className }: PDFSidebarProps) {
  const [numPages, setNumPages] = React.useState<number>(0);
  const [pageNumber, setPageNumber] = React.useState<number>(1);
  const [containerWidth, setContainerWidth] = React.useState<number>(600);
  const [uploadedPDF, setUploadedPDF] = React.useState<string | null>(null);
  const [fileName, setFileName] = React.useState<string>("");
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const [chatPDFs, setChatPDFs] = React.useState<PDFInfo[]>([]);
  const [currentPDFFile, setCurrentPDFFile] = React.useState<File | null>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Container width calculation
  React.useEffect(() => {
    if (isOpen && containerRef.current) {
      const updateWidth = () => {
        if (containerRef.current) {
          const width = containerRef.current.clientWidth;
          if (width > 0) {
            setContainerWidth(width - 48);
          }
        }
      };

      const interval = setInterval(updateWidth, 50);
      const timeout = setTimeout(() => {
        clearInterval(interval);
        updateWidth();
      }, 400);

      window.addEventListener('resize', updateWidth);
      return () => {
        window.removeEventListener('resize', updateWidth);
        clearInterval(interval);
        clearTimeout(timeout);
      };
    }
  }, [isOpen]);

  // Load PDFs when chat changes
  React.useEffect(() => {
    if (activeChatId) {
      loadChatPDFs(activeChatId);
    } else {
      // No active chat — clear everything
      setChatPDFs([]);
      setUploadedPDF(null);
      setFileName("");
      setCurrentPDFFile(null);
      setPageNumber(1);
      setNumPages(0);
      setUploadError(null);
      onPDFChange?.(false);
    }
  }, [activeChatId]);

  const loadChatPDFs = async (chatId: string) => {
    try {
      const res = await listChatPDFs(chatId);
      setChatPDFs(res.pdfs);
      onPDFChange?.(res.has_pdfs);
    } catch (err) {
      console.error("Failed to load chat PDFs:", err);
      setChatPDFs([]);
      onPDFChange?.(false);
    }
  };

  const uploadToBackend = async (file: File, chatId: string) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      console.log(`[PDF] Uploading to backend for chat ${chatId}`);
      const response = await uploadPDF(file, chatId);
      console.log(`[PDF] Upload successful:`, response);
      // Refresh the PDF list
      await loadChatPDFs(chatId);
    } catch (err: any) {
      console.error("PDF upload failed:", err);
      const errorMsg = err.message || "Failed to upload PDF for AI context";
      setUploadError(errorMsg);
      console.error("[PDF Upload Error]", errorMsg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || file.type !== "application/pdf") {
      setUploadError("Only PDF files are supported");
      return;
    }

    // Show the PDF locally immediately for viewing
    const fileURL = URL.createObjectURL(file);
    setUploadedPDF(fileURL);
    setFileName(file.name);
    setCurrentPDFFile(file);
    setPageNumber(1);
    setNumPages(0);
    setUploadError(null);

    console.log(`[PDF] File selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);

    // If there's an active chat, upload to backend for RAG
    let chatIdForUpload = activeChatId;
    if (chatIdForUpload) {
      console.log(`[PDF] Active chat found: ${chatIdForUpload}, uploading PDF...`);
      await uploadToBackend(file, chatIdForUpload);
    } else {
      // No active chat — create one automatically for this PDF
      console.log(`[PDF] No active chat. Creating new chat for PDF upload...`);
      setIsUploading(true);
      setUploadError(null);
      try {
        const newChat = await createChat(`Chat with ${file.name}`);
        chatIdForUpload = newChat.chat_id;
        console.log(`[PDF] Created new chat: ${chatIdForUpload}`);
        
        // Notify parent about new chat
        onChatCreated?.(newChat.chat_id);
        
        // Now upload the PDF to the new chat
        await uploadToBackend(file, newChat.chat_id);
      } catch (err: any) {
        console.error("Failed to create chat for PDF upload:", err);
        setUploadError(`Failed to create chat: ${err.message || "Unknown error"}`);
        setIsUploading(false);
      }
    }

    // Reset file input so the same file can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // When a new chat is created after PDF was uploaded locally, upload it
  React.useEffect(() => {
    if (activeChatId && currentPDFFile && chatPDFs.length === 0 && !isUploading) {
      // Check if this PDF was already uploaded by checking filename match
      const alreadyUploaded = chatPDFs.some(p => p.filename === currentPDFFile.name);
      if (!alreadyUploaded) {
        uploadToBackend(currentPDFFile, activeChatId);
      }
    }
  }, [activeChatId]);

  const handleDeletePDF = async (pdfId: string) => {
    try {
      await deletePDF(pdfId);
      if (activeChatId) {
        await loadChatPDFs(activeChatId);
      }
      // If we just deleted the currently displayed PDF, clear the viewer
      const remaining = chatPDFs.filter(p => p.pdf_id !== pdfId);
      if (remaining.length === 0) {
        setUploadedPDF(null);
        setFileName("");
        setCurrentPDFFile(null);
        setPageNumber(1);
        setNumPages(0);
      }
    } catch (err) {
      console.error("Failed to delete PDF:", err);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
    setPageNumber(1);
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        "flex flex-col h-full bg-zinc-950 border-l border-zinc-800/50 backdrop-blur-xl transition-all duration-300 ease-in-out shrink-0",
        isOpen ? "w-[35vw] opacity-100 border-l" : "w-0 opacity-0 border-none overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800/50 bg-zinc-900/50 min-w-[300px]">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-white tracking-wider">
            {fileName || "REFERENCE MATERIAL"}
          </h3>
          {fileName && (
            <p className="text-xs text-zinc-500 mt-0.5 truncate">{fileName}</p>
          )}
          {isUploading && (
            <p className="text-xs text-cyan-400 mt-0.5 flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              Indexing for AI context...
            </p>
          )}
          {uploadError && (
            <p className="text-xs text-red-400 mt-0.5 truncate">{uploadError}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleUploadClick}
            disabled={isUploading}
            className="h-8 w-8 text-zinc-400 hover:text-cyan-400 transition-colors"
            title="Upload PDF"
          >
            <Upload className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 text-zinc-400 hover:text-white">
            <X className="w-4 h-4" />
          </Button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>

      {/* Indexed PDFs list (when chat has PDFs) */}
      {chatPDFs.length > 0 && (
        <div className="px-4 py-2 border-b border-zinc-800/50 bg-zinc-900/30 min-w-[300px]">
          <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-1.5">
            Indexed for AI ({chatPDFs.length})
          </p>
          <div className="space-y-1 max-h-24 overflow-y-auto">
            {chatPDFs.map((pdf) => (
              <div key={pdf.pdf_id} className="flex items-center gap-2 text-xs text-zinc-400 group">
                <FileText className="w-3 h-3 text-cyan-500/60 shrink-0" />
                <span className="truncate flex-1">{pdf.filename}</span>
                <span className="text-zinc-600 shrink-0">{pdf.chunks} chunks</span>
                <button
                  onClick={() => handleDeletePDF(pdf.pdf_id)}
                  className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition-all"
                  title="Remove from AI context"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PDF Viewer */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 flex justify-center bg-zinc-950/30 min-w-[300px]">
        {uploadedPDF ? (
          <Document
            file={uploadedPDF}
            onLoadSuccess={onDocumentLoadSuccess}
            className="flex flex-col items-center"
            loading={
              <div className="flex items-center justify-center h-40 text-zinc-500 text-xs animate-pulse">
                Loading PDF...
              </div>
            }
          >
            <Page
              pageNumber={pageNumber}
              width={containerWidth > 0 ? containerWidth : 200}
              className="shadow-2xl mb-4 border border-zinc-800"
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
          </Document>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="mb-6 p-8 rounded-full bg-zinc-900/50 border border-zinc-800/50">
              <Upload className="w-12 h-12 text-zinc-600" />
            </div>
            <h4 className="text-lg font-medium text-white mb-2">No PDF Uploaded</h4>
            <p className="text-sm text-zinc-500 mb-6 max-w-xs">
              Upload a PDF to ground AI responses in your study material
            </p>
            <Button
              onClick={handleUploadClick}
              className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
            >
              <Upload className="w-4 h-4 mr-2" />
              Upload PDF
            </Button>
          </div>
        )}
      </div>

      {/* Footer Controls */}
      {numPages > 0 && (
        <div className="p-4 border-t border-zinc-800/50 bg-zinc-900/80 backdrop-blur flex items-center justify-center gap-4 min-w-[300px]">
          <Button
            variant="ghost"
            size="icon"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber(prev => prev - 1)}
            className="h-8 w-8"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-xs text-zinc-400 font-mono">
            Page {pageNumber} of {numPages}
          </span>
          <Button
            variant="ghost"
            size="icon"
            disabled={pageNumber >= numPages}
            onClick={() => setPageNumber(prev => prev + 1)}
            className="h-8 w-8"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
