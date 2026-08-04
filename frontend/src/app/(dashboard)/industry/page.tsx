"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { industryApi } from "@/lib/api-client";
import { toast } from "sonner";
import {
  Heart, GraduationCap, Stethoscope, Sprout, Compass, Landmark, Briefcase,
  Loader2, Send, Search, Book, Shield, Package, Code, Grid, Bot,
  CheckCircle, XCircle, Plus, Download, Star,
} from "lucide-react";

const INDUSTRY_META: Record<string, { icon: any; color: string; label: string }> = {
  ngo: { icon: Heart, color: "text-emerald-500", label: "NGO & Development" },
  education: { icon: GraduationCap, color: "text-blue-500", label: "Education" },
  healthcare: { icon: Stethoscope, color: "text-red-500", label: "Healthcare" },
  agriculture: { icon: Sprout, color: "text-green-500", label: "Agriculture" },
  tourism: { icon: Compass, color: "text-amber-500", label: "Tourism & Hospitality" },
  government: { icon: Landmark, color: "text-indigo-500", label: "Government" },
  business: { icon: Briefcase, color: "text-violet-500", label: "Business" },
};

type SubTab = "overview" | "agents" | "knowledge" | "workflows" | "templates" | "compliance" | "packages" | "chat";

export default function IndustryPage() {
  const [industries, setIndustries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [subTab, setSubTab] = useState<SubTab>("overview");
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const res = await industryApi.list();
      const list = res.data;
      setIndustries(list);
      if (list.length > 0 && !selectedSlug) setSelectedSlug(list[0].slug);
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { if (selectedSlug) loadDashboard(); }, [selectedSlug]);

  const loadDashboard = async () => {
    try {
      const res = await industryApi.dashboard(selectedSlug!);
      setDashboard(res.data);
    } catch { setDashboard(null); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Industry Solutions</h1>
        <p className="text-muted-foreground mt-1">Specialized AI solutions for every sector — agents, knowledge, workflows, templates, and compliance</p>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {industries.map((ind) => {
          const meta = INDUSTRY_META[ind.slug] || { icon: Grid, color: "text-muted-foreground", label: ind.name };
          const Icon = meta.icon;
          return (
            <button
              key={ind.id}
              onClick={() => { setSelectedSlug(ind.slug); setSubTab("overview"); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
                selectedSlug === ind.slug ? "bg-primary/10 text-primary font-medium border border-primary/30" : "text-muted-foreground hover:bg-muted border border-transparent"
              }`}
            >
              <Icon className={`w-4 h-4 ${meta.color}`} />
              <span className="hidden sm:inline">{meta.label}</span>
            </button>
          );
        })}
      </div>

      {selectedSlug && (
        <>
          {dashboard && (
            <div className="grid gap-4 md:grid-cols-5">
              <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.agents}</p><p className="text-xs text-muted-foreground">AI Agents</p></CardContent></Card>
              <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.workflows}</p><p className="text-xs text-muted-foreground">Workflows</p></CardContent></Card>
              <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.knowledge_entries}</p><p className="text-xs text-muted-foreground">Knowledge</p></CardContent></Card>
              <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.templates}</p><p className="text-xs text-muted-foreground">Templates</p></CardContent></Card>
              <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.packages}</p><p className="text-xs text-muted-foreground">Packages</p></CardContent></Card>
            </div>
          )}

          <div className="flex gap-2 overflow-x-auto pb-2">
            {[
              { key: "overview" as SubTab, label: "Overview", icon: Grid },
              { key: "agents" as SubTab, label: "Agents", icon: Bot },
              { key: "knowledge" as SubTab, label: "Knowledge", icon: Book },
              { key: "workflows" as SubTab, label: "Workflows", icon: Code },
              { key: "templates" as SubTab, label: "Templates", icon: Package },
              { key: "compliance" as SubTab, label: "Compliance", icon: Shield },
              { key: "packages" as SubTab, label: "Packages", icon: Download },
              { key: "chat" as SubTab, label: "AI Chat", icon: Send },
            ].map((t) => (
              <button
                key={t.key}
                onClick={() => setSubTab(t.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
                  subTab === t.key ? "bg-primary/10 text-primary font-medium border border-primary/30" : "text-muted-foreground hover:bg-muted border border-transparent"
                }`}
              >
                <t.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{t.label}</span>
              </button>
            ))}
          </div>

          {subTab === "overview" && <OverviewTab slug={selectedSlug} dashboard={dashboard} />}
          {subTab === "agents" && <AgentsTab slug={selectedSlug} />}
          {subTab === "knowledge" && <KnowledgeTab slug={selectedSlug} />}
          {subTab === "workflows" && <WorkflowsTab slug={selectedSlug} />}
          {subTab === "templates" && <TemplatesTab slug={selectedSlug} />}
          {subTab === "compliance" && <ComplianceTab slug={selectedSlug} />}
          {subTab === "packages" && <PackagesTab slug={selectedSlug} />}
          {subTab === "chat" && <ChatTab slug={selectedSlug} />}
        </>
      )}
    </div>
  );
}

