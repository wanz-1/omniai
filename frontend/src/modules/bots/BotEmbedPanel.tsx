"use client";

import { useState } from "react";
import { Code, Copy, Check, Palette, MessageSquare, Eye } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { botsApi } from "@/lib/api-client";
import { toast } from "sonner";

interface BotEmbedPanelProps {
  botId: string;
  botName: string;
  embedCode?: string;
  widgetConfig?: any;
  className?: string;
}

export function BotEmbedPanel({
  botId,
  botName,
  embedCode: initialCode,
  widgetConfig: initialConfig,
  className,
}: BotEmbedPanelProps) {
  const [embedCode, setEmbedCode] = useState(initialCode || "");
  const [copied, setCopied] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [config, setConfig] = useState({
    primary: initialConfig?.primary_color || "#2563EB",
    position: initialConfig?.position || "right",
    greeting: initialConfig?.greeting || "Hello! How can I help?",
  });
  const [showPreview, setShowPreview] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await botsApi.embed(botId, { theme: config });
      setEmbedCode(res.data.embed_code);
      toast.success("Embed code generated!");
    } catch {
      toast.error("Failed to generate embed code");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(embedCode);
      setCopied(true);
      toast.success("Copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy");
    }
  };

  const languages = [
    { id: "en", label: "English" },
    { id: "es", label: "Spanish" },
    { id: "fr", label: "French" },
    { id: "de", label: "German" },
  ];

  return (
    <div className={cn("space-y-6 overflow-y-auto h-full", className)}>
      <div>
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Code className="w-4 h-4" />
          Embed Widget
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Add this bot to any website with a simple embed code
        </p>
      </div>

      <div className="space-y-4 p-4 rounded-xl border border-border bg-card">
        <h3 className="text-sm font-medium flex items-center gap-2">
          <Palette className="w-4 h-4" />
          Widget Customization
        </h3>

        <div>
          <label className="text-xs font-medium block mb-1.5">Primary Color</label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={config.primary}
              onChange={(e) => setConfig({ ...config, primary: e.target.value })}
              className="w-10 h-10 rounded-lg border border-border cursor-pointer"
            />
            <input
              value={config.primary}
              onChange={(e) => setConfig({ ...config, primary: e.target.value })}
              className="flex-1 px-3 py-2 rounded-lg border border-border bg-background text-xs font-mono focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-medium block mb-1.5">Widget Position</label>
          <div className="grid grid-cols-2 gap-2">
            {["left", "right"].map((pos) => (
              <button
                key={pos}
                onClick={() => setConfig({ ...config, position: pos })}
                className={cn(
                  "px-3 py-2 rounded-lg border text-xs capitalize transition-colors",
                  config.position === pos
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border hover:bg-muted"
                )}
              >
                {pos}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs font-medium block mb-1.5">Greeting Message</label>
          <input
            value={config.greeting}
            onChange={(e) => setConfig({ ...config, greeting: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            placeholder="Hello! How can I help?"
          />
        </div>

        <Button
          size="sm"
          onClick={handleGenerate}
          isLoading={isGenerating}
          className="w-full"
        >
          <Code className="w-4 h-4 mr-1.5" />
          Generate Embed Code
        </Button>
      </div>

      {embedCode && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <Code className="w-4 h-4" />
              Embed Code
            </h3>
            <Button variant="outline" size="sm" onClick={handleCopy}>
              {copied ? (
                <Check className="w-3.5 h-3.5 mr-1" />
              ) : (
                <Copy className="w-3.5 h-3.5 mr-1" />
              )}
              {copied ? "Copied!" : "Copy"}
            </Button>
          </div>
          <pre className="p-4 rounded-xl bg-muted overflow-x-auto text-xs leading-relaxed max-h-60 overflow-y-auto">
            <code>{embedCode}</code>
          </pre>
          <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-900">
            <MessageSquare className="w-4 h-4 text-amber-500 shrink-0" />
            <p className="text-xs text-amber-700 dark:text-amber-300">
              Paste this code right before the closing <code className="bg-amber-100 dark:bg-amber-900 px-1 rounded">&lt;/body&gt;</code> tag on your website.
            </p>
          </div>
        </div>
      )}

      {showPreview && config && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="bg-card rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium">Widget Preview</h3>
              <button onClick={() => setShowPreview(false)} className="text-muted-foreground hover:text-foreground">
                Close
              </button>
            </div>
            <div className="relative h-80 bg-gray-100 dark:bg-gray-800 rounded-xl overflow-hidden">
              <div
                className="absolute bottom-4 right-4 w-14 h-14 rounded-full flex items-center justify-center shadow-lg cursor-pointer"
                style={{ backgroundColor: config.primary }}
              >
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div
                className="absolute bottom-20 right-4 w-72 bg-white dark:bg-gray-900 rounded-xl shadow-xl overflow-hidden"
                style={{ display: showPreview ? "block" : "none" }}
              >
                <div className="px-4 py-3 text-white text-sm font-medium" style={{ backgroundColor: config.primary }}>
                  {config.greeting}
                </div>
                <div className="h-44" />
                <div className="flex items-center gap-2 p-3 border-t border-border">
                  <input
                    readOnly
                    value="Type a message..."
                    className="flex-1 px-3 py-2 rounded-lg border border-border text-xs bg-background"
                  />
                  <button className="px-3 py-2 rounded-lg text-white text-xs" style={{ backgroundColor: config.primary }}>
                    Send
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
