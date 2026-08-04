"use client";

import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

interface ReadabilityScoreProps {
  fleschScore: number;
  aiProbability: number;
  humanizedAiScore?: number;
  readingLevel?: string;
  sentenceComplexity?: number;
  wordDiversity?: number;
  vocabularyScore?: number;
  improvements?: string[];
  className?: string;
}

function ScoreGauge({ value, label, color }: { value: number; label: string; color: string }) {
  const degrees = (value / 100) * 180;
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-20 h-10 overflow-hidden">
        <div
          className="absolute bottom-0 left-0 w-full h-full rounded-t-full"
          style={{
            background: `conic-gradient(${color} ${degrees}deg, transparent ${degrees}deg)`,
            transformOrigin: "bottom center",
          }}
        />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-16 h-8 bg-card rounded-t-full" />
        <span className="absolute bottom-0 left-1/2 -translate-x-1/2 text-sm font-bold">
          {Math.round(value)}
        </span>
      </div>
      <span className="text-xs text-muted-foreground text-center">{label}</span>
    </div>
  );
}

export function ReadabilityScore({
  fleschScore,
  aiProbability,
  humanizedAiScore,
  readingLevel,
  sentenceComplexity,
  wordDiversity,
  vocabularyScore,
  improvements = [],
  className,
}: ReadabilityScoreProps) {
  const getReadabilityLabel = (score: number) => {
    if (score >= 90) return "Very Easy";
    if (score >= 80) return "Easy";
    if (score >= 70) return "Fairly Easy";
    if (score >= 60) return "Standard";
    if (score >= 50) return "Fairly Difficult";
    if (score >= 30) return "Difficult";
    return "Very Difficult";
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <CardTitle className="text-sm">Text Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-around">
          <ScoreGauge
            value={fleschScore}
            label={`Readability\n${getReadabilityLabel(fleschScore)}`}
            color="#2563EB"
          />
          <ScoreGauge
            value={100 - aiProbability}
            label="Human-like Score"
            color="#7C3AED"
          />
          {humanizedAiScore !== undefined && (
            <ScoreGauge
              value={100 - humanizedAiScore}
              label="Post-Humanize"
              color="#06B6D4"
            />
          )}
        </div>

        {readingLevel && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Reading Level</span>
            <span className="font-medium capitalize">{readingLevel}</span>
          </div>
        )}

        {sentenceComplexity !== undefined && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Sentence Complexity</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-1.5 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${Math.min(sentenceComplexity * 20, 100)}%` }}
                />
              </div>
              <span className="font-medium w-8 text-right">
                {sentenceComplexity.toFixed(1)}
              </span>
            </div>
          </div>
        )}

        {wordDiversity !== undefined && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Word Diversity</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-1.5 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-secondary"
                  style={{ width: `${Math.min(wordDiversity * 20, 100)}%` }}
                />
              </div>
              <span className="font-medium w-8 text-right">
                {wordDiversity.toFixed(1)}
              </span>
            </div>
          </div>
        )}

        {vocabularyScore !== undefined && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Vocabulary Level</span>
            <span className="font-medium">{Math.round(vocabularyScore)}%</span>
          </div>
        )}

        {improvements.length > 0 && (
          <div className="space-y-1.5 pt-2 border-t border-border">
            <span className="text-sm font-medium">Suggestions</span>
            <ul className="space-y-1">
              {improvements.map((imp, i) => (
                <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                  <span className="text-primary mt-0.5">•</span>
                  {imp}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
