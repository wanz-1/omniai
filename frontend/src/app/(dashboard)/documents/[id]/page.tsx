"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Save,
  Wand2,
  Sparkles,
  Languages,
  Clock,
  Loader2,
} from "lucide-react";
import { documentsApi } from "@/lib/api-client";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useStreamingAI } from "@/hooks/useStreamingAI";
import { DocumentEditor } from "@/modules/documents/DocumentEditor";
import { DocumentUploader } from "@/modules/documents/DocumentUploader";
import { HumanizeOptions } from "@/modules/documents/HumanizeOptions";
import { ReadabilityScore } from "@/modules/documents/ReadabilityScore";
import { DocumentVersions } from "@/modules/documents/DocumentVersions";
import { GrammarAssistant } from "@/modules/documents/GrammarAssistant";
import { TranslationPane } from "@/modules/documents/TranslationPane";
import { ExportBar } from "@/modules/documents/ExportBar";

type Tone = "academic" | "professional" | "business" | "casual" | "creative" | "ngo" | "technical" | "executive";

interface AnalysisData {
  flesch_score: number;
  original_ai_score: number;
  humanized_ai_score?: number;
  reading_level?: string;
  sentence_complexity?: number;
  word_diversity?: number;
  vocabulary_score?: number;
  improvements?: string[];
  word_count: number;
}

