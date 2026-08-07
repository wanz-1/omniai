"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { activeAgentsApi } from "@/lib/api-client";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { toast } from "sonner";
import {
  ArrowLeft,
  Play,
  Pause,
  Square,
  Loader2,
  Activity,
  Clock,
  FileText,
  AlertTriangle,
  Terminal,
  BarChart3,
  Bot,
  Award,
  Plus,
  Trash2,
  Sparkles,
  BookOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface LogEntry {
  id: string;
  level: string;
  event_type: string;
  message: string;
  data?: any;
  created_at: string;
}

interface ActiveAgentDetail {
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
  last_error?: string | null;
  agent_name?: string;
  agent_role?: string;
  config?: any;
  created_at: string;
  started_at?: string | null;
}

export default function ActiveAgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [agent, setAgent] = useState<ActiveAgentDetail | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [logsLoading, setLogsLoading] = useState(false);
  const [skillsLoading, setSkillsLoading] = useState(false);
  const [taskTitle, setTaskTitle] = useState("");
  const [assigning, setAssigning] = useState(false);

  const loadAgent = useCallback(async () => {
    try {
      const res = await activeAgentsApi.get(id);
      setAgent(res.data);
    } catch {
      toast.error("Failed to load active agent");
      router.push("/active-agents");
    } finally {
      setLoading(false);
    }
  }, [id, router]);

  const loadLogs = useCallback(async () => {
    setLogsLoading(true);
    try {
      const res = await activeAgentsApi.logs(id, { limit: 100 });
      setLogs(res.data || []);
    } catch {
      // ignore
    } finally {
      setLogsLoading(false);
    }
  }, [id]);

  const loadSkills = useCallback(async () => {
    setSkillsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${base}/skills/active-agent/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSkills(data.skills || []);
      }
      // Also load recommendations
      const recRes = await fetch(`${base}/skills/active-agent/${id}/recommend`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (recRes.ok) {
        const recData = await recRes.json();
        setRecommendations(recData.recommendations || []);
      }
    } catch {
      // ignore
    } finally {
      setSkillsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      loadAgent();
      loadLogs();
      loadSkills();
      const interval = setInterval(() => {
        loadAgent();
        loadLogs();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [id, loadAgent, loadLogs, loadSkills]);

  const handleAction = async (action: "start" | "stop" | "pause" | "resume") => {
    try {
      await activeAgentsApi[action](id);
      toast.success(`Agent ${action}ed`);
      loadAgent();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || `Failed to ${action}`);
    }
  };

  const handleAssignTask = async () => {
    if (!taskTitle.trim()) {
      toast.error("Task title required");
      return;
    }
    setAssigning(true);
    try {
      await activeAgentsApi.assignTask(id, {
        title: taskTitle,
        description: `Manual task assigned via UI at ${new Date().toISOString()}`,
        priority: 2,
      });
      toast.success("Task assigned");
      setTaskTitle("");
      loadLogs();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to assign task");
    } finally {
      setAssigning(false);
    }
  };

  const handleTrainSkill = async (skillName: string) => {
    try {
      const token = localStorage.getItem("access_token");
      const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${base}/skills/active-agent/${id}/train`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ skill_name: skillName, task_complexity: 3 }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message || `Trained ${skillName}`);
        loadSkills();
        loadLogs();
      } else {
        toast.error(data.detail || "Failed to train");
      }
    } catch {
      toast.error("Failed to train skill");
    }
  };

  const handleAddSkill = async (skillId: string) => {
    try {
      const token = localStorage.getItem("access_token");
      const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${base}/skills/active-agent/${id}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ skill_id: skillId, proficiency: 5 }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(`Added skill: ${data.name}`);
        loadSkills();
        loadLogs();
      } else {
        toast.error(data.detail || "Failed to add skill");
      }
    } catch {
      toast.error("Failed to add skill");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!agent) return null;

  const statusColor = (s: string) => {
    switch (s) {
      case "running":
        return "bg-green-500 text-white animate-pulse";
      case "idle":
        return "bg-blue-500 text-white";
      case "paused":
        return "bg-yellow-500 text-white";
      case "error":
        return "bg-red-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => router.push("/active-agents")}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back
        </Button>
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Bot className="w-5 h-5" />
          {agent.name}
        </h1>
        <Badge className={cn("text-xs", statusColor(agent.status))}>{agent.status}</Badge>
        <Badge variant="outline" className="text-xs">
          {agent.mode}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Control
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {(agent.status === "running" || agent.status === "idle") && (
                  <>
                    <Button size="sm" variant="outline" onClick={() => handleAction("pause")}>
                      <Pause className="w-4 h-4 mr-1" />
                      Pause
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleAction("stop")}>
                      <Square className="w-4 h-4 mr-1" />
                      Stop
                    </Button>
                  </>
                )}
                {agent.status === "paused" && (
                  <>
                    <Button size="sm" onClick={() => handleAction("resume")}>
                      <Play className="w-4 h-4 mr-1" />
                      Resume
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleAction("stop")}>
                      <Square className="w-4 h-4 mr-1" />
                      Stop
                    </Button>
                  </>
                )}
                {["stopped", "error"].includes(agent.status) && (
                  <Button size="sm" onClick={() => handleAction("start")}>
                    <Play className="w-4 h-4 mr-1" />
                    Start
                  </Button>
                )}
                <Button size="sm" variant="ghost" onClick={loadAgent}>
                  Refresh
                </Button>
              </div>

              {agent.last_error && (
                <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 rounded p-3 text-sm flex gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <span>{agent.last_error}</span>
                </div>
              )}

              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-muted/50 rounded p-3">
                  <div className="text-xl font-bold">{agent.run_count}</div>
                  <div className="text-xs text-muted-foreground">Runs</div>
                </div>
                <div className="bg-muted/50 rounded p-3">
                  <div className="text-xl font-bold">{agent.total_tasks_completed}</div>
                  <div className="text-xs text-muted-foreground">Tasks</div>
                </div>
                <div className="bg-muted/50 rounded p-3">
                  <div className="text-xl font-bold">{agent.total_tokens_used}</div>
                  <div className="text-xs text-muted-foreground">Tokens</div>
                </div>
              </div>

              <div className="text-xs text-muted-foreground space-y-1">
                <div className="flex justify-between">
                  <span>Agent Profile:</span>
                  <span className="font-medium">{agent.agent_name} ({agent.agent_role})</span>
                </div>
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span>{new Date(agent.created_at).toLocaleString()}</span>
                </div>
                {agent.started_at && (
                  <div className="flex justify-between">
                    <span>Started:</span>
                    <span>{new Date(agent.started_at).toLocaleString()}</span>
                  </div>
                )}
                {agent.heartbeat_at && (
                  <div className="flex justify-between">
                    <span>Last Heartbeat:</span>
                    <span>{new Date(agent.heartbeat_at).toLocaleString()}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Assign Task */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Assign Task
              </CardTitle>
            </CardHeader>
            <CardContent className="flex gap-2">
              <input
                value={taskTitle}
                onChange={(e) => setTaskTitle(e.target.value)}
                placeholder="e.g., Research latest AI news and summarize"
                className="flex-1 px-3 py-2 rounded-lg border border-border bg-background text-sm"
                onKeyDown={(e) => e.key === "Enter" && handleAssignTask()}
              />
              <Button onClick={handleAssignTask} disabled={assigning || !taskTitle.trim()}>
                {assigning ? <Loader2 className="w-4 h-4 animate-spin" /> : "Assign"}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Stats & Config */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Live Stats
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status</span>
                <Badge className={cn("text-[10px]", statusColor(agent.status))}>{agent.status}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Mode</span>
                <span>{agent.mode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Active</span>
                <span>{agent.is_active ? "Yes" : "No"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Heartbeat</span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {agent.heartbeat_at ? new Date(agent.heartbeat_at).toLocaleTimeString() : "—"}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Config</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-[200px]">
                {JSON.stringify(agent.config || {}, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Logs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Terminal className="w-4 h-4" />
            Live Logs
          </CardTitle>
          <Button size="sm" variant="ghost" onClick={loadLogs} disabled={logsLoading}>
            {logsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Refresh"}
          </Button>
        </CardHeader>
        <CardContent>
          <div className="bg-black text-green-400 font-mono text-xs rounded p-3 max-h-[400px] overflow-auto space-y-1">
            {logs.length === 0 ? (
              <div className="text-muted-foreground">No logs yet...</div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="flex gap-2">
                  <span className="text-gray-500">[{new Date(log.created_at).toLocaleTimeString()}]</span>
                  <span
                    className={cn(
                      "px-1 rounded text-[10px]",
                      log.level === "error" ? "bg-red-900 text-red-200" : log.level === "warn" ? "bg-yellow-900 text-yellow-200" : "bg-gray-800"
                    )}
                  >
                    {log.level}
                  </span>
                  <span className="text-blue-300">{log.event_type}:</span>
                  <span className="flex-1">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Skills */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Award className="w-4 h-4" />
              Skills ({skills.length})
              {skillsLoading && <Loader2 className="w-4 h-4 animate-spin ml-2" />}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[400px] overflow-auto">
            {skills.length === 0 ? (
              <div className="text-sm text-muted-foreground">No skills yet. Add from recommendations.</div>
            ) : (
              skills.map((skill: any) => (
                <div key={skill.id} className="flex items-center justify-between p-2 rounded border bg-muted/30">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span>{skill.icon || "🔧"}</span>
                      <span className="font-medium text-sm">{skill.name}</span>
                      <Badge variant="outline" className="text-[10px]">
                        Lvl {skill.proficiency}/10
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground line-clamp-1">{skill.description}</div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                      <div
                        className="bg-primary h-1.5 rounded-full transition-all"
                        style={{ width: `${(skill.proficiency / 10) * 100}%` }}
                      />
                    </div>
                  </div>
                  <Button size="sm" variant="ghost" className="h-7 ml-2" onClick={() => handleTrainSkill(skill.name)}>
                    <Sparkles className="w-3 h-3 mr-1" />
                    Train
                  </Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              Recommended Skills
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[400px] overflow-auto">
            {recommendations.length === 0 ? (
              <div className="text-sm text-muted-foreground">No recommendations. Complete tasks to get suggestions.</div>
            ) : (
              recommendations.map((rec: any) => (
                <div key={rec.id} className="p-2 rounded border hover:border-primary/50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span>{rec.icon}</span>
                        <span className="font-medium text-sm">{rec.name}</span>
                        <Badge className="text-[10px] bg-blue-500/10 text-blue-600 border-blue-200">{rec.category}</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground line-clamp-2">{rec.description}</div>
                      {rec.prerequisites?.length > 0 && (
                        <div className="text-[10px] text-muted-foreground mt-1">
                          Needs: {rec.prerequisites.join(", ")}
                        </div>
                      )}
                    </div>
                    <Button size="sm" variant="outline" className="h-7 ml-2" onClick={() => handleAddSkill(rec.id)}>
                      <Plus className="w-3 h-3 mr-1" />
                      Add
                    </Button>
                  </div>
                </div>
              ))
            )}
            {recommendations.length > 0 && (
              <Button
                size="sm"
                variant="secondary"
                className="w-full mt-2"
                onClick={async () => {
                  try {
                    const token = localStorage.getItem("access_token");
                    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
                    const res = await fetch(`${base}/skills/active-agent/${id}/auto-learn`, {
                      method: "POST",
                      headers: { Authorization: `Bearer ${token}` },
                    });
                    const data = await res.json();
                    if (res.ok) {
                      toast.success(data.message || "Auto-learned skills");
                      // @ts-ignore
                      loadSkills();
                    } else {
                      toast.error(data.detail || "Failed");
                    }
                  } catch {
                    toast.error("Failed to auto-learn");
                  }
                }}
              >
                <Sparkles className="w-4 h-4 mr-1" />
                Auto-Learn Top 2
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
