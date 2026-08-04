"use client";

import { useState } from "react";
import { Download, FileText, Loader2, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

const FORMATS = [
  { value: "docx", label: "DOCX", icon: "📄" },
  { value: "pdf", label: "PDF", icon: "📕" },
  { value: "md", label: "Markdown", icon: "📝" },
  { value: "txt", label: "Plain Text", icon: "📃" },
] as const;

interface ExportBarProps {
  onExport: (format: string) => Promise<void>;
  isExporting?: boolean;
  className?: string;
}

export function ExportBar({ onExport, isExporting, className }: ExportBarProps) {
  const [selectedFormat, setSelectedFormat] = useState("docx");
  const [exported, setExported] = useState<string | null>(null);

  const handleExport = async () => {
    setExported(null);
    await onExport(selectedFormat);
    setExported(selectedFormat);
    setTimeout(() => setExported(null), 3000);
  };

  return (
    <div className={cn("flex items-center gap-2 p-3 rounded-lg border border-border bg-card", className)}>
      <FileText className="w-4 h-4 text-muted-foreground" />
      <span className="text-sm text-muted-foreground mr-1">Export as:</span>
      <div className="flex gap-1">
        {FORMATS.map((fmt) => (
          <button
            key={fmt.value}
            onClick={() => setSelectedFormat(fmt.value)}
            className={cn(
              "px-3 py-1.5 rounded-md text-xs font-medium transition-all",
              selectedFormat === fmt.value
                ? "bg-primary/10 text-primary ring-1 ring-primary"
                : "text-muted-foreground hover:bg-muted"
            )}
          >
            {fmt.icon} {fmt.label}
          </button>
        ))}
      </div>
      <div className="flex-1" />
      <Button
        variant="secondary"
        size="sm"
        onClick={handleExport}
        isLoading={isExporting}
        disabled={isExporting}
      >
        {exported ? (
          <>
            <Check className="w-4 h-4 mr-1.5" />
            Exported
          </>
        ) : (
          <>
            <Download className="w-4 h-4 mr-1.5" />
            Download
          </>
        )}
      </Button>
    </div>
  );
}
