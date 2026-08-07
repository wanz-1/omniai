"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Bot,
  Plus,
  Loader2,
  Play,
  Pause,
  Square,
  Activity,
  Clock,
  Zap,
  AlertCircle,
  BarChart3,
  FileText,
  Settings,
  Trash2,
} from "lucide-react";
import { activeAgentsApi, agentsApi, ACTIVE_AGENT_TEMPLATES } from "@/lib/api-client";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";

interface ActiveAgent {
  id: string;
  name: string;
  agent_id: string;
  status: string;
  mode: string;
  is_active: boolean;
  heartbeat_at: string | null;
  run_count: number;
  total_tasks_completed: number;
  total_tokens_used: number;
  agent_name?: string;
  agent_role?: string;
  last_error?: string | null;
  created_at: string;
}

interface Stats {
  total_active: number;
  running: number;
  idle: number;
  paused: number;
  error: number;
  total_runs: number;
  total_tasks_completed: number;
}

export default function ActiveAgentsPage() {
  const router = useRouter();
  const [activeAgents, setActiveAgents] = useState<ActiveAgent[]>([]);
  const [agents, setAgents] = useState<any[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [selectedMode, setSelectedMode] = useState<string>("continuous");
  const [creating, setCreating] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [activeRes, agentsRes, statsRes] = await Promise.all([
        activeAgentsApi.list(),
        agentsApi.list(),
        activeAgentsApi.stats(),
      ]);
      setActiveAgents(activeRes.data || []);
      setAgents(agentsRes.data || []);
      setStats(statsRes.data || null);
    } catch (err: any) {
      toast.error("Failed to load active agents");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    // Poll every 10 seconds for active agents status
    const interval = setInterval(() => {
      activeAgentsApi.list().then((res) => setActiveAgents(res.data || [])).catch(() => {});
      activeAgentsApi.stats().then((res) => setStats(res.data || null)).catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleCreate = async (template?: typeof ACTIVE_AGENT_TEMPLATES[number]) => {
    setCreating(true);
    try {
      if (template) {
        // Use from-template endpoint which auto-creates base agent if needed
        const res = await activeAgentsApi.createFromTemplate(template.id, {
          agent_id: selectedAgentId || undefined,
          name: `${template.name} - Active`,
        });
        toast.success(`Active agent deployed: ${res.data.name} 🚀`);
      } else {
        if (!selectedAgentId) {
          toast.error("Select a base agent");
          return;
        }
        const payload = {
          agent_id: selectedAgentId,
          mode: selectedMode,
          cron_schedule: selectedMode === "scheduled" ? "*/5 * * * *" : undefined,
        };
        const res = await activeAgentsApi.create(payload);
        toast.success(`Active agent created: ${res.data.name}`);
      }
      setShowCreate(false);
      setSelectedAgentId("");
      loadData();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to create active agent");
    } finally {
      setCreating(false);
    }
  };

  const handleAction = async (id: string, action: "start" | "stop" | "pause" | "resume") => {
    try {
      await activeAgentsApi[action](id);
      toast.success(`Agent ${action}ed`);
      loadData();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || `Failed to ${action}`);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this active agent? This will stop it if running.")) return;
    try {
      await activeAgentsApi.delete(id);
      toast.success("Active agent deleted");
      loadData();
    } catch {
      toast.error("Failed to delete");
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-500 text-white animate-pulse";
      case "idle":
        return "bg-blue-500 text-white";
      case "paused":
        return "bg-yellow-500 text-white";
      case "error":
        return "bg-red-500 text-white";
      case "starting":
        return "bg-purple-500 text-white animate-pulse";
      case "stopped":
        return "bg-gray-500 text-white";
      default:
        return "bg-gray-200 text-gray-800";
    }
  };

  const modeIcon = (mode: string) => {
    switch (mode) {
      case "continuous":
        return <Activity className="w-3 h-3" />;
      case "scheduled":
        return <Clock className="w-3 h-3" />;
      case "on_demand":
        return <Zap className="w-3 h-3" />;
      default:
        return <Bot className="w-3 h-3" />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="w-6 h-6 text-green-500" />
            Active AI Agents
          </h1>
          <p className="text-muted-foreground mt-1">
            Autonomous agents running 24/7 — research, monitoring, support, and more
          </p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="w-4 h-4 mr-1.5" />
          New Active Agent
        </Button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          <Card className="p-3">
            <div className="text-2xl font-bold">{stats.total_active}</div>
            <div className="text-xs text-muted-foreground">Total Active</div>
          </Card>
          <Card className="p-3 bg-green-50 dark:bg-green-950/20 border-green-200">
            <div className="text-2xl font-bold text-green-600">{stats.running}</div>
            <div className="text-xs text-muted-foreground">Running</div>
          </Card>
          <Card className="p-3 bg-blue-50 dark:bg-blue-950/20 border-blue-200">
            <div className="text-2xl font-bold text-blue-600">{stats.idle}</div>
            <div className="text-xs text-muted-foreground">Idle</div>
          </Card>
          <Card className="p-3 bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200">
            <div className="text-2xl font-bold text-yellow-600">{stats.paused}</div>
            <div className="text-xs text-muted-foreground">Paused</div>
          </Card>
          <Card className="p-3 bg-red-50 dark:bg-red-950/20 border-red-200">
            <div className="text-2xl font-bold text-red-600">{stats.error}</div>
            <div className="text-xs text-muted-foreground">Error</div>
          </Card>
          <Card className="p-3">
            <div className="text-2xl font-bold">{stats.total_runs}</div>
            <div className="text-xs text-muted-foreground">Total Runs</div>
          </Card>
          <Card className="p-3">
            <div className="text-2xl font-bold">{stats.total_tasks_completed}</div>
            <div className="text-xs text-muted-foreground">Tasks Done</div>
          </Card>
        </div>
      )}

      {/* Create Form */}
      {showCreate && (
        <Card className="border-primary/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="w-5 h-5" />
              Deploy New Active Agent
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Templates */}
            <div>
              <label className="text-sm font-medium">Quick Start Templates</label>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mt-2">
                {ACTIVE_AGENT_TEMPLATES.map((tpl) => (
                  <div
                    key={tpl.id}
                    className="p-3 rounded-lg border hover:border-primary cursor-pointer transition-all hover:shadow-md group"
                    onClick={() => handleCreate(tpl as any)}
                  >
                    <div className="text-2xl mb-1 group-hover:scale-110 transition-transform">{tpl.icon}</div>
                    <div className="font-medium text-sm">{tpl.name}</div>
                    <div className="text-xs text-muted-foreground line-clamp-2">{tpl.description}</div>
                    <div className="flex gap-1 mt-2">
                      <Badge variant="outline" className="text-[10px]">
                        {tpl.defaultMode}
                      </Badge>
                      {(tpl as any).isSystem && (
                        <Badge className="text-[10px] bg-purple-500 text-white">SYSTEM</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t pt-4 space-y-3">
              <div>
                <label className="text-sm font-medium">Base Agent Profile *</label>
                <select
                  value={selectedAgentId}
                  onChange={(e) => setSelectedAgentId(e.target.value)}
                  className="w-full mt-1 p-2 rounded-lg border border-border bg-background text-sm"
                >
                  <option value="">Select an agent...</option>
                  {agents.map((a: any) => (
                    <option key={a.id} value={a.id}>
                      {a.name} ({a.role})
                    </option>
                  ))}
                </select>
                {agents.length === 0 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    No agents found. <button onClick={() => router.push("/agents/new")} className="text-primary underline">Create one</button>
                  </p>
                )}
              </div>

              <div>
                <label className="text-sm font-medium">Mode</label>
                <select
                  value={selectedMode}
                  onChange={(e) => setSelectedMode(e.target.value)}
                  className="w-full mt-1 p-2 rounded-lg border border-border bg-background text-sm"
                >
                  <option value="continuous">Continuous (always on)</option>
                  <option value="on_demand">On Demand (task triggered)</option>
                  <option value="scheduled">Scheduled (cron)</option>
                  <option value="event_driven">Event Driven (webhooks)</option>
                </select>
              </div>

              <div className="flex gap-2">
                <Button onClick={() => handleCreate()} disabled={creating || !selectedAgentId}>
                  {creating ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : <Play className="w-4 h-4 mr-1.5" />}
                  Deploy & Start
                </Button>
                <Button variant="outline" onClick={() => setShowCreate(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Agents List */}
      {isLoading ? (
        <div className="flex items-center justify-center min-h-[30vh]">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : activeAgents.length === 0 ? (
        <Card className="p-8 text-center">
          <Activity className="w-16 h-16 text-primary/20 mx-auto mb-4" />
          <h3 className="text-lg font-medium">No active agents running</h3>
          <p className="text-sm text-muted-foreground mt-1 mb-4 max-w-md mx-auto">
            Deploy an agent to run autonomously 24/7. It will handle tasks, monitor data, and take actions without manual intervention.
          </p>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="w-4 h-4 mr-1.5" />
            Deploy First Active Agent
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {activeAgents.map((aa) => (
            <Card key={aa.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-base flex items-center gap-2">
                      <span className="text-lg">{ACTIVE_AGENT_TEMPLATES.find((t) => aa.name.toLowerCase().includes(t.name.toLowerCase().split(" ")[0]))?.icon || "🤖"}</span>
                      {aa.name}
                    </CardTitle>
                    <div className="text-xs text-muted-foreground mt-1">
                      Base: {aa.agent_name || aa.agent_id.slice(0, 8)} • {aa.agent_role || "agent"}
                    </div>
                  </div>
                  <Badge className={cn("text-[10px]", statusColor(aa.status))}>{aa.status}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-xs">
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-muted">
                    {modeIcon(aa.mode)} {aa.mode}
                  </span>
                  {aa.heartbeat_at && (
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(aa.heartbeat_at).toLocaleTimeString()}
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-muted/50 rounded p-2">
                    <div className="font-bold text-sm">{aa.run_count}</div>
                    <div className="text-muted-foreground">Runs</div>
                  </div>
                  <div className="bg-muted/50 rounded p-2">
                    <div className="font-bold text-sm">{aa.total_tasks_completed}</div>
                    <div className="text-muted-foreground">Tasks</div>
                  </div>
                  <div className="bg-muted/50 rounded p-2">
                    <div className="font-bold text-sm">{aa.total_tokens_used}</div>
                    <div className="text-muted-foreground">Tokens</div>
                  </div>
                </div>

                {aa.last_error && (
                  <div className="text-xs bg-red-50 dark:bg-red-950/30 border border-red-200 rounded p-2 flex gap-2">
                    <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                    <span className="line-clamp-2">{aa.last_error}</span>
                  </div>
                )}

                <div className="flex flex-wrap gap-1.5">
                  {aa.status === "running" || aa.status === "idle" ? (
                    <>
                      <Button size="sm" variant="outline" onClick={() => handleAction(aa.id, "pause")} className="h-7 text-xs">
                        <Pause className="w-3 h-3 mr-1" />
                        Pause
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleAction(aa.id, "stop")} className="h-7 text-xs">
                        <Square className="w-3 h-3 mr-1" />
                        Stop
                      </Button>
                    </>
                  ) : aa.status === "paused" ? (
                    <>
                      <Button size="sm" onClick={() => handleAction(aa.id, "resume")} className="h-7 text-xs">
                        <Play className="w-3 h-3 mr-1" />
                        Resume
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleAction(aa.id, "stop")} className="h-7 text-xs">
                        <Square className="w-3 h-3 mr-1" />
                        Stop
                      </Button>
                    </>
                  ) : (
                    <Button size="sm" onClick={() => handleAction(aa.id, "start")} className="h-7 text-xs">
                      <Play className="w-3 h-3 mr-1" />
                      Start
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => router.push(`/active-agents/${aa.id}`)} className="h-7 text-xs">
                    <FileText className="w-3 h-3 mr-1" />
                    Logs
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => handleDelete(aa.id)} className="h-7 text-xs text-red-600">
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Help Section */}
      <Card className="bg-gradient-to-br from-primary/5 to-purple-500/5 border-primary/20">
        <CardContent className="p-4">
          <h4 className="font-medium flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            What are Active AI Agents?
          </h4>
          <p className="text-sm text-muted-foreground mt-1">
            Unlike regular agents that respond on-demand, <strong>Active Agents</strong> run continuously in the background,
            autonomously handling tasks, monitoring data, and taking actions 24/7. They have their own lifecycle, heartbeat,
            logs, and can be deployed in continuous, scheduled, or event-driven modes.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3 text-xs">
            <div className="flex items-center gap-1.5"><Activity className="w-3 h-3" /> Continuous loop</div>
            <div className="flex items-center gap-1.5"><Clock className="w-3 h-3" /> Cron scheduling</div>
            <div className="flex items-center gap-1.5"><Zap className="w-3 h-3" /> Auto task pickup</div>
            <div className="flex items-center gap-1.5"><Settings className="w-3 h-3" /> Celery & asyncio</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
