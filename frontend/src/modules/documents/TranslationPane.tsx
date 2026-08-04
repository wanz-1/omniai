"use client";

import { useState } from "react";
import { Languages, ArrowRightLeft, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "sw", label: "Swahili" },
  { code: "fr", label: "French" },
  { code: "es", label: "Spanish" },
  { code: "de", label: "German" },
  { code: "ar", label: "Arabic" },
  { code: "zh", label: "Chinese" },
] as const;

interface TranslationPaneProps {
  sourceText: string;
  translatedText?: string;
  onTranslate: (targetLang: string) => void;
  isTranslating?: boolean;
  className?: string;
}

export function TranslationPane({
  sourceText,
  translatedText,
  onTranslate,
  isTranslating,
  className,
}: TranslationPaneProps) {
  const [targetLang, setTargetLang] = useState("sw");
  const [showSource, setShowSource] = useState(true);

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <CardTitle className="text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Languages className="w-4 h-4" />
            Translation
          </div>
          <div className="flex items-center gap-2">
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="h-8 rounded-md border border-input bg-background px-2 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.label}
                </option>
              ))}
            </select>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onTranslate(targetLang)}
              isLoading={isTranslating}
              disabled={isTranslating || !sourceText}
            >
              {isTranslating ? "Translating..." : "Translate"}
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className={cn("transition-all", !showSource && "hidden")}>
            <label className="text-xs text-muted-foreground mb-1 block">Source Text</label>
            <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm min-h-[120px] max-h-[300px] overflow-y-auto">
              {sourceText || <span className="text-muted-foreground italic">No text to translate</span>}
            </div>
          </div>
          <div className="col-span-2 md:col-span-1">
            <label className="text-xs text-muted-foreground mb-1 block">
              Translation ({LANGUAGES.find((l) => l.code === targetLang)?.label})
            </label>
            <div className="rounded-lg border border-border bg-primary/5 p-3 text-sm min-h-[120px] max-h-[300px] overflow-y-auto">
              {isTranslating ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-5 h-5 animate-spin text-primary" />
                </div>
              ) : translatedText ? (
                translatedText
              ) : (
                <span className="text-muted-foreground italic">Translation will appear here</span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
