"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { infrastructureApi } from "@/lib/api-client";
import { toast } from "sonner";
import {
  Globe, Server, Cpu, Shield, Activity, Database, FileText, Key,
  Loader2, CheckCircle, XCircle, AlertTriangle, Plus, Trash2,
  LayoutDashboard, Cloud, BarChart3, Settings,
} from "lucide-react";

type Tab = "overview" | "regions" | "clusters" | "models" | "monitoring" | "security" | "backups" | "compliance" | "developers";

export default function InfrastructurePage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("overview");
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
    try {
      const res = await infrastructureApi.dashboard();
      setDashboard(res.data);
    } catch {}
  };

  const tabs: { key: Tab; label: string; icon: any; description: string }[] = [
    { key: "overview", label: "Overview", icon: LayoutDashboard, description: "Infrastructure at a glance" },
    { key: "regions", label: "Regions", icon: Globe, description: "Multi-region deployment" },
    { key: "clusters", label: "Clusters", icon: Server, description: "Kubernetes clusters" },
    { key: "models", label: "Models", icon: Cpu, description: "AI model registry & routing" },
    { key: "monitoring", label: "Monitoring", icon: Activity, description: "System health & metrics" },
    { key: "security", label: "Security", icon: Shield, description: "Security events & threats" },
    { key: "backups", label: "Backups", icon: Database, description: "Backup & disaster recovery" },
    { key: "compliance", label: "Compliance", icon: FileText, description: "Governance & policies" },
    { key: "developers", label: "Developers", icon: Key, description: "API keys & developer tools" },
  ];

  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Enterprise Command Center</h1>
        <p className="text-muted-foreground mt-1">Global infrastructure management — regions, clusters, models, security, monitoring, and compliance</p>
      </div>

      {dashboard && (
        <div className="grid gap-4 md:grid-cols-6">
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.regions}</p><p className="text-xs text-muted-foreground">Regions</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.clusters}</p><p className="text-xs text-muted-foreground">Clusters</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.services}</p><p className="text-xs text-muted-foreground">Services</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.models}</p><p className="text-xs text-muted-foreground">AI Models</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-red-500">{dashboard.stats.unresolved_events}</p><p className="text-xs text-muted-foreground">Security Events</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{dashboard.stats.backups}</p><p className="text-xs text-muted-foreground">Backups</p></CardContent></Card>
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

      {tab === "overview" && <OverviewTab />}
      {tab === "regions" && <RegionsTab />}
      {tab === "clusters" && <ClustersTab />}
      {tab === "models" && <ModelsTab />}
      {tab === "monitoring" && <MonitoringTab />}
      {tab === "security" && <SecurityTab />}
      {tab === "backups" && <BackupsTab />}
      {tab === "compliance" && <ComplianceTab orgId={orgId} />}
      {tab === "developers" && <DevelopersTab orgId={orgId} />}
    </div>
  );
}

