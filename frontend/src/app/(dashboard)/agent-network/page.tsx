"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { agentNetworkApi } from "@/lib/api-client";
import { toast } from "sonner";
import {
  Users, MessageSquare, Brain, Shield, Search, Code, Bot,
  Loader2, Send, Plus, Trash2, CheckCircle, XCircle,
  Play, Award, Cpu,
} from "lucide-react";

type Tab = "orchestrate" | "teams" | "communication" | "memory" | "evaluation" | "governance" | "research" | "dev";

export default function AgentNetworkPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("orchestrate");
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => { loadOrg(); }, []);
  useEffect(() => { if (orgId) loadDashboard(); }, [orgId]);

  const loadOrg = async () => {
    try {
      const res = await fetch("/api/organizations");
      const orgs = await res.json();
      if (orgs.length > 0) setOrgId(orgs[0].id);
    } catch {} finally { setLoading(false); }
  };

  const loadDashboard = async () => {
    if (!orgId) return;
    try {
      const res = await agentNetworkApi.dashboard(orgId);
      setDashboard(res.data);
    } catch {}
  };

  const tabs: { key: Tab; label: string; icon: any; description: string }[] = [
    { key: "orchestrate", label: "Orchestrate", icon: Cpu, description: "Multi-agent planning & execution" },
    { key: "teams", label: "Teams", icon: Users, description: "AI team builder & management" },
    { key: "communication", label: "Communication", icon: MessageSquare, description: "Inter-agent messaging" },
    { key: "memory", label: "Memory", icon: Brain, description: "Shared knowledge network" },
    { key: "evaluation", label: "Evaluation", icon: Award, description: "Review & performance" },
    { key: "governance", label: "Governance", icon: Shield, description: "Permissions & safety" },
    { key: "research", label: "Research", icon: Search, description: "Autonomous research" },
    { key: "dev", label: "Dev Studio", icon: Code, description: "AI software development" },
  ];

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Agent Network</h1>
        <p className="text-muted-foreground mt-1">Collaborative AI workforce — multi-agent orchestration, teams, communication, and governance</p>
      </div>

      {dashboard && (
        <div className="grid gap-4 md:grid-cols-5">
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.team_count}</p><p className="text-xs text-muted-foreground">Teams</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.recent_tasks?.length || 0}</p><p className="text-xs text-muted-foreground">Recent Tasks</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.research_count}</p><p className="text-xs text-muted-foreground">Research</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.dev_projects_count}</p><p className="text-xs text-muted-foreground">Dev Projects</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.top_agents?.length || 0}</p><p className="text-xs text-muted-foreground">Top Agents</p></CardContent></Card>
        </div>
      )}

      <div className="flex gap-2 overflow-x-auto pb-2">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
              tab === t.key ? "bg-primary/10 text-primary font-medium border border-primary/30" : "text-muted-foreground hover:bg-muted border border-transparent"
            }`}
          >
            <t.icon className="w-4 h-4" />
            <span className="hidden sm:inline">{t.label}</span>
          </button>
        ))}
      </div>

      {tab === "orchestrate" && <OrchestrateTab orgId={orgId} />}
      {tab === "teams" && <TeamsTab orgId={orgId} />}
      {tab === "communication" && <CommunicationTab orgId={orgId} />}
      {tab === "memory" && <MemoryTab orgId={orgId} />}
      {tab === "evaluation" && <EvaluationTab orgId={orgId} />}
      {tab === "governance" && <GovernanceTab orgId={orgId} />}
      {tab === "research" && <ResearchTab orgId={orgId} />}
      {tab === "dev" && <DevTab orgId={orgId} />}
    </div>
  );
}

function OrchestrateTab({ orgId }: { orgId: string | null }) {
  const [task, setTask] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleOrchestrate = async () => {
    if (!task.trim() || !orgId) return;
    setLoading(true);
    try {
      const res = await agentNetworkApi.orchestrate({ organization_id: orgId, task, team_config: {} });
      setResult(res.data);
      toast.success("Orchestration complete");
    } catch { toast.error("Orchestration failed"); } finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>Multi-Agent Orchestration</CardTitle><CardDescription>Describe a complex task and let the orchestrator break it down across specialized AI agents</CardDescription></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <input className="flex-1 h-10 rounded-lg border border-input bg-background px-3 py-2 text-sm" value={task} onChange={(e) => setTask(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleOrchestrate()} placeholder="e.g. Create a business plan for a tourism company..." />
            <Button onClick={handleOrchestrate} isLoading={loading}><Send className="w-4 h-4" /></Button>
          </div>
          {result && (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {result.agents_involved?.map((a: string, i: number) => (
                  <Badge key={i} variant="default">{a}</Badge>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">{result.steps_completed} steps completed</p>
              <Card className="bg-muted/30"><CardContent className="pt-4 text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">{result.final_output}</CardContent></Card>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function TeamsTab({ orgId }: { orgId: string | null }) {
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [purpose, setPurpose] = useState("");

  useEffect(() => { if (orgId) loadTeams(); }, [orgId]);

  const loadTeams = async () => {
    if (!orgId) return;
    try { const res = await agentNetworkApi.teams(orgId); setTeams(res.data); } catch {} finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if (!name.trim() || !orgId) return;
    try {
      await agentNetworkApi.createTeam({ name, purpose, organization_id: orgId });
      toast.success("Team created");
      setShowCreate(false); setName(""); setPurpose("");
      loadTeams();
    } catch { toast.error("Failed to create team"); }
  };

  const handleAutoCreate = async () => {
    if (!orgId) return;
    try {
      const res = await agentNetworkApi.autoCreateTeam({ organization_id: orgId, task: purpose || "General purpose", team_config: {} });
      toast.success("Team auto-created");
      loadTeams();
    } catch { toast.error("Auto-create failed"); }
  };

  const handleDelete = async (id: string) => {
    try { await agentNetworkApi.deleteTeam(id); toast.success("Team deleted"); loadTeams(); } catch { toast.error("Failed"); }
  };

  if (loading) return <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin" /></div>;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button onClick={() => setShowCreate(!showCreate)}><Plus className="w-4 h-4 mr-1" /> Create Team</Button>
        <Button variant="outline" onClick={handleAutoCreate}><Bot className="w-4 h-4 mr-1" /> Auto-Create</Button>
      </div>
      {showCreate && (
        <Card><CardContent className="pt-4 space-y-3">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Team name" />
          <Input value={purpose} onChange={(e) => setPurpose(e.target.value)} placeholder="Purpose / roles (comma-separated)" />
          <Button onClick={handleCreate}>Create</Button>
        </CardContent></Card>
      )}
      <div className="grid gap-4 md:grid-cols-2">
        {teams.map((team: any) => (
          <Card key={team.id}>
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-base">{team.name}</CardTitle>
                  {team.purpose && <CardDescription className="text-xs">{team.purpose}</CardDescription>}
                </div>
                <div className="flex gap-1">
                  <Badge variant={team.is_active ? "default" : "outline"}>{team.is_active ? "Active" : "Inactive"}</Badge>
                  <button onClick={() => handleDelete(team.id)} className="text-muted-foreground hover:text-destructive"><Trash2 className="w-3 h-3" /></button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Members: {team.members?.length || 0}</p>
              {team.members?.map((m: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-xs mt-1 p-1 bg-muted/30 rounded">
                  <Bot className="w-3 h-3" /> {m.role} {m.is_lead && <Badge variant="default" className="text-[10px] px-1">Lead</Badge>}
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
        {teams.length === 0 && <p className="text-sm text-muted-foreground col-span-2 text-center py-8">No teams yet. Create one to start collaborating.</p>}
      </div>
    </div>
  );
}

function CommunicationTab({ orgId }: { orgId: string | null }) {
  const [messages, setMessages] = useState<any[]>([]);
  const [content, setContent] = useState("");

  return (
    <Card>
      <CardHeader><CardTitle>Inter-Agent Communication</CardTitle><CardDescription>Agent-to-agent messaging and task delegation</CardDescription></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2"><Input value={content} onChange={(e) => setContent(e.target.value)} placeholder="Type a message to broadcast..." /><Button><Send className="w-4 h-4" /></Button></div>
        <div className="text-sm text-muted-foreground">Use the Teams tab to select agents and communicate directly. Messages appear here once agents are connected.</div>
      </CardContent>
    </Card>
  );
}

function MemoryTab({ orgId }: { orgId: string | null }) {
  const [memories, setMemories] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [key, setKey] = useState("");
  const [content, setContent] = useState("");

  const handleSearch = async () => {
    if (!searchQuery) return;
    try { const res = await agentNetworkApi.searchMemory(searchQuery, undefined, orgId || undefined); setMemories(res.data); } catch {}
  };

  const handleStore = async () => {
    if (!key.trim() || !content.trim()) return;
    try {
      await agentNetworkApi.storeMemory({ key, content, organization_id: orgId });
      toast.success("Memory stored");
      setKey(""); setContent("");
    } catch { toast.error("Failed"); }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader><CardTitle className="text-sm">Store Memory</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Input value={key} onChange={(e) => setKey(e.target.value)} placeholder="Memory key" />
          <textarea className="w-full h-24 rounded-lg border border-input bg-background px-3 py-2 text-sm" value={content} onChange={(e) => setContent(e.target.value)} placeholder="Memory content" />
          <Button onClick={handleStore} size="sm"><Brain className="w-3 h-3 mr-1" /> Store</Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-sm">Search Memory</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSearch()} placeholder="Search knowledge..." />
            <Button onClick={handleSearch} size="sm"><Search className="w-3 h-3" /></Button>
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {memories.map((m: any, i: number) => (
              <div key={i} className="text-sm p-2 bg-muted/30 rounded">
                <p className="font-medium text-xs">{m.key} <Badge variant="outline" className="text-[10px] px-1">{m.memory_type}</Badge></p>
                <p className="text-xs text-muted-foreground truncate">{m.content}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function EvaluationTab({ orgId }: { orgId: string | null }) {
  const [reviews, setReviews] = useState<any[]>([]);
  const [agentId, setAgentId] = useState("");

  const loadReviews = async () => {
    if (!agentId) return;
    try { const res = await agentNetworkApi.getReviews(agentId); setReviews(res.data); } catch {}
  };

  return (
    <Card>
      <CardHeader><CardTitle>Agent Evaluation</CardTitle><CardDescription>Review, score, and track agent performance</CardDescription></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input value={agentId} onChange={(e) => setAgentId(e.target.value)} placeholder="Agent ID to review" />
          <Button onClick={loadReviews} size="sm"><Search className="w-3 h-3" /></Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {reviews.map((r: any, i: number) => (
            <Card key={i}>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <Badge variant={r.is_approved ? "success" : "warning"}>{r.is_approved ? "Approved" : "Pending"}</Badge>
                  <span className="text-lg font-bold">{r.score}/10</span>
                </div>
                <p className="text-xs text-muted-foreground mt-2">{r.review_type} review</p>
                {r.suggestions?.length > 0 && <p className="text-xs mt-2">Suggestions: {r.suggestions.join(", ")}</p>}
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function GovernanceTab({ orgId }: { orgId: string | null }) {
  const [permissions, setPermissions] = useState<any[]>([]);
  const [agentId, setAgentId] = useState("");

  const loadPermissions = async () => {
    if (!agentId) return;
    try { const res = await agentNetworkApi.getPermissions(agentId); setPermissions(res.data); } catch {}
  };

  const handleRevoke = async (id: string) => {
    try { await agentNetworkApi.revokePermission(id); toast.success("Revoked"); loadPermissions(); } catch {}
  };

  return (
    <Card>
      <CardHeader><CardTitle>Governance & Permissions</CardTitle><CardDescription>Control agent access to resources and actions</CardDescription></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input value={agentId} onChange={(e) => setAgentId(e.target.value)} placeholder="Agent ID" />
          <Button onClick={loadPermissions} size="sm"><Search className="w-3 h-3" /></Button>
        </div>
        <div className="space-y-2">
          {permissions.map((p: any, i: number) => (
            <div key={i} className="flex items-center justify-between text-sm p-2 bg-muted/30 rounded">
              <div>
                <span className="font-medium">{p.resource}</span> / <span>{p.action}</span>
                <Badge variant={p.access_level === "allow" ? "success" : "outline"} className="ml-2 text-[10px]">{p.access_level}</Badge>
              </div>
              <button onClick={() => handleRevoke(p.id)} className="text-muted-foreground hover:text-destructive"><XCircle className="w-4 h-4" /></button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ResearchTab({ orgId }: { orgId: string | null }) {
  const [research, setResearch] = useState<any[]>([]);
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [depth, setDepth] = useState("standard");
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<any>(null);

  useEffect(() => { loadResearch(); }, []);

  const loadResearch = async () => {
    try { const res = await agentNetworkApi.listResearch(); setResearch(res.data); } catch {}
  };

  const handleResearch = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const res = await agentNetworkApi.conductResearch({ title: title || topic, topic, depth, organization_id: orgId });
      setSelected(res.data);
      toast.success("Research complete");
      loadResearch();
    } catch { toast.error("Research failed"); } finally { setLoading(false); }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="space-y-4">
        <Card>
          <CardHeader><CardTitle className="text-sm">New Research</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Research title" />
            <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Research topic" />
            <select className="w-full h-10 rounded-lg border border-input bg-background px-3 text-sm" value={depth} onChange={(e) => setDepth(e.target.value)}>
              <option value="quick">Quick</option>
              <option value="standard">Standard</option>
              <option value="deep">Deep</option>
            </select>
            <Button onClick={handleResearch} isLoading={loading}><Search className="w-4 h-4 mr-1" /> Research</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">History</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-60 overflow-y-auto">
            {research.map((r: any, i: number) => (
              <button key={i} onClick={() => setSelected(r)} className="w-full text-left text-sm p-2 bg-muted/30 rounded hover:bg-muted transition-colors">
                <p className="font-medium truncate">{r.title}</p>
                <div className="flex gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline">{r.depth}</Badge>
                  <span>{r.status}</span>
                </div>
              </button>
            ))}
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-sm">{selected ? selected.title : "Research Results"}</CardTitle></CardHeader>
        <CardContent className="space-y-3 max-h-96 overflow-y-auto">
          {selected ? (
            <>
              {selected.summary && <div><p className="text-xs font-medium text-muted-foreground">Summary</p><p className="text-sm whitespace-pre-wrap">{selected.summary}</p></div>}
              {selected.recommendations?.length > 0 && (
                <div><p className="text-xs font-medium text-muted-foreground">Recommendations</p><ul className="list-disc list-inside text-sm">{selected.recommendations.map((r: string, i: number) => <li key={i}>{r}</li>)}</ul></div>
              )}
              {selected.confidence && <p className="text-xs text-muted-foreground">Confidence: {Math.round(selected.confidence * 100)}%</p>}
              {selected.report && <div><p className="text-xs font-medium text-muted-foreground">Full Report</p><p className="text-sm whitespace-pre-wrap">{selected.report}</p></div>}
            </>
          ) : <p className="text-sm text-muted-foreground">Select or conduct research to view results</p>}
        </CardContent>
      </Card>
    </div>
  );
}

function DevTab({ orgId }: { orgId: string | null }) {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [techStack, setTechStack] = useState("");
  const [requirements, setRequirements] = useState("");
  const [selectedProject, setSelectedProject] = useState<any>(null);

  useEffect(() => { if (orgId) loadProjects(); }, [orgId]);

  const loadProjects = async () => {
    if (!orgId) return;
    try { const res = await agentNetworkApi.listDevProjects(orgId); setProjects(res.data); } catch {} finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if (!name.trim()) return;
    try {
      const res = await agentNetworkApi.createDevProject({
        name, description, tech_stack: techStack.split(",").map((s) => s.trim()).filter(Boolean),
        requirements, organization_id: orgId,
      });
      setSelectedProject(res.data);
      toast.success("Project created");
      setShowCreate(false); setName(""); setDescription(""); setTechStack(""); setRequirements("");
      loadProjects();
    } catch { toast.error("Failed"); }
  };

  const handleGenerateCode = async (id: string) => {
    try { const res = await agentNetworkApi.generateCode(id); toast.success(`Generated ${res.data.files?.length || 0} files`); loadProjects(); } catch { toast.error("Failed"); }
  };

  const handleSecurity = async (id: string) => {
    try { await agentNetworkApi.securityReview(id); toast.success("Security review done"); } catch { toast.error("Failed"); }
  };

  const handleTests = async (id: string) => {
    try { await agentNetworkApi.runTests(id); toast.success("Tests completed"); } catch { toast.error("Failed"); }
  };

  const handleComplete = async (id: string) => {
    try { await agentNetworkApi.completeDevProject(id); toast.success("Project completed!"); loadProjects(); } catch { toast.error("Failed"); }
  };

  if (loading) return <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin" /></div>;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="space-y-4">
        <Button onClick={() => setShowCreate(!showCreate)}><Plus className="w-4 h-4 mr-1" /> New Dev Project</Button>
        {showCreate && (
          <Card><CardContent className="pt-4 space-y-3">
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Project name" />
            <textarea className="w-full h-20 rounded-lg border border-input bg-background px-3 py-2 text-sm" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
            <Input value={techStack} onChange={(e) => setTechStack(e.target.value)} placeholder="Tech stack (comma-separated)" />
            <textarea className="w-full h-20 rounded-lg border border-input bg-background px-3 py-2 text-sm" value={requirements} onChange={(e) => setRequirements(e.target.value)} placeholder="Requirements" />
            <Button onClick={handleCreate}>Create Project</Button>
          </CardContent></Card>
        )}
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {projects.map((p: any, i: number) => (
            <button key={i} onClick={() => setSelectedProject(p)} className={`w-full text-left p-3 rounded-lg border transition-colors ${selectedProject?.id === p.id ? "border-primary bg-primary/5" : "border-border hover:bg-muted"}`}>
              <div className="flex justify-between items-start">
                <p className="font-medium text-sm truncate">{p.name}</p>
                <Badge variant={p.status === "completed" ? "success" : p.status === "planning" ? "outline" : "warning"} className="text-[10px]">{p.status}</Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1">{p.tech_stack?.join(", ") || "No stack"}</p>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden"><div className="h-full bg-primary rounded-full transition-all" style={{ width: `${p.progress || 0}%` }} /></div>
                <span className="text-xs text-muted-foreground">{Math.round(p.progress || 0)}%</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{selectedProject ? selectedProject.name : "Project Workspace"}</CardTitle>
          {selectedProject?.status && <CardDescription>Status: {selectedProject.status}</CardDescription>}
        </CardHeader>
        <CardContent className="space-y-3">
          {selectedProject ? (
            <>
              {selectedProject.description && <p className="text-xs text-muted-foreground">{selectedProject.description}</p>}
              <div className="flex gap-2 flex-wrap">
                <Button size="sm" variant="outline" onClick={() => handleGenerateCode(selectedProject.id)}><Code className="w-3 h-3 mr-1" /> Generate Code</Button>
                <Button size="sm" variant="outline" onClick={() => handleSecurity(selectedProject.id)}><Shield className="w-3 h-3 mr-1" /> Security</Button>
                <Button size="sm" variant="outline" onClick={() => handleTests(selectedProject.id)}><CheckCircle className="w-3 h-3 mr-1" /> Tests</Button>
                <Button size="sm" onClick={() => handleComplete(selectedProject.id)}><Play className="w-3 h-3 mr-1" /> Complete</Button>
              </div>
              {selectedProject.architecture && (
                <div><p className="text-xs font-medium text-muted-foreground">Architecture</p><pre className="text-xs bg-muted/30 p-2 rounded max-h-40 overflow-y-auto">{JSON.stringify(selectedProject.architecture, null, 2)}</pre></div>
              )}
              {selectedProject.generated_code && (
                <div><p className="text-xs font-medium text-muted-foreground">Generated Files ({Object.keys(selectedProject.generated_code).length})</p><pre className="text-xs bg-muted/30 p-2 rounded max-h-40 overflow-y-auto">{Object.keys(selectedProject.generated_code).join("\n")}</pre></div>
              )}
            </>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Code className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p className="text-sm">Create a dev project to start building with the AI Software Development Team</p>
              <p className="text-xs mt-2">Product Manager → Architect → Developer → Security → QA → Deploy</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
