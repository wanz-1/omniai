"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  Activity,
  AlertTriangle,
  Brain,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  Loader2,
  MessageSquare,
  Shield,
  Star,
  ThumbsUp,
} from "lucide-react";
import { v6GovernanceApi } from "@/lib/api-client";

interface DashboardData {
  prompt_count: number;
  evaluation_count: number;
  review_count: number;
  feedback_count: number;
  decision_count: number;
  passed_evaluations: number;
  health_score: number;
}

interface ModelSummary {
  model: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
  avg_quality_score: number | null;
}

export default function GovernancePage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [models, setModels] = useState<ModelSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [dashRes, modelsRes] = await Promise.all([
          v6GovernanceApi.dashboard(),
          v6GovernanceApi.listModels(),
        ]);
        setDashboard(dashRes.data);
        setModels(modelsRes.data);
        setError(null);
      } catch (err: any) {
        setError(err?.message || "Failed to load governance data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <AlertTriangle className="w-12 h-12 text-destructive" />
        <p className="text-muted-foreground">{error}</p>
        <Button onClick={() => window.location.reload()}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Governance</h1>
        <p className="text-muted-foreground">
          Monitor and manage AI model quality, safety, and compliance
        </p>
      </div>

      {dashboard && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Health Score</CardTitle>
                <Shield className="w-4 h-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboard.health_score}%
                </div>
                <p className="text-xs text-muted-foreground">
                  Evaluation pass rate
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Evaluations</CardTitle>
                <ClipboardCheck className="w-4 h-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboard.evaluation_count}
                </div>
                <p className="text-xs text-muted-foreground">
                  {dashboard.passed_evaluations} passed
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Prompts</CardTitle>
                <FileText className="w-4 h-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboard.prompt_count}</div>
                <p className="text-xs text-muted-foreground">Registered prompt templates</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Reviews Pending</CardTitle>
                <MessageSquare className="w-4 h-4 text-amber-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboard.review_count}</div>
                <p className="text-xs text-muted-foreground">Awaiting human review</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Decisions</CardTitle>
                <Activity className="w-4 h-4 text-purple-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboard.decision_count}</div>
                <p className="text-xs text-muted-foreground">AI decisions logged</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Feedback</CardTitle>
                <ThumbsUp className="w-4 h-4 text-pink-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboard.feedback_count}</div>
                <p className="text-xs text-muted-foreground">User ratings collected</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Quality Score</CardTitle>
                <Star className="w-4 h-4 text-yellow-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboard.evaluation_count > 0
                    ? `${(dashboard.passed_evaluations / dashboard.evaluation_count * 5).toFixed(1)}`
                    : "N/A"}
                </div>
                <p className="text-xs text-muted-foreground">Out of 5.0</p>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Model Monitoring
          </CardTitle>
          <CardDescription>Performance and usage metrics by model</CardDescription>
        </CardHeader>
        <CardContent>
          {models.length === 0 ? (
            <p className="text-sm text-muted-foreground">No model data available yet</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium">Model</th>
                    <th className="text-right py-3 px-2 font-medium">Requests</th>
                    <th className="text-right py-3 px-2 font-medium">Success</th>
                    <th className="text-right py-3 px-2 font-medium">Failed</th>
                    <th className="text-right py-3 px-2 font-medium">Tokens</th>
                    <th className="text-right py-3 px-2 font-medium">Avg Latency</th>
                    <th className="text-right py-3 px-2 font-medium">Quality</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((m) => (
                    <tr key={m.model} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-2 font-medium">{m.model}</td>
                      <td className="text-right py-3 px-2">{m.total_requests}</td>
                      <td className="text-right py-3 px-2 text-green-600">{m.successful_requests}</td>
                      <td className="text-right py-3 px-2 text-red-500">{m.failed_requests}</td>
                      <td className="text-right py-3 px-2">{(m.total_tokens / 1000).toFixed(1)}k</td>
                      <td className="text-right py-3 px-2">{m.avg_latency_ms.toFixed(0)}ms</td>
                      <td className="text-right py-3 px-2">
                        {m.avg_quality_score != null ? (
                          <Badge variant={m.avg_quality_score >= 4 ? "success" : m.avg_quality_score >= 3 ? "warning" : "error"}>
                            {m.avg_quality_score.toFixed(2)}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
