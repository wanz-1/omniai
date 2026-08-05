"use client";

import { useState } from "react";
import { Save, Settings, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

const MODELS = [
  { id: "gpt-4o", label: "GPT-4o", provider: "OpenAI" },
  { id: "gpt-4o-mini", label: "GPT-4o Mini", provider: "OpenAI" },
  { id: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet", provider: "Anthropic" },
  { id: "claude-3-haiku-20240307", label: "Claude 3 Haiku", provider: "Anthropic" },
  { id: "llama3", label: "Llama 3", provider: "Ollama" },
  { id: "mistral", label: "Mistral", provider: "Ollama" },
];

const TONES = [
  { id: "professional", label: "Professional" },
  { id: "friendly", label: "Friendly" },
  { id: "casual", label: "Casual" },
  { id: "formal", label: "Formal" },
  { id: "humorous", label: "Humorous" },
  { id: "empathetic", label: "Empathetic" },
];

const INDUSTRIES = [
  { id: "tech", label: "Technology" },
  { id: "healthcare", label: "Healthcare" },
  { id: "finance", label: "Finance" },
  { id: "education", label: "Education" },
  { id: "ecommerce", label: "E-commerce" },
  { id: "legal", label: "Legal" },
  { id: "realestate", label: "Real Estate" },
  { id: "hospitality", label: "Hospitality" },
  { id: "other", label: "Other" },
];

interface BotSettingsEditorProps {
  bot: any;
  onUpdate: (data: any) => void;
  onSave: () => void;
  isSaving: boolean;
  className?: string;
}

export function BotSettingsEditor({
  bot,
  onUpdate,
  onSave,
  isSaving,
  className,
}: BotSettingsEditorProps) {
  const [showPromptGuide, setShowPromptGuide] = useState(false);

  const promptExamples = [
    "You are a helpful customer support agent for an e-commerce store. Answer questions about orders, returns, and shipping policies.",
    "You are a technical writing assistant. Help users write clear documentation, API references, and tutorials.",
    "You are a mental health support companion. Provide empathetic, non-judgmental responses and resources.",
  ];

  return (
    <div className={cn("space-y-6 overflow-y-auto h-full", className)}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Bot Settings
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Configure your bot&apos;s personality and behavior
          </p>
        </div>
        <Button size="sm" onClick={onSave} isLoading={isSaving}>
          <Save className="w-4 h-4 mr-1.5" />
          Save
        </Button>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium block mb-1.5">Name</label>
          <input
            value={bot.name || ""}
            onChange={(e) => onUpdate({ ...bot, name: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            placeholder="My Assistant"
          />
        </div>

        <div>
          <label className="text-sm font-medium block mb-1.5">Description</label>
          <input
            value={bot.description || ""}
            onChange={(e) => onUpdate({ ...bot, description: e.target.value })}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            placeholder="A brief description of what this bot does"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium block mb-1.5">Industry</label>
            <select
              value={bot.industry || ""}
              onChange={(e) => onUpdate({ ...bot, industry: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">Select industry...</option>
              {INDUSTRIES.map((ind) => (
                <option key={ind.id} value={ind.id}>{ind.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium block mb-1.5">Tone</label>
            <select
              value={bot.tone || ""}
              onChange={(e) => onUpdate({ ...bot, tone: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">Select tone...</option>
              {TONES.map((t) => (
                <option key={t.id} value={t.id}>{t.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-sm font-medium">System Prompt</label>
            <button
              onClick={() => setShowPromptGuide(!showPromptGuide)}
              className="text-xs text-primary hover:underline flex items-center gap-1"
            >
              <Sparkles className="w-3 h-3" />
              Examples
            </button>
          </div>
          <textarea
            value={bot.system_prompt || ""}
            onChange={(e) => onUpdate({ ...bot, system_prompt: e.target.value })}
            rows={6}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-y font-mono"
            placeholder="You are a helpful AI assistant..."
          />
          {showPromptGuide && (
            <div className="mt-2 space-y-1.5">
              <p className="text-xs text-muted-foreground">Click an example to use it:</p>
              {promptExamples.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => onUpdate({ ...bot, system_prompt: ex })}
                  className="w-full text-left text-xs p-2 rounded-lg border border-border hover:bg-muted/50 transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium block mb-1.5">Model</label>
            <select
              value={bot.model || "gpt-4o"}
              onChange={(e) => onUpdate({ ...bot, model: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              {MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label} ({m.provider})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium block mb-1.5">
              Temperature: {bot.temperature ?? 0.7}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={bot.temperature ?? 0.7}
              onChange={(e) => onUpdate({ ...bot, temperature: parseFloat(e.target.value) })}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Precise</span>
              <span>Creative</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
