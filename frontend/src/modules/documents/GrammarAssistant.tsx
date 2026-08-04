"use client";

import { useState } from "react";
import { Check, X, Sparkles, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

interface Correction {
  original: string;
  suggestion: string;
  type: string;
  explanation?: string;
  severity?: string;
}

interface GrammarAssistantProps {
  corrections: Correction[];
  onApply: (correction: Correction) => void;
  onReject: (correction: Correction) => void;
  onApplyAll: () => void;
  className?: string;
}

export function GrammarAssistant({
  corrections,
  onApply,
  onReject,
  onApplyAll,
  className,
}: GrammarAssistantProps) {
  const [applied, setApplied] = useState<Set<number>>(new Set());
  const [rejected, setRejected] = useState<Set<number>>(new Set());

  if (corrections.length === 0) {
    return (
      <Card className={cn("", className)}>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            Grammar Assistant
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No suggestions found</p>
        </CardContent>
      </Card>
    );
  }

  const pendingCount = corrections.length - applied.size - rejected.size;

  const handleApply = (index: number, correction: Correction) => {
    onApply(correction);
    setApplied((prev) => new Set(prev).add(index));
  };

  const handleReject = (index: number, correction: Correction) => {
    onReject(correction);
    setRejected((prev) => new Set(prev).add(index));
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <CardTitle className="text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            Grammar Assistant
          </div>
          <div className="flex items-center gap-2">
            {pendingCount > 0 && (
              <Badge variant="warning">{pendingCount} pending</Badge>
            )}
            {pendingCount > 0 && (
              <Button variant="outline" size="sm" onClick={onApplyAll}>
                Apply All
              </Button>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 pt-0 max-h-[400px] overflow-y-auto">
        {corrections.map((correction, index) => {
          const isApplied = applied.has(index);
          const isRejected = rejected.has(index);
          if (isRejected) return null;

          return (
            <div
              key={index}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg border text-sm transition-all",
                isApplied
                  ? "border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800"
                  : "border-border hover:border-primary/30"
              )}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      correction.severity === "error"
                        ? "error"
                        : correction.severity === "warning"
                          ? "warning"
                          : "default"
                    }
                    className="text-[10px] px-1.5"
                  >
                    {correction.type}
                  </Badge>
                  {isApplied && (
                    <Badge variant="success" className="text-[10px] px-1.5">Applied</Badge>
                  )}
                </div>
                <div className="mt-1.5 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground line-through text-xs">
                      {correction.original}
                    </span>
                    <ArrowRight className="w-3 h-3 text-muted-foreground" />
                    <span className="font-medium text-xs">{correction.suggestion}</span>
                  </div>
                  {correction.explanation && (
                    <p className="text-xs text-muted-foreground flex items-start gap-1">
                      <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                      {correction.explanation}
                    </p>
                  )}
                </div>
              </div>
              {!isApplied && (
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => handleApply(index, correction)}
                    className="w-7 h-7 flex items-center justify-center rounded hover:bg-green-100 dark:hover:bg-green-900/30 text-green-600 transition-colors"
                    title="Apply"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleReject(index, correction)}
                    className="w-7 h-7 flex items-center justify-center rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500 transition-colors"
                    title="Reject"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

function ArrowRight({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
    </svg>
  );
}
