"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { codeStudioApi } from "@/lib/api-client";
import { toast } from "sonner";
import {
  Code, FolderOpen, Wand2, Bug, Shield, TestTube, Rocket, FileText,
  Loader2, Trash2, Play, Github, BookOpen,
} from "lucide-react";

type Tab = "workspace" | "generate" | "debug" | "tests" | "security" | "deploy";

interface StudioProject {
  id: string; name: string; status: string; language: string; project_type: string;
  frontend_framework?: string; backend_framework?: string; database_type?: string;
  file_tree?: Record<string, any>; config?: any; created_at?: string;
}

interface StudioFile {
  id: string; path: string; name: string; content?: string; language?: string; size: number;
}

export default function CodeStudioPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("workspace");
  const [projects, setProjects] = useState<StudioProject[]>([]);
  const [activeProject, setActiveProject] = useState<StudioProject | null>(null);
  const [files, setFiles] = useState<StudioFile[]>([]);
  const [activeFile, setActiveFile] = useState<StudioFile | null>(null);
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => { loadOrg(); }, []);
  useEffect(() => { if (orgId) { loadProjects(); loadDashboard(); } }, [orgId]);
  useEffect(() => { if (activeProject) loadFiles(); }, [activeProject]);

  const loadOrg = async () => {
    try { const res = await fetch("/api/organizations"); const orgs = await res.json(); if (orgs.length > 0) setOrgId(orgs[0].id); } catch {} finally { setLoading(false); }
  };

  const loadProjects = async () => {
    if (!orgId) return;
    try { const res = await codeStudioApi.projects(orgId); setProjects(res.data); if (res.data.length > 0 && !activeProject) setActiveProject(res.data[0]); } catch {}
  };

  const loadDashboard = async () => {
    if (!orgId) return;
    try { const res = await codeStudioApi.dashboard(orgId); setDashboard(res.data); } catch {}
  };

  const loadFiles = async () => {
    if (!activeProject) return;
    try { const res = await codeStudioApi.files(activeProject.id); setFiles(res.data); } catch {}
  };

  const handleDeleteProject = async (id: string) => {
    try { await codeStudioApi.deleteProject(id); toast.success("Deleted"); loadProjects(); if (activeProject?.id === id) { setActiveProject(null); setFiles([]); } } catch { toast.error("Failed"); }
  };

  const tabs: { key: Tab; label: string; icon: any; description: string }[] = [
    { key: "workspace", label: "Workspace", icon: FolderOpen, description: "Project files & editor" },
    { key: "generate", label: "Generate", icon: Wand2, description: "AI app generator" },
    { key: "debug", label: "Debug", icon: Bug, description: "AI debugging" },
    { key: "tests", label: "Tests", icon: TestTube, description: "Test generation" },
    { key: "security", label: "Security", icon: Shield, description: "Vulnerability scan" },
    { key: "deploy", label: "Deploy", icon: Rocket, description: "Build & deploy" },
  ];

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Code Studio</h1>
          <p className="text-muted-foreground mt-1">AI-powered software development environment</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setTab("generate")}><Wand2 className="w-4 h-4 mr-1" /> New App</Button>
          <Button variant="outline" size="sm" onClick={() => setTab("workspace")}><FolderOpen className="w-4 h-4 mr-1" /> Workspace</Button>
        </div>
      </div>

      {dashboard?.stats && (
        <div className="grid gap-3 grid-cols-3 sm:grid-cols-6">
          <Card><CardContent className="pt-3 pb-2 text-center"><p className="text-lg font-bold">{dashboard.stats.projects}</p><p className="text-[10px] text-muted-foreground">Projects</p></CardContent></Card>
          <Card><CardContent className="pt-3 pb-2 text-center"><p className="text-lg font-bold">{dashboard.stats.repos}</p><p className="text-[10px] text-muted-foreground">Repos</p></CardContent></Card>
          <Card><CardContent className="pt-3 pb-2 text-center"><p className="text-lg font-bold">{dashboard.stats.builds}</p><p className="text-[10px] text-muted-foreground">Builds</p></CardContent></Card>
          <Card><CardContent className="pt-3 pb-2 text-center"><p className="text-lg font-bold">{dashboard.stats.deployments}</p><p className="text-[10px] text-muted-foreground">Deploys</p></CardContent></Card>
          <Card><CardContent className="pt-3 pb-2 text-center"><p className="text-lg font-bold">{dashboard.stats.tests}</p><p className="text-[10px] text-muted-foreground">Tests</p></CardContent></Card>
          <Card><CardContent className="pt-3 pb-2 text-center"><p className="text-lg font-bold">{dashboard.stats.security_scans}</p><p className="text-[10px] text-muted-foreground">Scans</p></CardContent></Card>
        </div>
      )}

      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
              tab === t.key ? "bg-primary/10 text-primary font-medium border border-primary/30" : "text-muted-foreground hover:bg-muted border border-transparent"
            }`}
          ><t.icon className="w-4 h-4" /><span className="hidden sm:inline">{t.label}</span></button>
        ))}
      </div>

      {tab === "workspace" && <WorkspaceTab projects={projects} activeProject={activeProject} setActiveProject={setActiveProject} files={files} activeFile={activeFile} setActiveFile={setActiveFile} onDelete={handleDeleteProject} />}
      {tab === "generate" && <GenerateTab orgId={orgId} onCreated={(p: StudioProject) => { setActiveProject(p); setTab("workspace"); loadProjects(); }} />}
      {tab === "debug" && <DebugTab />}
      {tab === "tests" && <TestsTab activeProject={activeProject} />}
      {tab === "security" && <SecurityTab activeProject={activeProject} />}
      {tab === "deploy" && <DeployTab activeProject={activeProject} />}
    </div>
  );
}

function WorkspaceTab({ projects, activeProject, setActiveProject, files, activeFile, setActiveFile, onDelete }: {
  projects: StudioProject[]; activeProject: StudioProject | null; setActiveProject: (p: StudioProject) => void;
  files: StudioFile[]; activeFile: StudioFile | null; setActiveFile: (f: StudioFile | null) => void; onDelete: (id: string) => void;
}) {
  const [fileContent, setFileContent] = useState("");
  const [codePrompt, setCodePrompt] = useState("");
  const [codeResult, setCodeResult] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  useEffect(() => { if (activeFile) { setFileContent(activeFile.content || ""); } }, [activeFile]);

  const handleGenerateCode = async () => {
    if (!codePrompt.trim()) return;
    setChatLoading(true);
    try {
      const res = await codeStudioApi.generateCode({ prompt: codePrompt, language: activeProject?.language || "python" });
      setCodeResult(res.data.code);
    } catch { toast.error("Generation failed"); } finally { setChatLoading(false); }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-1 space-y-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Projects</CardTitle></CardHeader>
          <CardContent className="space-y-1 max-h-60 overflow-y-auto">
            {projects.map((p) => (
              <div key={p.id} className={`flex items-center justify-between p-2 rounded-lg cursor-pointer text-sm ${activeProject?.id === p.id ? "bg-primary/10 text-primary" : "hover:bg-muted"}`}
                onClick={() => setActiveProject(p)}>
                <div className="flex items-center gap-2"><Code className="w-3 h-3" /><span className="truncate">{p.name}</span></div>
                <div className="flex gap-1">
                  <Badge variant="outline" className="text-[10px]">{p.status}</Badge>
                  <button onClick={(e) => { e.stopPropagation(); onDelete(p.id); }} className="text-muted-foreground hover:text-destructive"><Trash2 className="w-3 h-3" /></button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
        {activeProject && (
          <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Files ({files.length})</CardTitle></CardHeader>
            <CardContent className="space-y-1 max-h-80 overflow-y-auto">
              {files.map((f) => (
                <div key={f.id} className={`flex items-center gap-2 p-1.5 rounded cursor-pointer text-xs ${activeFile?.id === f.id ? "bg-primary/10 text-primary" : "hover:bg-muted"}`}
                  onClick={() => setActiveFile(f)}>
                  <FileText className="w-3 h-3 flex-shrink-0" />
                  <span className="truncate">{f.path}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
        <Card><CardContent className="pt-4 space-y-2">
          <div className="flex gap-2"><input className="flex-1 h-9 rounded-lg border border-input bg-background px-3 text-xs" value={codePrompt} onChange={(e) => setCodePrompt(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleGenerateCode()} placeholder="Generate code..." /><Button size="sm" onClick={handleGenerateCode} isLoading={chatLoading}><Play className="w-3 h-3" /></Button></div>
          {codeResult && <pre className="text-xs bg-muted/30 p-2 rounded max-h-32 overflow-y-auto whitespace-pre-wrap">{codeResult}</pre>}
        </CardContent></Card>
      </div>
      <div className="lg:col-span-2">
        <Card className="h-full">
          <CardHeader className="pb-2"><CardTitle className="text-sm">{activeFile ? activeFile.path : "Code Editor"}</CardTitle></CardHeader>
          <CardContent>
            {activeFile ? (
              <textarea className="w-full h-[500px] font-mono text-sm bg-muted/20 border border-input rounded-lg p-3 resize-none focus:outline-none focus:ring-1 focus:ring-primary" value={fileContent} onChange={(e) => setFileContent(e.target.value)} />
            ) : (
              <div className="flex flex-col items-center justify-center h-[500px] text-muted-foreground">
                <Code className="w-16 h-16 mb-4 opacity-20" />
                <p className="text-sm">Select a file to edit</p>
                <p className="text-xs mt-2">Or use <strong>Generate</strong> tab to create a new app</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function GenerateTab({ orgId, onCreated }: { orgId: string | null; onCreated: (p: any) => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState("web");
  const [frontend, setFrontend] = useState("");
  const [backend, setBackend] = useState("");
  const [db, setDb] = useState("");
  const [lang, setLang] = useState("python");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleGenerate = async () => {
    if (!name.trim() || !description.trim()) return;
    setLoading(true);
    try {
      const res = await codeStudioApi.generateApp({ name, description, project_type: type, frontend_framework: frontend || undefined, backend_framework: backend || undefined, database_type: db || undefined, language: lang, organization_id: orgId });
      setResult(res.data);
      toast.success(`Generated ${res.data.files_created} files`);
      onCreated(res.data);
    } catch { toast.error("Generation failed"); } finally { setLoading(false); }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader><CardTitle>AI App Generator</CardTitle><CardDescription>Describe your app idea and AI builds it</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="App name" />
          <textarea className="w-full h-28 rounded-lg border border-input bg-background px-3 py-2 text-sm" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Describe your app idea in detail..." />
          <div className="grid grid-cols-2 gap-3">
            <select className="h-10 rounded-lg border border-input bg-background px-3 text-sm" value={type} onChange={(e) => setType(e.target.value)}>
              <option value="web">Web App</option>
              <option value="api">API</option>
              <option value="mobile">Mobile</option>
              <option value="cli">CLI</option>
              <option value="desktop">Desktop</option>
            </select>
            <select className="h-10 rounded-lg border border-input bg-background px-3 text-sm" value={lang} onChange={(e) => setLang(e.target.value)}>
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="go">Go</option>
              <option value="rust">Rust</option>
              <option value="java">Java</option>
            </select>
            <Input value={frontend} onChange={(e) => setFrontend(e.target.value)} placeholder="Frontend (React, Vue...)" />
            <Input value={backend} onChange={(e) => setBackend(e.target.value)} placeholder="Backend (FastAPI, Node...)" />
          </div>
          <Input value={db} onChange={(e) => setDb(e.target.value)} placeholder="Database (PostgreSQL, MongoDB...)" />
          <Button onClick={handleGenerate} isLoading={loading} className="w-full"><Wand2 className="w-4 h-4 mr-1" /> Generate App</Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>{result ? result.name : "Generated Result"}</CardTitle></CardHeader>
        <CardContent>
          {result ? (
            <div className="space-y-3">
              <div className="flex gap-2">
                <Badge variant="default">{result.status}</Badge>
                <Badge variant="outline">{result.files_created} files</Badge>
              </div>
              {result.summary && <p className="text-sm text-muted-foreground whitespace-pre-wrap">{result.summary}</p>}
              {result.file_tree && (
                <div><p className="text-xs font-medium mb-1">File Structure</p>
                  <pre className="text-xs bg-muted/30 p-2 rounded max-h-60 overflow-y-auto">{Object.keys(result.file_tree).join("\n")}</pre>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Wand2 className="w-16 h-16 mb-4 opacity-20" />
              <p className="text-sm">Describe your app idea on the left</p>
              <div className="mt-4 space-y-2 text-xs">
                <p className="font-medium">Examples:</p>
                <p>&ldquo;A school management system with student registration and attendance&rdquo;</p>
                <p>&ldquo;An e-commerce platform with cart, checkout, and admin panel&rdquo;</p>
                <p>&ldquo;A task management app with real-time collaboration&rdquo;</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DebugTab() {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [lang, setLang] = useState("python");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleDebug = async () => {
    if (!code.trim() && !error.trim()) return;
    setLoading(true);
    try {
      const res = await codeStudioApi.debug({ code: code || undefined, error_message: error || undefined, language: lang });
      setResult(res.data);
    } catch { toast.error("Debug failed"); } finally { setLoading(false); }
  };

  const handleReview = async () => {
    if (!code.trim()) return;
    setLoading(true);
    try {
      const res = await codeStudioApi.reviewCode(code, lang);
      setResult(res.data);
    } catch { toast.error("Review failed"); } finally { setLoading(false); }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader><CardTitle>AI Debugger</CardTitle><CardDescription>Paste code or an error message for AI analysis</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <select className="h-10 rounded-lg border border-input bg-background px-3 text-sm flex-1" value={lang} onChange={(e) => setLang(e.target.value)}>
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="go">Go</option>
              <option value="rust">Rust</option>
              <option value="java">Java</option>
              <option value="sql">SQL</option>
            </select>
            <Button onClick={handleDebug} isLoading={loading} size="sm"><Bug className="w-3 h-3 mr-1" /> Debug</Button>
            <Button onClick={handleReview} isLoading={loading} variant="outline" size="sm"><Shield className="w-3 h-3 mr-1" /> Review</Button>
          </div>
          <textarea className="w-full h-32 rounded-lg border border-input bg-background px-3 py-2 text-sm font-mono" value={code} onChange={(e) => setCode(e.target.value)} placeholder="Paste your code here..." />
          <textarea className="w-full h-20 rounded-lg border border-input bg-background px-3 py-2 text-sm" value={error} onChange={(e) => setError(e.target.value)} placeholder="Error message (optional)" />
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-sm">Analysis Result</CardTitle></CardHeader>
        <CardContent className="space-y-3 max-h-[500px] overflow-y-auto">
          {result ? (
            <>
              {result.root_cause && <div><p className="text-xs font-medium text-destructive">Root Cause</p><p className="text-sm whitespace-pre-wrap">{result.root_cause}</p></div>}
              {result.solution && <div><p className="text-xs font-medium text-green-600">Solution</p><p className="text-sm whitespace-pre-wrap">{result.solution}</p></div>}
              {result.fixed_code && <div><p className="text-xs font-medium">Fixed Code</p><pre className="text-xs bg-muted/30 p-2 rounded max-h-40 overflow-y-auto">{result.fixed_code}</pre></div>}
              {result.suggestions?.length > 0 && <div><p className="text-xs font-medium">Suggestions</p><ul className="list-disc list-inside text-xs space-y-1">{result.suggestions.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul></div>}
              {result.issues?.length > 0 && <div><p className="text-xs font-medium">Issues Found ({result.issues.length})</p>{result.issues.map((issue: any, i: number) => <div key={i} className="text-xs p-2 bg-muted/30 rounded mt-1"><Badge variant="warning" className="text-[10px] mr-1">{issue.severity}</Badge>{issue.description}</div>)}</div>}
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Bug className="w-12 h-12 mb-3 opacity-20" />
              <p className="text-sm">Paste code and click Debug</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function TestsTab({ activeProject }: { activeProject: StudioProject | null }) {
  const [testRuns, setTestRuns] = useState<any[]>([]);
  const [testType, setTestType] = useState("unit");
  const [framework, setFramework] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { if (activeProject) loadTests(); }, [activeProject]);

  const loadTests = async () => {
    if (!activeProject) return;
    try { const res = await codeStudioApi.testRuns(activeProject.id); setTestRuns(res.data); } catch {}
  };

  const handleGenerate = async () => {
    if (!activeProject) return;
    setLoading(true);
    try {
      await codeStudioApi.generateTests(activeProject.id, { test_type: testType, framework: framework || undefined });
      toast.success("Tests generated");
      loadTests();
    } catch { toast.error("Failed"); } finally { setLoading(false); }
  };

  if (!activeProject) return <Card><CardContent className="py-12 text-center text-muted-foreground"><TestTube className="w-12 h-12 mx-auto mb-4 opacity-20" /><p>Select a project first</p></CardContent></Card>;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card><CardHeader><CardTitle className="text-sm">Generate Tests</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <select className="w-full h-10 rounded-lg border border-input bg-background px-3 text-sm" value={testType} onChange={(e) => setTestType(e.target.value)}>
            <option value="unit">Unit Tests</option>
            <option value="integration">Integration Tests</option>
            <option value="api">API Tests</option>
            <option value="security">Security Tests</option>
            <option value="performance">Performance Tests</option>
          </select>
          <Input value={framework} onChange={(e) => setFramework(e.target.value)} placeholder="Framework (pytest, jest...)" />
          <Button onClick={handleGenerate} isLoading={loading}><TestTube className="w-4 h-4 mr-1" /> Generate Tests</Button>
        </CardContent>
      </Card>
      <Card><CardHeader><CardTitle className="text-sm">Test Runs</CardTitle></CardHeader>
        <CardContent className="space-y-2 max-h-80 overflow-y-auto">
          {testRuns.map((t: any, i: number) => (
            <div key={i} className="flex items-center justify-between p-2 bg-muted/30 rounded text-sm">
              <div><p className="text-xs font-medium">{t.name}</p><p className="text-[10px] text-muted-foreground">{t.test_type} &middot; {t.framework}</p></div>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-green-600">{t.passed} passed</span>
                {t.failed > 0 && <span className="text-red-600">{t.failed} failed</span>}
                {t.coverage != null && <Badge variant="outline">{t.coverage}%</Badge>}
              </div>
            </div>
          ))}
          {testRuns.length === 0 && <p className="text-xs text-muted-foreground text-center py-8">No test runs yet</p>}
        </CardContent>
      </Card>
    </div>
  );
}

function SecurityTab({ activeProject }: { activeProject: StudioProject | null }) {
  const [scans, setScans] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedScan, setSelectedScan] = useState<any>(null);

  useEffect(() => { if (activeProject) { loadScans(); loadSummary(); } }, [activeProject]);

  const loadScans = async () => {
    if (!activeProject) return;
    try { const [s, sm] = await Promise.all([codeStudioApi.securityScans(activeProject.id), codeStudioApi.securitySummary(activeProject.id)]); setScans(s.data); setSummary(sm.data); } catch {}
  };

  const loadSummary = async () => {
    if (!activeProject) return;
    try { const res = await codeStudioApi.securitySummary(activeProject.id); setSummary(res.data); } catch {}
  };

  const handleScan = async () => {
    if (!activeProject) return;
    setLoading(true);
    try { const res = await codeStudioApi.securityScan(activeProject.id); setSelectedScan(res.data); toast.success("Scan complete"); loadScans(); } catch { toast.error("Scan failed"); } finally { setLoading(false); }
  };

  if (!activeProject) return <Card><CardContent className="py-12 text-center text-muted-foreground"><Shield className="w-12 h-12 mx-auto mb-4 opacity-20" /><p>Select a project first</p></CardContent></Card>;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card><CardHeader><CardTitle className="text-sm">Security Scanner</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {summary && (
            <div className="grid grid-cols-4 gap-2">
              <Card><CardContent className="pt-2 pb-2 text-center"><p className="text-lg font-bold text-red-600">{summary.critical}</p><p className="text-[10px]">Critical</p></CardContent></Card>
              <Card><CardContent className="pt-2 pb-2 text-center"><p className="text-lg font-bold text-orange-500">{summary.high}</p><p className="text-[10px]">High</p></CardContent></Card>
              <Card><CardContent className="pt-2 pb-2 text-center"><p className="text-lg font-bold text-yellow-500">{summary.medium}</p><p className="text-[10px]">Medium</p></CardContent></Card>
              <Card><CardContent className="pt-2 pb-2 text-center"><p className="text-lg font-bold text-muted-foreground">{summary.low}</p><p className="text-[10px]">Low</p></CardContent></Card>
            </div>
          )}
          <Button onClick={handleScan} isLoading={loading}><Shield className="w-4 h-4 mr-1" /> Run Full Scan</Button>
          {scans.length > 0 && (
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {scans.map((s: any, i: number) => (
                <button key={i} onClick={() => setSelectedScan(s)} className="w-full text-left text-xs p-2 bg-muted/30 rounded hover:bg-muted">
                  <span className="font-medium capitalize">{s.scan_type}</span>
                  <Badge variant={s.risk_score != null && s.risk_score > 70 ? "error" : s.risk_score != null && s.risk_score > 40 ? "warning" : "success"} className="ml-2 text-[10px]">
                    Risk: {s.risk_score != null ? Math.round(s.risk_score) : "N/A"}
                  </Badge>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      <Card><CardHeader><CardTitle className="text-sm">{selectedScan ? "Scan Results" : "Results"}</CardTitle></CardHeader>
        <CardContent className="space-y-3 max-h-96 overflow-y-auto">
          {selectedScan ? (
            <>
              {selectedScan.summary && <p className="text-sm">{selectedScan.summary}</p>}
              {selectedScan.vulnerabilities?.map((v: any, i: number) => (
                <div key={i} className="text-xs p-2 bg-muted/30 rounded space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={v.severity === "critical" ? "error" : v.severity === "high" ? "warning" : "default"} className="text-[10px]">{v.severity}</Badge>
                    <span className="font-medium">{v.type}</span>
                  </div>
                  {v.file && <p className="text-muted-foreground">File: {v.file}{v.line ? `:${v.line}` : ""}</p>}
                  <p>{v.description}</p>
                  {v.fix && <p className="text-green-600">Fix: {v.fix}</p>}
                </div>
              ))}
              {selectedScan.recommendations?.length > 0 && (
                <div><p className="text-xs font-medium mb-1">Recommendations</p>
                  <ul className="list-disc list-inside text-xs space-y-1">{selectedScan.recommendations.map((r: string, i: number) => <li key={i}>{r}</li>)}</ul>
                </div>
              )}
            </>
          ) : <p className="text-xs text-muted-foreground text-center py-12">Run a scan to see results</p>}
        </CardContent>
      </Card>
    </div>
  );
}

function DeployTab({ activeProject }: { activeProject: StudioProject | null }) {
  const [builds, setBuilds] = useState<any[]>([]);
  const [deployments, setDeployments] = useState<any[]>([]);
  const [docs, setDocs] = useState<any[]>([]);
  const [deployTarget, setDeployTarget] = useState("vercel");
  const [deployEnv, setDeployEnv] = useState("production");
  const [loading, setLoading] = useState(false);
  const [cicdResult, setCicdResult] = useState("");

  useEffect(() => { if (activeProject) { loadBuilds(); loadDeployments(); loadDocs(); } }, [activeProject]);

  const loadBuilds = async () => { if (!activeProject) return; try { const res = await codeStudioApi.builds(activeProject.id); setBuilds(res.data); } catch {} };
  const loadDeployments = async () => { if (!activeProject) return; try { const res = await codeStudioApi.deployments(activeProject.id); setDeployments(res.data); } catch {} };
  const loadDocs = async () => { if (!activeProject) return; try { const res = await codeStudioApi.docs(activeProject.id); setDocs(res.data); } catch {} };

  const handleBuild = async () => {
    if (!activeProject) return;
    try { await codeStudioApi.buildProject(activeProject.id); toast.success("Build started"); loadBuilds(); } catch { toast.error("Build failed"); }
  };

  const handleDeploy = async () => {
    if (!activeProject) return;
    setLoading(true);
    try { await codeStudioApi.deployProject(activeProject.id, { target: deployTarget, environment: deployEnv }); toast.success("Deployment configured"); loadDeployments(); } catch { toast.error("Deploy failed"); } finally { setLoading(false); }
  };

  const handleGenDocs = async (type: string) => {
    if (!activeProject) return;
    try { await codeStudioApi.generateDoc(activeProject.id, type); toast.success("Doc generated"); loadDocs(); } catch { toast.error("Failed"); }
  };

  const handleGenCICD = async () => {
    if (!activeProject) return;
    try { const res = await codeStudioApi.generateCICD(activeProject.id, "github"); setCicdResult(res.data.pipeline); } catch { toast.error("Failed"); }
  };

  const handleGenAllDocs = async () => {
    if (!activeProject) return;
    try { await codeStudioApi.generateAllDocs(activeProject.id); toast.success("All docs generated"); loadDocs(); } catch { toast.error("Failed"); }
  };

  if (!activeProject) return <Card><CardContent className="py-12 text-center text-muted-foreground"><Rocket className="w-12 h-12 mx-auto mb-4 opacity-20" /><p>Select a project first</p></CardContent></Card>;

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-3">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Build</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Button onClick={handleBuild} size="sm"><Play className="w-3 h-3 mr-1" /> Build Project</Button>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {builds.map((b: any, i: number) => (
                <div key={i} className="flex justify-between text-xs p-1.5 bg-muted/30 rounded">
                  <span>#{b.build_number} {b.branch}</span>
                  <Badge variant={b.status === "success" ? "success" : b.status === "failed" ? "error" : "warning"} className="text-[10px]">{b.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Deploy</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <select className="w-full h-9 rounded-lg border border-input bg-background px-3 text-xs" value={deployTarget} onChange={(e) => setDeployTarget(e.target.value)}>
              <option value="vercel">Vercel</option>
              <option value="netlify">Netlify</option>
              <option value="docker">Docker</option>
              <option value="kubernetes">Kubernetes</option>
              <option value="aws">AWS</option>
            </select>
            <select className="w-full h-9 rounded-lg border border-input bg-background px-3 text-xs" value={deployEnv} onChange={(e) => setDeployEnv(e.target.value)}>
              <option value="production">Production</option><option value="staging">Staging</option><option value="development">Development</option>
            </select>
            <div className="flex gap-2">
              <Button onClick={handleDeploy} isLoading={loading} size="sm"><Rocket className="w-3 h-3 mr-1" /> Configure Deploy</Button>
              <Button onClick={handleGenCICD} variant="outline" size="sm"><Github className="w-3 h-3 mr-1" /> CI/CD</Button>
            </div>
            {cicdResult && <pre className="text-xs bg-muted/30 p-2 rounded max-h-32 overflow-y-auto">{cicdResult}</pre>}
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {deployments.map((d: any, i: number) => (
                <div key={i} className="flex justify-between text-xs p-1.5 bg-muted/30 rounded">
                  <span>#{d.deployment_number} {d.target}</span>
                  <div className="flex gap-2">
                    <span className="text-muted-foreground">{d.environment}</span>
                    <Badge variant={d.status === "deployed" ? "success" : "outline"} className="text-[10px]">{d.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Documentation</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <Button onClick={handleGenAllDocs} size="sm" variant="outline"><BookOpen className="w-3 h-3 mr-1" /> Generate All</Button>
            <div className="flex gap-1 flex-wrap">
              {["readme", "api_docs", "user_manual", "dev_guide", "architecture"].map((t) => (
                <Button key={t} size="sm" variant="ghost" className="text-[10px] h-7" onClick={() => handleGenDocs(t)}>{t.replace("_", " ")}</Button>
              ))}
            </div>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {docs.map((d: any, i: number) => (
                <div key={i} className="text-xs p-1.5 bg-muted/30 rounded cursor-pointer hover:bg-muted">
                  <p className="font-medium">{d.title}</p>
                  <p className="text-muted-foreground">{d.doc_type}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
