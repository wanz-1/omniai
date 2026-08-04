"use client";

import { useState } from "react";
import { Wand2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const TONES = [
  { id: "academic", label: "Academic", description: "Formal, scholarly tone for research papers" },
  { id: "professional", label: "Professional", description: "Polished, business-appropriate language" },
  { id: "business", label: "Business", description: "Strategic, action-oriented communication" },
  { id: "casual", label: "Casual", description: "Relaxed, conversational style" },
  { id: "creative", label: "Creative", description: "Expressive, imaginative writing" },
  { id: "ngo", label: "NGO", description: "Compassionate, advocacy-focused language" },
  { id: "technical", label: "Technical", description: "Precise, industry-specific terminology" },
  { id: "executive", label: "Executive", description: "Concise, leadership-level briefing" },
] as const;

type ToneId = (typeof TONES)[number]["id"];

interface HumanizeOptionsProps {
  selectedTone: ToneId;
  onToneChange: (tone: ToneId) => void;
  audience: string;
  onAudienceChange: (audience: string) => void;
  preserveMeaning: boolean;
  onPreserveMeaningChange: (preserve: boolean) => void;
  onHumanize: () => void;
  isHumanizing: boolean;
  humanized: boolean;
  className?: string;
}

export function HumanizeOptions({
  selectedTone,
  onToneChange,
  audience,
  onAudienceChange,
  preserveMeaning,
  onPreserveMeaningChange,
  onHumanize,
  isHumanizing,
  humanized,
  className,
}: HumanizeOptionsProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <div>
        <label className="text-sm font-medium mb-2 block">Tone</label>
        <div className="grid grid-cols-2 gap-2">
          {TONES.map((tone) => (
            <button
              key={tone.id}
              onClick={() => onToneChange(tone.id)}
              className={cn(
                "text-left p-2.5 rounded-lg border text-sm transition-all",
                selectedTone === tone.id
                  ? "border-primary bg-primary/5 ring-1 ring-primary"
                  : "border-border hover:border-primary/30 hover:bg-muted/30"
              )}
            >
              <div className="font-medium">{tone.label}</div>
              <div className="text-xs text-muted-foreground mt-0.5 leading-tight">
                {tone.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label htmlFor="audience" className="text-sm font-medium mb-1 block">
          Target Audience
        </label>
        <input
          id="audience"
          value={audience}
          onChange={(e) => onAudienceChange(e.target.value)}
          placeholder="e.g., college students, C-suite executives"
          className="w-full h-10 px-3 rounded-lg border border-input bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={preserveMeaning}
          onChange={(e) => onPreserveMeaningChange(e.target.checked)}
          className="rounded border-border"
        />
        <span className="text-sm">Preserve original meaning</span>
      </label>

      <Button
        onClick={onHumanize}
        isLoading={isHumanizing}
        disabled={isHumanizing}
        className="w-full"
      >
        {isHumanizing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Humanizing...
          </>
        ) : (
          <>
            <Wand2 className="w-4 h-4 mr-2" />
            {humanized ? "Re-humanize" : "Humanize Text"}
          </>
        )}
      </Button>
    </div>
  );
}
