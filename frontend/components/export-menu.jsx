"use client";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Download, FileText, FileJson } from "lucide-react";

export function ExportMenu({ analysis, metadata, filename }) {
  const exportAsMarkdown = () => {
    let markdown = `# Paper Analysis: ${filename}\n\n`;
    markdown += `Analysis Date: ${new Date().toLocaleDateString()}\n\n`;

    if (metadata) {
      markdown += `## Metadata\n`;
      markdown += `- Pages: ${metadata.pages || "N/A"}\n`;
      markdown += `- Tables: ${metadata.block_stats?.table || 0}\n`;
      markdown += `- Code Blocks: ${metadata.block_stats?.code || 0}\n`;
      markdown += `- Equations: ${metadata.block_stats?.equations?.equations || 0}\n\n`;
    }

    ["pass_1", "pass_2", "pass_3"].forEach((pass, idx) => {
      if (analysis[pass]) {
        markdown += `## Pass ${idx + 1} Analysis\n\n`;
        markdown += "```json\n";
        markdown += JSON.stringify(analysis[pass], null, 2);
        markdown += "\n```\n\n";
      }
    });

    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename.replace(".pdf", "")}-analysis.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportAsJSON = () => {
    const data = {
      filename,
      analysisDate: new Date().toISOString(),
      metadata,
      analysis,
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename.replace(".pdf", "")}-analysis.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const hasAnalysis =
    analysis.pass_1 || analysis.pass_2 || analysis.pass_3;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" disabled={!hasAnalysis}>
          <Download className="h-4 w-4 mr-2" />
          Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={exportAsMarkdown}>
          <FileText className="h-4 w-4 mr-2" />
          Export as Markdown
        </DropdownMenuItem>
        <DropdownMenuItem onClick={exportAsJSON}>
          <FileJson className="h-4 w-4 mr-2" />
          Export as JSON
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
