"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { visionApi } from "@/lib/api-client";
import { toast } from "sonner";
import { ImagePlus, ScanLine, FileText, Loader2, X } from "lucide-react";

interface VisionAnalyzerProps {
  onResult?: (result: any) => void;
}

type Mode = "analyze" | "ocr" | "scan";

export function VisionAnalyzer({ onResult }: VisionAnalyzerProps) {
  const [image, setImage] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<Mode>("analyze");
  const [prompt, setPrompt] = useState("Describe this image in detail.");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    const reader = new FileReader();
    reader.onload = (ev) => setImage(ev.target?.result as string);
    reader.readAsDataURL(f);
    setResult(null);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    try {
      let res;
      if (mode === "ocr") res = await visionApi.ocr(file);
      else if (mode === "scan") res = await visionApi.scan(file);
      else res = await visionApi.analyze(file, prompt);
      setResult(res.data);
      onResult?.(res.data);
    } catch {
      toast.error("Vision analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const clearImage = () => {
    setImage(null);
    setFile(null);
    setResult(null);
  };

  const modes: { key: Mode; label: string; icon: any }[] = [
    { key: "analyze", label: "Analyze", icon: ImagePlus },
    { key: "ocr", label: "OCR", icon: FileText },
    { key: "scan", label: "Scan", icon: ScanLine },
  ];

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {modes.map(({ key, label, icon: Icon }) => (
          <Button
            key={key}
            variant={mode === key ? "primary" : "outline"}
            size="sm"
            onClick={() => setMode(key)}
          >
            <Icon className="w-4 h-4 mr-1" />
            {label}
          </Button>
        ))}
      </div>

      {!image ? (
        <div
          className="border-2 border-dashed border-border rounded-xl p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
          onClick={() => inputRef.current?.click()}
        >
          <ImagePlus className="w-10 h-10 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Upload an image</p>
          <p className="text-xs text-muted-foreground mt-1">Screenshot, photo, diagram, or document</p>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileSelect}
          />
        </div>
      ) : (
        <div className="relative">
          <img src={image} alt="Uploaded" className="max-h-64 rounded-xl object-contain w-full bg-muted/30" />
          <Button variant="ghost" size="sm" className="absolute top-2 right-2" onClick={clearImage}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      )}

      {mode === "analyze" && image && (
        <input
          className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="What do you want to know about this image?"
        />
      )}

      {image && (
        <Button onClick={handleSubmit} isLoading={loading} className="w-full">
          {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
          {mode === "analyze" ? "Analyze Image" : mode === "ocr" ? "Extract Text" : "Scan Document"}
        </Button>
      )}

      {result && (
        <Card>
          <CardContent className="pt-6 space-y-2">
            {mode === "analyze" && (
              <p className="text-sm whitespace-pre-wrap">{result.description}</p>
            )}
            {mode === "ocr" && (
              <>
                <h4 className="font-medium text-sm">Extracted Text</h4>
                <pre className="text-sm bg-muted/50 p-3 rounded-lg whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {result.raw_text}
                </pre>
                {result.structured_data && Object.keys(result.structured_data).length > 0 && (
                  <div>
                    <h4 className="font-medium text-sm mt-2">Structured Data</h4>
                    <pre className="text-xs bg-muted/50 p-3 rounded-lg overflow-x-auto">
                      {JSON.stringify(result.structured_data, null, 2)}
                    </pre>
                  </div>
                )}
              </>
            )}
            {mode === "scan" && (
              <>
                <h4 className="font-medium text-sm">Document Analysis</h4>
                <pre className="text-xs bg-muted/50 p-3 rounded-lg overflow-x-auto max-h-64 overflow-y-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
