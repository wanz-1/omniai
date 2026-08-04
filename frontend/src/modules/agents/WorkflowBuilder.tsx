"use client";

import { useState } from "react";
import { Plus, Trash2, GripVertical, ArrowDown, Play, Save, Zap, GitBranch, MessageSquare, Bell, Clock, UserCheck, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

interface Step {
  id: string;
  name: string;
  step_type: string;
  config?: Record<string, any>;
  order: number;
}

interface WorkflowBuilderProps {
  workflow?: { id?: string; name: string; steps: Step[] };
  onSave: (data: any) => void;
  isSaving?: boolean;
  className?: string;
}

const STEP_TYPES = [
  { id: "trigger", label: "Trigger", icon: Zap, color: "text-green-500 bg-green-50 dark:bg-green-950" },
  { id: "ai_decision", label: "AI Decision", icon: GitBranch, color: "text-purple-500 bg-purple-50 dark:bg-purple-950" },
  { id: "condition", label: "Condition", icon: GitBranch, color: "text-amber-500 bg-amber-50 dark:bg-amber-950" },
  { id: "action", label: "Action", icon: Play, color: "text-blue-500 bg-blue-50 dark:bg-blue-950" },
  { id: "tool_call", label: "Tool Call", icon: Globe, color: "text-cyan-500 bg-cyan-50 dark:bg-cyan-950" },
  { id: "notification", label: "Notification", icon: Bell, color: "text-rose-500 bg-rose-50 dark:bg-rose-950" },
  { id: "human_approval", label: "Human Approval", icon: UserCheck, color: "text-orange-500 bg-orange-50 dark:bg-orange-950" },
  { id: "delay", label: "Delay", icon: Clock, color: "text-gray-500 bg-gray-50 dark:bg-gray-950" },
  { id: "api_call", label: "API Call", icon: Globe, color: "text-indigo-500 bg-indigo-50 dark:bg-indigo-950" },
];

export function WorkflowBuilder({ workflow, onSave, isSaving, className }: WorkflowBuilderProps) {
  const [name, setName] = useState(workflow?.name || "");
  const [steps, setSteps] = useState<Step[]>(workflow?.steps || []);
  const [showAddStep, setShowAddStep] = useState(false);

  const addStep = (stepType: string) => {
    const typeDef = STEP_TYPES.find((s) => s.id === stepType);
    const newStep: Step = {
      id: Date.now().toString(),
      name: typeDef?.label || stepType,
      step_type: stepType,
      config: {},
      order: steps.length,
    };
    setSteps([...steps, newStep]);
    setShowAddStep(false);
  };

  const removeStep = (id: string) => {
    setSteps(steps.filter((s) => s.id !== id).map((s, i) => ({ ...s, order: i })));
  };

  const updateStep = (id: string, updates: Partial<Step>) => {
    setSteps(steps.map((s) => (s.id === id ? { ...s, ...updates } : s)));
  };

  const handleSave = () => {
    onSave({ name: name || "Untitled Workflow", steps: steps.map((s) => ({ name: s.name, step_type: s.step_type, config: s.config, order: s.order })) });
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div className="flex items-center justify-between p-3 border-b border-border">
        <div className="flex items-center gap-2 flex-1">
          <Zap className="w-4 h-4 text-primary" />
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Workflow name" className="text-sm font-medium bg-transparent border-none outline-none flex-1" />
        </div>
        <Button size="sm" onClick={handleSave} isLoading={isSaving}>
          <Save className="w-3.5 h-3.5 mr-1" /> Save
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {steps.map((step, i) => {
          const typeDef = STEP_TYPES.find((s) => s.id === step.step_type);
          const Icon = typeDef?.icon || Play;
          return (
            <div key={step.id} className="relative">
              <div className={cn("flex items-start gap-3 p-3 rounded-xl border border-border bg-card hover:shadow-sm transition-shadow")}>
                <div className="flex flex-col items-center gap-1">
                  <GripVertical className="w-3.5 h-3.5 text-muted-foreground cursor-grab opacity-0 group-hover:opacity-100" />
                  <div className={cn("p-2 rounded-lg", typeDef?.color || "bg-muted")}>
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-muted-foreground">Step {i + 1}</span>
                    <span className={cn("text-[10px] px-1.5 py-0.5 rounded", typeDef?.color || "bg-muted")}>{typeDef?.label || step.step_type}</span>
                  </div>
                  <input value={step.name} onChange={(e) => updateStep(step.id, { name: e.target.value })} className="text-sm font-medium bg-transparent border-none outline-none mt-0.5 w-full" placeholder="Step name" />
                  {step.step_type === "condition" && (
                    <input value={step.config?.condition || ""} onChange={(e) => updateStep(step.id, { config: { ...step.config, condition: e.target.value } })} placeholder="e.g. amount > 1000" className="w-full mt-1 px-2 py-1 rounded border border-border bg-background text-xs font-mono" />
                  )}
                  {step.step_type === "action" && (
                    <textarea value={step.config?.content || ""} onChange={(e) => updateStep(step.id, { config: { ...step.config, content: e.target.value } })} rows={2} placeholder="Action content (use {{variable}} for dynamic values)" className="w-full mt-1 px-2 py-1 rounded border border-border bg-background text-xs resize-y" />
                  )}
                  {step.step_type === "tool_call" && (
                    <div className="flex gap-2 mt-1">
                      <input value={step.config?.tool_name || ""} onChange={(e) => updateStep(step.id, { config: { ...step.config, tool_name: e.target.value } })} placeholder="Tool name" className="flex-1 px-2 py-1 rounded border border-border bg-background text-xs" />
                    </div>
                  )}
                  {step.step_type === "api_call" && (
                    <div className="flex gap-2 mt-1">
                      <input value={step.config?.url || ""} onChange={(e) => updateStep(step.id, { config: { ...step.config, url: e.target.value } })} placeholder="https://api.example.com/endpoint" className="flex-1 px-2 py-1 rounded border border-border bg-background text-xs font-mono" />
                    </div>
                  )}
                  {step.step_type === "delay" && (
                    <input value={step.config?.seconds || 1} onChange={(e) => updateStep(step.id, { config: { ...step.config, seconds: parseInt(e.target.value) || 1 } })} type="number" min="1" className="mt-1 px-2 py-1 rounded border border-border bg-background text-xs w-24" />
                  )}
                  {step.step_type === "notification" && (
                    <input value={step.config?.message || ""} onChange={(e) => updateStep(step.id, { config: { ...step.config, message: e.target.value } })} placeholder="Notification message" className="w-full mt-1 px-2 py-1 rounded border border-border bg-background text-xs" />
                  )}
                </div>
                <button onClick={() => removeStep(step.id)} className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-muted-foreground hover:text-red-500">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              {i < steps.length - 1 && (
                <div className="flex justify-center py-1">
                  <ArrowDown className="w-4 h-4 text-muted-foreground/50" />
                </div>
              )}
            </div>
          );
        })}

        <div className="relative">
          <Button variant="outline" size="sm" onClick={() => setShowAddStep(!showAddStep)} className="w-full border-dashed">
            <Plus className="w-4 h-4 mr-1.5" /> Add Step
          </Button>
          {showAddStep && (
            <div className="absolute top-full left-0 right-0 mt-1 p-2 bg-card border border-border rounded-xl shadow-lg z-10 grid grid-cols-3 gap-1 max-h-48 overflow-y-auto">
              {STEP_TYPES.map((st) => (
                <button key={st.id} onClick={() => addStep(st.id)} className="flex flex-col items-center gap-1 p-2 rounded-lg hover:bg-muted text-xs transition-colors">
                  <div className={cn("p-1.5 rounded-lg", st.color)}><st.icon className="w-3.5 h-3.5" /></div>
                  <span className="text-[10px]">{st.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