function OverviewTab() {
  const [health, setHealth] = useState<any>(null);
  const [uptime, setUptime] = useState<any>(null);
  const [security, setSecurity] = useState<any>(null);
  const [backupSum, setBackupSum] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      infrastructureApi.systemHealth(),
      infrastructureApi.apiUptime(30),
      infrastructureApi.securitySummary(),
      infrastructureApi.backupSummary(),
    ]).then(([h, u, s, b]) => { setHealth(h.data); setUptime(u.data); setSecurity(s.data); setBackupSum(b.data); }).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Platform Health</h3>
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-green-500/20">
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-green-500">{health?.health_percentage?.toFixed(1) || "—"}%</p>
            <p className="text-xs text-muted-foreground">Cluster Health</p>
            <p className="text-xs text-muted-foreground">{health?.healthy_clusters}/{health?.total_clusters} healthy</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold">{uptime?.uptime?.toFixed(2) || "—"}%</p>
            <p className="text-xs text-muted-foreground">API Uptime (30d)</p>
          </CardContent>
        </Card>
        <Card className={security?.unresolved > 0 ? "border-red-500/20" : ""}>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold text-red-500">{security?.unresolved || 0}</p>
            <p className="text-xs text-muted-foreground">Unresolved Security Events</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <p className="text-2xl font-bold">{backupSum?.completed || 0}/{backupSum?.total || 0}</p>
            <p className="text-xs text-muted-foreground">Backups Completed</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function RegionsTab() {
  const [regions, setRegions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    infrastructureApi.regions().then((res) => setRegions(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Global Regions</h3>
      <div className="grid gap-4 md:grid-cols-2">
        {regions.map((r) => (
          <Card key={r.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-sm">{r.name}</CardTitle>
                  <CardDescription>{r.description}</CardDescription>
                </div>
                <Badge variant={r.status === "active" ? "default" : "outline"}>{r.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 text-xs text-muted-foreground">
                <Badge variant="outline">{r.provider}</Badge>
                <Badge variant="outline">{r.location}</Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ClustersTab() {
  const [clusters, setClusters] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      infrastructureApi.clusters(),
      infrastructureApi.services(),
    ]).then(([c, s]) => { setClusters(c.data); setServices(s.data); }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Kubernetes Clusters ({clusters.length})</h3>
        <div className="grid gap-4 md:grid-cols-2 mt-4">
          {clusters.map((c) => (
            <Card key={c.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-sm">{c.name}</CardTitle>
                  <Badge variant={c.health_status === "healthy" ? "default" : c.health_status === "degraded" ? "warning" : "error"}>{c.health_status}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline">{c.cluster_type}</Badge>
                  <Badge variant="outline">v{c.version}</Badge>
                  <Badge variant="outline">{c.node_count} nodes</Badge>
                  <Badge variant="outline">{c.status}</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold">Deployed Services ({services.length})</h3>
        <div className="grid gap-4 md:grid-cols-3 mt-4">
          {services.map((s) => (
            <Card key={s.id}>
              <CardHeader>
                <CardTitle className="text-sm">{s.service_name}</CardTitle>
                <CardDescription className="text-xs">{s.service_type}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">v{s.version}</span>
                  <div className="flex gap-1">
                    <Badge variant="outline">{s.replicas} pods</Badge>
                    <Badge variant={s.status === "running" ? "default" : "outline"}>{s.status}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

function ModelsTab() {
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [routeResult, setRouteResult] = useState<any>(null);
  const [routeTask, setRouteTask] = useState("");

  useEffect(() => {
    infrastructureApi.models().then((res) => setModels(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleRoute = async () => {
    if (!routeTask.trim()) return;
    try {
      const res = await infrastructureApi.routeModel({ task: routeTask, complexity: "medium" });
      setRouteResult(res.data);
    } catch { toast.error("Routing failed"); }
  };

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">AI Model Registry</h3>
        <div className="grid gap-4 md:grid-cols-2 mt-4">
          {models.map((m) => (
            <Card key={m.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-sm">{m.name}</CardTitle>
                    <CardDescription className="text-xs">{m.provider} — {m.model_id}</CardDescription>
                  </div>
                  <Badge variant={m.is_active ? "default" : "outline"}>{m.model_type}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div><span className="text-muted-foreground">Cost:</span> ${m.cost_per_token?.toFixed(4)}/token</div>
                  <div><span className="text-muted-foreground">P50:</span> {m.latency_p50?.toFixed(1)}s</div>
                  <div><span className="text-muted-foreground">P99:</span> {m.latency_p99?.toFixed(1)}s</div>
                  <div className="col-span-3"><span className="text-muted-foreground">Max tokens:</span> {m.max_tokens?.toLocaleString()}</div>
                </div>
                {m.capabilities?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {m.capabilities.map((c: string, i: number) => <Badge key={i} variant="outline" className="text-xs">{c}</Badge>)}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">AI Model Router 2.0</CardTitle><CardDescription>Route requests to the optimal model based on task, cost, and latency</CardDescription></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input placeholder="Describe the task (e.g., 'Write Python code for API')" value={routeTask} onChange={(e) => setRouteTask(e.target.value)} className="flex-1" />
            <Button onClick={handleRoute}><Cpu className="w-4 h-4 mr-2" />Route</Button>
          </div>
          {routeResult && (
            <div className="bg-muted p-3 rounded-lg">
              <p className="text-sm font-medium">{routeResult.name} ({routeResult.provider})</p>
              <p className="text-xs text-muted-foreground">Model: {routeResult.model_id}</p>
              <p className="text-xs text-muted-foreground">Cost: ${routeResult.cost?.toFixed(4)}/token | Latency: {routeResult.latency?.toFixed(1)}s</p>
              <p className="text-xs text-muted-foreground">{routeResult.reason}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function MonitoringTab() {
  const [health, setHealth] = useState<any>(null);
  const [uptime, setUptime] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      infrastructureApi.systemHealth(),
      infrastructureApi.apiUptime(30),
    ]).then(([h, u]) => { setHealth(h.data); setUptime(u.data); }).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">System Monitoring</h3>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader><CardTitle className="text-sm">Cluster Health</CardTitle></CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-500">{health?.health_percentage?.toFixed(1) || "—"}%</p>
            <p className="text-sm text-muted-foreground">{health?.healthy_clusters}/{health?.total_clusters} clusters healthy</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">API Uptime (30d)</CardTitle></CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{uptime?.uptime?.toFixed(2) || "—"}%</p>
            <p className="text-sm text-muted-foreground">Service Level Agreement</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">System Status</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">All systems operational</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SecurityTab() {
  const [events, setEvents] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      infrastructureApi.securityEvents({ limit: 20 }),
      infrastructureApi.securitySummary(),
    ]).then(([e, s]) => { setEvents(e.data); setSummary(s.data); }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      {summary && (
        <div className="grid gap-4 md:grid-cols-5">
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{summary.total_events}</p><p className="text-xs text-muted-foreground">Total</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-red-500">{summary.critical}</p><p className="text-xs text-muted-foreground">Critical</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-orange-500">{summary.high}</p><p className="text-xs text-muted-foreground">High</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-green-500">{summary.resolved}</p><p className="text-xs text-muted-foreground">Resolved</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-red-500">{summary.unresolved}</p><p className="text-xs text-muted-foreground">Unresolved</p></CardContent></Card>
        </div>
      )}
      <h3 className="text-lg font-semibold">Recent Security Events</h3>
      <div className="space-y-2">
        {events.map((e) => (
          <Card key={e.id} className={e.severity === "critical" || e.severity === "high" ? "border-red-500/20" : ""}>
            <CardContent className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                {e.severity === "critical" || e.severity === "high" ? <AlertTriangle className="w-4 h-4 text-red-500" /> : <Shield className="w-4 h-4 text-muted-foreground" />}
                <div>
                  <p className="text-sm font-medium">{e.event_type}</p>
                  <p className="text-xs text-muted-foreground">{e.description || e.source || "No details"}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={e.severity === "critical" ? "error" : e.severity === "high" ? "warning" : "outline"}>{e.severity}</Badge>
                {e.is_resolved ? <CheckCircle className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function BackupsTab() {
  const [backups, setBackups] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      infrastructureApi.backups(),
      infrastructureApi.backupSummary(),
    ]).then(([b, s]) => { setBackups(b.data); setSummary(s.data); }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      {summary && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{summary.total}</p><p className="text-xs text-muted-foreground">Total</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-green-500">{summary.completed}</p><p className="text-xs text-muted-foreground">Completed</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold text-red-500">{summary.failed}</p><p className="text-xs text-muted-foreground">Failed</p></CardContent></Card>
          <Card><CardContent className="pt-4 text-center"><p className="text-2xl font-bold">{(summary.total_size_bytes / 1073741824).toFixed(2)}</p><p className="text-xs text-muted-foreground">Total (GB)</p></CardContent></Card>
        </div>
      )}
      <h3 className="text-lg font-semibold">Backup Records</h3>
      <div className="space-y-2">
        {backups.map((b) => (
          <Card key={b.id}>
            <CardContent className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium">{b.name}</p>
                <p className="text-xs text-muted-foreground">{b.backup_type} — {b.target}</p>
              </div>
              <Badge variant={b.status === "completed" ? "default" : b.status === "failed" ? "error" : "warning"}>{b.status}</Badge>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ComplianceTab({ orgId }: { orgId: string | null }) {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    infrastructureApi.complianceReports({ organization_id: orgId }).then((res) => setReports(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, [orgId]);

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Compliance Reports & Governance</h3>
      <div className="grid gap-4 md:grid-cols-2">
        {reports.map((r) => (
          <Card key={r.id}>
            <CardHeader>
              <CardTitle className="text-sm">{r.title}</CardTitle>
              <CardDescription>{r.report_type}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <Badge variant={r.status === "generated" ? "default" : "outline"}>{r.status}</Badge>
                <span className="text-xs text-muted-foreground">{r.generated_at ? new Date(r.generated_at).toLocaleDateString() : "Not generated"}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function DevelopersTab({ orgId }: { orgId: string | null }) {
  const [keys, setKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", scopes: "read" });
  const [newKey, setNewKey] = useState("");

  useEffect(() => {
    if (orgId) infrastructureApi.apiKeys(orgId).then((res) => setKeys(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, [orgId]);

  const handleCreate = async () => {
    if (!orgId) return;
    try {
      await infrastructureApi.createApiKey(orgId, { name: form.name, scopes: form.scopes.split(",").map((s) => s.trim()) });
      toast.success("API key created");
      setShowCreate(false);
      setForm({ name: "", scopes: "read" });
      const result = await infrastructureApi.apiKeys(orgId);
      setKeys(result.data);
    } catch { toast.error("Failed to create key"); }
  };

  const handleDelete = async (keyId: string) => {
    if (!orgId) return;
    try {
      await infrastructureApi.deleteApiKey(keyId);
      toast.success("API key deleted");
      const res = await infrastructureApi.apiKeys(orgId);
      setKeys(res.data);
    } catch { toast.error("Failed to delete"); }
  };

  if (loading) return <Loader2 className="w-6 h-6 animate-spin" />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Developer API Keys</h3>
        <Button onClick={() => setShowCreate(!showCreate)}><Plus className="w-4 h-4 mr-2" />Create Key</Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader><CardTitle className="text-sm">New API Key</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Input placeholder="Key name (e.g., 'Production API')" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input placeholder="Scopes (comma-separated: read, write, admin)" value={form.scopes} onChange={(e) => setForm({ ...form, scopes: e.target.value })} />
            <Button onClick={handleCreate}><Key className="w-4 h-4 mr-2" />Generate</Button>
          </CardContent>
        </Card>
      )}

      {newKey && (
        <Card className="border-primary/30">
          <CardContent className="pt-4">
            <p className="text-sm font-medium">Your API Key (copy now — won't be shown again):</p>
            <code className="block bg-muted p-2 rounded mt-1 text-sm break-all">{newKey}</code>
          </CardContent>
        </Card>
      )}

      <div className="space-y-2">
        {keys.map((k) => (
          <Card key={k.id}>
            <CardContent className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium">{k.name}</p>
                <div className="flex gap-2 text-xs text-muted-foreground">
                  <span>{k.key_prefix}...</span>
                  {k.scopes?.length > 0 && <span>Scopes: {k.scopes.join(", ")}</span>}
                  <span>Rate: {k.rate_limit}/hr</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={k.is_active ? "default" : "outline"}>{k.is_active ? "Active" : "Inactive"}</Badge>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(k.id)}><Trash2 className="w-3 h-3 text-red-500" /></Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
