"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft, Save, Bot, MessageSquare, Brain, Wrench, Workflow, ListTodo, BarChart3, Store, Loader2, Settings, Play,
} from "lucide-react";
import { agentsApi } from "@/lib/api-client";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { AgentChatConsole } from "@/modules/agents/AgentChatConsole";
import { AgentSkillsEditor } from "@/modules/agents/AgentSkillsEditor";
import { AgentToolsConfig } from "@/modules/agents/AgentToolsConfig";
import { AgentMemoryBrowser } from "@/modules/agents/AgentMemoryBrowser";
import { WorkflowBuilder } from "@/modules/agents/WorkflowBuilder";
import { TaskList } from "@/modules/agents/TaskList";
import { AgentAnalyticsPanel } from "@/modules/agents/AgentAnalytics";

type TabId = "chat" | "skills" | "tools" | "memory" | "workflows" | "tasks" | "analytics" | "settings";

interface AgentData {
  id: string;
  name: string;
  role: string;
  description?: string;
  system_prompt?: string;
  model: string;
  temperature: number;
  status: string;
  is_template: boolean;
  icon?: string;
  color?: string;
  published?: boolean;
  skills: any[];
  tools: any[];
  workflows: any[];
  memories?: any[];
  tasks?: any[];
  created_at: string;
}

