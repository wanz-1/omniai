"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { v5KnowledgeApi, v5CopilotApi, v5SimulationApi, v5ComplianceApi, v5ConnectorApi, v5CollaborationApi } from "@/lib/api-client";
import { toast } from "sonner";
import {
  Brain, Search, Network, Shield,
  Link, FileText, GitBranch, Zap, BookOpen,
  User, Workflow, BarChart3, CheckCircle,
  Heart, DollarSign, Sun, GraduationCap, Sprout,
  Building, ClipboardList, MessageSquare,
  TrendingUp, Activity, Target, AlertTriangle,
  Box, GitFork,
  Scale, FileCheck, ClipboardCheck, Eye,
  Gavel, KeyRound, RefreshCw, Webhook, Puzzle,
  TerminalSquare, Store, ShieldCheck, Cable,
  Cloud, Code2, MessageCircle, Globe, Database,
  Video, Monitor, Pen, Radio, Headphones,
  PictureInPicture, Presentation, Play,
} from "lucide-react";

type Tab = "connectors" | "documents" | "search" | "reasoning" | "graph" | "permissions"
  | "copilot" | "ngo" | "finance" | "hospitality" | "education" | "agriculture" | "business" | "approvals" | "copilot-analytics"
  | "scenarios" | "sim-run" | "financial-sim" | "project-sim" | "risk-sim" | "optimize" | "digital-twin" | "sim-analytics"
  | "compliance-policies" | "compliance-docs" | "compliance-audits" | "compliance-findings" | "compliance-risk" | "compliance-dashboard"
  | "cp-install" | "cp-integrations" | "cp-auth" | "cp-sync" | "cp-webhooks" | "cp-custom" | "cp-marketplace" | "cp-logs" | "cp-dashboard"
  | "collab-sessions" | "collab-messages" | "collab-whiteboard" | "collab-screen" | "collab-recordings" | "collab-insights" | "collab-agents" | "collab-documents" | "collab-dashboard";

export default function V5Page() {
  const [tab, setTab] = useState<Tab>("connectors");

  const knowledgeTabs: { key: Tab; label: string; icon: any }[] = [
    { key: "connectors", label: "Connectors", icon: Link },
    { key: "documents", label: "Documents", icon: FileText },
    { key: "search", label: "Search", icon: Search },
    { key: "reasoning", label: "Reasoning", icon: Brain },
    { key: "graph", label: "Graph", icon: GitBranch },
    { key: "permissions", label: "Perms", icon: Shield },
  ];

  const copilotTabs: { key: Tab; label: string; icon: any }[] = [
    { key: "copilot", label: "Copilot Chat", icon: MessageSquare },
    { key: "ngo", label: "NGO", icon: Heart },
    { key: "finance", label: "Finance", icon: DollarSign },
    { key: "hospitality", label: "Tourism", icon: Sun },
    { key: "education", label: "Education", icon: GraduationCap },
    { key: "agriculture", label: "Agri", icon: Sprout },
    { key: "business", label: "Business", icon: Building },
    { key: "approvals", label: "Approvals", icon: CheckCircle },
    { key: "copilot-analytics", label: "Analytics", icon: BarChart3 },
  ];

  const simTabs: { key: Tab; label: string; icon: any }[] = [
    { key: "scenarios", label: "Scenarios", icon: ClipboardList },
    { key: "sim-run", label: "Run", icon: Activity },
    { key: "financial-sim", label: "Financial", icon: TrendingUp },
    { key: "project-sim", label: "Project", icon: GitFork },
    { key: "risk-sim", label: "Risk", icon: AlertTriangle },
    { key: "optimize", label: "Optimize", icon: Target },
    { key: "digital-twin", label: "Twin", icon: Box },
    { key: "sim-analytics", label: "Sim Analytics", icon: BarChart3 },
  ];

  const complianceTabs: { key: Tab; label: string; icon: any }[] = [
    { key: "compliance-policies", label: "Policies", icon: Scale },
    { key: "compliance-docs", label: "Doc Review", icon: FileCheck },
    { key: "compliance-audits", label: "Audits", icon: ClipboardCheck },
    { key: "compliance-findings", label: "Findings", icon: AlertTriangle },
    { key: "compliance-risk", label: "Risk", icon: Eye },
    { key: "compliance-dashboard", label: "Dashboard", icon: Gavel },
  ];

  const connectorTabs: { key: Tab; label: string; icon: any }[] = [
    { key: "cp-install", label: "Install", icon: Cloud },
    { key: "cp-integrations", label: "Integrations", icon: Cable },
    { key: "cp-auth", label: "Auth", icon: KeyRound },
    { key: "cp-sync", label: "Sync", icon: RefreshCw },
    { key: "cp-webhooks", label: "Webhooks", icon: Webhook },
    { key: "cp-custom", label: "Custom API", icon: TerminalSquare },
    { key: "cp-marketplace", label: "Marketplace", icon: Store },
    { key: "cp-logs", label: "Logs", icon: ClipboardList },
    { key: "cp-dashboard", label: "Dashboard", icon: Puzzle },
  ];

  const isCopilotTab = tab === "copilot" || tab === "ngo" || tab === "finance" || tab === "hospitality" || tab === "education" || tab === "agriculture" || tab === "business" || tab === "approvals" || tab === "copilot-analytics";
  const isSimTab = tab === "scenarios" || tab === "sim-run" || tab === "financial-sim" || tab === "project-sim" || tab === "risk-sim" || tab === "optimize" || tab === "digital-twin" || tab === "sim-analytics";
  const isComplianceTab = tab.startsWith("compliance-");
  const isConnectorTab = tab.startsWith("cp-");

  const collabTabs: { key: Tab; label: string; icon: any }[] = [
    { key: "collab-sessions", label: "Sessions", icon: Video },
    { key: "collab-messages", label: "Messages", icon: MessageCircle },
    { key: "collab-whiteboard", label: "Whiteboard", icon: Pen },
    { key: "collab-screen", label: "Screen", icon: Monitor },
    { key: "collab-recordings", label: "Recordings", icon: Radio },
    { key: "collab-insights", label: "AI Insights", icon: Brain },
    { key: "collab-agents", label: "AI Agents", icon: Headphones },
    { key: "collab-documents", label: "Docs", icon: FileText },
    { key: "collab-dashboard", label: "Dashboard", icon: Presentation },
  ];

  const isCollabTab = tab.startsWith("collab-");

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center">
          <Brain className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">V5 Enterprise Intelligence</h1>
          <p className="text-muted-foreground mt-1">Knowledge intelligence + Industry copilots — connect, reason, and automate across your enterprise</p>
        </div>
      </div>

      <div className="space-y-1">
        <p className="text-xs text-muted-foreground font-medium px-1">KNOWLEDGE INTELLIGENCE</p>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {knowledgeTabs.map((p) => (
            <button key={p.key} onClick={() => setTab(p.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
                tab === p.key ? "bg-indigo-500/10 text-indigo-600 font-medium border border-indigo-500/30" : "text-muted-foreground hover:bg-muted border border-transparent"
              }`}
            ><p.icon className="w-4 h-4" /><span className="hidden sm:inline">{p.label}</span></button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground font-medium px-1 pt-1">INDUSTRY COPILOTS</p>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {copilotTabs.map((p) => (
            <button key={p.key} onClick={() => setTab(p.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
                tab === p.key ? (isCopilotTab ? "bg-emerald-500/10 text-emerald-600 font-medium border border-emerald-500/30" : "") : "text-muted-foreground hover:bg-muted border border-transparent"
              }`}
            ><p.icon className="w-4 h-4" /><span className="hidden sm:inline">{p.label}</span></button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground font-medium px-1 pt-1">SIMULATION INTELLIGENCE</p>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {simTabs.map((p) => (
            <button key={p.key} onClick={() => setTab(p.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
                tab === p.key ? (isSimTab ? "bg-blue-500/10 text-blue-600 font-medium border border-blue-500/30" : "") : "text-muted-foreground hover:bg-muted border border-transparent"
              }`}
            ><p.icon className="w-4 h-4" /><span className="hidden sm:inline">{p.label}</span></button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground font-medium px-1 pt-1">COMPLIANCE INTELLIGENCE</p>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {complianceTabs.map((p) => (
            <button key={p.key} onClick={() => setTab(p.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
                tab === p.key ? (isComplianceTab ? "bg-rose-500/10 text-rose-600 font-medium border border-rose-500/30" : "") : "text-muted-foreground hover:bg-muted border border-transparent"
              }`}
            ><p.icon className="w-4 h-4" /><span className="hidden sm:inline">{p.label}</span></button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground font-medium px-1 pt-1">CONNECTOR PLATFORM</p>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {connectorTabs.map((p) => (
            <button key={p.key} onClick={() => setTab(p.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
                tab === p.key ? (isConnectorTab ? "bg-cyan-500/10 text-cyan-600 font-medium border border-cyan-500/30" : "") : "text-muted-foreground hover:bg-muted border border-transparent"
              }`}
            ><p.icon className="w-4 h-4" /><span className="hidden sm:inline">{p.label}</span></button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground font-medium px-1 pt-1">MULTIMODAL COLLABORATION</p>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {collabTabs.map((p) => (
            <button key={p.key} onClick={() => setTab(p.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm whitespace-nowrap transition-all ${
                tab === p.key ? (isCollabTab ? "bg-violet-500/10 text-violet-600 font-medium border border-violet-500/30" : "") : "text-muted-foreground hover:bg-muted border border-transparent"
              }`}
            ><p.icon className="w-4 h-4" /><span className="hidden sm:inline">{p.label}</span></button>
          ))}
        </div>
      </div>

      {tab === "connectors" && <ConnectorsTab />}
      {tab === "documents" && <DocumentsTab />}
      {tab === "search" && <SearchTab />}
      {tab === "reasoning" && <ReasoningTab />}
      {tab === "graph" && <GraphTab />}
      {tab === "permissions" && <PermissionsTab />}
      {tab === "copilot" && <CopilotChatTab />}
      {tab === "ngo" && <NgoTab />}
      {tab === "finance" && <FinanceTab />}
      {tab === "hospitality" && <HospitalityTab />}
      {tab === "education" && <EducationTab />}
      {tab === "agriculture" && <AgricultureTab />}
      {tab === "business" && <BusinessTab />}
      {tab === "approvals" && <ApprovalsTab />}
      {tab === "copilot-analytics" && <CopilotAnalyticsTab />}
      {tab === "scenarios" && <ScenariosTab />}
      {tab === "sim-run" && <RunSimulationTab />}
      {tab === "financial-sim" && <FinancialSimTab />}
      {tab === "project-sim" && <ProjectSimTab />}
      {tab === "risk-sim" && <RiskSimTab />}
      {tab === "optimize" && <OptimizeTab />}
      {tab === "digital-twin" && <DigitalTwinTab />}
      {tab === "sim-analytics" && <SimAnalyticsTab />}
      {tab === "compliance-policies" && <CompliancePoliciesTab />}
      {tab === "compliance-docs" && <ComplianceDocReviewTab />}
      {tab === "compliance-audits" && <ComplianceAuditsTab />}
      {tab === "compliance-findings" && <ComplianceFindingsTab />}
      {tab === "compliance-risk" && <ComplianceRiskTab />}
      {tab === "compliance-dashboard" && <ComplianceDashboardTab />}
      {tab === "cp-install" && <ConnectorInstallTab />}
      {tab === "cp-integrations" && <ConnectorIntegrationsTab />}
      {tab === "cp-auth" && <ConnectorAuthTab />}
      {tab === "cp-sync" && <ConnectorSyncTab />}
      {tab === "cp-webhooks" && <ConnectorWebhooksTab />}
      {tab === "cp-custom" && <ConnectorCustomTab />}
      {tab === "cp-marketplace" && <ConnectorMarketplaceTab />}
      {tab === "cp-logs" && <ConnectorLogsTab />}
      {tab === "cp-dashboard" && <ConnectorPlatformDashboardTab />}
      {tab === "collab-sessions" && <CollabSessionsTab />}
      {tab === "collab-messages" && <CollabMessagesTab />}
      {tab === "collab-whiteboard" && <CollabWhiteboardTab />}
      {tab === "collab-screen" && <CollabScreenTab />}
      {tab === "collab-recordings" && <CollabRecordingsTab />}
      {tab === "collab-insights" && <CollabInsightsTab />}
      {tab === "collab-agents" && <CollabAgentsTab />}
      {tab === "collab-documents" && <CollabDocumentsTab />}
      {tab === "collab-dashboard" && <CollabDashboardTab />}
    </div>
  );
}