export default function DocumentWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const docId = params.id as string;
  const isNew = docId === "new";

  const [title, setTitle] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [humanizedContent, setHumanizedContent] = useState("");
  const [isLoading, setIsLoading] = useState(!isNew);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [fullscreen, setFullscreen] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"humanize" | "grammar" | "translate" | "versions">("humanize");

  const [tone, setTone] = useState<Tone>("professional");
  const [audience, setAudience] = useState("");
  const [preserveMeaning, setPreserveMeaning] = useState(true);

  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [corrections, setCorrections] = useState<any[]>([]);
  const [translatedText, setTranslatedText] = useState<string | undefined>();
  const [isExporting, setIsExporting] = useState(false);

  const { stream, cancel, isStreaming } = useStreamingAI();
  const autoSaveRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isNew && docId) loadDocument();
  }, [docId]);

  const loadDocument = async () => {
    setIsLoading(true);
    try {
      const [docRes, versionsRes] = await Promise.all([
        documentsApi.get(docId),
        documentsApi.versions.list(docId),
      ]);
      const doc = docRes.data;
      setTitle(doc.title || "");
      setOriginalContent(doc.content || "");
      setHumanizedContent(doc.humanized_content || "");
      setVersions(versionsRes.data || []);
    } catch {
      toast.error("Failed to load document");
      router.push("/documents");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await documentsApi.create(formData as any);
      toast.success("File uploaded");
      router.push(`/documents/${res.data.id}`);
    } catch {
      toast.error("Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const handleHumanize = async () => {
    if (!originalContent.trim()) {
      toast.error("No content to humanize");
      return;
    }

    const body = { tone, audience: audience || undefined, preserve_meaning: preserveMeaning, stream: true };

    setHumanizedContent("");

    stream(
      `http://localhost:8000/api/v1/documents/${docId}/humanize/stream`,
      body,
      {
        onToken: (token) => {
          setHumanizedContent((prev) => prev + token);
        },
        onComplete: async (fullText) => {
          toast.success("Humanization complete");
          try {
            const [versionRes, analyzeRes] = await Promise.all([
              documentsApi.versions.save(docId, { content: fullText, change_summary: `Humanized (${tone})` }),
              documentsApi.analyze(docId),
            ]);
            setVersions((prev) => [versionRes.data, ...prev]);
            setAnalysis(analyzeRes.data);
          } catch {}
        },
        onError: (err) => {
          toast.error("Humanization failed");
        },
      }
    );
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const content = humanizedContent || originalContent;
      await documentsApi.update(docId, { content, title });
      toast.success("Saved");
    } catch {
      toast.error("Save failed");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCheckGrammar = async () => {
    try {
      const res = await documentsApi.grammar(docId);
      setCorrections(res.data.corrections || []);
      setActiveTab("grammar");
      toast.success(`Found ${res.data.corrections?.length || 0} suggestions`);
    } catch {
      toast.error("Grammar check failed");
    }
  };

  const handleTranslate = async (targetLang: string) => {
    try {
      const res = await documentsApi.translate(docId, { target_language: targetLang });
      setTranslatedText(res.data.translated_content);
      setActiveTab("translate");
      toast.success("Translation complete");
    } catch {
      toast.error("Translation failed");
    }
  };

  const handleExport = async (format: string) => {
    setIsExporting(true);
    try {
      const res = await documentsApi.export(docId, { format });
      const blob = new Blob([res.data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${title}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Download started");
    } catch {
      toast.error("Export failed");
    } finally {
      setIsExporting(false);
    }
  };

  const handleRestoreVersion = async (versionId: string) => {
    try {
      const res = await documentsApi.versions.restore(docId, versionId);
      setOriginalContent(res.data.content || "");
      setHumanizedContent(res.data.humanized_content || "");
      toast.success("Version restored");
    } catch {
      toast.error("Restore failed");
    }
  };

  const handleApplyCorrection = (correction: any) => {
    setHumanizedContent((prev) => prev.replace(correction.original, correction.suggestion));
  };

  const handleApplyAllCorrections = () => {
    let content = humanizedContent;
    corrections.forEach((c) => {
      content = content.replace(c.original, c.suggestion);
    });
    setHumanizedContent(content);
    toast.success("All corrections applied");
  };

  if (isNew) {
    return (
      <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold">New Document</h1>
          <p className="text-muted-foreground mt-1">Upload a file to get started</p>
        </div>
        <DocumentUploader onUpload={handleUpload} isUploading={isUploading} />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const rightPanel = fullscreen === "right" ? "w-full" : fullscreen === "left" ? "hidden" : "w-80";

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col animate-fade-in">
      <header className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/documents")} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="text-lg font-semibold bg-transparent border-none outline-none focus-visible:ring-0 px-1"
          />
          <Badge variant="outline" className="text-[10px]">{tone}</Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleCheckGrammar}>
            <Sparkles className="w-4 h-4 mr-1.5" />
            Grammar
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setActiveTab("versions")}>
            <Clock className="w-4 h-4 mr-1.5" />
            Versions
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setActiveTab("translate")}>
            <Languages className="w-4 h-4 mr-1.5" />
            Translate
          </Button>
          <Button variant="outline" size="sm" onClick={handleSave} isLoading={isSaving}>
            <Save className="w-4 h-4 mr-1.5" />
            Save
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className={cn("flex-1 flex flex-col overflow-hidden", fullscreen === "left" && "w-full")}>
          <div className="flex-1 grid grid-cols-2 divide-x divide-border overflow-hidden">
            <DocumentEditor
              content={originalContent}
              onChange={setOriginalContent}
              label="Original"
              placeholder="Paste or write your content here..."
              className="overflow-hidden"
            />
            <DocumentEditor
              content={humanizedContent}
              onChange={setHumanizedContent}
              label="Humanized"
              placeholder="Humanized text will appear here..."
              readonly={isStreaming}
              className="overflow-hidden"
            />
          </div>

          <ExportBar
            onExport={handleExport}
            isExporting={isExporting}
            className="shrink-0 mx-4 mb-2"
          />
        </div>

        <aside className={cn("border-l border-border bg-card overflow-y-auto shrink-0", rightPanel)}>
          <div className="flex border-b border-border">
            {[
              { id: "humanize", label: "Humanize", icon: Wand2 },
              { id: "grammar", label: "Grammar", icon: Sparkles },
              { id: "translate", label: "Translate", icon: Languages },
              { id: "versions", label: "Versions", icon: Clock },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
                  activeTab === tab.id
                    ? "text-primary border-b-2 border-primary bg-primary/5"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
                }`}
              >
                <tab.icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-3 space-y-4">
            {activeTab === "humanize" && (
              <>
                <HumanizeOptions
                  selectedTone={tone}
                  onToneChange={setTone}
                  audience={audience}
                  onAudienceChange={setAudience}
                  preserveMeaning={preserveMeaning}
                  onPreserveMeaningChange={setPreserveMeaning}
                  onHumanize={handleHumanize}
                  isHumanizing={isStreaming}
                  humanized={!!humanizedContent}
                />
                {analysis && (
                  <ReadabilityScore
                    fleschScore={analysis.flesch_score}
                    aiProbability={analysis.original_ai_score}
                    humanizedAiScore={analysis.humanized_ai_score}
                    readingLevel={analysis.reading_level}
                    sentenceComplexity={analysis.sentence_complexity}
                    wordDiversity={analysis.word_diversity}
                    vocabularyScore={analysis.vocabulary_score}
                    improvements={analysis.improvements}
                  />
                )}
              </>
            )}

            {activeTab === "grammar" && (
              <GrammarAssistant
                corrections={corrections}
                onApply={handleApplyCorrection}
                onReject={() => {}}
                onApplyAll={handleApplyAllCorrections}
              />
            )}

            {activeTab === "translate" && (
              <TranslationPane
                sourceText={humanizedContent || originalContent}
                translatedText={translatedText}
                onTranslate={handleTranslate}
              />
            )}

            {activeTab === "versions" && (
              <DocumentVersions
                versions={versions}
                onRestore={handleRestoreVersion}
                onCompare={(id) => {
                  const v = versions.find((v) => v.id === id);
                  if (v) setOriginalContent(v.content);
                }}
              />
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