function OverviewTab({ slug, dashboard }: { slug: string; dashboard: any }) {
  const meta = INDUSTRY_META[slug] || { icon: Grid, color: "text-muted-foreground", label: slug };
  const Icon = meta.icon;
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Icon className={`w-8 h-8 ${meta.color}`} />
            <div>
              <CardTitle>{meta.label}</CardTitle>
              <CardDescription>{dashboard?.industry?.description || "AI-powered industry solution"}</CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>
      {dashboard?.stats && (
        <div className="grid gap-4 md:grid-cols-3">
          {Object.entries(dashboard.stats).map(([key, val]: [string, any]) => (
            <Card key={key}>
              <CardContent className="pt-4">
                <p className="text-2xl font-bold">{val}</p>
                <p className="text-sm text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentsTab({ slug }: { slug: string }) {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    industryApi.agents(slug).then((res) => setAgents(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Industry AI Agents</h3>
      <div className="grid gap-4 md:grid-cols-2">
        {agents.map((a) => (
          <Card key={a.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{a.name}</CardTitle>
                  <CardDescription className="line-clamp-1">{a.description}</CardDescription>
                </div>
                <Badge variant={a.is_active ? "default" : "outline"}>{a.agent_type}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1">
                {(a.capabilities || []).map((c: string, i: number) => (
                  <Badge key={i} variant="outline" className="text-xs">{c}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
        {agents.length === 0 && <p className="col-span-2 text-muted-foreground py-8 text-center">No agents configured</p>}
      </div>
    </div>
  );
}

function KnowledgeTab({ slug }: { slug: string }) {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    industryApi.knowledge(slug).then((res) => setEntries(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, [slug]);

  const filtered = entries.filter((e) => !search || e.title?.toLowerCase().includes(search.toLowerCase()));

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search knowledge..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-10" />
        </div>
      </div>
      <div className="grid gap-3">
        {filtered.map((e) => (
          <Card key={e.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle className="text-sm">{e.title}</CardTitle>
                {e.category && <Badge variant="outline">{e.category}</Badge>}
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground line-clamp-2">{e.content}</p>
              {e.tags?.length > 0 && (
                <div className="flex gap-1 mt-2">
                  {e.tags.map((t: string, i: number) => <Badge key={i} variant="outline" className="text-xs">{t}</Badge>)}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
        {filtered.length === 0 && <p className="text-muted-foreground py-8 text-center">No knowledge entries</p>}
      </div>
    </div>
  );
}

function WorkflowsTab({ slug }: { slug: string }) {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    industryApi.workflows(slug).then((res) => setWorkflows(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Industry Workflows</h3>
      <div className="grid gap-4 md:grid-cols-2">
        {workflows.map((w) => (
          <Card key={w.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{w.name}</CardTitle>
                  <CardDescription className="line-clamp-1">{w.description}</CardDescription>
                </div>
                <Badge variant={w.is_active ? "default" : "outline"}>{w.workflow_type}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {w.trigger && <p className="text-xs text-muted-foreground">Trigger: {w.trigger}</p>}
              {w.steps && <p className="text-xs text-muted-foreground mt-1">{w.steps.length} step(s)</p>}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function TemplatesTab({ slug }: { slug: string }) {
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    industryApi.templates(slug).then((res) => setTemplates(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Industry Templates</h3>
      <div className="grid gap-4 md:grid-cols-2">
        {templates.map((t) => (
          <Card key={t.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{t.name}</CardTitle>
                  <CardDescription className="line-clamp-1">{t.description}</CardDescription>
                </div>
                <Badge variant="outline">{t.template_type}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {t.category && <Badge variant="outline" className="text-xs">{t.category}</Badge>}
              {t.variables?.length > 0 && <p className="text-xs text-muted-foreground mt-1">Variables: {t.variables.join(", ")}</p>}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ComplianceTab({ slug }: { slug: string }) {
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    industryApi.compliance(slug).then((res) => setRules(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Compliance Rules</h3>
      <div className="grid gap-4 md:grid-cols-2">
        {rules.map((r) => (
          <Card key={r.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{r.name}</CardTitle>
                  <CardDescription className="line-clamp-1">{r.description}</CardDescription>
                </div>
                <Badge
                  variant={r.severity === "high" ? "error" : r.severity === "medium" ? "warning" : "default"}
                >{r.severity}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 text-xs text-muted-foreground">
                <Badge variant="outline">{r.rule_type}</Badge>
                {r.is_active ? <Badge variant="default" className="bg-green-500/10 text-green-600">Active</Badge> : <Badge variant="outline">Inactive</Badge>}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function PackagesTab({ slug }: { slug: string }) {
  const [packages, setPackages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    industryApi.packages(slug).then((res) => setPackages(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, [slug]);

  const handleInstall = async (pkgId: string) => {
    try {
      await industryApi.installPackage(pkgId);
      toast.success("Package installed");
      const res = await industryApi.packages(slug);
      setPackages(res.data);
    } catch { toast.error("Install failed"); }
  };

  const handleUninstall = async (pkgId: string) => {
    try {
      await industryApi.uninstallPackage(pkgId);
      toast.success("Package uninstalled");
      const res = await industryApi.packages(slug);
      setPackages(res.data);
    } catch { toast.error("Uninstall failed"); }
  };

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Solution Packages</h3>
      <div className="grid gap-4 md:grid-cols-2">
        {packages.map((p) => (
          <Card key={p.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{p.name}</CardTitle>
                  <CardDescription className="line-clamp-1">{p.description}</CardDescription>
                </div>
                <Badge variant={p.is_installed ? "default" : "outline"}>{p.is_installed ? "Installed" : "Available"}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">v{p.version}</span>
                {p.is_installed ? (
                  <Button variant="outline" size="sm" onClick={() => handleUninstall(p.id)}>Uninstall</Button>
                ) : (
                  <Button size="sm" onClick={() => handleInstall(p.id)}><Download className="w-3 h-3 mr-1" />Install</Button>
                )}
              </div>
              {p.capabilities?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {p.capabilities.map((c: string, i: number) => <Badge key={i} variant="outline" className="text-xs">{c}</Badge>)}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ChatTab({ slug }: { slug: string }) {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResponse("");
    try {
      const res = await industryApi.query({ industry_slug: slug, query: query.trim() });
      setResponse(res.data.response);
    } catch { setResponse("Failed to get response"); } finally { setLoading(false); }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Ask the Industry AI</CardTitle>
          <CardDescription>Get expert AI assistance for {INDUSTRY_META[slug]?.label || slug}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Ask anything about this industry..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleQuery()}
              className="flex-1"
            />
            <Button onClick={handleQuery} disabled={loading || !query.trim()}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
          {response && (
            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm whitespace-pre-wrap">{response}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
