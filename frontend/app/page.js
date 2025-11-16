"use client";

import { useState, useCallback, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
} from "@/components/ui/alert-dialog";
import {
  Loader2,
  AlertCircle,
  Moon,
  Sun,
  Keyboard,
  Sparkles,
  FileText,
  TrendingUp,
  Brain,
  Key,
} from "lucide-react";
import { ThemeProvider, useTheme } from "@/components/theme-provider";
import { useKeyboardShortcuts, useVimMode } from "@/hooks/useVimMode";
import { KeyboardHelp } from "@/components/keyboard-help";
import { ExportMenu } from "@/components/export-menu";
import { PaperLibrary } from "@/components/paper-library";
import { ApiKeySettings } from "@/components/api-key-settings";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ImageDisplay = ({ imageData }) => {
  return (
    <Card className="w-full mb-4 overflow-hidden animate-fade-in">
      <CardContent className="p-0">
        <div className="relative">
          <img
            src={`data:image/png;base64,${imageData.image}`}
            alt={imageData.caption || "Paper figure"}
            className="w-full h-auto object-contain"
          />
          {imageData.caption && (
            <div className="p-4 bg-gradient-to-t from-background/90 to-transparent">
              <p className="text-sm text-muted-foreground">{imageData.caption}</p>
            </div>
          )}
          <div className="absolute top-2 right-2 px-2 py-1 bg-background/80 backdrop-blur-sm rounded text-xs text-muted-foreground">
            Page {imageData.page_number}
            {imageData.reference && ` • ${imageData.reference}`}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

function MainContent() {
  const searchParams = useSearchParams();
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [analysis, setAnalysis] = useState({
    pass_1: null,
    pass_2: null,
    pass_3: null,
  });
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPass, setCurrentPass] = useState(1);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null);
  const [deepResearch, setDeepResearch] = useState(null);
  const [deepResearchLoading, setDeepResearchLoading] = useState(false);
  const [question, setQuestion] = useState("");
  const [arxivUrl, setArxivUrl] = useState("");
  const [uploadMode, setUploadMode] = useState("file"); // "file" or "url"
  const [showApiKeySettings, setShowApiKeySettings] = useState(false);

  const { theme, toggleTheme } = useTheme();
  const { vimMode, showHelp, setShowHelp } = useVimMode();

  // Get user's API key from localStorage
  const getUserApiKey = () => {
    return localStorage.getItem("arxow-api-key") || "";
  };

  // Auto-fetch paper from URL parameter
  useEffect(() => {
    const arxivParam = searchParams.get("arxiv");
    if (arxivParam && !documentId) {
      setArxivUrl(arxivParam);
      setUploadMode("url");
      // Auto-fetch the paper
      setTimeout(() => {
        uploadFromUrlDirect(arxivParam);
      }, 500);
    }
  }, [searchParams]);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    setFile(file);
    setAnalysis({
      pass_1: null,
      pass_2: null,
      pass_3: null,
    });
    setImages([]);
    setDocumentId(null);
    setCurrentPass(1);
    setMetadata(null);
    setError(null);
    setDeepResearch(null);
  };

  const uploadDocument = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const headers = {};
      const userApiKey = getUserApiKey();
      if (userApiKey) {
        headers["X-API-Key"] = userApiKey;
      }

      const response = await fetch(`${API_URL}/upload/paper`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to upload document");
      }

      const data = await response.json();
      setDocumentId(data.document_id);
      setMetadata(data.metadata);
      setFile(new File([""], data.filename || file.name, { type: "application/pdf" }));

      // Save to library
      savePaperToLibrary({
        id: data.document_id,
        filename: file.name,
        timestamp: Date.now(),
        metadata: data.metadata,
      });

      return data.document_id;
    } catch (error) {
      console.error("Error uploading document:", error);
      setError(error.message || "Failed to upload document");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const uploadFromUrlDirect = async (url) => {
    if (!url.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const userApiKey = getUserApiKey();
      const headers = {
        "Content-Type": "application/json",
      };
      if (userApiKey) {
        headers["X-API-Key"] = userApiKey;
      }

      const response = await fetch(`${API_URL}/upload/from-url`, {
        method: "POST",
        headers,
        body: JSON.stringify({ url: url.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to fetch paper from URL");
      }

      const data = await response.json();
      setDocumentId(data.document_id);
      setMetadata(data.metadata);
      setFile(new File([""], data.filename, { type: "application/pdf" }));

      // Save to library
      savePaperToLibrary({
        id: data.document_id,
        filename: data.filename,
        timestamp: Date.now(),
        metadata: data.metadata,
        arxiv_id: data.arxiv_id,
        source_url: data.source_url,
      });

      return data.document_id;
    } catch (error) {
      console.error("Error fetching paper from URL:", error);
      setError(error.message || "Failed to fetch paper from URL");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const uploadFromUrl = async () => {
    return await uploadFromUrlDirect(arxivUrl);
  };

  const analyzePaper = async (passNumber) => {
    let docIdToUse = documentId;

    if (!documentId && uploadMode === "file" && file) {
      const newDocId = await uploadDocument();
      if (!newDocId) return;
      docIdToUse = newDocId;
    } else if (!documentId && uploadMode === "url" && arxivUrl.trim()) {
      const newDocId = await uploadFromUrl();
      if (!newDocId) return;
      docIdToUse = newDocId;
    }

    setLoading(true);
    setError(null);

    try {
      const userApiKey = getUserApiKey();
      const headers = {};
      if (userApiKey) {
        headers["X-API-Key"] = userApiKey;
      }

      const response = await fetch(
        `${API_URL}/analyze/paper/${docIdToUse}?pass_number=${passNumber}`,
        {
          method: "POST",
          headers,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to analyze paper");
      }

      const data = await response.json();

      if (data.analysis && data.analysis.error) {
        throw new Error(data.analysis.details || "Analysis failed");
      }

      setAnalysis((prev) => ({
        ...prev,
        [`pass_${passNumber}`]: data.analysis,
      }));

      if (data.images) {
        setImages(data.images);
      }

      setCurrentPass(passNumber);
    } catch (error) {
      console.error("Error analyzing paper:", error);
      setError(error.message || "Failed to analyze paper");
    } finally {
      setLoading(false);
    }
  };

  const handleDeepResearch = async () => {
    if (!question.trim() || !documentId) return;

    setDeepResearchLoading(true);
    setError(null);

    try {
      const userApiKey = getUserApiKey();
      const headers = {
        "Content-Type": "application/json",
      };
      if (userApiKey) {
        headers["X-API-Key"] = userApiKey;
      }

      const response = await fetch(`${API_URL}/deep-research/${documentId}`, {
        method: "POST",
        headers,
        body: JSON.stringify({ question: question.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Deep research failed");
      }

      const data = await response.json();
      setDeepResearch({
        question: question.trim(),
        answer: data.answer,
        timestamp: Date.now(),
      });
      setQuestion("");
    } catch (error) {
      console.error("Error in deep research:", error);
      setError(error.message || "Deep research failed");
    } finally {
      setDeepResearchLoading(false);
    }
  };

  const savePaperToLibrary = (paper) => {
    const existing = JSON.parse(localStorage.getItem("arxow-papers") || "[]");
    const filtered = existing.filter((p) => p.id !== paper.id);
    const updated = [paper, ...filtered].slice(0, 10);
    localStorage.setItem("arxow-papers", JSON.stringify(updated));
  };

  const handleLoadPaper = (paper) => {
    setDocumentId(paper.id);
    setMetadata(paper.metadata);
    setFile(new File([""], paper.filename, { type: "application/pdf" }));
  };

  const handleExport = useCallback(() => {
    // Export functionality is handled by ExportMenu component
  }, []);

  useKeyboardShortcuts({
    onFirstPass: () => analyzePaper(1),
    onSecondPass: () => analyzePaper(2),
    onThirdPass: () => analyzePaper(3),
    onToggleHelp: () => setShowHelp((prev) => !prev),
    onToggleTheme: toggleTheme,
    onExport: handleExport,
    vimMode,
  });

  const renderAnalysisContent = (content) => {
    try {
      const parsedContent =
        typeof content === "string" ? JSON.parse(content) : content;

      return (
        <div className="space-y-4">
          {Object.entries(parsedContent).map(([key, value]) => (
            <Card key={key} className="w-full border-l-4 border-l-primary/50 animate-fade-in">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  {key.replace(/_/g, " ").toUpperCase()}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {typeof value === "object" ? (
                  Array.isArray(value) ? (
                    <ul className="list-disc pl-6 space-y-2">
                      {value.map((item, index) => (
                        <li key={index} className="text-sm leading-relaxed">
                          {typeof item === "object"
                            ? JSON.stringify(item, null, 2)
                            : item}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <dl className="space-y-3">
                      {Object.entries(value).map(([subKey, subValue]) => (
                        <div key={subKey} className="border-l-2 border-muted pl-4">
                          <dt className="text-sm font-semibold text-muted-foreground mb-1">
                            {subKey.replace(/_/g, " ")}
                          </dt>
                          <dd className="text-sm">
                            {typeof subValue === "object"
                              ? JSON.stringify(subValue, null, 2)
                              : String(subValue)}
                          </dd>
                        </div>
                      ))}
                    </dl>
                  )
                ) : (
                  <p className="text-sm leading-relaxed">{value}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      );
    } catch (error) {
      console.error("Error rendering content:", error);
      return (
        <Card className="w-full border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">Error rendering analysis</p>
          </CardContent>
        </Card>
      );
    }
  };

  const getPassIcon = (passNum) => {
    switch (passNum) {
      case 1:
        return <FileText className="h-4 w-4" />;
      case 2:
        return <TrendingUp className="h-4 w-4" />;
      case 3:
        return <Brain className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8 animate-fade-in">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
              arxow
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              AI-Powered Research Paper Analyzer
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setShowApiKeySettings(true)}
              title="API Key Settings"
            >
              <Key className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setShowHelp(true)}
              title="Keyboard shortcuts (?)"
            >
              <Keyboard className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={toggleTheme}
              title="Toggle theme (Shift+D)"
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Paper Library */}
        <PaperLibrary onLoadPaper={handleLoadPaper} />

        {/* Upload Card */}
        <Card className="mb-8 animate-fade-in">
          <CardContent className="pt-6">
            <div className="space-y-6">
              {/* Upload Mode Selector */}
              <div className="flex gap-2 p-1 bg-muted rounded-lg">
                <button
                  onClick={() => setUploadMode("file")}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    uploadMode === "file"
                      ? "bg-background shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Upload PDF
                </button>
                <button
                  onClick={() => setUploadMode("url")}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    uploadMode === "url"
                      ? "bg-background shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  From arXiv URL
                </button>
              </div>

              {/* File Upload */}
              {uploadMode === "file" && (
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Upload Research Paper (PDF)
                  </label>
                  <Input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileUpload}
                    className="w-full cursor-pointer"
                  />
                </div>
              )}

              {/* URL Input */}
              {uploadMode === "url" && (
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Paste arXiv URL
                  </label>
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      placeholder="https://arxiv.org/abs/2301.12345 or just 2301.12345"
                      value={arxivUrl}
                      onChange={(e) => setArxivUrl(e.target.value)}
                      onKeyPress={(e) => e.key === "Enter" && uploadFromUrl()}
                      className="flex-1"
                    />
                    <Button
                      onClick={uploadFromUrl}
                      disabled={!arxivUrl.trim() || loading}
                    >
                      Fetch
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Supports: arxiv.org/abs/ID, arxiv.org/pdf/ID.pdf, or just the ID
                  </p>
                </div>
              )}

              <div className="flex flex-wrap gap-3 justify-center">
                {[1, 2, 3].map((passNum) => (
                  <Button
                    key={passNum}
                    onClick={() => analyzePaper(passNum)}
                    disabled={
                      (uploadMode === "file" && !file) ||
                      (uploadMode === "url" && !arxivUrl.trim()) ||
                      loading ||
                      (passNum === 2 && !analysis.pass_1) ||
                      (passNum === 3 && !analysis.pass_2)
                    }
                    variant={currentPass === passNum ? "default" : "outline"}
                    className="flex-1 min-w-[150px]"
                  >
                    {getPassIcon(passNum)}
                    <span className="ml-2">
                      Pass {passNum}
                      {passNum === 1 && " (1)"}
                      {passNum === 2 && " (2)"}
                      {passNum === 3 && " (3)"}
                    </span>
                  </Button>
                ))}
                <ExportMenu
                  analysis={analysis}
                  metadata={metadata}
                  filename={file?.name || "paper"}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Deep Research */}
        {documentId && (
          <Card className="mb-8 border-2 border-primary/20 animate-fade-in">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Deep Research Q&A
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  placeholder="Ask a question about the paper..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleDeepResearch()}
                  disabled={deepResearchLoading}
                />
                <Button
                  onClick={handleDeepResearch}
                  disabled={!question.trim() || deepResearchLoading}
                >
                  {deepResearchLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    "Ask"
                  )}
                </Button>
              </div>
              {deepResearch && (
                <div className="mt-4 p-4 bg-muted/50 rounded-lg">
                  <p className="text-sm font-semibold mb-2">
                    Q: {deepResearch.question}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    A: {deepResearch.answer}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Error Display */}
        {error && (
          <Card className="mb-8 border-destructive animate-fade-in">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3 text-destructive">
                <AlertCircle className="h-5 w-5 mt-0.5" />
                <div>
                  <h3 className="font-semibold mb-1">Error</h3>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Loading Dialog */}
        {loading && (
          <AlertDialog open={loading}>
            <AlertDialogContent className="max-w-md">
              <AlertDialogHeader>
                <AlertDialogTitle className="flex items-center gap-2">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  {documentId ? "Analyzing Paper" : "Uploading Paper"}
                </AlertDialogTitle>
                <AlertDialogDescription>
                  Please wait while we {documentId ? "analyze" : "upload"} your
                  paper. This may take a minute...
                </AlertDialogDescription>
              </AlertDialogHeader>
            </AlertDialogContent>
          </AlertDialog>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Analysis Content */}
          <div className="space-y-6">
            {metadata && (
              <Card className="w-full animate-fade-in">
                <CardHeader>
                  <CardTitle>Document Metadata</CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <dt className="font-semibold text-muted-foreground">
                        Pages
                      </dt>
                      <dd>{metadata.pages || "N/A"}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-muted-foreground">
                        Tables
                      </dt>
                      <dd>{metadata.block_stats?.table || 0}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-muted-foreground">
                        Code Blocks
                      </dt>
                      <dd>{metadata.block_stats?.code || 0}</dd>
                    </div>
                    <div>
                      <dt className="font-semibold text-muted-foreground">
                        Equations
                      </dt>
                      <dd>
                        {metadata.block_stats?.equations?.equations || 0}
                      </dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>
            )}

            {analysis[`pass_${currentPass}`] && (
              <div>
                <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                  {getPassIcon(currentPass)}
                  Pass {currentPass} Analysis
                </h2>
                {renderAnalysisContent(analysis[`pass_${currentPass}`])}
              </div>
            )}
          </div>

          {/* Images Panel */}
          {images.length > 0 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-semibold mb-4">Paper Figures</h2>
              <div className="space-y-4">
                {images.map((imageData, index) => (
                  <ImageDisplay key={index} imageData={imageData} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Vim Mode Indicator */}
        {vimMode && (
          <div className="fixed bottom-4 right-4 px-3 py-1.5 bg-primary text-primary-foreground rounded-full text-xs font-medium shadow-lg">
            VIM Mode • Press ? for help
          </div>
        )}
      </div>

      {/* Keyboard Help Modal */}
      <KeyboardHelp open={showHelp} onClose={() => setShowHelp(false)} />

      {/* API Key Settings Modal */}
      <ApiKeySettings
        open={showApiKeySettings}
        onClose={() => setShowApiKeySettings(false)}
      />
    </div>
  );
}

export default function Home() {
  return (
    <ThemeProvider>
      <MainContent />
    </ThemeProvider>
  );
}
