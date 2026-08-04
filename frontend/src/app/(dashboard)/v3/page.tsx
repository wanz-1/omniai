"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  v3PersonalApi, v3OrganizationApi, v3CreationApi, v3CollaborationApi,
} from "@/lib/api-client";
import { toast } from "sonner";
import {
  User, Building2, Lightbulb, Users, MessageSquare, GraduationCap,
  Cpu, Loader2, Send, Plus, CheckCircle, Star, Briefcase,
  Heart, Target, Palette, Bot, Zap, Clock,
} from "lucide-react";

type PhaseTab = "personal" | "organization" | "creation" | "collaboration" | "physical";
type SubTab = string;

export default function V3Page() {
  const [tab, setTab] = useState<PhaseTab>("personal");
  const [orgId, setOrgId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/organizations").then((r) => r.json()).then((orgs) => {
      if (orgs.length > 0) setOrgId(orgs[0].id);
    }).catch(() => {});
  }, []);

  const phases: { key: PhaseTab; label: string; icon: any; description: string }[] = [
    { key: "personal", label: "Personal AI", icon: User, description: "Personal AI employees & executive team" },
    { key: "organization", label: "Organization", icon: Building2, description: "AI organization operating system" },
    { key: "creation", label: "Creation Engine", icon: Lightbulb, description: "AI startup builder & design studio" },
    { key: "collaboration", label: "Collaboration", icon: Users, description: "Meetings, communication & learning" },
    { key: "physical", label: "Physical World", icon: Cpu, description: "IoT, devices & robotics integration" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 flex items-center justify-center">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">V3 Intelligence Ecosystem</h1>
          <p className="text-muted-foreground mt-1">Autonomous AI — personal employees, organization OS, creation engine, human-AI collaboration, and physical world integration</p>
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {phases.map((p) => (
          <button
            key={p.key}
            onClick={() => setTab(p.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
              tab === p.key ? "bg-violet-500/10 text-violet-600 font-medium border border-violet-500/30" : "text-muted-foreground hover:bg-muted border border-transparent"
            }`}
          >
            <p.icon className="w-4 h-4" />
            <span className="hidden sm:inline">{p.label}</span>
          </button>
        ))}
      </div>

      {tab === "personal" && <PersonalTab />}
      {tab === "organization" && <OrganizationTab orgId={orgId} />}
      {tab === "creation" && <CreationTab />}
      {tab === "collaboration" && <CollaborationTab />}
      {tab === "physical" && <PhysicalTab />}
    </div>
  );
}

function PersonalTab() {
  const [sub, setSub] = useState<SubTab>("assistants");
  const [assistants, setAssistants] = useState<any[]>([]);
  const [executives, setExecutives] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [selectedAsst, setSelectedAsst] = useState<string | null>(null);

  useEffect(() => {
    v3PersonalApi.assistants().then((r) => setAssistants(r.data)).catch(() => {});
    v3PersonalApi.executives().then((r) => setExecutives(r.data)).catch(() => {});
    v3PersonalApi.tasks().then((r) => setTasks(r.data)).catch(() => {});
  }, []);

  const handleQuery = async () => {
    if (!query.trim() || !selectedAsst) return;
    try {
      const res = await v3PersonalApi.queryAssistant({ assistant_id: selectedAsst, query: query.trim() });
      setResponse(res.data.response);
    } catch { toast.error("Query failed"); }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {["assistants", "executives", "tasks", "query"].map((s) => (
          <button key={s} onClick={() => setSub(s)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              sub === s ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-muted"
            }`}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
        ))}
      </div>

      {sub === "assistants" && (
        <div className="grid gap-4 md:grid-cols-3">
          {assistants.map((a) => (
            <Card key={a.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Bot className="w-5 h-5 text-violet-500" />
                  <CardTitle className="text-sm">{a.name}</CardTitle>
                </div>
                <CardDescription>Role: {a.role} | {a.total_interactions} interactions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1">
                  {(a.capabilities || []).map((c: string, i: number) => <Badge key={i} variant="outline" className="text-xs">{c}</Badge>)}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sub === "executives" && (
        <div className="grid gap-4 md:grid-cols-2">
          {executives.map((e) => (
            <Card key={e.id} className="border-violet-500/20">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-violet-500" />
                  <CardTitle className="text-sm uppercase">{e.role} — {e.name}</CardTitle>
                </div>
                <CardDescription>{e.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1">
                  {(e.capabilities || []).map((c: string, i: number) => <Badge key={i} variant="outline" className="text-xs">{c}</Badge>)}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sub === "tasks" && (
        <div className="space-y-2">
          {tasks.map((t) => (
            <Card key={t.id}>
              <CardContent className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium">{t.title}</p>
                  <p className="text-xs text-muted-foreground">{t.category} — {t.priority}</p>
                </div>
                <Badge variant={t.status === "completed" ? "default" : "outline"}>{t.status}</Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sub === "query" && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Ask Your Personal AI</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <select
              value={selectedAsst || ""}
              onChange={(e) => setSelectedAsst(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border bg-background"
            >
              <option value="">Select assistant</option>
              {assistants.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <div className="flex gap-2">
              <Input placeholder="Ask anything..." value={query} onChange={(e) => setQuery(e.target.value)} />
              <Button onClick={handleQuery} disabled={!selectedAsst || !query.trim()}><Send className="w-4 h-4" /></Button>
            </div>
            {response && <div className="bg-muted p-3 rounded-lg text-sm"><p className="whitespace-pre-wrap">{response}</p></div>}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function OrganizationTab({ orgId }: { orgId: string | null }) {
  const [sub, setSub] = useState<SubTab>("departments");
  const [departments, setDepartments] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");

  useEffect(() => {
    if (!orgId) return;
    v3OrganizationApi.departments(orgId).then((r) => setDepartments(r.data)).catch(() => {});
    v3OrganizationApi.workflows(orgId).then((r) => setWorkflows(r.data)).catch(() => {});
  }, [orgId]);

  const handleQuery = async () => {
    if (!query.trim() || !orgId) return;
    try {
      const res = await v3OrganizationApi.query({ organization_id: orgId, query: query.trim() });
      setResponse(res.data.response);
    } catch {}
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {["departments", "workflows", "query"].map((s) => (
          <button key={s} onClick={() => setSub(s)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              sub === s ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-muted"
            }`}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
        ))}
      </div>

      {sub === "departments" && (
        <div className="grid gap-4 md:grid-cols-2">
          {departments.map((d) => (
            <Card key={d.id}>
              <CardHeader>
                <CardTitle className="text-sm">{d.name}</CardTitle>
                <CardDescription>{d.department_type} — {d.capabilities?.length} agents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1">
                  {(d.capabilities || []).map((c: string, i: number) => <Badge key={i} variant="outline" className="text-xs">{c}</Badge>)}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sub === "workflows" && (
        <div className="grid gap-4 md:grid-cols-2">
          {workflows.map((w) => (
            <Card key={w.id}>
              <CardHeader>
                <CardTitle className="text-sm">{w.name}</CardTitle>
                <CardDescription>{w.workflow_type} — {w.execution_count} executions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Badge variant={w.is_automatic ? "default" : "outline"}>{w.is_automatic ? "Automatic" : "Manual"}</Badge>
                  <Badge variant="outline">{w.status}</Badge>
                  {w.trigger && <Badge variant="outline">Trigger: {w.trigger}</Badge>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sub === "query" && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Query Organization OS</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Input placeholder="Ask your organization AI..." value={query} onChange={(e) => setQuery(e.target.value)} />
              <Button onClick={handleQuery}><Send className="w-4 h-4" /></Button>
            </div>
            {response && <div className="bg-muted p-3 rounded-lg text-sm whitespace-pre-wrap">{response}</div>}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CreationTab() {
  const [sub, setSub] = useState<SubTab>("startups");
  const [startups, setStartups] = useState<any[]>([]);
  const [ideas, setIdeas] = useState<any[]>([]);
  const [designs, setDesigns] = useState<any[]>([]);

  useEffect(() => {
    v3CreationApi.startups().then((r) => setStartups(r.data)).catch(() => {});
    v3CreationApi.designs().then((r) => setDesigns(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {["startups", "ideas", "designs"].map((s) => (
          <button key={s} onClick={() => setSub(s)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              sub === s ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-muted"
            }`}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
        ))}
      </div>

      {sub === "startups" && (
        <div className="grid gap-4 md:grid-cols-2">
          {startups.map((s) => (
            <Card key={s.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <CardTitle className="text-sm">{s.name}</CardTitle>
                <CardDescription>{s.industry || "General"} — {s.status}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground line-clamp-2">{s.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sub === "ideas" && (
        <div className="grid gap-4 md:grid-cols-3">
          {([...Array(3)]).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-amber-500" />
                  <CardTitle className="text-sm">Sample Idea {i + 1}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">AI-powered product concept in development</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sub === "designs" && (
        <div className="grid gap-4 md:grid-cols-3">
          {designs.map((d) => (
            <Card key={d.id}>
              <CardHeader>
                <CardTitle className="text-sm">{d.name}</CardTitle>
                <CardDescription>{d.asset_type} — {d.style}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground line-clamp-2">{d.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function CollaborationTab() {
  const [sub, setSub] = useState<SubTab>("meetings");
  const [meetings, setMeetings] = useState<any[]>([]);
  const [communications, setCommunications] = useState<any[]>([]);
  const [learning, setLearning] = useState<any[]>([]);

  useEffect(() => {
    v3CollaborationApi.meetings().then((r) => setMeetings(r.data)).catch(() => {});
    v3CollaborationApi.communications().then((r) => setCommunications(r.data)).catch(() => {});
    v3CollaborationApi.learningPaths().then((r) => setLearning(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {["meetings", "communications", "learning"].map((s) => (
          <button key={s} onClick={() => setSub(s)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              sub === s ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-muted"
            }`}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
        ))}
      </div>

      {sub === "meetings" && (
        <div className="grid gap-4 md:grid-cols-2">
          {meetings.map((m) => (
            <Card key={m.id}>
              <CardHeader>
                <CardTitle className="text-sm">{m.title}</CardTitle>
                <CardDescription>{m.participants?.length || 0} participants — {m.status}</CardDescription>
              </CardHeader>
              <CardContent>
                {m.summary && <p className="text-xs text-muted-foreground line-clamp-2">{m.summary}</p>}
                {m.action_items?.length > 0 && <p className="text-xs mt-1">{m.action_items.length} action items</p>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sub === "communications" && (
        <div className="grid gap-4 md:grid-cols-2">
          {communications.map((c) => (
            <Card key={c.id}>
              <CardHeader>
                <CardTitle className="text-sm">{c.title}</CardTitle>
                <CardDescription>{c.communication_type} — {c.tone}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground line-clamp-2">{c.generated_content || c.content}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sub === "learning" && (
        <div className="grid gap-4 md:grid-cols-2">
          {learning.map((l) => (
            <Card key={l.id}>
              <CardHeader>
                <CardTitle className="text-sm">{l.title}</CardTitle>
                <CardDescription>{l.subject} — {l.skill_level}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-muted rounded-full h-2">
                    <div className="bg-primary h-2 rounded-full" style={{ width: `${l.progress}%` }} />
                  </div>
                  <span className="text-xs text-muted-foreground">{l.progress}%</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function PhysicalTab() {
  const [devices, setDevices] = useState<any[]>([]);

  useEffect(() => {
    v3CollaborationApi.devices().then((r) => setDevices(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-blue-500/20">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-500" />
              <CardTitle className="text-sm">IoT & Devices</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{devices.length}</p>
            <p className="text-xs text-muted-foreground">Registered Devices</p>
          </CardContent>
        </Card>
        <Card className="border-green-500/20">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-green-500" />
              <CardTitle className="text-sm">Status</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-bold text-green-500">{devices.filter((d) => d.status === "online").length} Online</p>
            <p className="text-xs text-muted-foreground">{devices.filter((d) => d.status !== "online").length} Offline</p>
          </CardContent>
        </Card>
        <Card className="border-amber-500/20">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-500" />
              <CardTitle className="text-sm">Schedules</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">—</p>
            <p className="text-xs text-muted-foreground">Active Schedules</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {devices.map((d) => (
          <Card key={d.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{d.name}</CardTitle>
                  <CardDescription>{d.device_type} — {d.protocol}</CardDescription>
                </div>
                <Badge variant={d.status === "online" ? "default" : "outline"}>{d.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1">
                {(d.capabilities || []).map((c: string, i: number) => <Badge key={i} variant="outline" className="text-xs">{c}</Badge>)}
              </div>
              {d.last_seen && <p className="text-xs text-muted-foreground mt-1">Last seen: {new Date(d.last_seen).toLocaleString()}</p>}
            </CardContent>
          </Card>
        ))}
        {devices.length === 0 && <p className="col-span-2 text-center text-muted-foreground py-8">No devices registered. Connect IoT devices to begin monitoring.</p>}
      </div>
    </div>
  );
}

function Activity(props: any) { return <div {...props} />; }
