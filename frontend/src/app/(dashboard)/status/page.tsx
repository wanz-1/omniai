"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  CheckCircle, XCircle, AlertTriangle, Loader2,
  Activity, Database, Brain, Globe, Cpu, Server,
  RefreshCw,
} from "lucide-react";

type ServiceStatus = "healthy" | "degraded" | "unhealthy" | "loading";

interface StatusResponse {
  status: string;
  version: string;
  timestamp: string;
  checks: { name: string; healthy: boolean; detail: string; latency_ms?: number }[];
}

const serviceIcons: Record<string, React.ElementType> = {
  database: Database,
  redis: Server,
  storage: Globe,
  ai_router: Brain,
  app: Cpu,
};

export default function StatusPage() {
  const [health, setHealth] = useState<StatusResponse | null>(null);
  const [ready, setReady] = useState<StatusResponse | null>(null);
  const [live, setLive] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const [healthRes, readyRes, liveRes] = await Promise.all([
        fetch("/health"),
        fetch("/ready"),
        fetch("/live"),
      ]);
      setHealth(healthRes.ok ? await healthRes.json() : null);
      setReady(readyRes.ok ? await readyRes.json() : null);
      setLive(liveRes.ok ? await liveRes.json() : null);
      setError(null);
    } catch (err) {
      setError("Failed to fetch system status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string | undefined): { icon: React.ElementType; label: string; variant: string } => {
    if (!status) return { icon: XCircle, label: "Unknown", variant: "destructive" };
    switch (status) {
      case "healthy":
        return { icon: CheckCircle, label: "Operational", variant: "success" };
      case "degraded":
        return { icon: AlertTriangle, label: "Degraded", variant: "warning" };
      default:
        return { icon: XCircle, label: "Down", variant: "destructive" };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const mainStatus = health?.status || ready?.status || "unknown";
  const badge = getStatusBadge(mainStatus);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Status</h1>
          <p className="text-muted-foreground mt-1">
            Real-time operational status of all OmniAI services
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={badge.variant as any} className="text-sm px-3 py-1">
            <badge.icon className="w-4 h-4 mr-1 inline" />
            {badge.label}
          </Badge>
          <button onClick={fetchStatus} className="p-2 rounded-lg hover:bg-muted transition-colors">
            <RefreshCw className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </div>

      {ready?.checks && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {ready.checks.map((check) => {
            const Icon = serviceIcons[check.name] || Activity;
            return (
              <Card key={check.name}>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <div className="flex items-center gap-2">
                    <Icon className="w-5 h-5 text-muted-foreground" />
                    <CardTitle className="text-sm font-medium capitalize">
                      {check.name.replace(/_/g, " ")}
                    </CardTitle>
                  </div>
                  {check.healthy ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                </CardHeader>
                <CardContent>
                  <CardDescription className={check.healthy ? "text-green-600" : "text-red-600"}>
                    {check.detail}
                  </CardDescription>
                  {check.latency_ms && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {check.latency_ms}ms
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-muted-foreground" />
              <CardTitle className="text-sm">Health</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {getStatusBadge(health?.status).label === "Operational" ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : (
                <XCircle className="w-4 h-4 text-red-500" />
              )}
              <span className="text-lg font-semibold capitalize">{health?.status || "unknown"}</span>
            </div>
            {health?.timestamp && (
              <p className="text-xs text-muted-foreground mt-2">
                Last checked: {new Date(health.timestamp).toLocaleTimeString()}
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-muted-foreground" />
              <CardTitle className="text-sm">Readiness</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {getStatusBadge(ready?.status).label === "Operational" ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : ready?.status === "degraded" ? (
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
              ) : (
                <XCircle className="w-4 h-4 text-red-500" />
              )}
              <span className="text-lg font-semibold capitalize">{ready?.status || "unknown"}</span>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-muted-foreground" />
              <CardTitle className="text-sm">Liveness</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {getStatusBadge(live?.status).label === "Operational" ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : (
                <XCircle className="w-4 h-4 text-red-500" />
              )}
              <span className="text-lg font-semibold capitalize">{live?.status || "unknown"}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Incident History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-muted-foreground">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span>No recent incidents</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
