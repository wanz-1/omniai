"use client";

import { AlertTriangle, Bug, Zap, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

interface Suggestion {
  line: number;
  severity: string;
  message: string;
  recommendation?: string;
}

interface ReviewPanelProps {
  suggestions: Suggestion[];
  securityIssues: string[];
  performanceNotes: string[];
  onApplySuggestion?: (suggestion: Suggestion) => void;
  className?: string;
}

export function ReviewPanel({
  suggestions,
  securityIssues,
  performanceNotes,
  onApplySuggestion,
  className,
}: ReviewPanelProps) {
  const severityIcon = (severity: string) => {
    switch (severity) {
      case "error": return <Bug className="w-4 h-4 text-red-500" />;
      case "warning": return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default: return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  const severityBadge = (severity: string) => {
    switch (severity) {
      case "error": return "error" as const;
      case "warning": return "warning" as const;
      default: return "default" as const;
    }
  };

  if (suggestions.length === 0 && securityIssues.length === 0 && performanceNotes.length === 0) {
    return (
      <Card className={cn("", className)}>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Code Review
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No review results yet. Generate code first, then run a review.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Code Review
          <Badge variant="outline" className="ml-1">{suggestions.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 max-h-[500px] overflow-y-auto">
        {securityIssues.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-red-500 mb-2 flex items-center gap-1.5">
              <Bug className="w-3.5 h-3.5" />
              Security Issues
            </h4>
            <ul className="space-y-1">
              {securityIssues.map((issue, i) => (
                <li key={i} className="text-xs text-muted-foreground flex items-start gap-2 p-2 rounded-lg bg-red-50 dark:bg-red-900/10">
                  <span className="text-red-500 mt-0.5">•</span>
                  {issue}
                </li>
              ))}
            </ul>
          </div>
        )}

        {performanceNotes.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-blue-500 mb-2 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5" />
              Performance
            </h4>
            <ul className="space-y-1">
              {performanceNotes.map((note, i) => (
                <li key={i} className="text-xs text-muted-foreground flex items-start gap-2 p-2 rounded-lg bg-blue-50 dark:bg-blue-900/10">
                  <span className="text-blue-500 mt-0.5">•</span>
                  {note}
                </li>
              ))}
            </ul>
          </div>
        )}

        {suggestions.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium mb-2">Suggestions</h4>
            {suggestions.map((s, i) => (
              <div
                key={i}
                className="p-3 rounded-lg border border-border text-sm hover:border-primary/30 transition-colors"
              >
                <div className="flex items-start gap-2">
                  {severityIcon(s.severity)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={severityBadge(s.severity)} className="text-[10px] px-1.5">
                        Line {s.line}
                      </Badge>
                      <span className="text-xs font-medium capitalize">{s.severity}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{s.message}</p>
                    {s.recommendation && (
                      <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                        <span className="font-medium">Fix: </span>
                        {s.recommendation}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
