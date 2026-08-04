"use client";

import { useState } from "react";
import { BookOpen, Upload, FileText, Link, Trash2, Plus, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { toast } from "sonner";

interface Source {
  id: string;
  type: "file" | "text" | "url";
  name: string;
  content: string;
  addedAt: string;
}

interface KnowledgeBasePanelProps {
  sources: Source[];
  onSourcesChange: (sources: Source[]) => void;
  onTrain: () => void;
  isTraining: boolean;
  className?: string;
}

export function KnowledgeBasePanel({
  sources,
  onSourcesChange,
  onTrain,
  isTraining,
  className,
}: KnowledgeBasePanelProps) {
  const [showAddText, setShowAddText] = useState(false);
  const [showAddUrl, setShowAddUrl] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [textName, setTextName] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [urlName, setUrlName] = useState("");

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const newSources: Source[] = Array.from(files).map((f) => ({
      id: Date.now().toString() + Math.random(),
      type: "file" as const,
      name: f.name,
      content: `Uploaded file: ${f.name} (${(f.size / 1024).toFixed(1)} KB)`,
      addedAt: new Date().toISOString(),
    }));
    onSourcesChange([...sources, ...newSources]);
    toast.success(`${files.length} file(s) added`);
    e.target.value = "";
  };

  const handleAddText = () => {
    if (!textInput.trim()) return;
    const newSource: Source = {
      id: Date.now().toString(),
      type: "text",
      name: textName.trim() || `Snippet ${sources.length + 1}`,
      content: textInput,
      addedAt: new Date().toISOString(),
    };
    onSourcesChange([...sources, newSource]);
    setTextInput("");
    setTextName("");
    setShowAddText(false);
    toast.success("Text snippet added");
  };

  const handleAddUrl = () => {
    if (!urlInput.trim()) return;
    const newSource: Source = {
      id: Date.now().toString(),
      type: "url",
      name: urlName.trim() || urlInput,
      content: urlInput,
      addedAt: new Date().toISOString(),
    };
    onSourcesChange([...sources, newSource]);
    setUrlInput("");
    setUrlName("");
    setShowAddUrl(false);
    toast.success("URL added");
  };

  const handleRemoveSource = (id: string) => {
    onSourcesChange(sources.filter((s) => s.id !== id));
  };

  const typeIcons = {
    file: FileText,
    text: BookOpen,
    url: Link,
  };

  const typeColors = {
    file: "text-blue-500 bg-blue-50 dark:bg-blue-950",
    text: "text-green-500 bg-green-50 dark:bg-green-950",
    url: "text-purple-500 bg-purple-50 dark:bg-purple-950",
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex items-center justify-between p-3 border-b border-border">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <BookOpen className="w-4 h-4" />
          Knowledge Base
        </h2>
        <Button size="sm" onClick={onTrain} isLoading={isTraining} disabled={sources.length === 0}>
          Train Bot
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {sources.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <BookOpen className="w-10 h-10 mb-3 opacity-40" />
            <p className="text-sm font-medium">No knowledge sources</p>
            <p className="text-xs mt-1">Upload files or add text to train your bot</p>
          </div>
        )}
        {sources.map((source) => {
          const Icon = typeIcons[source.type];
          return (
            <div
              key={source.id}
              className="flex items-start gap-3 p-3 rounded-lg border border-border bg-card"
            >
              <div className={cn("p-2 rounded-lg", typeColors[source.type])}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{source.name}</p>
                <p className="text-xs text-muted-foreground mt-0.5 truncate">{source.content}</p>
                <p className="text-[10px] text-muted-foreground mt-1">
                  Added {new Date(source.addedAt).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => handleRemoveSource(source.id)}
                className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-muted-foreground hover:text-red-500 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>

      <div className="border-t border-border p-3 space-y-2">
        <input
          type="file"
          id="kb-file-upload"
          multiple
          accept=".pdf,.docx,.txt,.md,.csv"
          onChange={handleFileUpload}
          className="hidden"
        />
        <label
          htmlFor="kb-file-upload"
          className="flex items-center justify-center gap-2 w-full py-2 px-3 rounded-lg border-2 border-dashed border-border hover:border-primary/50 cursor-pointer text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <Upload className="w-4 h-4" />
          Upload PDF, DOCX, or TXT
        </label>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddText(!showAddText)}
            className="flex-1"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            Text
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddUrl(!showAddUrl)}
            className="flex-1"
          >
            <Link className="w-3.5 h-3.5 mr-1" />
            URL
          </Button>
        </div>

        {showAddText && (
          <div className="space-y-2 p-3 rounded-lg border border-border bg-card">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium">Add Text Snippet</span>
              <button onClick={() => setShowAddText(false)}>
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <input
              value={textName}
              onChange={(e) => setTextName(e.target.value)}
              placeholder="Source name (optional)"
              className="w-full px-2 py-1.5 rounded border border-border bg-background text-xs"
            />
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              rows={4}
              placeholder="Paste your text content here..."
              className="w-full px-2 py-1.5 rounded border border-border bg-background text-xs resize-y"
            />
            <Button size="sm" onClick={handleAddText} disabled={!textInput.trim()} className="w-full">
              Add Text
            </Button>
          </div>
        )}

        {showAddUrl && (
          <div className="space-y-2 p-3 rounded-lg border border-border bg-card">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium">Add URL</span>
              <button onClick={() => setShowAddUrl(false)}>
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <input
              value={urlName}
              onChange={(e) => setUrlName(e.target.value)}
              placeholder="Label (optional)"
              className="w-full px-2 py-1.5 rounded border border-border bg-background text-xs"
            />
            <input
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://example.com/docs"
              className="w-full px-2 py-1.5 rounded border border-border bg-background text-xs"
            />
            <Button size="sm" onClick={handleAddUrl} disabled={!urlInput.trim()} className="w-full">
              Add URL
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