function ConnectorsTab() {
  const [connectors, setConnectors] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [connectorType, setConnectorType] = useState("google_drive");
  const [showForm, setShowForm] = useState(false);
  const fetchConnectors = () => { v5KnowledgeApi.listConnectors().then((r) => setConnectors(r.data)).catch(() => {}); };
  useEffect(() => { fetchConnectors(); }, []);
  const handleConnect = async () => {
    if (!name.trim()) return;
    await v5KnowledgeApi.connectSource({ connector_type: connectorType, name: name.trim(), credentials: {} });
    toast.success("Connector created"); setName(""); setShowForm(false); fetchConnectors();
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="text-sm text-muted-foreground">{connectors.length} connected source(s)</p>
        <Button onClick={() => setShowForm(!showForm)}><Link className="w-4 h-4 mr-1" />{showForm ? "Cancel" : "Connect Source"}</Button>
      </div>
      {showForm && (
        <Card className="border-indigo-500/20">
          <CardHeader><CardTitle className="text-sm">Connect Knowledge Source</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <select value={connectorType} onChange={(e) => setConnectorType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background">
                <option value="google_drive">Google Drive</option>
                <option value="sharepoint">SharePoint</option>
                <option value="onedrive">OneDrive</option>
                <option value="notion">Notion</option>
                <option value="github">GitHub</option>
                <option value="slack">Slack</option>
                <option value="dropbox">Dropbox</option>
                <option value="database">Database</option>
                <option value="internal">Internal</option>
              </select>
              <Input placeholder="Connection name" value={name} onChange={(e) => setName(e.target.value)} className="flex-1" />
            </div>
            <Button onClick={handleConnect} className="w-full"><Zap className="w-4 h-4 mr-1" />Connect</Button>
          </CardContent>
        </Card>
      )}
      <div className="grid gap-4 md:grid-cols-3">
        {connectors.map((c) => (
          <Card key={c.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2"><Database className="w-4 h-4 text-indigo-500" /><CardTitle className="text-sm">{c.name}</CardTitle></div>
                <Badge variant={c.auth_status === "connected" ? "default" : "outline"}>{c.auth_status}</Badge>
              </div>
              <CardDescription>{c.connector_type}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{c.total_documents || 0} documents</span>
                <span>{c.last_sync_at ? new Date(c.last_sync_at).toLocaleDateString() : "Never"}</span>
              </div>
              <div className="flex gap-2 mt-3">
                <Button size="sm" variant="outline" className="flex-1" onClick={async () => { await v5KnowledgeApi.syncConnector(c.id); toast.success("Sync started"); fetchConnectors(); }}><Zap className="w-3 h-3 mr-1" />Sync</Button>
                <Button size="sm" variant="outline" className="flex-1" onClick={async () => { await v5KnowledgeApi.disconnectSource(c.id); toast.success("Disconnected"); fetchConnectors(); }}>Disconnect</Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {connectors.length === 0 && !showForm && <p className="text-center text-muted-foreground col-span-3 py-8">No sources connected.</p>}
      </div>
    </div>
  );
}

function DocumentsTab() {
  const [documents, setDocuments] = useState<any[]>([]);
  useEffect(() => { v5KnowledgeApi.listDocuments().then((r) => setDocuments(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-indigo-500/20"><CardHeader className="pb-2"><CardTitle className="text-sm"><FileText className="w-4 h-4 inline mr-1" />Documents</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{documents.length}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Indexed</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-green-500">{documents.filter((d) => d.is_indexed).length}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Types</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{new Set(documents.map((d) => d.file_type)).size}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Connectors</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{new Set(documents.map((d) => d.connector_id)).size}</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-sm">All Documents</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {documents.map((d) => (
              <div key={d.id} className="flex items-center justify-between border-b pb-2">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  <div><p className="text-sm font-medium">{d.title}</p><p className="text-xs text-muted-foreground">{d.file_type} | {d.author || "Unknown"}</p></div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={d.is_indexed ? "default" : "outline"} className="text-xs">{d.is_indexed ? "Indexed" : "Pending"}</Badge>
                  <span className="text-xs text-muted-foreground">{d.indexed_at ? new Date(d.indexed_at).toLocaleDateString() : "-"}</span>
                </div>
              </div>
            ))}
            {documents.length === 0 && <p className="text-center text-muted-foreground py-4">No documents indexed yet.</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function SearchTab() {
  const [query, setQuery] = useState(""); const [results, setResults] = useState<any>(null);
  const handleSearch = async () => {
    if (!query.trim()) return; const res = await v5KnowledgeApi.search({ query: query.trim(), max_results: 10, include_citations: true }); setResults(res.data);
  };
  return (
    <Card className="border-indigo-500/20">
      <CardHeader><CardTitle className="text-sm"><Search className="w-4 h-4 inline mr-1" />Semantic Search</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input placeholder="Search across all connected knowledge sources..." value={query} onChange={(e) => setQuery(e.target.value)} className="flex-1" onKeyDown={(e) => e.key === "Enter" && handleSearch()} />
          <Button onClick={handleSearch}><Search className="w-4 h-4" /></Button>
        </div>
        {results && <div className="space-y-2">
          <p className="text-xs text-muted-foreground">{results.total_results} results in {(results.execution_time_ms || 0).toFixed(0)}ms</p>
          {results.results.map((r: any) => (
            <div key={r.id} className="border rounded-lg p-3">
              <div className="flex items-start justify-between"><p className="text-sm font-medium">{r.title}</p><Badge variant="outline" className="text-xs">{(r.relevance * 100).toFixed(0)}%</Badge></div>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{r.snippet}</p>
            </div>
          ))}
        </div>}
      </CardContent>
    </Card>
  );
}

function ReasoningTab() {
  const [query, setQuery] = useState(""); const [answer, setAnswer] = useState<any>(null); const [loading, setLoading] = useState(false);
  const handleQuery = async () => {
    if (!query.trim()) return; setLoading(true);
    try { const res = await v5KnowledgeApi.queryWithReasoning(query.trim()); setAnswer(res.data); } catch { toast.error("Query failed"); }
    setLoading(false);
  };
  return (
    <Card className="border-indigo-500/20">
      <CardHeader><CardTitle className="text-sm"><Brain className="w-4 h-4 inline mr-1" />AI Reasoning with Citations</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input placeholder="e.g., What are our top security findings this quarter?" value={query} onChange={(e) => setQuery(e.target.value)} className="flex-1" onKeyDown={(e) => e.key === "Enter" && handleQuery()} />
          <Button onClick={handleQuery} disabled={loading}>{loading ? "Thinking..." : <Brain className="w-4 h-4" />}</Button>
        </div>
        {answer && (
          <div className="space-y-3">
            <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap leading-relaxed">{answer.answer}</div>
            {answer.citations?.length > 0 && <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Sources</p>
              {answer.citations.map((c: any, i: number) => (
                <div key={i} className="border-l-2 border-indigo-500 pl-3 py-1 mb-1"><p className="text-xs"><span className="font-medium">{c.document_title}</span></p><p className="text-xs text-muted-foreground">"{c.cited_text}"</p></div>
              ))}
            </div>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function GraphTab() {
  const [query, setQuery] = useState(""); const [graphData, setGraphData] = useState<any>(null);
  const handleQuery = async () => {
    if (!query.trim()) return; const res = await v5KnowledgeApi.queryKnowledgeGraph({ query: query.trim(), max_depth: 2 }); setGraphData(res.data);
  };
  return (
    <Card className="border-indigo-500/20">
      <CardHeader><CardTitle className="text-sm"><GitBranch className="w-4 h-4 inline mr-1" />Knowledge Graph</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input placeholder="Search entities..." value={query} onChange={(e) => setQuery(e.target.value)} className="flex-1" onKeyDown={(e) => e.key === "Enter" && handleQuery()} />
          <Button onClick={handleQuery}><Network className="w-4 h-4" /></Button>
        </div>
        {graphData && <div className="grid gap-4 md:grid-cols-2">
          <Card><CardHeader><CardTitle className="text-sm"><User className="w-4 h-4 inline mr-1" />Entities ({graphData.nodes?.length || 0})</CardTitle></CardHeader>
            <CardContent><div className="space-y-2 max-h-60 overflow-y-auto">{(graphData.nodes || []).map((n: any) => (
              <div key={n.id} className="flex items-center justify-between border-b pb-1 text-sm"><span className="font-medium">{n.name}</span><Badge variant="outline" className="text-xs">{n.node_type}</Badge></div>
            ))}</div></CardContent></Card>
          <Card><CardHeader><CardTitle className="text-sm"><Workflow className="w-4 h-4 inline mr-1" />Relationships ({graphData.edges?.length || 0})</CardTitle></CardHeader>
            <CardContent><div className="space-y-2 max-h-60 overflow-y-auto">{(graphData.edges || []).map((e: any) => (
              <div key={e.id} className="flex items-center justify-between border-b pb-1 text-sm"><span className="text-xs text-muted-foreground">{e.edge_type}</span><Badge variant="outline" className="text-xs">{e.edge_type}</Badge></div>
            ))}</div></CardContent></Card>
        </div>}
        {graphData && <p className="text-xs text-muted-foreground">{graphData.explanation}</p>}
      </CardContent>
    </Card>
  );
}

function PermissionsTab() {
  const [docId, setDocId] = useState(""); const [principalId, setPrincipalId] = useState(""); const [message, setMessage] = useState("");
  const handleGrant = async () => { setMessage("Permission grant ready (implement full in next sprint)"); };
  return (
    <Card className="border-indigo-500/20">
      <CardHeader><CardTitle className="text-sm"><Shield className="w-4 h-4 inline mr-1" />Document Permissions</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-3 md:grid-cols-2">
          <Input placeholder="Document ID" value={docId} onChange={(e) => setDocId(e.target.value)} />
          <Input placeholder="Principal ID" value={principalId} onChange={(e) => setPrincipalId(e.target.value)} />
        </div>
        <Button onClick={handleGrant} className="w-full"><Shield className="w-4 h-4 mr-1" />Grant Permission</Button>
        {message && <p className="text-xs text-muted-foreground">{message}</p>}
      </CardContent>
    </Card>
  );
}

function CopilotChatTab() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<{role:string;content:string}[]>([]);
  const [copilotId, setCopilotId] = useState<string>("");
  const [copilots, setCopilots] = useState<any[]>([]);

  useEffect(() => { v5CopilotApi.listConfigs().then((r) => { setCopilots(r.data); if (r.data.length > 0) setCopilotId(r.data[0].id); }).catch(() => {}); }, []);

  const handleSend = async () => {
    if (!message.trim() || !copilotId) return;
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    const res = await v5CopilotApi.chat({ copilot_id: copilotId, message: message.trim(), session_id: sessionId });
    setSessionId(res.data.session_id);
    setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply }]);
    setMessage("");
  };

  return (
    <div className="space-y-4">
      <Card className="border-emerald-500/20">
        <CardHeader><CardTitle className="text-sm"><MessageSquare className="w-4 h-4 inline mr-1" />Industry Copilot Chat</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <select value={copilotId} onChange={(e) => setCopilotId(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
            {copilots.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.industry})</option>)}
            {copilots.length === 0 && <option value="">No copilots configured</option>}
          </select>
          <div className="border rounded-lg p-4 space-y-3 max-h-80 overflow-y-auto bg-muted/30">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] p-3 rounded-lg text-sm ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-card border"}`}>{m.content}</div>
              </div>
            ))}
            {messages.length === 0 && <p className="text-sm text-muted-foreground text-center py-8">Ask the copilot anything about your industry</p>}
          </div>
          <div className="flex gap-2">
            <Input placeholder="Type your message..." value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSend()} className="flex-1" />
            <Button onClick={handleSend}>Send</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function NgoTab() {
  const [grantDesc, setGrantDesc] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <div className="space-y-4">
      <Card className="border-emerald-500/20">
        <CardHeader><CardTitle className="text-sm"><Heart className="w-4 h-4 inline mr-1" />NGO Development Copilot</CardTitle>
          <CardDescription>Grant analysis, proposal drafting, report generation, logframe creation, donor compliance</CardDescription></CardHeader>
        <CardContent className="space-y-3">
          <Textarea placeholder="Describe a grant opportunity or paste the call text..." value={grantDesc} onChange={(e) => setGrantDesc(e.target.value)} rows={4} />
          <div className="flex gap-2">
            <Button onClick={async () => { if (!grantDesc.trim()) return; setLoading(true); const r = await v5CopilotApi.ngoAnalyzeGrant(grantDesc.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>{loading ? "Analyzing..." : "Analyze Grant"}</Button>
            <Button variant="outline" onClick={async () => { if (!grantDesc.trim()) return; setLoading(true); const r = await v5CopilotApi.ngoDraftProposal("Organization: Example NGO\nFocus: Education\nBudget: $500k", grantDesc.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Draft Proposal</Button>
          </div>
          {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
        </CardContent>
      </Card>
    </div>
  );
}

function FinanceTab() {
  const [data, setData] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <Card className="border-emerald-500/20">
      <CardHeader><CardTitle className="text-sm"><DollarSign className="w-4 h-4 inline mr-1" />Finance Copilot</CardTitle>
        <CardDescription>Budget analysis, forecasting, anomaly detection, cash flow analysis, financial reports</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <Textarea placeholder="Paste financial data, transactions, or budget figures..." value={data} onChange={(e) => setData(e.target.value)} rows={4} />
        <div className="flex gap-2 flex-wrap">
          <Button onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.financeAnalyzeBudget(data.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Analyze Budget</Button>
          <Button variant="outline" onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.financeForecast(data.trim(), "quarterly"); setResult(r.data.result); setLoading(false); }} disabled={loading}>Forecast</Button>
          <Button variant="outline" onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.financeDetectAnomalies(data.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Detect Anomalies</Button>
        </div>
        {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
      </CardContent>
    </Card>
  );
}

function HospitalityTab() {
  const [data, setData] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <Card className="border-emerald-500/20">
      <CardHeader><CardTitle className="text-sm"><Sun className="w-4 h-4 inline mr-1" />Hospitality & Tourism Copilot</CardTitle>
        <CardDescription>Occupancy analysis, pricing optimization, marketing content, feedback analysis</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <Textarea placeholder="Paste occupancy data, property info, or market data..." value={data} onChange={(e) => setData(e.target.value)} rows={4} />
        <div className="flex gap-2">
          <Button onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.hospitalityAnalyzeOccupancy(data.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Analyze Occupancy</Button>
          <Button variant="outline" onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.hospitalityOptimizePricing(data.trim(), "market data"); setResult(r.data.result); setLoading(false); }} disabled={loading}>Optimize Pricing</Button>
        </div>
        {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
      </CardContent>
    </Card>
  );
}

function EducationTab() {
  const [subject, setSubject] = useState(""); const [topic, setTopic] = useState(""); const [grade, setGrade] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <Card className="border-emerald-500/20">
      <CardHeader><CardTitle className="text-sm"><GraduationCap className="w-4 h-4 inline mr-1" />Education Copilot</CardTitle>
        <CardDescription>Lesson planning, assessments, study plans, student performance analysis</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-3 md:grid-cols-3">
          <Input placeholder="Subject (e.g., Math)" value={subject} onChange={(e) => setSubject(e.target.value)} />
          <Input placeholder="Grade (e.g., Grade 5)" value={grade} onChange={(e) => setGrade(e.target.value)} />
          <Input placeholder="Topic (e.g., Fractions)" value={topic} onChange={(e) => setTopic(e.target.value)} />
        </div>
        <div className="flex gap-2">
          <Button onClick={async () => { if (!subject.trim() || !topic.trim()) return; setLoading(true); const r = await v5CopilotApi.educationPlanLesson(subject.trim(), grade.trim() || "General", topic.trim(), 60); setResult(r.data.result); setLoading(false); }} disabled={loading}>Plan Lesson</Button>
          <Button variant="outline" onClick={async () => { if (!subject.trim() || !topic.trim()) return; setLoading(true); const r = await v5CopilotApi.educationCreateAssessment(subject.trim(), grade.trim() || "General", topic.trim(), 10); setResult(r.data.result); setLoading(false); }} disabled={loading}>Create Assessment</Button>
        </div>
        {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
      </CardContent>
    </Card>
  );
}

function AgricultureTab() {
  const [data, setData] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <Card className="border-emerald-500/20">
      <CardHeader><CardTitle className="text-sm"><Sprout className="w-4 h-4 inline mr-1" />Agriculture Copilot</CardTitle>
        <CardDescription>Farm planning, cost analysis, market insights, training materials</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <Textarea placeholder="Describe your farm, crop type, region, or cost data..." value={data} onChange={(e) => setData(e.target.value)} rows={4} />
        <div className="flex gap-2">
          <Button onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.agriculturePlanFarming(data.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Plan Farming</Button>
          <Button variant="outline" onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.agricultureMarketInsights(data.trim(), "Global"); setResult(r.data.result); setLoading(false); }} disabled={loading}>Market Insights</Button>
        </div>
        {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
      </CardContent>
    </Card>
  );
}

function BusinessTab() {
  const [data, setData] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <Card className="border-emerald-500/20">
      <CardHeader><CardTitle className="text-sm"><Building className="w-4 h-4 inline mr-1" />Business Operations Copilot</CardTitle>
        <CardDescription>Strategy analysis, KPI monitoring, sales analysis, customer insights, process improvement</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <Textarea placeholder="Describe your business, strategy, KPIs, or customer data..." value={data} onChange={(e) => setData(e.target.value)} rows={4} />
        <div className="flex gap-2 flex-wrap">
          <Button onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.businessAnalyzeStrategy(data.trim(), "market data"); setResult(r.data.result); setLoading(false); }} disabled={loading}>Analyze Strategy</Button>
          <Button variant="outline" onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.businessAnalyzeKpis(data.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Analyze KPIs</Button>
          <Button variant="outline" onClick={async () => { if (!data.trim()) return; setLoading(true); const r = await v5CopilotApi.businessCustomerInsights(data.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Customer Insights</Button>
        </div>
        {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
      </CardContent>
    </Card>
  );
}

function ApprovalsTab() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [reqType, setReqType] = useState("financial_transaction");
  const [description, setDescription] = useState("");

  const fetchApprovals = () => { v5CopilotApi.listPendingApprovals().then((r) => setApprovals(r.data)).catch(() => {}); };
  useEffect(() => { fetchApprovals(); }, []);

  const handleCreate = async () => {
    if (!description.trim()) return;
    await v5CopilotApi.createApproval({ request_type: reqType, description: description.trim(), details: {} });
    toast.success("Approval request created"); setDescription(""); fetchApprovals();
  };

  const handleReview = async (id: string, approved: boolean) => {
    await v5CopilotApi.reviewApproval(id, { approved, reviewer_comment: approved ? "Approved" : "Rejected" });
    toast.success(approved ? "Approved" : "Rejected"); fetchApprovals();
  };

  return (
    <div className="space-y-4">
      <Card className="border-emerald-500/20">
        <CardHeader><CardTitle className="text-sm"><CheckCircle className="w-4 h-4 inline mr-1" />Approval Requests</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <select value={reqType} onChange={(e) => setReqType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background">
              <option value="financial_transaction">Financial Transaction</option>
              <option value="official_report">Official Report</option>
              <option value="external_communication">External Communication</option>
              <option value="policy_change">Policy Change</option>
            </select>
            <Input placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} className="flex-1" />
            <Button onClick={handleCreate}>Create</Button>
          </div>
        </CardContent>
      </Card>
      {approvals.map((a) => (
        <Card key={a.id}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between"><CardTitle className="text-sm">{a.request_type}</CardTitle><Badge>{a.status}</Badge></div>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{a.description}</p>
            {a.status === "pending" && <div className="flex gap-2 mt-3">
              <Button size="sm" variant="outline" className="text-green-600" onClick={() => handleReview(a.id, true)}>Approve</Button>
              <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleReview(a.id, false)}>Reject</Button>
            </div>}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function CopilotAnalyticsTab() {
  const [analytics, setAnalytics] = useState<any>(null);
  useEffect(() => { v5CopilotApi.getAnalyticsDashboard().then((r) => setAnalytics(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-emerald-500/20"><CardHeader className="pb-2"><CardTitle className="text-sm"><MessageSquare className="w-4 h-4 inline mr-1" />Sessions</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{analytics?.total_sessions || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><Zap className="w-4 h-4 inline mr-1" />Recommendations</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{analytics?.total_recommendations || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><Workflow className="w-4 h-4 inline mr-1" />Workflows</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{analytics?.total_workflows_executed || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><BarChart3 className="w-4 h-4 inline mr-1" />Events</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{Object.values(analytics?.event_counts || {}).reduce((a: number, b: any) => a + (typeof b === 'number' ? b : 0), 0)}</p></CardContent></Card>
      </div>
      {analytics?.event_counts && <Card>
        <CardHeader><CardTitle className="text-sm">Event Breakdown</CardTitle></CardHeader>
        <CardContent><div className="space-y-2">{[...Object.entries(analytics.event_counts)].map(([k, v]) => (
          <div key={k} className="flex items-center justify-between border-b pb-1 text-sm"><span className="font-medium capitalize">{k.replace(/_/g, " ")}</span><Badge variant="outline">{v as number}</Badge></div>
        ))}</div></CardContent>
      </Card>}
    </div>
  );
}

function ScenariosTab() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [name, setName] = useState(""); const [desc, setDesc] = useState(""); const [type, setType] = useState("what_if"); const [showForm, setShowForm] = useState(false);
  const fetchScenarios = () => { v5SimulationApi.listScenarios().then((r) => setScenarios(r.data)).catch(() => {}); };
  useEffect(() => { fetchScenarios(); }, []);
  const handleCreate = async () => {
    if (!name.trim()) return;
    await v5SimulationApi.createScenario({ name: name.trim(), description: desc.trim(), scenario_type: type, variables: [], assumptions: [] });
    toast.success("Scenario created"); setName(""); setDesc(""); setShowForm(false); fetchScenarios();
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><p className="text-sm text-muted-foreground">{scenarios.length} scenario(s)</p><Button onClick={() => setShowForm(!showForm)}><ClipboardList className="w-4 h-4 mr-1" />{showForm ? "Cancel" : "New Scenario"}</Button></div>
      {showForm && <Card className="border-blue-500/20">
        <CardHeader><CardTitle className="text-sm">Create Scenario</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Input placeholder="Scenario name" value={name} onChange={(e) => setName(e.target.value)} />
          <Input placeholder="Description" value={desc} onChange={(e) => setDesc(e.target.value)} />
          <select value={type} onChange={(e) => setType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
            <option value="what_if">What-If</option><option value="forecast">Forecast</option><option value="optimization">Optimization</option><option value="risk">Risk</option>
          </select>
          <Button onClick={handleCreate} className="w-full">Create Scenario</Button>
        </CardContent>
      </Card>}
      <div className="grid gap-4 md:grid-cols-3">
        {scenarios.map((s) => (
          <Card key={s.id}>
            <CardHeader>
              <div className="flex items-center justify-between"><CardTitle className="text-sm">{s.name}</CardTitle><Badge>{s.scenario_type}</Badge></div>
              <CardDescription>{s.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="flex-1" onClick={async () => { const r = await v5SimulationApi.runSimulation({ scenario_id: s.id, simulation_type: s.scenario_type }); toast.success("Simulation started"); }}><Activity className="w-3 h-3 mr-1" />Run</Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {scenarios.length === 0 && !showForm && <p className="text-center text-muted-foreground col-span-3 py-8">No scenarios yet.</p>}
      </div>
    </div>
  );
}

function RunSimulationTab() {
  const [sims, setSims] = useState<any[]>([]);
  const [results, setResults] = useState<any>(null);
  useEffect(() => { v5SimulationApi.listSimulations().then((r) => setSims(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-blue-500/20"><CardHeader className="pb-2"><CardTitle className="text-sm"><Activity className="w-4 h-4 inline mr-1" />Total</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{sims.length}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Completed</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-green-500">{sims.filter((s) => s.status === "completed").length}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Running</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-blue-500">{sims.filter((s) => s.status === "running").length}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Failed</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-red-500">{sims.filter((s) => s.status === "failed").length}</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-sm">Simulation Runs</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {sims.map((s) => (
              <div key={s.id} className="flex items-center justify-between border-b pb-2">
                <div><p className="text-sm font-medium">{s.simulation_type}</p><p className="text-xs text-muted-foreground">{s.started_at ? new Date(s.started_at).toLocaleString() : "-"}</p></div>
                <div className="flex items-center gap-2">
                  <Badge variant={s.status === "completed" ? "default" : "outline"}>{s.status}</Badge>
                  <Button size="sm" variant="outline" onClick={async () => { const r = await v5SimulationApi.getSimulationResults(s.id); setResults(r.data); }}>View</Button>
                </div>
              </div>
            ))}
            {sims.length === 0 && <p className="text-center text-muted-foreground py-4">No simulations run yet.</p>}
          </div>
        </CardContent>
      </Card>
      {results && <Card>
        <CardHeader><CardTitle className="text-sm">Simulation Results</CardTitle></CardHeader>
        <CardContent><div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{results.output_data?.result || JSON.stringify(results, null, 2)}</div></CardContent>
      </Card>}
    </div>
  );
}

function FinancialSimTab() {
  const [budget, setBudget] = useState(""); const [scenario, setScenario] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <Card className="border-blue-500/20">
      <CardHeader><CardTitle className="text-sm"><TrendingUp className="w-4 h-4 inline mr-1" />Financial Simulation</CardTitle>
        <CardDescription>Budget scenarios, cash flow projections, revenue forecasts, cost impact analysis</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <Input placeholder="Current budget or financial data" value={budget} onChange={(e) => setBudget(e.target.value)} />
        <Textarea placeholder="Describe your scenario (e.g., 'Reduce funding by 20%' or 'Increase costs by 15%')" value={scenario} onChange={(e) => setScenario(e.target.value)} rows={3} />
        <div className="flex gap-2 flex-wrap">
          <Button onClick={async () => { if (!budget.trim() || !scenario.trim()) return; setLoading(true); const r = await v5SimulationApi.budgetScenario(parseFloat(budget) || 0, scenario.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Budget Scenario</Button>
          <Button variant="outline" onClick={async () => { if (!budget.trim() || !scenario.trim()) return; setLoading(true); const r = await v5SimulationApi.cashflowProjection(budget.trim(), scenario.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Cash Flow</Button>
          <Button variant="outline" onClick={async () => { if (!budget.trim() || !scenario.trim()) return; setLoading(true); const r = await v5SimulationApi.revenueForecast(budget.trim(), scenario.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Revenue Forecast</Button>
          <Button variant="outline" onClick={async () => { if (!budget.trim() || !scenario.trim()) return; setLoading(true); const r = await v5SimulationApi.costImpactAnalysis(budget.trim(), scenario.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Cost Impact</Button>
        </div>
        {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
      </CardContent>
    </Card>
  );
}

function ProjectSimTab() {
  const [projectData, setProjectData] = useState(""); const [scenario, setScenario] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <Card className="border-blue-500/20">
      <CardHeader><CardTitle className="text-sm"><GitFork className="w-4 h-4 inline mr-1" />Project Simulation</CardTitle>
        <CardDescription>Simulate project timelines, resource changes, and delay scenarios</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <Textarea placeholder="Describe your project (budget, timeline, resources, activities...)" value={projectData} onChange={(e) => setProjectData(e.target.value)} rows={3} />
        <Textarea placeholder="Describe the scenario to simulate (e.g., 'Staff shortage', 'Budget cut 10%')" value={scenario} onChange={(e) => setScenario(e.target.value)} rows={2} />
        <div className="flex gap-2">
          <Button onClick={async () => { if (!projectData.trim() || !scenario.trim()) return; setLoading(true); const r = await v5SimulationApi.simulateProject(projectData.trim(), scenario.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Simulate Project</Button>
          <Button variant="outline" onClick={async () => { if (!projectData.trim() || !scenario.trim()) return; setLoading(true); const r = await v5SimulationApi.resourceImpact(projectData.trim(), scenario.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Resource Impact</Button>
          <Button variant="outline" onClick={async () => { if (!projectData.trim() || !scenario.trim()) return; setLoading(true); const r = await v5SimulationApi.timelineWhatIf(projectData.trim(), scenario.trim()); setResult(r.data.result); setLoading(false); }} disabled={loading}>Timeline What-If</Button>
        </div>
        {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
      </CardContent>
    </Card>
  );
}

function RiskSimTab() {
  const [simId, setSimId] = useState(""); const [matrix, setMatrix] = useState<any>(null); const [result, setResult] = useState("");
  return (
    <div className="space-y-4">
      <Card className="border-blue-500/20">
        <CardHeader><CardTitle className="text-sm"><AlertTriangle className="w-4 h-4 inline mr-1" />Risk Analysis</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Input placeholder="Simulation ID to analyze risks for" value={simId} onChange={(e) => setSimId(e.target.value)} />
          <Button onClick={async () => { if (!simId.trim()) return; const r = await v5SimulationApi.analyzeRisks(simId.trim()); setResult(r.data.description || JSON.stringify(r.data)); }}>Analyze Risks</Button>
          {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-sm">Risk Matrix</CardTitle></CardHeader>
        <CardContent>
          <Button variant="outline" onClick={async () => { const r = await v5SimulationApi.getRiskMatrix(); setMatrix(r.data); }} className="mb-3">Load Risk Matrix</Button>
          {matrix && <div className="grid gap-3 md:grid-cols-2">
            <div className="p-3 border border-red-300 rounded-lg bg-red-50/50"><p className="font-medium text-sm text-red-700 mb-1">Critical ({matrix.critical?.length || 0})</p>{matrix.critical?.map((r: any) => <p key={r.id} className="text-xs">{r.risk_name}</p>)}</div>
            <div className="p-3 border border-orange-300 rounded-lg bg-orange-50/50"><p className="font-medium text-sm text-orange-700 mb-1">High ({matrix.high?.length || 0})</p>{matrix.high?.map((r: any) => <p key={r.id} className="text-xs">{r.risk_name}</p>)}</div>
            <div className="p-3 border border-yellow-300 rounded-lg bg-yellow-50/50"><p className="font-medium text-sm text-yellow-700 mb-1">Medium ({matrix.medium?.length || 0})</p>{matrix.medium?.map((r: any) => <p key={r.id} className="text-xs">{r.risk_name}</p>)}</div>
            <div className="p-3 border border-green-300 rounded-lg bg-green-50/50"><p className="font-medium text-sm text-green-700 mb-1">Low ({matrix.low?.length || 0})</p>{matrix.low?.map((r: any) => <p key={r.id} className="text-xs">{r.risk_name}</p>)}</div>
          </div>}
        </CardContent>
      </Card>
    </div>
  );
}

function OptimizeTab() {
  const [objective, setObjective] = useState(""); const [constraints, setConstraints] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <Card className="border-blue-500/20">
      <CardHeader><CardTitle className="text-sm"><Target className="w-4 h-4 inline mr-1" />Resource Optimization</CardTitle>
        <CardDescription>Optimize budget allocation, staff distribution, and resource utilization</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <Input placeholder="Objective (e.g., 'Maximize project output with limited budget')" value={objective} onChange={(e) => setObjective(e.target.value)} />
        <Textarea placeholder="Constraints (e.g., 'Total budget: $100k, Min 5 staff per project')" value={constraints} onChange={(e) => setConstraints(e.target.value)} rows={3} />
        <Button onClick={async () => { if (!objective.trim() || !constraints.trim()) return; setLoading(true); const r = await v5SimulationApi.optimizeResources({ objective: objective.trim(), constraints: { text: constraints.trim() }, variables: [] }); setResult(r.data.description || JSON.stringify(r.data)); setLoading(false); }} disabled={loading} className="w-full">Optimize</Button>
        {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
      </CardContent>
    </Card>
  );
}

function DigitalTwinTab() {
  const [twins, setTwins] = useState<any[]>([]); const [name, setName] = useState(""); const [desc, setDesc] = useState(""); const [twinType, setTwinType] = useState("project"); const [showForm, setShowForm] = useState(false);
  const fetchTwins = () => { v5SimulationApi.listDigitalTwins().then((r) => setTwins(r.data)).catch(() => {}); };
  useEffect(() => { fetchTwins(); }, []);
  const handleCreate = async () => {
    if (!name.trim()) return; await v5SimulationApi.createDigitalTwin({ name: name.trim(), description: desc.trim(), twin_type: twinType }); toast.success("Digital twin created"); setName(""); setDesc(""); setShowForm(false); fetchTwins();
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><p className="text-sm text-muted-foreground">{twins.length} digital twin(s)</p><Button onClick={() => setShowForm(!showForm)}><Box className="w-4 h-4 mr-1" />{showForm ? "Cancel" : "New Twin"}</Button></div>
      {showForm && <Card className="border-blue-500/20">
        <CardHeader><CardTitle className="text-sm">Create Digital Twin</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Input placeholder="Twin name" value={name} onChange={(e) => setName(e.target.value)} />
          <Input placeholder="Description" value={desc} onChange={(e) => setDesc(e.target.value)} />
          <select value={twinType} onChange={(e) => setTwinType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
            <option value="project">Project</option><option value="department">Department</option><option value="org">Organization</option><option value="financial">Financial</option>
          </select>
          <Button onClick={handleCreate} className="w-full">Create</Button>
        </CardContent>
      </Card>}
      <div className="grid gap-4 md:grid-cols-3">
        {twins.map((t) => (
          <Card key={t.id}>
            <CardHeader>
              <div className="flex items-center justify-between"><CardTitle className="text-sm">{t.name}</CardTitle><Badge>{t.twin_type}</Badge></div>
              <CardDescription>{t.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="flex-1" onClick={async () => { const r = await v5SimulationApi.analyzeTwin(t.id); toast.success(r.data.analysis?.slice(0, 50)); }}><Activity className="w-3 h-3 mr-1" />Analyze</Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {twins.length === 0 && !showForm && <p className="text-center text-muted-foreground col-span-3 py-8">No digital twins yet.</p>}
      </div>
    </div>
  );
}

function SimAnalyticsTab() {
  const [analytics, setAnalytics] = useState<any>(null);
  useEffect(() => { v5SimulationApi.getAnalyticsDashboard().then((r) => setAnalytics(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-blue-500/20"><CardHeader className="pb-2"><CardTitle className="text-sm"><Activity className="w-4 h-4 inline mr-1" />Simulations</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{analytics?.total_simulations || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><ClipboardList className="w-4 h-4 inline mr-1" />Scenarios</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{analytics?.total_scenarios || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><AlertTriangle className="w-4 h-4 inline mr-1" />Risks</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{analytics?.total_risks || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><Target className="w-4 h-4 inline mr-1" />Recommendations</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{analytics?.total_recommendations || 0}</p></CardContent></Card>
      </div>
      {analytics?.by_type && <Card>
        <CardHeader><CardTitle className="text-sm">By Simulation Type</CardTitle></CardHeader>
        <CardContent><div className="space-y-2">{[...Object.entries(analytics.by_type)].map(([k, v]) => (
          <div key={k} className="flex items-center justify-between border-b pb-1 text-sm"><span className="font-medium capitalize">{k}</span><Badge variant="outline">{v as number}</Badge></div>
        ))}</div></CardContent>
      </Card>}
    </div>
  );
}

function CompliancePoliciesTab() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [content, setContent] = useState(""); const [result, setResult] = useState("");
  const fetchPolicies = () => { v5ComplianceApi.listPolicies().then((r) => setPolicies(r.data)).catch(() => {}); };
  useEffect(() => { fetchPolicies(); }, []);
  return (
    <div className="space-y-4">
      <Card className="border-rose-500/20">
        <CardHeader><CardTitle className="text-sm"><Scale className="w-4 h-4 inline mr-1" />AI Policy Analyzer</CardTitle>
          <CardDescription>Analyze policies for compliance, completeness, and regulatory alignment</CardDescription></CardHeader>
        <CardContent className="space-y-3">
          <Textarea placeholder="Paste policy content to analyze..." value={content} onChange={(e) => setContent(e.target.value)} rows={4} />
          <Button onClick={async () => { if (!content.trim()) return; const r = await v5ComplianceApi.analyzePolicy({ content: content.trim() }); setResult(r.data.analysis || JSON.stringify(r.data)); }}>Analyze Policy</Button>
          {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-sm">Existing Policies ({policies.length})</CardTitle></CardHeader>
        <CardContent><div className="space-y-2 max-h-60 overflow-y-auto">
          {policies.map((p) => (
            <div key={p.id} className="flex items-center justify-between border-b pb-1 text-sm">
              <span className="font-medium">{p.name}</span>
              <Badge variant={p.status === "active" ? "default" : "outline"}>{p.status}</Badge>
            </div>
          ))}
        </div></CardContent>
      </Card>
    </div>
  );
}

function ComplianceDocReviewTab() {
  const [docType, setDocType] = useState("contract"); const [content, setContent] = useState(""); const [result, setResult] = useState(""); const [loading, setLoading] = useState(false);
  return (
    <Card className="border-rose-500/20">
      <CardHeader><CardTitle className="text-sm"><FileCheck className="w-4 h-4 inline mr-1" />Document Compliance Review</CardTitle>
        <CardDescription>Review contracts, reports, budgets, proposals for compliance issues</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <select value={docType} onChange={(e) => setDocType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
          <option value="contract">Contract</option><option value="report">Report</option><option value="budget">Budget</option><option value="proposal">Proposal</option><option value="policy">Policy</option>
        </select>
        <Textarea placeholder="Paste document content for compliance review..." value={content} onChange={(e) => setContent(e.target.value)} rows={5} />
        <Button onClick={async () => { if (!content.trim()) return; setLoading(true); const r = await v5ComplianceApi.reviewDocument({ title: "Document Review", content: content.trim(), document_type: docType }); setResult(r.data.analysis || JSON.stringify(r.data)); setLoading(false); }} disabled={loading} className="w-full">{loading ? "Reviewing..." : "Review Document"}</Button>
        {result && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{result}</div>}
      </CardContent>
    </Card>
  );
}

function ComplianceAuditsTab() {
  const [audits, setAudits] = useState<any[]>([]);
  const [title, setTitle] = useState(""); const [desc, setDesc] = useState(""); const [auditType, setAuditType] = useState("financial"); const [showForm, setShowForm] = useState(false);
  const fetchAudits = () => { v5ComplianceApi.listAudits().then((r) => setAudits(r.data)).catch(() => {}); };
  useEffect(() => { fetchAudits(); }, []);
  const handleCreate = async () => {
    if (!title.trim()) return; await v5ComplianceApi.createAudit({ audit_type: auditType, title: title.trim(), description: desc.trim() });
    toast.success("Audit created"); setTitle(""); setDesc(""); setShowForm(false); fetchAudits();
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><p className="text-sm text-muted-foreground">{audits.length} audit(s)</p><Button onClick={() => setShowForm(!showForm)}><ClipboardCheck className="w-4 h-4 mr-1" />{showForm ? "Cancel" : "New Audit"}</Button></div>
      {showForm && <Card className="border-rose-500/20">
        <CardHeader><CardTitle className="text-sm">Create Audit</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <select value={auditType} onChange={(e) => setAuditType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
            <option value="financial">Financial</option><option value="operational">Operational</option><option value="compliance">Compliance</option><option value="security">Security</option><option value="external">External</option>
          </select>
          <Input placeholder="Audit title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <Textarea placeholder="Description" value={desc} onChange={(e) => setDesc(e.target.value)} rows={2} />
          <Button onClick={handleCreate} className="w-full">Create Audit</Button>
        </CardContent>
      </Card>}
      <div className="grid gap-4 md:grid-cols-2">
        {audits.map((a) => (
          <Card key={a.id}>
            <CardHeader>
              <div className="flex items-center justify-between"><CardTitle className="text-sm">{a.title}</CardTitle><Badge>{a.status}</Badge></div>
              <CardDescription>{a.audit_type} — {a.description?.slice(0, 100)}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={async () => { const r = await v5ComplianceApi.generateAuditChecklist(a.id); toast.success("Checklist generated"); }}><ClipboardCheck className="w-3 h-3 mr-1" />Checklist</Button>
                <Button size="sm" variant="outline" onClick={async () => { const r = await v5ComplianceApi.generateAuditPackage(a.id); toast.success("Package generated"); }}><FileCheck className="w-3 h-3 mr-1" />Package</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ComplianceFindingsTab() {
  const [findings, setFindings] = useState<any[]>([]); const [actions, setActions] = useState<any[]>([]);
  const [fType, setFType] = useState("gap"); const [fTitle, setFTitle] = useState(""); const [fDesc, setFDesc] = useState(""); const [fSev, setFSev] = useState("medium"); const [showForm, setShowForm] = useState(false);
  const fetchFindings = () => { v5ComplianceApi.listFindings().then((r) => setFindings(r.data)).catch(() => {}); v5ComplianceApi.listCorrectiveActions().then((r) => setActions(r.data)).catch(() => {}); };
  useEffect(() => { fetchFindings(); }, []);
  const handleCreate = async () => {
    if (!fTitle.trim()) return; await v5ComplianceApi.createFinding({ finding_type: fType, title: fTitle.trim(), description: fDesc.trim(), severity: fSev }); toast.success("Finding created"); setFTitle(""); setFDesc(""); setShowForm(false); fetchFindings();
  };
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><p className="text-sm text-muted-foreground">{findings.length} finding(s) | {actions.length} action(s)</p><Button onClick={() => setShowForm(!showForm)}><AlertTriangle className="w-4 h-4 mr-1" />{showForm ? "Cancel" : "New Finding"}</Button></div>
      {showForm && <Card className="border-rose-500/20">
        <CardHeader><CardTitle className="text-sm">Create Finding</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <select value={fType} onChange={(e) => setFType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
            <option value="policy_violation">Policy Violation</option><option value="gap">Gap</option><option value="risk">Risk</option><option value="observation">Observation</option>
          </select>
          <Input placeholder="Finding title" value={fTitle} onChange={(e) => setFTitle(e.target.value)} />
          <Textarea placeholder="Description" value={fDesc} onChange={(e) => setFDesc(e.target.value)} rows={2} />
          <select value={fSev} onChange={(e) => setFSev(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
            <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
          </select>
          <Button onClick={handleCreate} className="w-full">Create</Button>
        </CardContent>
      </Card>}
      <div className="grid gap-4 md:grid-cols-2">
        <Card><CardHeader><CardTitle className="text-sm">Open Findings</CardTitle></CardHeader>
          <CardContent><div className="space-y-2 max-h-80 overflow-y-auto">
            {findings.filter((f) => f.status === "open" || f.status === "in_progress").map((f) => (
              <div key={f.id} className="border-b pb-2">
                <div className="flex items-center justify-between"><p className="text-sm font-medium">{f.title}</p><Badge variant={f.severity === "critical" || f.severity === "high" ? "default" : "outline"}>{f.severity}</Badge></div>
                <p className="text-xs text-muted-foreground">{f.description?.slice(0, 100)}</p>
              </div>
            ))}
          </div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Corrective Actions</CardTitle></CardHeader>
          <CardContent><div className="space-y-2 max-h-80 overflow-y-auto">
            {actions.map((a) => (
              <div key={a.id} className="border-b pb-2">
                <div className="flex items-center justify-between"><p className="text-sm font-medium">{a.title}</p><Badge>{a.status}</Badge></div>
                <p className="text-xs text-muted-foreground">{a.description?.slice(0, 100)}</p>
              </div>
            ))}
          </div></CardContent></Card>
      </div>
    </div>
  );
}

function ComplianceRiskTab() {
  const [riskDash, setRiskDash] = useState<any>(null);
  return (
    <div className="space-y-4">
      <Card className="border-rose-500/20">
        <CardHeader><CardTitle className="text-sm"><Eye className="w-4 h-4 inline mr-1" />Compliance Risk Assessment</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Button onClick={async () => { const r = await v5ComplianceApi.assessRisks(); toast.success("Risk assessment complete"); }} className="w-full">Run Full Risk Assessment</Button>
          <Button variant="outline" onClick={async () => { const r = await v5ComplianceApi.getRiskDashboard(); setRiskDash(r.data); }} className="w-full">Load Risk Dashboard</Button>
          {riskDash && <div>
            <div className="grid gap-3 md:grid-cols-2 mb-3">
              <Card><CardHeader className="pb-1"><CardTitle className="text-xs">Open Findings</CardTitle></CardHeader><CardContent><p className="text-xl font-bold">{riskDash.open_findings}</p></CardContent></Card>
              <Card><CardHeader className="pb-1"><CardTitle className="text-xs">Open Actions</CardTitle></CardHeader><CardContent><p className="text-xl font-bold">{riskDash.open_actions}</p></CardContent></Card>
            </div>
            {riskDash.scores && <div>
              <p className="text-sm font-medium mb-2">Risk Scores</p>
              <div className="space-y-2">{Object.entries(riskDash.scores).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between text-sm border-b pb-1"><span className="font-medium capitalize">{k}</span><Badge>{(v as number).toFixed(0)}/100</Badge></div>
              ))}</div>
            </div>}
          </div>}
        </CardContent>
      </Card>
    </div>
  );
}

function ComplianceDashboardTab() {
  const [dashboard, setDashboard] = useState<any>(null);
  useEffect(() => { v5ComplianceApi.getComplianceDashboard().then((r) => setDashboard(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-rose-500/20"><CardHeader className="pb-2"><CardTitle className="text-sm"><Scale className="w-4 h-4 inline mr-1" />Policies</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dashboard?.total_policies || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><ClipboardCheck className="w-4 h-4 inline mr-1" />Checks</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dashboard?.total_checks || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><AlertTriangle className="w-4 h-4 inline mr-1" />Findings</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-amber-500">{dashboard?.total_findings || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><CheckCircle className="w-4 h-4 inline mr-1" />Actions</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dashboard?.total_actions || 0}</p></CardContent></Card>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Open Findings</CardTitle></CardHeader><CardContent><p className={`text-2xl font-bold ${(dashboard?.open_findings || 0) > 0 ? "text-red-500" : "text-green-500"}`}>{dashboard?.open_findings || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Audits</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dashboard?.total_audits || 0}</p></CardContent></Card>
        <Card className={dashboard?.overall_score ? (dashboard.overall_score >= 80 ? "border-green-500/20" : "border-amber-500/20") : ""}>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Overall Score</CardTitle></CardHeader>
          <CardContent><p className={`text-2xl font-bold ${dashboard?.overall_score ? (dashboard.overall_score >= 80 ? "text-green-500" : "text-amber-500") : ""}`}>{dashboard?.overall_score ? `${dashboard.overall_score.toFixed(0)}%` : "N/A"}</p></CardContent>
        </Card>
      </div>
    </div>
  );
}

function ConnectorInstallTab() {
  const [defs, setDefs] = useState<any[]>([]);
  const [name, setName] = useState(""); const [selectedId, setSelectedId] = useState(""); const [category, setCategory] = useState("");
  useEffect(() => { v5ConnectorApi.listDefinitions().then((r) => setDefs(r.data)).catch(() => {}); }, []);
  const handleInstall = async () => { if (!selectedId || !name.trim()) return; await v5ConnectorApi.install({ connector_id: selectedId, name: name.trim() }); toast.success("Connector installed"); setName(""); };
  return (
    <div className="space-y-4">
      <Card className="border-cyan-500/20">
        <CardHeader><CardTitle className="text-sm"><Cloud className="w-4 h-4 inline mr-1" />Install Connector</CardTitle><CardDescription>Browse available connectors and install them into your organization</CardDescription></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input placeholder="Filter by category" value={category} onChange={(e) => setCategory(e.target.value)} className="w-48" />
            <Button variant="outline" onClick={async () => { const r = await v5ConnectorApi.listDefinitions(category || undefined); setDefs(r.data); }}>Filter</Button>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {defs.map((d) => (
              <Card key={d.id} className={`cursor-pointer transition-all ${selectedId === d.id ? "ring-2 ring-cyan-500" : ""}`} onClick={() => setSelectedId(d.id)}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between"><CardTitle className="text-sm">{d.name}</CardTitle><Badge variant={d.is_official ? "default" : "outline"}>{d.is_official ? "Official" : "Community"}</Badge></div>
                  <CardDescription className="text-xs">{d.category} | {d.auth_type}</CardDescription>
                </CardHeader>
                <CardContent><p className="text-xs text-muted-foreground">{d.description?.slice(0, 120)}</p></CardContent>
              </Card>
            ))}
            {defs.length === 0 && <p className="text-center text-muted-foreground col-span-3 py-4">No connectors available.</p>}
          </div>
          {selectedId && <div className="flex gap-2">
            <Input placeholder="Integration name" value={name} onChange={(e) => setName(e.target.value)} className="flex-1" />
            <Button onClick={handleInstall}><Zap className="w-4 h-4 mr-1" />Install</Button>
          </div>}
        </CardContent>
      </Card>
    </div>
  );
}

function ConnectorIntegrationsTab() {
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [defs, setDefs] = useState<any[]>([]);
  useEffect(() => { v5ConnectorApi.listIntegrations().then((r) => setIntegrations(r.data)); v5ConnectorApi.listDefinitions().then((r) => setDefs(r.data)); }, []);
  const defMap = Object.fromEntries(defs.map((d) => [d.id, d]));
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><p className="text-sm text-muted-foreground">{integrations.length} integration(s)</p></div>
      <div className="grid gap-4 md:grid-cols-3">
        {integrations.map((i) => (
          <Card key={i.id}>
            <CardHeader>
              <div className="flex items-center justify-between"><CardTitle className="text-sm">{i.name}</CardTitle><Badge variant={i.status === "connected" ? "default" : "outline"}>{i.status}</Badge></div>
              <CardDescription>{defMap[i.connector_id]?.name || i.connector_id.slice(0, 8)} | {i.last_sync_at ? new Date(i.last_sync_at).toLocaleDateString() : "Never synced"}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={async () => { await v5ConnectorApi.authenticate({ integration_id: i.id, auth_data: { auth_type: "oauth2" } }); toast.success("Authenticated"); setIntegrations([]); }}><KeyRound className="w-3 h-3 mr-1" />Auth</Button>
                <Button size="sm" variant="outline" onClick={async () => { await v5ConnectorApi.startSync({ integration_id: i.id, sync_type: "full" }); toast.success("Sync started"); }}><RefreshCw className="w-3 h-3 mr-1" />Sync</Button>
                <Button size="sm" variant="outline" onClick={async () => { await v5ConnectorApi.uninstall(i.id); toast.success("Uninstalled"); setIntegrations([]); }}>Remove</Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {integrations.length === 0 && <p className="text-center text-muted-foreground col-span-3 py-8">No integrations installed.</p>}
      </div>
    </div>
  );
}

function ConnectorAuthTab() {
  const [keys, setKeys] = useState<any[]>([]); const [keyName, setKeyName] = useState(""); const [newKey, setNewKey] = useState<any>(null);
  const fetchKeys = () => { v5ConnectorApi.listApiKeys().then((r) => setKeys(r.data)).catch(() => {}); };
  useEffect(() => { fetchKeys(); }, []);
  return (
    <div className="space-y-4">
      <Card className="border-cyan-500/20">
        <CardHeader><CardTitle className="text-sm"><KeyRound className="w-4 h-4 inline mr-1" />API Keys & Authentication</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input placeholder="Key name" value={keyName} onChange={(e) => setKeyName(e.target.value)} className="flex-1" />
            <Button onClick={async () => { if (!keyName.trim()) return; const r = await v5ConnectorApi.createApiKey({ name: keyName.trim() }); setNewKey(r.data); setKeyName(""); fetchKeys(); }}>Create Key</Button>
          </div>
          {newKey && <div className="bg-muted p-4 rounded-lg text-sm"><p className="font-medium mb-1">New API Key Created</p><code className="bg-background px-2 py-1 rounded text-xs">{newKey.key_prefix}... (hash stored)</code></div>}
          <div className="space-y-2">
            {keys.map((k) => (
              <div key={k.id} className="flex items-center justify-between border-b pb-1 text-sm">
                <span className="font-medium">{k.name}</span>
                <div className="flex items-center gap-2">
                  <Badge variant={k.status === "active" ? "default" : "outline"}>{k.status}</Badge>
                  <Button size="sm" variant="ghost" className="text-red-500" onClick={async () => { await v5ConnectorApi.revokeApiKey(k.id); fetchKeys(); }}>Revoke</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ConnectorSyncTab() {
  const [jobs, setJobs] = useState<any[]>([]); const [summary, setSummary] = useState<any>(null);
  useEffect(() => { v5ConnectorApi.listSyncJobs().then((r) => setJobs(r.data)); v5ConnectorApi.getSyncSummary().then((r) => setSummary(r.data)); }, []);
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-cyan-500/20"><CardHeader className="pb-2"><CardTitle className="text-sm"><RefreshCw className="w-4 h-4 inline mr-1" />Total Syncs</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary?.total_syncs || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Running</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-blue-500">{summary?.running || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Failed</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-red-500">{summary?.failed || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Items</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{summary?.total_items_processed || 0}</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-sm">Sync Jobs</CardTitle></CardHeader>
        <CardContent><div className="space-y-2 max-h-80 overflow-y-auto">
          {jobs.map((j) => (
            <div key={j.id} className="flex items-center justify-between border-b pb-1 text-sm">
              <span className="font-medium">{j.sync_type}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">{j.items_processed}/{j.items_total}</span>
                <Badge variant={j.status === "completed" ? "default" : "outline"}>{j.status}</Badge>
              </div>
            </div>
          ))}
        </div></CardContent>
      </Card>
    </div>
  );
}

function ConnectorWebhooksTab() {
  const [events, setEvents] = useState<any[]>([]);
  const [eventType, setEventType] = useState(""); const [targetUrl, setTargetUrl] = useState(""); const [integrationId, setIntegrationId] = useState("");
  const fetchEvents = () => { v5ConnectorApi.listWebhookEvents().then((r) => setEvents(r.data)).catch(() => {}); };
  useEffect(() => { fetchEvents(); }, []);
  return (
    <div className="space-y-4">
      <Card className="border-cyan-500/20">
        <CardHeader><CardTitle className="text-sm"><Webhook className="w-4 h-4 inline mr-1" />Webhook Automation</CardTitle><CardDescription>Register webhooks to trigger AI actions on external events</CardDescription></CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-3">
            <Input placeholder="Integration ID" value={integrationId} onChange={(e) => setIntegrationId(e.target.value)} />
            <Input placeholder="Event type (e.g., file_created)" value={eventType} onChange={(e) => setEventType(e.target.value)} />
            <Input placeholder="Target URL" value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} />
          </div>
          <Button onClick={async () => { if (!integrationId.trim() || !eventType.trim() || !targetUrl.trim()) return; await v5ConnectorApi.registerWebhook({ integration_id: integrationId.trim(), event_type: eventType.trim(), target_url: targetUrl.trim() }); toast.success("Webhook registered"); }}><Webhook className="w-4 h-4 mr-1" />Register Webhook</Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-sm">Recent Events ({events.length})</CardTitle></CardHeader>
        <CardContent><div className="space-y-2 max-h-60 overflow-y-auto">
          {events.map((e) => (
            <div key={e.id} className="flex items-center justify-between border-b pb-1 text-sm">
              <div><span className="font-medium">{e.event_type}</span><span className="text-xs text-muted-foreground ml-2">from {e.source}</span></div>
              <Badge variant={e.status === "processed" ? "default" : "outline"}>{e.status}</Badge>
            </div>
          ))}
        </div></CardContent>
      </Card>
    </div>
  );
}

function ConnectorCustomTab() {
  const [customs, setCustoms] = useState<any[]>([]);
  const [name, setName] = useState(""); const [baseUrl, setBaseUrl] = useState(""); const [apiType, setApiType] = useState("rest"); const [authMethod, setAuthMethod] = useState("api_key");
  useEffect(() => { v5ConnectorApi.listCustomConnectors().then((r) => setCustoms(r.data)).catch(() => {}); }, []);
  const handleCreate = async () => { if (!name.trim() || !baseUrl.trim()) return; await v5ConnectorApi.createCustomConnector({ name: name.trim(), api_type: apiType, base_url: baseUrl.trim(), auth_method: authMethod }); toast.success("Custom connector created"); setName(""); setBaseUrl(""); };
  return (
    <div className="space-y-4">
      <Card className="border-cyan-500/20">
        <CardHeader><CardTitle className="text-sm"><TerminalSquare className="w-4 h-4 inline mr-1" />Custom API Connector Builder</CardTitle><CardDescription>Create custom REST/GraphQL connectors for any API</CardDescription></CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <Input placeholder="Connector name" value={name} onChange={(e) => setName(e.target.value)} />
            <Input placeholder="Base URL (e.g., https://api.example.com)" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <select value={apiType} onChange={(e) => setApiType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background"><option value="rest">REST</option><option value="graphql">GraphQL</option></select>
            <select value={authMethod} onChange={(e) => setAuthMethod(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background"><option value="api_key">API Key</option><option value="oauth2">OAuth 2.0</option><option value="basic">Basic Auth</option><option value="bearer">Bearer Token</option></select>
            <Button onClick={handleCreate}><Globe className="w-4 h-4 mr-1" />Create</Button>
          </div>
        </CardContent>
      </Card>
      <div className="grid gap-4 md:grid-cols-3">
        {customs.map((c) => (
          <Card key={c.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between"><CardTitle className="text-sm">{c.name}</CardTitle><Badge>{c.api_type}</Badge></div>
              <CardDescription className="text-xs">{c.base_url}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="flex-1" onClick={async () => { const r = await v5ConnectorApi.executeCustomApi(c.id, "test"); toast.success("Executed"); }}><Code2 className="w-3 h-3 mr-1" />Test</Button>
                <Button size="sm" variant="outline" onClick={async () => { await v5ConnectorApi.deleteCustomConnector(c.id); toast.success("Deleted"); setCustoms([]); }}>Delete</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ConnectorMarketplaceTab() {
  const [items, setItems] = useState<any[]>([]); const [search, setSearch] = useState(""); const [selected, setSelected] = useState<any>(null);
  useEffect(() => { v5ConnectorApi.listMarketplace().then((r) => setItems(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input placeholder="Search marketplace..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-md" />
        <Button variant="outline" onClick={async () => { const r = await v5ConnectorApi.listMarketplace(undefined, search || undefined); setItems(r.data); }}><Search className="w-4 h-4" /></Button>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        {items.map((item) => (
          <Card key={item.id} className="cursor-pointer hover:border-cyan-500/30 transition-all" onClick={() => setSelected(item)}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between"><CardTitle className="text-sm">{item.name}</CardTitle><Badge variant={item.is_verified ? "default" : "outline"}>{item.pricing_tier}</Badge></div>
              <CardDescription className="text-xs">{item.category} | {(item.rating || 0).toFixed(1)} ★ | {item.download_count} downloads</CardDescription>
            </CardHeader>
            <CardContent><p className="text-xs text-muted-foreground line-clamp-2">{item.description}</p></CardContent>
          </Card>
        ))}
      </div>
      {selected && <Card className="border-cyan-500/20">
        <CardHeader><CardTitle className="text-sm">{selected.name}</CardTitle><CardDescription>{selected.category} | Auth: {selected.auth_type}</CardDescription></CardHeader>
        <CardContent>
          <p className="text-sm mb-3">{selected.description}</p>
          <div className="flex gap-2">
            <Button onClick={async () => { await v5ConnectorApi.install({ connector_id: selected.connector_id, name: selected.name }); toast.success("Installed from marketplace"); }}><Store className="w-4 h-4 mr-1" />Install</Button>
            <Button variant="outline" onClick={async () => { const r = await v5ConnectorApi.getMarketplaceItem(selected.id); setSelected(r.data); }}><RefreshCw className="w-4 h-4 mr-1" />Refresh</Button>
          </div>
        </CardContent>
      </Card>}
    </div>
  );
}

function ConnectorLogsTab() {
  const [logs, setLogs] = useState<any[]>([]); const [level, setLevel] = useState(""); const [analysis, setAnalysis] = useState("");
  useEffect(() => { v5ConnectorApi.getLogs(undefined, level || undefined).then((r) => setLogs(r.data)).catch(() => {}); }, [level]);
  return (
    <div className="space-y-4">
      <Card className="border-cyan-500/20">
        <CardHeader><CardTitle className="text-sm"><ClipboardList className="w-4 h-4 inline mr-1" />Connector Activity Logs</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <select value={level} onChange={(e) => setLevel(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background">
              <option value="">All levels</option><option value="info">Info</option><option value="warning">Warning</option><option value="error">Error</option>
            </select>
            <Button variant="outline" onClick={async () => { const r = await v5ConnectorApi.analyzeLogs(); setAnalysis(r.data.analysis); }}>AI Analyze</Button>
          </div>
          {analysis && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{analysis}</div>}
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {logs.map((l) => (
              <div key={l.id} className="flex items-start gap-2 border-b pb-1 text-sm">
                <Badge variant={l.level === "error" ? "error" : l.level === "warning" ? "warning" : "default"} className="text-xs min-w-14">{l.level}</Badge>
                <span className="font-medium text-xs min-w-24">{l.action}</span>
                <span className="text-xs text-muted-foreground">{l.message?.slice(0, 200)}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ConnectorPlatformDashboardTab() {
  const [dash, setDash] = useState<any>(null);
  useEffect(() => { v5ConnectorApi.getDashboard().then((r) => setDash(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-cyan-500/20"><CardHeader className="pb-2"><CardTitle className="text-sm"><Puzzle className="w-4 h-4 inline mr-1" />Connectors</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dash?.total_connectors || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><Cable className="w-4 h-4 inline mr-1" />Active</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-green-500">{dash?.active_connectors || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><RefreshCw className="w-4 h-4 inline mr-1" />Syncs</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dash?.total_syncs || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><Webhook className="w-4 h-4 inline mr-1" />Webhooks</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dash?.total_webhooks || 0}</p></CardContent></Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">By Category</CardTitle></CardHeader>
          <CardContent><div className="space-y-2">{dash?.by_category && Object.entries(dash.by_category).map(([k, v]) => (
            <div key={k} className="flex items-center justify-between border-b pb-1 text-sm"><span className="font-medium capitalize">{k}</span><Badge variant="outline">{v as number}</Badge></div>
          ))}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Status</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm"><span>Last Sync</span><span className="font-medium">{dash?.last_sync_at ? new Date(dash.last_sync_at).toLocaleString() : "Never"}</span></div>
              <div className="flex items-center justify-between text-sm"><span>Recent Webhooks</span><span className="font-medium">{dash?.recent_webhooks || 0}</span></div>
              <div className="flex items-center justify-between text-sm"><span className="text-red-500">Errors</span><span className="font-medium">{dash?.total_errors || 0}</span></div>
            </div>
          </CardContent></Card>
      </div>
    </div>
  );
}

function CollabSessionsTab() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [title, setTitle] = useState(""); const [type, setType] = useState("meeting"); const [desc, setDesc] = useState(""); const [showForm, setShowForm] = useState(false);
  const fetchSessions = () => { v5CollaborationApi.listSessions().then((r) => setSessions(r.data)).catch(() => {}); };
  useEffect(() => { fetchSessions(); }, []);
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center"><p className="text-sm text-muted-foreground">{sessions.length} session(s)</p><Button onClick={() => setShowForm(!showForm)}><Video className="w-4 h-4 mr-1" />{showForm ? "Cancel" : "New Session"}</Button></div>
      {showForm && <Card className="border-violet-500/20">
        <CardHeader><CardTitle className="text-sm">Create Collaboration Session</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Input placeholder="Session title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <select value={type} onChange={(e) => setType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
            <option value="meeting">Meeting</option><option value="brainstorming">Brainstorming</option><option value="workshop">Workshop</option><option value="presentation">Presentation</option><option value="pair_programming">Pair Programming</option>
          </select>
          <Textarea placeholder="Description" value={desc} onChange={(e) => setDesc(e.target.value)} rows={2} />
          <Button onClick={async () => { if (!title.trim()) return; await v5CollaborationApi.createSession({ title: title.trim(), session_type: type, description: desc.trim() || null }); toast.success("Session created"); setTitle(""); setDesc(""); setShowForm(false); fetchSessions(); }}>Create</Button>
        </CardContent>
      </Card>}
      <div className="grid gap-4 md:grid-cols-3">
        {sessions.map((s) => (
          <Card key={s.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between"><CardTitle className="text-sm">{s.title}</CardTitle><Badge>{s.status}</Badge></div>
              <CardDescription>{s.session_type} | {s.started_at ? new Date(s.started_at).toLocaleString() : "Not started"}</CardDescription>
            </CardHeader>
            <CardContent><div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={async () => { await v5CollaborationApi.startSession(s.id); toast.success("Started"); fetchSessions(); }}><Play className="w-3 h-3 mr-1" />Start</Button>
              <Button size="sm" variant="outline" onClick={async () => { await v5CollaborationApi.endSession(s.id); toast.success("Ended"); fetchSessions(); }}>End</Button>
              <Button size="sm" variant="outline" onClick={async () => { const r = await v5CollaborationApi.joinSession(s.id); toast.success("Joined"); }}><User className="w-3 h-3 mr-1" />Join</Button>
            </div></CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function CollabMessagesTab() {
  const [sessionId, setSessionId] = useState(""); const [messages, setMessages] = useState<any[]>([]); const [content, setContent] = useState("");
  const [type, setType] = useState("text"); const [sessions, setSessions] = useState<any[]>([]);
  useEffect(() => { v5CollaborationApi.listSessions().then((r) => setSessions(r.data)).catch(() => {}); }, []);
  return (
    <Card className="border-violet-500/20">
      <CardHeader><CardTitle className="text-sm"><MessageCircle className="w-4 h-4 inline mr-1" />Multimodal Messages</CardTitle><CardDescription>Send text, voice, video, or image messages in sessions</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <select value={sessionId} onChange={(e) => { setSessionId(e.target.value); v5CollaborationApi.getMessages(e.target.value).then((r) => setMessages(r.data)).catch(() => {}); }} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
          <option value="">Select session</option>
          {sessions.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
        </select>
        <div className="border rounded-lg p-4 space-y-2 max-h-60 overflow-y-auto bg-muted/30">
          {messages.map((m) => (
            <div key={m.id} className="flex items-start gap-2 border-b pb-1 text-sm"><Badge variant="outline" className="text-xs">{m.message_type}</Badge><span className="text-xs text-muted-foreground">{m.content || "(media)"}</span></div>
          ))}
          {messages.length === 0 && <p className="text-xs text-muted-foreground text-center py-4">No messages</p>}
        </div>
        <div className="flex gap-2">
          <select value={type} onChange={(e) => setType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-28">
            <option value="text">Text</option><option value="voice">Voice</option><option value="video">Video</option><option value="image">Image</option>
          </select>
          <Input placeholder="Message content" value={content} onChange={(e) => setContent(e.target.value)} className="flex-1" />
          <Button onClick={async () => { if (!sessionId || !content.trim()) return; await v5CollaborationApi.sendMessage({ session_id: sessionId, message_type: type, content: content.trim() }); setContent(""); const r = await v5CollaborationApi.getMessages(sessionId); setMessages(r.data); }}>Send</Button>
        </div>
      </CardContent>
    </Card>
  );
}

function CollabWhiteboardTab() {
  const [sessionId, setSessionId] = useState(""); const [sessions, setSessions] = useState<any[]>([]); const [wbs, setWbs] = useState<any[]>([]); const [title, setTitle] = useState(""); const [suggestion, setSuggestion] = useState("");
  useEffect(() => { v5CollaborationApi.listSessions().then((r) => setSessions(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <Card className="border-violet-500/20">
        <CardHeader><CardTitle className="text-sm"><Pen className="w-4 h-4 inline mr-1" />AI-Powered Whiteboard</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <select value={sessionId} onChange={(e) => { setSessionId(e.target.value); v5CollaborationApi.listWhiteboards(e.target.value).then((r) => setWbs(r.data)).catch(() => {}); }} className="border rounded-lg px-3 py-2 text-sm bg-background flex-1">
              <option value="">Select session</option>
              {sessions.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
            </select>
            <Input placeholder="Board title" value={title} onChange={(e) => setTitle(e.target.value)} className="w-48" />
            <Button onClick={async () => { if (!sessionId || !title.trim()) return; await v5CollaborationApi.createWhiteboard({ session_id: sessionId, title: title.trim() }); toast.success("Board created"); setTitle(""); }}>Create</Button>
          </div>
        </CardContent>
      </Card>
      <div className="grid gap-4 md:grid-cols-3">
        {wbs.map((w) => (
          <Card key={w.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between"><CardTitle className="text-sm">{w.title}</CardTitle>{w.is_locked && <Badge>Locked</Badge>}</div>
              <CardDescription>{w.strokes?.length || 0} strokes, {w.shapes?.length || 0} shapes</CardDescription>
            </CardHeader>
            <CardContent><div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={async () => { await v5CollaborationApi.lockWhiteboard(w.id, !w.is_locked); toast.success(w.is_locked ? "Unlocked" : "Locked"); }}>{w.is_locked ? "Unlock" : "Lock"}</Button>
              <Button size="sm" variant="outline" onClick={async () => { const r = await v5CollaborationApi.aiWhiteboardSuggest(w.id, "Suggest improvements and next steps for this whiteboard"); setSuggestion(r.data.suggestion); }}>AI Suggest</Button>
            </div></CardContent>
          </Card>
        ))}
      </div>
      {suggestion && <Card><CardHeader><CardTitle className="text-sm">AI Suggestion</CardTitle></CardHeader><CardContent><p className="text-sm whitespace-pre-wrap">{suggestion}</p></CardContent></Card>}
    </div>
  );
}

function CollabScreenTab() {
  const [sessionId, setSessionId] = useState(""); const [sessions, setSessions] = useState<any[]>([]); const [shares, setShares] = useState<any[]>([]);
  useEffect(() => { v5CollaborationApi.listSessions().then((r) => setSessions(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <Card className="border-violet-500/20">
        <CardHeader><CardTitle className="text-sm"><Monitor className="w-4 h-4 inline mr-1" />Screen Sharing</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <select value={sessionId} onChange={(e) => setSessionId(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
            <option value="">Select session</option>
            {sessions.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
          </select>
          <div className="flex gap-2">
            <Button onClick={async () => { if (!sessionId) return; await v5CollaborationApi.startScreenShare(sessionId); toast.success("Screen share started"); }}><Monitor className="w-4 h-4 mr-1" />Start Sharing</Button>
            <Button variant="outline" onClick={async () => { if (!sessionId) return; const r = await v5CollaborationApi.listScreenShares(sessionId); setShares(r.data); }}>View Shares</Button>
          </div>
          {shares.map((s) => (
            <div key={s.id} className="flex items-center justify-between border-b pb-1 text-sm">
              <span>Share {s.id.slice(0, 8)}</span>
              <div className="flex gap-2"><Badge variant={s.is_active ? "default" : "outline"}>{s.is_active ? "Active" : "Ended"}</Badge><Button size="sm" variant="outline" onClick={async () => { await v5CollaborationApi.stopScreenShare(s.id); toast.success("Stopped"); }}>Stop</Button></div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function CollabRecordingsTab() {
  const [sessionId, setSessionId] = useState(""); const [sessions, setSessions] = useState<any[]>([]); const [recordings, setRecordings] = useState<any[]>([]);
  useEffect(() => { v5CollaborationApi.listSessions().then((r) => setSessions(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <Card className="border-violet-500/20">
        <CardHeader><CardTitle className="text-sm"><Radio className="w-4 h-4 inline mr-1" />Session Recordings</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <select value={sessionId} onChange={(e) => setSessionId(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background flex-1">
              <option value="">Select session</option>
              {sessions.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
            </select>
            <Button onClick={async () => { if (!sessionId) return; await v5CollaborationApi.startRecording(sessionId); toast.success("Recording started"); }}>Start Recording</Button>
            <Button variant="outline" onClick={async () => { if (!sessionId) return; const r = await v5CollaborationApi.listRecordings(sessionId); setRecordings(r.data); }}>List</Button>
          </div>
          <div className="space-y-2">{[...recordings].reverse().map((r) => (
            <div key={r.id} className="flex items-center justify-between border-b pb-1 text-sm">
              <span className="font-medium">{r.recording_type}</span>
              <div className="flex gap-2"><Badge>{r.status}</Badge><span className="text-xs text-muted-foreground">{r.duration_seconds ? `${r.duration_seconds}s` : "-"}</span><Button size="sm" variant="outline" onClick={async () => { const res = await v5CollaborationApi.transcribeRecording(r.id); toast.success("Transcribed"); }}>Transcribe</Button></div>
            </div>
          ))}</div>
        </CardContent>
      </Card>
    </div>
  );
}

function CollabInsightsTab() {
  const [sessionId, setSessionId] = useState(""); const [sessions, setSessions] = useState<any[]>([]); const [insights, setInsights] = useState<any>(null);
  useEffect(() => { v5CollaborationApi.listSessions().then((r) => setSessions(r.data)).catch(() => {}); }, []);
  return (
    <Card className="border-violet-500/20">
      <CardHeader><CardTitle className="text-sm"><Brain className="w-4 h-4 inline mr-1" />AI Meeting Intelligence</CardTitle><CardDescription>Generate summaries, action items, decisions, and sentiment from collaboration sessions</CardDescription></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <select value={sessionId} onChange={(e) => setSessionId(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background flex-1">
            <option value="">Select session</option>
            {sessions.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
          </select>
          <Button onClick={async () => { if (!sessionId) return; await v5CollaborationApi.generateInsights(sessionId); toast.success("Insights generated"); }}>Generate</Button>
          <Button variant="outline" onClick={async () => { if (!sessionId) return; const r = await v5CollaborationApi.getInsights(sessionId); setInsights(r.data); }}>View</Button>
        </div>
        {insights && <div className="space-y-3">
          {insights.summary && <div><p className="text-xs font-medium text-muted-foreground mb-1">Summary</p><div className="bg-muted p-3 rounded-lg text-sm">{insights.summary}</div></div>}
          {insights.action_items?.length > 0 && <div><p className="text-xs font-medium text-muted-foreground mb-1">Action Items ({insights.action_items.length})</p>{insights.action_items.map((a: any, i: number) => <div key={i} className="flex items-center gap-2 text-sm border-b pb-1"><CheckCircle className="w-3 h-3 text-green-500" /><span>{typeof a === 'string' ? a : a.text || JSON.stringify(a)}</span></div>)}</div>}
          {insights.sentiment && <div><p className="text-xs font-medium text-muted-foreground mb-1">Sentiment</p><Badge>{insights.sentiment}</Badge></div>}
        </div>}
      </CardContent>
    </Card>
  );
}

function CollabAgentsTab() {
  const [agents, setAgents] = useState<any[]>([]); const [sessions, setSessions] = useState<any[]>([]);
  const [name, setName] = useState(""); const [type, setType] = useState("assistant"); const [capabilities, setCapabilities] = useState(""); const [showForm, setShowForm] = useState(false);
  const [agentId, setAgentId] = useState(""); const [sessionId, setSessionId] = useState(""); const [message, setMessage] = useState(""); const [reply, setReply] = useState("");
  useEffect(() => { v5CollaborationApi.listAgents().then((r) => setAgents(r.data)); v5CollaborationApi.listSessions().then((r) => setSessions(r.data)); }, []);
  return (
    <div className="space-y-4">
      <Card className="border-violet-500/20">
        <CardHeader><CardTitle className="text-sm"><Headphones className="w-4 h-4 inline mr-1" />AI Collaboration Agents</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "New Agent"}</Button>
          {showForm && <div className="space-y-3">
            <Input placeholder="Agent name" value={name} onChange={(e) => setName(e.target.value)} />
            <select value={type} onChange={(e) => setType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background w-full">
              <option value="assistant">Assistant</option><option value="note_taker">Note Taker</option><option value="facilitator">Facilitator</option><option value="analyst">Analyst</option>
            </select>
            <Input placeholder="Capabilities (comma-separated)" value={capabilities} onChange={(e) => setCapabilities(e.target.value)} />
            <Button onClick={async () => { if (!name.trim()) return; await v5CollaborationApi.createAgent({ name: name.trim(), agent_type: type, capabilities: capabilities.split(",").map((s) => s.trim()), config: {} }); toast.success("Agent created"); setName(""); setCapabilities(""); setShowForm(false); }}>Create Agent</Button>
          </div>}
        </CardContent>
      </Card>
      <div className="grid gap-4 md:grid-cols-3">
        {agents.map((a) => (
          <Card key={a.id}>
            <CardHeader className="pb-2"><CardTitle className="text-sm">{a.name}</CardTitle><CardDescription>{a.agent_type} | {a.capabilities?.join(", ")}</CardDescription></CardHeader>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader><CardTitle className="text-sm">Chat with Agent in Session</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <select value={agentId} onChange={(e) => setAgentId(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background"><option value="">Select agent</option>{agents.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select>
            <select value={sessionId} onChange={(e) => setSessionId(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background"><option value="">Select session</option>{sessions.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}</select>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={async () => { if (!agentId || !sessionId) return; await v5CollaborationApi.joinAgentToSession({ agent_id: agentId, session_id: sessionId }); toast.success("Agent joined session"); }}>Join Session</Button>
          </div>
          <div className="flex gap-2">
            <Input placeholder="Message to agent" value={message} onChange={(e) => setMessage(e.target.value)} className="flex-1" />
            <Button onClick={async () => { if (!agentId || !sessionId || !message.trim()) return; const r = await v5CollaborationApi.chatWithAgent(agentId, sessionId, message.trim()); setReply(r.data.reply); setMessage(""); }}>Send</Button>
          </div>
          {reply && <div className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap">{reply}</div>}
        </CardContent>
      </Card>
    </div>
  );
}

function CollabDocumentsTab() {
  const [sessionId, setSessionId] = useState(""); const [sessions, setSessions] = useState<any[]>([]); const [docs, setDocs] = useState<any[]>([]);
  const [title, setTitle] = useState(""); const [docType, setDocType] = useState("document"); const [editResult, setEditResult] = useState("");
  useEffect(() => { v5CollaborationApi.listSessions().then((r) => setSessions(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <Card className="border-violet-500/20">
        <CardHeader><CardTitle className="text-sm"><FileText className="w-4 h-4 inline mr-1" />Collaborative Documents</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <select value={sessionId} onChange={(e) => { setSessionId(e.target.value); v5CollaborationApi.listDocumentCollabs(e.target.value).then((r) => setDocs(r.data)).catch(() => {}); }} className="border rounded-lg px-3 py-2 text-sm bg-background flex-1">
              <option value="">Select session</option>
              {sessions.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}
            </select>
            <Input placeholder="Doc title" value={title} onChange={(e) => setTitle(e.target.value)} />
            <select value={docType} onChange={(e) => setDocType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm bg-background">
              <option value="document">Document</option><option value="spreadsheet">Spreadsheet</option><option value="presentation">Presentation</option>
            </select>
            <Button onClick={async () => { if (!sessionId || !title.trim()) return; await v5CollaborationApi.createDocumentCollab(sessionId, "00000000-0000-0000-0000-000000000000", docType, title.trim()); toast.success("Doc created"); }}>Create</Button>
          </div>
          <div className="space-y-2">{[...docs].reverse().map((d) => (
            <div key={d.id} className="flex items-center justify-between border-b pb-1 text-sm">
              <span className="font-medium">{d.title}</span>
              <div className="flex gap-2"><Badge variant="outline">{d.document_type}</Badge><span className="text-xs text-muted-foreground">v{d.version}</span></div>
            </div>
          ))}</div>
        </CardContent>
      </Card>
    </div>
  );
}

function CollabDashboardTab() {
  const [dash, setDash] = useState<any>(null);
  useEffect(() => { v5CollaborationApi.getDashboard().then((r) => setDash(r.data)).catch(() => {}); }, []);
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-violet-500/20"><CardHeader className="pb-2"><CardTitle className="text-sm"><Video className="w-4 h-4 inline mr-1" />Sessions</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dash?.total_sessions || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><Activity className="w-4 h-4 inline mr-1" />Active</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-green-500">{dash?.active_sessions || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><User className="w-4 h-4 inline mr-1" />Participants</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dash?.total_participants || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><MessageCircle className="w-4 h-4 inline mr-1" />Messages</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dash?.total_messages || 0}</p></CardContent></Card>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><Radio className="w-4 h-4 inline mr-1" />Recordings</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dash?.total_recordings || 0}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm"><Pen className="w-4 h-4 inline mr-1" />Whiteboards</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold">{dash?.total_whiteboards || 0}</p></CardContent></Card>
      </div>
      {dash?.by_type && <Card>
        <CardHeader><CardTitle className="text-sm">By Session Type</CardTitle></CardHeader>
        <CardContent><div className="space-y-2">{Object.entries(dash.by_type).map(([k, v]) => (
          <div key={k} className="flex items-center justify-between border-b pb-1 text-sm"><span className="font-medium capitalize">{k}</span><Badge variant="outline">{v as number}</Badge></div>
        ))}</div></CardContent>
      </Card>}
    </div>
  );
}
