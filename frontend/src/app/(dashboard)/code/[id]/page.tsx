"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Save,
  Sparkles,
  Code,
  FileCode,
  Loader2,
  Copy,
  Check,
  Zap,
  Plus,
} from "lucide-react";
import { codeApi } from "@/lib/api-client";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { CodeEditor } from "@/modules/code/CodeEditor";
import { FileTree } from "@/modules/code/FileTree";
import { ReviewPanel } from "@/modules/code/ReviewPanel";

interface CodeProject {
  id: string;
  name: string;
  description?: string;
  language: string;
  framework?: string;
  files?: any[];
  created_at: string;
  updated_at: string;
}

interface FileNode {
  path: string;
  content?: string;
  type?: "folder" | "file";
  children?: FileNode[];
}

const LANGUAGES = [
  { id: "python", label: "Python" },
  { id: "javascript", label: "JavaScript" },
  { id: "typescript", label: "TypeScript" },
  { id: "go", label: "Go" },
  { id: "rust", label: "Rust" },
  { id: "java", label: "Java" },
  { id: "cpp", label: "C++" },
  { id: "php", label: "PHP" },
  { id: "ruby", label: "Ruby" },
  { id: "swift", label: "Swift" },
];

export default function CodeProjectWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<CodeProject | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState<"editor" | "review">("editor");
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [outputCode, setOutputCode] = useState("");
  const [reviewResults, setReviewResults] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    const loadProject = async () => {
      setIsLoading(true);
      try {
        const res = await codeApi.getProject(projectId);
        setProject(res.data);
        const files = res.data.files || [];
        if (files.length > 0) {
          setActiveFile(files[0].path);
          setOutputCode(files[0].content || "");
        }
      } catch {
        toast.error("Failed to load project");
        router.push("/code");
      } finally {
        setIsLoading(false);
      }
    };
    loadProject();
  }, [projectId, router]);
  const loadProject = async () => {
    setIsLoading(true);
    try {
      const res = await codeApi.getProject(projectId);
      setProject(res.data);
      const files = res.data.files || [];
      if (files.length > 0) {
        setActiveFile(files[0].path);
        setOutputCode(files[0].content || "");
      }
    } catch {
      toast.error("Failed to load project");
      router.push("/code");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error("Please describe what code to generate");
      return;
    }
    setIsGenerating(true);
    try {
      const res = await codeApi.generateForProject(projectId, {
        prompt,
        language: project?.language || "python",
        framework: project?.framework,
      });
      setOutputCode(res.data.code);
      toast.success("Code generated!");

      const filePath = prompt.toLowerCase().replace(/[^a-z0-9]+/g, "_").slice(0, 30) + "." + (project?.language === "typescript" ? "ts" : project?.language === "javascript" ? "js" : project?.language || "py");
      const newFile: FileNode = { path: filePath, content: res.data.code };
      const existingFiles = project?.files || [];
      await codeApi.updateProject(projectId, {
        files: [...existingFiles, newFile],
      });
      setActiveFile(filePath);
      const updated = await codeApi.getProject(projectId);
      setProject(updated.data);

      setPrompt("");
    } catch {
      toast.error("Generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReview = async () => {
    if (!outputCode) return;
    try {
      const res = await codeApi.review({
        code: outputCode,
        language: project?.language || "python",
      });
      setReviewResults(res.data);
      setActiveTab("review");
      toast.success("Review complete");
    } catch {
      toast.error("Review failed");
    }
  };

  const handleSave = async () => {
    if (!project) return;
    setIsSaving(true);
    try {
      const files = (project.files || []).map((f: any) =>
        f.path === activeFile ? { ...f, content: outputCode } : f
      );
      if (!files.find((f: any) => f.path === activeFile) && activeFile) {
        files.push({ path: activeFile, content: outputCode });
      }
      await codeApi.updateProject(projectId, { files });
      const res = await codeApi.getProject(projectId);
      setProject(res.data);
      toast.success("Saved");
    } catch {
      toast.error("Save failed");
    } finally {
      setIsSaving(false);
    }
  };

  const handleFileSelect = (path: string) => {
    setActiveFile(path);
    const file = (project?.files || []).find((f: any) => f.path === path);
    if (file) setOutputCode(file.content || "");
  };

  const handleFileDelete = async (path: string) => {
    const files = (project?.files || []).filter((f: any) => f.path !== path);
    await codeApi.updateProject(projectId, { files });
    const res = await codeApi.getProject(projectId);
    setProject(res.data);
    if (activeFile === path) {
      setActiveFile(res.data.files?.[0]?.path || null);
      setOutputCode(res.data.files?.[0]?.content || "");
    }
  };

  const handleFileAdd = async (parentPath: string) => {
    const name = window.prompt("File name (e.g., main.py):");
    if (!name) return;
    const newFile: FileNode = { path: name, content: "" };
    const files = [...(project?.files || []), newFile];
    await codeApi.updateProject(projectId, { files });
    const res = await codeApi.getProject(projectId);
    setProject(res.data);
    setActiveFile(name);
    setOutputCode("");
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(outputCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success("Copied");
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!project) return null;

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col animate-fade-in">
      <header className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/code")} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-lg font-semibold">{project.name}</h1>
            {project.description && (
              <p className="text-xs text-muted-foreground">{project.description}</p>
            )}
          </div>
          <Badge variant="outline">{project.language}</Badge>
          {project.framework && <Badge variant="outline">{project.framework}</Badge>}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleReview} disabled={!outputCode}>
            <Zap className="w-4 h-4 mr-1.5" />
            Review
          </Button>
          <Button variant="outline" size="sm" onClick={handleSave} isLoading={isSaving}>
            <Save className="w-4 h-4 mr-1.5" />
            Save
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-56 border-r border-border bg-card overflow-y-auto shrink-0">
          <FileTree
            files={(project.files || []).map((f: any) => ({ ...f, type: "file" }))}
            activeFile={activeFile}
            onFileSelect={handleFileSelect}
            onFileDelete={handleFileDelete}
            onFileAdd={handleFileAdd}
          />
        </div>

        <div className="flex-1 flex flex-col overflow-hidden">
          {activeTab === "editor" ? (
            <>
              <div className="p-3 border-b border-border bg-muted/20 shrink-0">
                <div className="flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{activeFile || "No file selected"}</span>
                  <div className="flex-1" />
                  <div className="flex items-center gap-1">
                    <div className="flex flex-wrap gap-1">
                      {LANGUAGES.map((lang) => (
                        <button
                          key={lang.id}
                          onClick={() => setProject({ ...project, language: lang.id })}
                          className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                            project.language === lang.id
                              ? "bg-primary/10 text-primary"
                              : "text-muted-foreground hover:bg-muted"
                          }`}
                        >
                          {lang.label}
                        </button>
                      ))}
                    </div>
                    <button
                      onClick={handleCopy}
                      className="p-1.5 hover:bg-muted rounded text-muted-foreground"
                      title="Copy code"
                    >
                      {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
              <div className="flex-1 overflow-hidden">
                <CodeEditor
                  code={outputCode}
                  onChange={setOutputCode}
                  language={project.language}
                  className="h-full"
                />
              </div>
            </>
          ) : (
            <div className="flex-1 overflow-y-auto p-4">
              <ReviewPanel
                suggestions={reviewResults?.suggestions || []}
                securityIssues={reviewResults?.security_issues || []}
                performanceNotes={reviewResults?.performance_notes || []}
              />
            </div>
          )}
        </div>

        <div className="w-72 border-l border-border bg-card overflow-y-auto shrink-0 p-3">
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium mb-1.5 block">Generate Code</label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe the code you want to generate..."
                rows={4}
                className="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
              />
              <Button
                size="sm"
                onClick={handleGenerate}
                isLoading={isGenerating}
                disabled={isGenerating || !prompt.trim()}
                className="w-full mt-2"
              >
                <Sparkles className="w-4 h-4 mr-1.5" />
                Generate
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
