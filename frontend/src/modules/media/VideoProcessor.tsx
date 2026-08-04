"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { videoApi } from "@/lib/api-client";
import { toast } from "sonner";
import { Video, Loader2, FileText, ListTree, Clock, CheckCircle2 } from "lucide-react";

type JobType = "summary" | "captions" | "analysis";

export function VideoProcessor() {
  const [file, setFile] = useState<File | null>(null);
  const [jobType, setJobType] = useState<JobType>("summary");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (!file) {
      toast.error("Select a video file first");
      return;
    }
    setLoading(true);
    try {
      const res = await videoApi.process(file, jobType);
      setResult(res.data);
      toast.success("Video processing complete");
    } catch {
      toast.error("Video processing failed");
    } finally {
      setLoading(false);
    }
  };

  const jobTypes: { key: JobType; label: string; icon: any }[] = [
    { key: "summary", label: "Summarize", icon: FileText },
    { key: "captions", label: "Captions", icon: Clock },
    { key: "analysis", label: "Analyze", icon: ListTree },
  ];

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {jobTypes.map(({ key, label, icon: Icon }) => (
          <Button
            key={key}
            variant={jobType === key ? "primary" : "outline"}
            size="sm"
            onClick={() => setJobType(key)}
          >
            <Icon className="w-4 h-4 mr-1" />
            {label}
          </Button>
        ))}
      </div>

      <div
        className="border-2 border-dashed border-border rounded-xl p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
        onClick={() => inputRef.current?.click()}
      >
        <Video className="w-10 h-10 mx-auto mb-2 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          {file ? file.name : "Upload a video file"}
        </p>
        <p className="text-xs text-muted-foreground mt-1">MP4, MOV, AVI, WebM</p>
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
      </div>

      <Button onClick={handleSubmit} isLoading={loading} className="w-full" disabled={!file}>
        {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
        Process Video
      </Button>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              Result
              <Badge variant="success">{result.job_type}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {result.output?.summary && (
              <div className="text-sm whitespace-pre-wrap">{result.output.summary}</div>
            )}
            {result.output?.transcript && (
              <div>
                <h4 className="font-medium text-sm mb-2">Transcript</h4>
                <pre className="text-sm bg-muted/50 p-3 rounded-lg whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {result.output.transcript}
                </pre>
              </div>
            )}
            {result.output?.srt && (
              <div>
                <h4 className="font-medium text-sm mb-2">SRT Captions</h4>
                <pre className="text-xs bg-muted/50 p-3 rounded-lg whitespace-pre-wrap max-h-48 overflow-y-auto font-mono">
                  {result.output.srt}
                </pre>
              </div>
            )}
            {result.output?.duration_seconds !== undefined && (
              <div className="text-sm text-muted-foreground mt-2">
                Duration: {Math.round(result.output.duration_seconds)}s &middot;
                Resolution: {result.output.resolution}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
