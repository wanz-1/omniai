"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

interface DocumentUploaderProps {
  onUpload: (file: File) => Promise<void>;
  isUploading?: boolean;
  className?: string;
}

const ACCEPTED_TYPES = {
  "text/plain": [".txt"],
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "text/markdown": [".md"],
};

const MAX_SIZE = 10 * 1024 * 1024; // 10MB

export function DocumentUploader({ onUpload, isUploading, className }: DocumentUploaderProps) {
  const [error, setError] = useState<string | null>(null);
  const [uploaded, setUploaded] = useState(false);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      setError(null);
      setUploaded(false);
      const file = acceptedFiles[0];
      if (!file) return;
      if (file.size > MAX_SIZE) {
        setError("File size exceeds 10MB limit");
        return;
      }
      try {
        await onUpload(file);
        setUploaded(true);
      } catch {
        setError("Failed to upload file");
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    disabled: isUploading,
  });

  return (
    <div className={cn("space-y-3", className)}>
      <div
        {...getRootProps()}
        className={cn(
          "relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-all cursor-pointer",
          isDragActive
            ? "border-primary bg-primary/5 scale-[1.02]"
            : "border-border hover:border-primary/50 hover:bg-muted/30",
          isUploading && "pointer-events-none opacity-60"
        )}
      >
        <input {...getInputProps()} />
        {isUploading ? (
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
        ) : uploaded ? (
          <CheckCircle className="w-10 h-10 text-green-500 mb-3" />
        ) : (
          <Upload className="w-10 h-10 text-muted-foreground mb-3" />
        )}
        <p className="text-sm font-medium">
          {isUploading
            ? "Uploading..."
            : uploaded
              ? "Upload complete!"
              : isDragActive
                ? "Drop your file here"
                : "Drag & drop or click to browse"}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Supports DOCX, PDF, TXT, MD (max 10MB)
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
}