export default function AgentWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<AgentData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isExecuting, setIsExecuting] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("chat");

  useEffect(() => {
    if (agentId) loadAgent();
  }, [agentId]);

  const loadAgent = async () => {
    setIsLoading(true);
    try {
      const res = await agentsApi.get(agentId);
      setAgent(res.data);
    } catch {
      toast.error("Failed to load agent");
      router.push("/agents");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!agent) return;
    setIsSaving(true);
    try {
      await agentsApi.update(agent.id, {
        name: agent.name,
        role: agent.role,
        description: agent.description,
        system_prompt: agent.system_prompt,
        model: agent.model,
        temperature: agent.temperature,
      });
      toast.success("Saved");
    } catch {
      toast.error("Save failed");
    } finally {
      setIsSaving(false);
    }
  };

  const handlePublish = async () => {
    if (!agent) return;
    try {
      await agentsApi.publish(agent.id, { marketplace_listed: false });
      toast.success("Agent published!");
      loadAgent();
    } catch {
      toast.error("Publish failed");
    }
  };

  const handleAddSkill = async (skill: any) => {
    if (!agent) return;
    try {
      const res = await agentsApi.skills.add(agent.id, skill);
      setAgent({ ...agent, skills: [...agent.skills, res.data] });
      toast.success("Skill added");
    } catch {
      toast.error("Failed to add skill");
    }
  };

  const handleDeleteSkill = async (skillId: string) => {
    if (!agent) return;
    try {
      await agentsApi.skills.delete(agent.id, skillId);
      setAgent({ ...agent, skills: agent.skills.filter((s: any) => s.id !== skillId) });
    } catch {
      toast.error("Failed to delete skill");
    }
  };

  const handleAddTool = async (tool: any) => {
    if (!agent) return;
    try {
      const res = await agentsApi.tools.add(agent.id, tool);
      setAgent({ ...agent, tools: [...agent.tools, res.data] });
      toast.success("Tool added");
    } catch {
      toast.error("Failed to add tool");
    }
  };

  const handleDeleteTool = async (toolId: string) => {
    if (!agent) return;
    try {
      await agentsApi.tools.delete(agent.id, toolId);
      setAgent({ ...agent, tools: agent.tools.filter((t: any) => t.id !== toolId) });
    } catch {
      toast.error("Failed to delete tool");
    }
  };

  const handleToggleTool = async (toolId: string) => {
    if (!agent) return;
    const tool = agent.tools.find((t: any) => t.id === toolId);
    if (!tool) return;
    try {
      await agentsApi.tools.add(agent.id, { ...tool, enabled: !tool.enabled });
      setAgent({
        ...agent,
        tools: agent.tools.map((t: any) => t.id === toolId ? { ...t, enabled: !t.enabled } : t),
      });
    } catch {
      toast.error("Failed to toggle tool");
    }
  };

  const handleDeleteMemory = async (memoryId: string) => {
    if (!agent) return;
    try {
      await agentsApi.memories.delete(agent.id, memoryId);
      setAgent({
        ...agent,
        memories: (agent.memories || []).filter((m: any) => m.id !== memoryId),
      });
    } catch {
      toast.error("Failed to delete memory");
    }
  };

  const handleClearMemories = async () => {
    if (!agent) return;
    try {
      await agentsApi.memories.clear(agent.id);
      setAgent({ ...agent, memories: [] });
      toast.success("Memories cleared");
    } catch {
      toast.error("Failed to clear memories");
    }
  };

  const handleAddTask = async (data: any) => {
    if (!agent) return;
    try {
      const res = await agentsApi.tasks.create(agent.id, data);
      setAgent({ ...agent, tasks: [...(agent.tasks || []), res.data] });
    } catch {
      toast.error("Failed to create task");
    }
  };

  const handleExecuteTask = async (taskId: string) => {
    if (!agent) return;
    setIsExecuting(taskId);
    try {
      const res = await agentsApi.tasks.execute(agent.id, taskId);
      setAgent({
        ...agent,
        tasks: (agent.tasks || []).map((t: any) => t.id === taskId ? res.data : t),
      });
      toast.success("Task completed!");
    } catch {
      toast.error("Task execution failed");
    } finally {
      setIsExecuting(null);
    }
  };

  const handleSaveWorkflow = async (data: any) => {
    if (!agent) return;
    try {
      if (agent.workflows.length > 0) {
        await agentsApi.workflows.update(agent.id, agent.workflows[0].id, data);
        toast.success("Workflow updated");
      } else {
        const res = await agentsApi.workflows.create(agent.id, data);
        setAgent({ ...agent, workflows: [...agent.workflows, res.data] });
        toast.success("Workflow created");
      }
      loadAgent();
    } catch {
      toast.error("Failed to save workflow");
    }
  };

  const tabs = [
    { id: "chat" as const, label: "Chat", icon: MessageSquare },
    { id: "skills" as const, label: "Skills", icon: Brain },
    { id: "tools" as const, label: "Tools", icon: Wrench },
    { id: "memory" as const, label: "Memory", icon: Brain },
    { id: "workflows" as const, label: "Workflows", icon: Workflow },
    { id: "tasks" as const, label: "Tasks", icon: ListTodo },
    { id: "analytics" as const, label: "Analytics", icon: BarChart3 },
    { id: "settings" as const, label: "Settings", icon: Settings },
  ];

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-[60vh]"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;
  }

  if (!agent) return null;

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col animate-fade-in">
      <header className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <button onClick={() => router.push("/agents")} className="p-1.5 rounded-lg hover:bg-muted transition-colors shrink-0">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm shrink-0" style={{ backgroundColor: agent.color || "#2563EB" }}>
            {agent.icon || agent.name.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0">
            <input value={agent.name} onChange={(e) => setAgent({ ...agent, name: e.target.value })} className="text-lg font-semibold bg-transparent border-none outline-none focus-visible:ring-0 px-1 w-full" />
            <p className="text-xs text-muted-foreground ml-1">{agent.role}</p>
          </div>
          <Badge variant={agent.status === "active" ? "success" : "default"}>{agent.status}</Badge>
          <Badge variant="outline">{agent.model}</Badge>
        </div>
        <div className="flex items-center gap-2">
          {!agent.is_template && !agent.published && (
            <Button variant="outline" size="sm" onClick={handlePublish}>
              <Store className="w-4 h-4 mr-1.5" /> Publish
            </Button>
          )}
          <Button size="sm" onClick={handleSave} isLoading={isSaving}>
            <Save className="w-4 h-4 mr-1.5" /> Save
          </Button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex flex-col border-r border-border bg-card w-56 shrink-0 overflow-y-auto">
          {tabs.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2.5 px-4 py-3 text-sm transition-colors text-left ${activeTab === tab.id ? "bg-primary/5 text-primary border-r-2 border-primary font-medium" : "text-muted-foreground hover:text-foreground hover:bg-muted/30"}`}>
              <tab.icon className="w-4 h-4" /> {tab.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-hidden">
          {activeTab === "chat" && (
            <AgentChatConsole agentId={agent.id} agentName={agent.name} className="h-full" />
          )}

          {activeTab === "skills" && (
            <div className="p-6 overflow-y-auto h-full max-w-2xl">
              <AgentSkillsEditor skills={agent.skills || []} onAdd={handleAddSkill} onDelete={handleDeleteSkill} />
            </div>
          )}

          {activeTab === "tools" && (
            <div className="p-6 overflow-y-auto h-full max-w-2xl">
              <AgentToolsConfig tools={agent.tools || []} onAdd={handleAddTool} onDelete={handleDeleteTool} onToggle={handleToggleTool} />
            </div>
          )}

          {activeTab === "memory" && (
            <AgentMemoryBrowser
              memories={agent.memories || []}
              onDelete={handleDeleteMemory}
              onClear={handleClearMemories}
              className="h-full max-w-2xl mx-auto"
            />
          )}

          {activeTab === "workflows" && (
            <WorkflowBuilder
              workflow={agent.workflows?.[0] ? { name: agent.workflows[0].name, steps: agent.workflows[0].steps || [], id: agent.workflows[0].id } : { name: "", steps: [] }}
              onSave={handleSaveWorkflow}
              className="h-full"
            />
          )}

          {activeTab === "tasks" && (
            <TaskList
              tasks={agent.tasks || []}
              onAdd={handleAddTask}
              onExecute={handleExecuteTask}
              isExecuting={isExecuting}
              className="h-full max-w-2xl mx-auto"
            />
          )}

          {activeTab === "analytics" && (
            <div className="p-6 overflow-y-auto h-full max-w-3xl">
              <AgentAnalyticsPanel analytics={undefined} />
            </div>
          )}

          {activeTab === "settings" && (
            <div className="p-6 overflow-y-auto h-full max-w-2xl space-y-4">
              <h2 className="text-lg font-semibold flex items-center gap-2"><Settings className="w-4 h-4" /> Settings</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium block mb-1.5">Name</label>
                  <input value={agent.name} onChange={(e) => setAgent({ ...agent, name: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm" />
                </div>
                <div>
                  <label className="text-sm font-medium block mb-1.5">Role</label>
                  <input value={agent.role} onChange={(e) => setAgent({ ...agent, role: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm" />
                </div>
                <div>
                  <label className="text-sm font-medium block mb-1.5">Description</label>
                  <textarea value={agent.description || ""} onChange={(e) => setAgent({ ...agent, description: e.target.value })} rows={3} className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm resize-y" />
                </div>
                <div>
                  <label className="text-sm font-medium block mb-1.5">System Prompt</label>
                  <textarea value={agent.system_prompt || ""} onChange={(e) => setAgent({ ...agent, system_prompt: e.target.value })} rows={6} className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm font-mono resize-y" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium block mb-1.5">Model</label>
                    <select value={agent.model} onChange={(e) => setAgent({ ...agent, model: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm">
                      <option value="gpt-4o">GPT-4o</option>
                      <option value="gpt-4o-mini">GPT-4o Mini</option>
                      <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                      <option value="llama3">Llama 3</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium block mb-1.5">Temperature: {agent.temperature}</label>
                    <input type="range" min="0" max="2" step="0.1" value={agent.temperature} onChange={(e) => setAgent({ ...agent, temperature: parseFloat(e.target.value) })} className="w-full accent-primary" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
