"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2, FileText, Clock } from "lucide-react";

export function PaperLibrary({ onLoadPaper }) {
  const [papers, setPapers] = useState([]);

  useEffect(() => {
    loadPapers();
  }, []);

  const loadPapers = () => {
    const saved = localStorage.getItem("arxow-papers");
    if (saved) {
      try {
        setPapers(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to load papers:", e);
      }
    }
  };

  const savePaper = (paper) => {
    const existing = papers.filter((p) => p.id !== paper.id);
    const updated = [paper, ...existing].slice(0, 10); // Keep last 10
    setPapers(updated);
    localStorage.setItem("arxow-papers", JSON.stringify(updated));
  };

  const deletePaper = (id) => {
    const updated = papers.filter((p) => p.id !== id);
    setPapers(updated);
    localStorage.setItem("arxow-papers", JSON.stringify(updated));
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (papers.length === 0) {
    return null;
  }

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Recent Papers
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {papers.map((paper) => (
            <div
              key={paper.id}
              className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium truncate">
                  {paper.filename}
                </h4>
                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                  <Clock className="h-3 w-3" />
                  {formatDate(paper.timestamp)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onLoadPaper(paper)}
                >
                  Load
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => deletePaper(paper.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Export the savePaper function for use in other components
export { PaperLibrary as default };
