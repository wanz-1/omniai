"use client";

import { useState } from "react";
import { Clock, RotateCcw, FileText, ChevronDown, ChevronRight } from "lucide-react";
import { cn, formatDateTime, formatRelativeTime } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

interface Version {
  id: string;
  version_number: number;
  content: string;
  change_summary?: string;
  created_at: string;
}

interface DocumentVersionsProps {
  versions: Version[];
  currentVersionId?: string;
  onRestore: (versionId: string) => void;
  onCompare: (versionId: string) => void;
  className?: string;
}

export function DocumentVersions({
  versions,
  currentVersionId,
  onRestore,
  onCompare,
  className,
}: DocumentVersionsProps) {
  const [expanded, setExpanded] = useState(false);

  if (versions.length === 0) {
    return (
      <Card className={cn("", className)}>
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Version History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No versions saved yet</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("", className)}>
      <CardHeader className="cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <CardTitle className="text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Version History
            <Badge variant="outline" className="ml-1">{versions.length}</Badge>
          </div>
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </CardTitle>
      </CardHeader>
      {expanded && (
        <CardContent className="space-y-2 pt-0">
          {versions.map((version) => (
            <div
              key={version.id}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg border text-sm transition-colors",
                version.id === currentVersionId
                  ? "border-primary bg-primary/5"
                  : "border-border hover:bg-muted/30"
              )}
            >
              <FileText className="w-4 h-4 mt-0.5 text-muted-foreground flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium">v{version.version_number}</span>
                  {version.id === currentVersionId && (
                    <Badge variant="success" className="text-[10px] px-1.5">Current</Badge>
                  )}
                </div>
                {version.change_summary && (
                  <p className="text-xs text-muted-foreground truncate mt-0.5">
                    {version.change_summary}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  {formatRelativeTime(version.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onCompare(version.id)}
                  title="Compare"
                >
                  <FileText className="w-3.5 h-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRestore(version.id)}
                  title="Restore"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      )}
    </Card>
  );
}
