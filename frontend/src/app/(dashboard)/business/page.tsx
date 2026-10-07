"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { businessApi } from "@/lib/api-client";
import { toast } from "sonner";
import {
  Briefcase, DollarSign, Users, Activity, TrendingUp, AlertTriangle,
  CheckCircle, Clock, FileText, MessageSquare, Loader2, Send, Building2
} from "lucide-react";

type AgentType = "business_manager" | "finance_officer" | "hr_manager" | "operations_manager" | "customer_success_manager";

interface DashboardData {
  reports: any[];
  alerts: any[];
  pending_approvals: any[];
  metrics_by_agent: Record<string, { count: number; avg_value: number }>;
}

const AGENTS: { type: AgentType; label: string; icon: any; color: string; description: string }[] = [
  { type: "business_manager", label: "Business Manager", icon: Briefcase, color: "text-blue-500", description: "Strategic analysis, KPIs, executive reports" },
  { type: "finance_officer", label: "Finance Officer", icon: DollarSign, color: "text-green-500", description: "Budgets, forecasts, financial reports" },
  { type: "hr_manager", label: "HR Manager", icon: Users, color: "text-purple-500", description: "CV screening, onboarding, policies" },
  { type: "operations_manager", label: "Operations Manager", icon: Activity, color: "text-orange-500", description: "Project tracking, workflows, risk" },
  { type: "customer_success_manager", label: "Customer Success", icon: MessageSquare, color: "text-pink-500", description: "Feedback, satisfaction, insights" },
];

export default function BusinessPage() {
  const [orgId, setOrgId] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeAgent, setActiveAgent] = useState<AgentType>("business_manager");
  const [query, setQuery] = useState("");
  const [queryResult, setQueryResult] = useState<string | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportResult, setReportResult] = useState<any>(null);
  const [tab, setTab] = useState<"chat" | "reports" | "approvals" | "knowledge" | "workflows">("chat");

  useEffect(() => {
    const loadOrg = async () => {
      try {
        const res = await fetch("/api/organizations");
        const orgs = await res.json();
        if (orgs.length > 0) {
          setOrgId(orgs[0].id);
          const dashboardRes = await businessApi.dashboard(orgs[0].id);
          setDashboard(dashboardRes.data);
        }
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    loadOrg();
  }, []);

  const loadDashboard = async (id: string) => {
    try {
      const res = await businessApi.dashboard(id);
      setDashboard(res.data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim() || !orgId) return;
    setQueryLoading(true);
    setQueryResult(null);
    try {
      const res = await businessApi.query({ agent_type: activeAgent, query, organization_id: orgId });
      setQueryResult(res.data.response);
    } catch {
      toast.error("Query failed");
    } finally {
      setQueryLoading(false);
    }
  };

  const handleGenerateReport = async (type: string) => {
    if (!orgId) return;
    setReportLoading(true);
    setReportResult(null);
    try {
      const res = await businessApi.generateReport({ agent_type: activeAgent, report_type: type, organization_id: orgId });
      setReportResult(res.data);
      toast.success("Report generated");
    } catch {
      toast.error("Report generation failed");
    } finally {
      setReportLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const agentConfig = AGENTS.find((a) => a.type === activeAgent)!;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Business AI</h1>
        <p className="text-muted-foreground mt-1">Autonomous business agents for your organization</p>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        {AGENTS.map((agent) => (
          <button
            key={agent.type}
            onClick={() => setActiveAgent(agent.type)}
            className={`p-4 rounded-xl border text-left transition-all duration-200 ${
              activeAgent === agent.type
                ? "border-primary bg-primary/5 ring-1 ring-primary"
                : "border-border bg-card hover:bg-muted/50"
            }`}
          >
            <agent.icon className={`w-6 h-6 mb-2 ${agent.color}`} />
            <p className="text-sm font-medium">{agent.label}</p>
            <p className="text-xs text-muted-foreground mt-1">{agent.description}</p>
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <agentConfig.icon className={`w-5 h-5 ${agentConfig.color}`} />
              <CardTitle className="text-lg">{agentConfig.label}</CardTitle>
            </div>
            <CardDescription>Ask questions and get AI-powered insights</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <input
                className="flex-1 h-10 rounded-lg border border-input bg-background px-3 py-2 text-sm"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleQuery()}
                placeholder={`Ask your ${agentConfig.label}...`}
              />
              <Button onClick={handleQuery} isLoading={queryLoading} size="sm">
                <Send className="w-4 h-4" />
              </Button>
            </div>

            {queryResult && (
              <Card className="bg-muted/30">
                <CardContent className="pt-4 text-sm whitespace-pre-wrap">
                  {queryResult}
                </CardContent>
              </Card>
            )}

            <div className="flex gap-2 flex-wrap">
              {["quarterly_review", "performance_analysis", "executive_summary", "budget_report", "financial_forecast", "hr_report", "operations_report", "customer_insights"].map((type) => (
                <Button
                  key={type}
                  variant="outline"
                  size="sm"
                  onClick={() => handleGenerateReport(type)}
                  isLoading={reportLoading}
                >
                  <FileText className="w-3 h-3 mr-1" />
                  {type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                </Button>
              ))}
            </div>

            {reportResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">{reportResult.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p className="font-medium">Summary</p>
                  <p className="text-muted-foreground whitespace-pre-wrap">{reportResult.summary}</p>
                  {reportResult.recommendations && reportResult.recommendations.length > 0 && (
                    <>
                      <p className="font-medium mt-2">Recommendations</p>
                      <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                        {reportResult.recommendations.map((r: string, i: number) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                Active Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard && dashboard.alerts.length > 0 ? (
                <div className="space-y-2">
                  {dashboard.alerts.slice(0, 5).map((alert: any, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-sm p-2 bg-muted/30 rounded-lg">
                      <Badge variant={alert.severity === "critical" ? "error" : alert.severity === "warning" ? "warning" : "default"}>
                        {alert.severity}
                      </Badge>
                      <span className="text-xs">{alert.title}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No active alerts</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-orange-500" />
                Pending Approvals
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard && dashboard.pending_approvals.length > 0 ? (
                <div className="space-y-2">
                  {dashboard.pending_approvals.slice(0, 5).map((a: any, i: number) => (
                    <div key={i} className="text-sm p-2 bg-muted/30 rounded-lg">
                      <p className="font-medium text-xs">{a.title}</p>
                      <p className="text-xs text-muted-foreground">{a.type} &middot; {a.priority}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No pending approvals</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                Agent Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard ? (
                <div className="space-y-2">
                  {Object.entries(dashboard.metrics_by_agent).map(([agent, data]: [string, any]) => (
                    <div key={agent} className="flex justify-between text-sm">
                      <span className="text-muted-foreground capitalize">{agent.replace(/_/g, " ")}</span>
                      <span className="font-medium">{data.count} metrics</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No metrics yet</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
