"use client";

import { useState } from "react";
import { Monitor, Tablet, Smartphone, Maximize2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface WebsitePreviewProps {
  previewUrl: string | null;
  isGenerating: boolean;
  onGenerate: () => void;
  className?: string;
}

type DeviceType = "desktop" | "tablet" | "mobile";

const DEVICE_WIDTHS: Record<DeviceType, string> = {
  desktop: "100%",
  tablet: "768px",
  mobile: "375px",
};

export function WebsitePreview({
  previewUrl,
  isGenerating,
  onGenerate,
  className,
}: WebsitePreviewProps) {
  const [device, setDevice] = useState<DeviceType>("desktop");

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex items-center justify-between p-2 border-b border-border bg-muted/20 shrink-0">
        <div className="flex items-center gap-1">
          {[
            { id: "desktop" as const, icon: Monitor, label: "Desktop" },
            { id: "tablet" as const, icon: Tablet, label: "Tablet" },
            { id: "mobile" as const, icon: Smartphone, label: "Mobile" },
          ].map((d) => (
            <button
              key={d.id}
              onClick={() => setDevice(d.id)}
              className={cn(
                "p-1.5 rounded-lg transition-colors",
                device === d.id
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted"
              )}
              title={d.label}
            >
              <d.icon className="w-4 h-4" />
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center bg-muted/30 p-4 overflow-auto">
        {isGenerating ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Generating preview...</p>
          </div>
        ) : previewUrl ? (
          <div
            className="bg-white rounded-lg shadow-lg overflow-hidden transition-all duration-300"
            style={{ width: DEVICE_WIDTHS[device], maxWidth: "100%" }}
          >
            <div className="bg-gray-100 px-4 py-2 flex items-center gap-2 text-xs text-gray-500">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                <div className="w-3 h-3 rounded-full bg-green-400" />
              </div>
              <span className="ml-2">Preview</span>
            </div>
            <iframe
              src={previewUrl}
              className="w-full border-0"
              style={{ height: device === "mobile" ? "667px" : "500px" }}
              title="Website preview"
            />
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 text-center">
            <Monitor className="w-12 h-12 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Generate your website first to see a preview
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
