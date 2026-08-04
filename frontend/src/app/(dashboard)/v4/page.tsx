"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  v4CloudApi, v4EnterpriseApi, v4EcosystemApi,
} from "@/lib/api-client";
import { toast } from "sonner";
import {
  Cloud, Store, Shield, Eye, Puzzle, Code, BarChart3,
  Layers, BookOpen, Cpu, Rocket, CheckCircle, Globe, Server,
  Database, Lock, Activity, Zap, TrendingUp, Download, Upload,
  Settings, Sliders, Users, Building, HardDrive, Workflow,
} from "lucide-react";

type Tab = "cloud" | "store" | "workflows" | "knowledge" | "governance" | "observability" | "integrations" | "builder" | "models" | "developer" | "analytics";

export default function V4Page() {
  const [tab, setTab] = useState<Tab>("cloud");

  const phases: { key: Tab; label: string; icon: any; description: string }[] = [
    { key: "cloud", label: "Cloud Platform", icon: Cloud, description: "Multi-tenant SaaS, HA, DR, auto-scaling" },
    { key: "store", label: "App Store", icon: Store, description: "AI applications marketplace" },
    { key: "workflows", label: "Workflows", icon: Workflow, description: "Automation workflow marketplace" },
    { key: "knowledge", label: "Knowledge", icon: BookOpen, description: "Enterprise knowledge hub" },
    { key: "governance", label: "Governance", icon: Shield, description: "AI governance center" },
    { key: "observability", label: "Observability", icon: Eye, description: "AI monitoring & dashboards" },
    { key: "integrations", label: "Integrations", icon: Puzzle, description: "Enterprise integrations" },
    { key: "builder", label: "Builder", icon: Code, description: "Low-code AI app builder" },
    { key: "models", label: "Models", icon: Cpu, description: "AI model management" },
    { key: "developer", label: "Developer", icon: Rocket, description: "SDKs, plugins, API platform" },
    { key: "analytics", label: "Analytics", icon: BarChart3, description: "Enterprise analytics" },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 via-orange-500 to-red-500 flex items-center justify-center">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">V4 Enterprise Platform</h1>
          <p className="text-muted-foreground mt-1">Cloud platform, AI app store, enterprise knowledge, governance, observability, low-code builder, model management, and developer platform</p>
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {phases.map((p) => (
          <button
            key={p.key}
            onClick={() => setTab(p.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
              tab === p.key ? "bg-amber-500/10 text-amber-600 font-medium border border-amber-500/30" : "text-muted-foreground hover:bg-muted border border-transparent"
            }`}
          >
            <p.icon className="w-4 h-4" />
            <span className="hidden sm:inline">{p.label}</span>
          </button>
        ))}
      </div>

      {tab === "cloud" && <CloudTab />}
      {tab === "store" && <AppStoreTab />}
      {tab === "workflows" && <WorkflowsTab />}
      {tab === "knowledge" && <KnowledgeTab />}
      {tab === "governance" && <GovernanceTab />}
      {tab === "observability" && <ObservabilityTab />}
      {tab === "integrations" && <IntegrationsTab />}
      {tab === "builder" && <BuilderTab />}
      {tab === "models" && <ModelsTab />}
      {tab === "developer" && <DeveloperTab />}
      {tab === "analytics" && <AnalyticsTab />}
    </div>
  );
}

function CloudTab() {
  const [environments, setEnvironments] = useState<any[]>([]);
  const [deployments, setDeployments] = useState<any[]>([]);
  const [backups, setBackups] = useState<any[]>([]);
  const [drPlans, setDrPlans] = useState<any[]>([]);

  useEffect(() => {
    v4CloudApi.listEnvironments("org-1").then((r) => setEnvironments(r.data)).catch(() => {});
    v4CloudApi.listDeployments("env-1").then((r) => setDeployments(r.data)).catch(() => {});
    v4CloudApi.listBackups("env-1").then((r) => setBackups(r.data)).catch(() => {});
    v4CloudApi.listDrPlans("env-1").then((r) => setDrPlans(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-amber-500/20">
          <CardHeader className="pb-2"><CardTitle className="text-sm"><Server className="w-4 h-4 inline mr-1" />Environments</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{environments.length}</p></CardContent>
        </Card>
        <Card className="border-amber-500/20">
          <CardHeader className="pb-2"><CardTitle className="text-sm"><Globe className="w-4 h-4 inline mr-1" />Deployments</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{deployments.length}</p></CardContent>
        </Card>
        <Card className="border-amber-500/20">
          <CardHeader className="pb-2"><CardTitle className="text-sm"><Database className="w-4 h-4 inline mr-1" />Backups</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{backups.length}</p></CardContent>
        </Card>
        <Card className="border-amber-500/20">
          <CardHeader className="pb-2"><CardTitle className="text-sm"><Shield className="w-4 h-4 inline mr-1" />DR Plans</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{drPlans.length}</p></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Environments</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {environments.map((e) => (
              <div key={e.id} className="border rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-sm">{e.name}</p>
                  <Badge variant="outline" className="text-xs">{e.environment_type}</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1">Region: {e.region} | Status: {e.status}</p>
                <div className="flex gap-2 mt-2">
                  <Badge variant={e.is_ha ? "default" : "outline"} className="text-xs">HA</Badge>
                  {e.scaling_policy && <Badge variant="outline" className="text-xs">Auto-scale</Badge>}
                </div>
              </div>
            ))}
            {environments.length === 0 && <p className="text-sm text-muted-foreground col-span-2">No environments yet. Create one to get started.</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AppStoreTab() {
  const [apps, setApps] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [installations, setInstallations] = useState<any[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    v4CloudApi.listApps().then((r) => setApps(r.data)).catch(() => {});
    v4CloudApi.listAppCategories().then((r) => setCategories(r.data)).catch(() => {});
    v4CloudApi.listInstallations("org-1").then((r) => setInstallations(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input placeholder="Search AI apps..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-md" />
        <Button onClick={() => v4CloudApi.searchApps(search).then((r) => setApps(r.data.apps)).catch(() => {})}>Search</Button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {categories.map((c) => <Badge key={c.id} variant="outline">{c.name}</Badge>)}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {apps.map((a) => (
          <Card key={a.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle className="text-sm">{a.name}</CardTitle>
                <Badge variant="outline" className="text-xs">{a.pricing_model}</Badge>
              </div>
              <CardDescription className="line-clamp-2">{a.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{a.total_installs || 0} installs</span>
                <span>{(a.avg_rating || 0).toFixed(1)} ★</span>
                {a.is_verified && <Badge variant="default" className="text-xs">Verified</Badge>}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function WorkflowsTab() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [installations, setInstallations] = useState<any[]>([]);

  useEffect(() => {
    v4CloudApi.listWorkflowTemplates().then((r) => setTemplates(r.data)).catch(() => {});
    v4CloudApi.listWorkflowInstallations("org-1").then((r) => setInstallations(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {templates.map((t) => (
          <Card key={t.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Workflow className="w-4 h-4 text-amber-500" />
                <CardTitle className="text-sm">{t.name}</CardTitle>
              </div>
              <CardDescription className="line-clamp-2">{t.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1 mb-2">
                {t.category && <Badge variant="outline" className="text-xs">{t.category}</Badge>}
                {t.industry && <Badge variant="outline" className="text-xs">{t.industry}</Badge>}
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{t.total_installs || 0} installs</span>
                <span>{(t.avg_rating || 0).toFixed(1)} ★</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function KnowledgeTab() {
  const [connectors, setConnectors] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");

  useEffect(() => {
    v4EnterpriseApi.listConnectors("org-1").then((r) => setConnectors(r.data)).catch(() => {});
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    const res = await v4EnterpriseApi.searchKnowledge({ organization_id: "org-1", query_text: query.trim() });
    setResponse(res.data.response);
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {connectors.map((c) => (
          <Card key={c.id}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-blue-500" />
                <CardTitle className="text-sm">{c.name}</CardTitle>
              </div>
              <CardDescription>{c.connector_type}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <Badge variant={c.status === "synced" ? "default" : "outline"}>{c.status}</Badge>
                <span className="text-xs text-muted-foreground">{c.last_sync_at ? new Date(c.last_sync_at).toLocaleDateString() : "Never synced"}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Enterprise Knowledge Search</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input placeholder="Search across all connected knowledge sources..." value={query} onChange={(e) => setQuery(e.target.value)} />
            <Button onClick={handleSearch}><SearchIcon className="w-4 h-4" /></Button>
          </div>
          {response && <div className="bg-muted p-3 rounded-lg text-sm whitespace-pre-wrap">{response}</div>}
        </CardContent>
      </Card>
    </div>
  );
}

function GovernanceTab() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [checkResult, setCheckResult] = useState<any>(null);

  useEffect(() => {
    v4EnterpriseApi.listPolicies("org-1").then((r) => setPolicies(r.data)).catch(() => {});
  }, []);

  const handleCheck = async () => {
    const res = await v4EnterpriseApi.checkPolicy({ organization_id: "org-1", policy_type: "agent_approval", resource_type: "agent", action: "deploy" });
    setCheckResult(res.data);
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-sm">AI Policies</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {policies.map((p) => (
                <div key={p.id} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <p className="text-sm font-medium">{p.name}</p>
                    <p className="text-xs text-muted-foreground">{p.policy_type} — {p.severity}</p>
                  </div>
                  <Badge variant={p.is_active ? "default" : "outline"}>{p.is_active ? "Active" : "Inactive"}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-sm">Policy Check</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Button onClick={handleCheck} variant="outline">Test Policy Enforcement</Button>
            {checkResult && (
              <div className={`p-3 rounded-lg text-sm ${checkResult.allowed ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                <p className="font-medium">{checkResult.allowed ? "Allowed ✓" : "Blocked ✗"}</p>
                <p>{checkResult.reason}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ObservabilityTab() {
  const [events, setEvents] = useState<any[]>([]);
  const [dashboards, setDashboards] = useState<any[]>([]);

  useEffect(() => {
    v4EnterpriseApi.getMonitoringEvents("org-1").then((r) => setEvents(r.data)).catch(() => {});
    v4EnterpriseApi.listObservabilityDashboards("org-1").then((r) => setDashboards(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-green-500/20">
          <CardHeader className="pb-2"><CardTitle className="text-sm"><Activity className="w-4 h-4 inline mr-1 text-green-500" />Events</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{events.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Success</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-green-500">{events.filter((e) => e.status === "success").length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Failed</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-red-500">{events.filter((e) => e.status === "error").length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Dashboards</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold">{dashboards.length}</p></CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-sm">Recent Events</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {events.slice(0, 10).map((e) => (
                <div key={e.id} className="flex items-center justify-between text-xs border-b pb-1">
                  <span>{e.event_type}</span>
                  <span className="text-muted-foreground">{e.model_provider} | {(e.latency_ms || 0).toFixed(0)}ms</span>
                  <Badge variant={e.status === "success" ? "default" : "outline"} className="text-xs">{e.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Dashboards</CardTitle></CardHeader>
          <CardContent>
            <div className="grid gap-2">
              {dashboards.map((d) => (
                <div key={d.id} className="border rounded-lg p-3">
                  <p className="text-sm font-medium">{d.name}</p>
                  <Badge variant="outline" className="text-xs">{d.dashboard_type}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function IntegrationsTab() {
  const [integrations, setIntegrations] = useState<any[]>([]);

  useEffect(() => {
    v4EcosystemApi.listIntegrations("org-1").then((r) => setIntegrations(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {integrations.map((i) => (
          <Card key={i.id}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Puzzle className="w-4 h-4 text-purple-500" />
                <CardTitle className="text-sm">{i.name}</CardTitle>
              </div>
              <CardDescription>{i.integration_type}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <Badge variant={i.status === "synced" ? "default" : "outline"}>{i.status}</Badge>
                <Button size="sm" variant="outline" onClick={async () => { await v4EcosystemApi.syncIntegration(i.id); toast.success("Sync started"); }}><Upload className="w-3 h-3 mr-1" />Sync</Button>
              </div>
              {i.last_sync_at && <p className="text-xs text-muted-foreground mt-2">Last sync: {new Date(i.last_sync_at).toLocaleString()}</p>}
            </CardContent>
          </Card>
        ))}
      </div>
      {integrations.length === 0 && <p className="text-center text-muted-foreground py-8">No integrations configured. Connect your enterprise tools.</p>}
    </div>
  );
}

function BuilderTab() {
  const [apps, setApps] = useState<any[]>([]);
  const [prompt, setPrompt] = useState("");

  useEffect(() => {
    v4EcosystemApi.listAppDefinitions("org-1").then((r) => setApps(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <Card className="border-amber-500/20">
        <CardHeader><CardTitle className="text-sm">Create App from Natural Language</CardTitle></CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input placeholder="Describe the app you want to build... e.g., 'Create a customer support dashboard with ticket tracking and AI responses'" value={prompt} onChange={(e) => setPrompt(e.target.value)} className="flex-1" />
            <Button onClick={async () => { if (!prompt.trim()) return; const res = await v4EcosystemApi.createAppDefinition({ organization_id: "org-1", user_id: "user-1", name: prompt.split(" ").slice(0, 3).join(" "), natural_language_prompt: prompt.trim() }); setApps([res.data, ...apps]); setPrompt(""); toast.success("App created!"); }}><Code className="w-4 h-4 mr-1" />Generate</Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {apps.map((a) => (
          <Card key={a.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">{a.name}</CardTitle>
                <Badge>{a.status}</Badge>
              </div>
              <CardDescription className="line-clamp-2">{a.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1">
                {(a.components || []).map((c: any, i: number) => <Badge key={i} variant="outline" className="text-xs">{c.type || c.component_type}</Badge>)}
              </div>
              <div className="flex gap-2 mt-2">
                <Button size="sm" variant="outline" onClick={async () => { await v4EcosystemApi.generateFromPrompt(a.id); toast.success("Generating..."); }}><Zap className="w-3 h-3 mr-1" />Build</Button>
                <Button size="sm" variant="outline" onClick={async () => { await v4EcosystemApi.publishApp(a.id); toast.success("Published!"); }}><Rocket className="w-3 h-3 mr-1" />Publish</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ModelsTab() {
  const [models, setModels] = useState<any[]>([]);
  const [sdks, setSdks] = useState<any[]>([]);

  useEffect(() => {
    v4EcosystemApi.listRegisteredModels("org-1").then((r) => setModels(r.data)).catch(() => {});
    v4EcosystemApi.listSdks().then((r) => setSdks(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle className="text-sm">Model Registry</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {models.map((m) => (
              <div key={m.id} className="border rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{m.model_name}</p>
                    <p className="text-xs text-muted-foreground">{m.model_provider} v{m.model_version}</p>
                  </div>
                  {m.is_default && <Badge>Default</Badge>}
                </div>
                <div className="flex gap-2 mt-2 text-xs text-muted-foreground">
                  <span>Input: ${m.cost_per_input_token || 0}/1K</span>
                  <span>Output: ${m.cost_per_output_token || 0}/1K</span>
                  <span>P50: {(m.latency_p50_ms || 0).toFixed(0)}ms</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function DeveloperTab() {
  const [plugins, setPlugins] = useState<any[]>([]);
  const [sdks, setSdks] = useState<any[]>([]);

  useEffect(() => {
    v4EcosystemApi.listPlugins().then((r) => setPlugins(r.data)).catch(() => {});
    v4EcosystemApi.listSdks().then((r) => setSdks(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-sm"><Download className="w-4 h-4 inline mr-1" />SDK Releases</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {sdks.map((s) => (
                <div key={s.id} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <p className="text-sm font-medium">{s.sdk_name}</p>
                    <p className="text-xs text-muted-foreground">{s.sdk_language} v{s.sdk_version}</p>
                  </div>
                  {s.is_latest && <Badge variant="default">Latest</Badge>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm"><Puzzle className="w-4 h-4 inline mr-1" />Plugin Ecosystem</CardTitle></CardHeader>
          <CardContent>
            <div className="grid gap-2">
              {plugins.map((p) => (
                <div key={p.id} className="border rounded-lg p-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{p.name}</p>
                    <Badge variant="outline" className="text-xs">{p.plugin_type}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{p.download_count || 0} downloads</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function AnalyticsTab() {
  const [records, setRecords] = useState<any[]>([]);
  const [category, setCategory] = useState("");

  useEffect(() => {
    v4EnterpriseApi.getAnalytics("org-1").then((r) => setRecords(r.data)).catch(() => {});
  }, []);

  const categories = [...new Set(records.map((r) => r.metric_category))];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        {categories.map((cat) => (
          <Card key={cat} className="border-amber-500/20">
            <CardHeader className="pb-2"><CardTitle className="text-sm capitalize">{cat}</CardTitle></CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{records.filter((r) => r.metric_category === cat).length}</p>
              <p className="text-xs text-muted-foreground">metrics</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Analytics Records</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {records.slice(0, 20).map((r) => (
              <div key={r.id} className="flex items-center justify-between border-b pb-1 text-sm">
                <div>
                  <span className="font-medium">{r.metric_name}</span>
                  <Badge variant="outline" className="ml-2 text-xs">{r.metric_category}</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono">{r.metric_value} {r.unit}</span>
                  <span className="text-xs text-muted-foreground">{r.period}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function SearchIcon(props: any) { return <div {...props} />; }
