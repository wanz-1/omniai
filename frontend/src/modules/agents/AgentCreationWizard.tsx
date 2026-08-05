"use client";

import { useState } from "react";
import { ArrowLeft, ArrowRight, Bot, Sparkles, Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

const AGENT_ICONS = ["🤖", "🧠", "💼", "📊", "🎯", "📝", "🔬", "🛠️", "🎨", "📈"];
const AGENT_COLORS = ["#2563EB", "#7C3AED", "#06B6D4", "#10B981", "#F59E0B", "#EF4444", "#EC4899", "#8B5CF6"];
const MODELS = [
  { id: "gpt-4o", label: "GPT-4o" },
  { id: "gpt-4o-mini", label: "GPT-4o Mini" },
  { id: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
  { id: "llama3", label: "Llama 3" },
];

interface AgentCreationWizardProps {
  onComplete: (data: any) => void;
  onCancel: () => void;
  isCreating?: boolean;
}

export function AgentCreationWizard({ onComplete, onCancel, isCreating }: AgentCreationWizardProps) {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    name: "",
    role: "",
    description: "",
    system_prompt: "",
    model: "gpt-4o",
    temperature: 0.7,
    icon: "🤖",
    color: "#2563EB",
    skills: [] as string[],
    tools: [] as string[],
  });
  const [skillInput, setSkillInput] = useState("");

  const steps = [
    { num: 1, label: "Identity" },
    { num: 2, label: "Personality" },
    { num: 3, label: "Skills & Tools" },
    { num: 4, label: "Review" },
  ];

  const addSkill = () => {
    if (skillInput.trim() && !form.skills.includes(skillInput.trim())) {
      setForm({ ...form, skills: [...form.skills, skillInput.trim()] });
      setSkillInput("");
    }
  };

  const removeSkill = (skill: string) => {
    setForm({ ...form, skills: form.skills.filter((s) => s !== skill) });
  };

  const toggleTool = (tool: string) => {
    setForm({
      ...form,
      tools: form.tools.includes(tool) ? form.tools.filter((t) => t !== tool) : [...form.tools, tool],
    });
  };

  const canProceed = () => {
    if (step === 1) return form.name.trim() && form.role.trim();
    if (step === 2) return true;
    if (step === 3) return true;
    return true;
  };

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Create AI Agent</h1>
        <button onClick={onCancel} className="text-sm text-muted-foreground hover:text-foreground">
          Cancel
        </button>
      </div>

      <div className="flex items-center gap-2 mb-8">
        {steps.map((s, i) => (
          <div key={s.num} className="flex items-center gap-2 flex-1">
            <div
              className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-colors",
                step > s.num
                  ? "bg-primary text-primary-foreground"
                  : step === s.num
                    ? "bg-primary/10 text-primary border border-primary"
                    : "bg-muted text-muted-foreground"
              )}
            >
              {step > s.num ? <Check className="w-4 h-4" /> : s.num}
            </div>
            <span className={cn("text-xs hidden sm:block", step >= s.num ? "text-foreground font-medium" : "text-muted-foreground")}>
              {s.label}
            </span>
            {i < steps.length - 1 && <div className="flex-1 h-px bg-border" />}
          </div>
        ))}
      </div>

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1.5">Agent Name</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              placeholder="e.g. Finance Assistant"
            />
          </div>
          <div>
            <label className="text-sm font-medium block mb-1.5">Role / Purpose</label>
            <input
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              placeholder="e.g. Financial Analyst & Budget Manager"
            />
          </div>
          <div>
            <label className="text-sm font-medium block mb-1.5">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-y"
              placeholder="Describe what this agent does..."
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium block mb-1.5">Icon</label>
              <div className="grid grid-cols-5 gap-1">
                {AGENT_ICONS.map((icon) => (
                  <button
                    key={icon}
                    onClick={() => setForm({ ...form, icon })}
                    className={cn("w-9 h-9 rounded-lg text-lg flex items-center justify-center hover:bg-muted transition-colors", form.icon === icon && "bg-primary/10 ring-1 ring-primary")}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1.5">Color</label>
              <div className="grid grid-cols-4 gap-1">
                {AGENT_COLORS.map((color) => (
                  <button
                    key={color}
                    onClick={() => setForm({ ...form, color })}
                    className={cn("w-9 h-9 rounded-lg transition-transform", form.color === color && "ring-2 ring-offset-2 scale-110")}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1.5">System Prompt</label>
            <textarea
              value={form.system_prompt}
              onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
              rows={8}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-y font-mono"
              placeholder={`You are a ${form.role || "helpful assistant"}. You help users with their tasks by breaking down problems, using available tools, and delivering high-quality results.`}
            />
            <p className="text-xs text-muted-foreground mt-1">
              The system prompt defines your agent&apos;s personality, constraints, and behavior.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium block mb-1.5">Model</label>
              <select
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm"
              >
                {MODELS.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-1.5">Temperature: {form.temperature}</label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={form.temperature}
                onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })}
                className="w-full accent-primary"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Precise</span>
                <span>Creative</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-6">
          <div>
            <label className="text-sm font-medium block mb-1.5">Skills</label>
            <div className="flex gap-2 mb-2">
              <input
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addSkill()}
                placeholder="Add a skill..."
                className="flex-1 px-3 py-2 rounded-lg border border-border bg-background text-sm"
              />
              <Button variant="outline" size="sm" onClick={addSkill}>Add</Button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {form.skills.map((s) => (
                <span key={s} className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-primary/10 text-primary text-xs">
                  {s}
                  <button onClick={() => removeSkill(s)} className="hover:text-primary/70">&times;</button>
                </span>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium block mb-2">Available Tools</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "web_search", label: "Web Search", desc: "Search the internet" },
                { id: "web_scrape", label: "Web Scraper", desc: "Extract web content" },
                { id: "document_read", label: "Document Reader", desc: "Read PDFs, DOCX, etc." },
                { id: "document_write", label: "Document Writer", desc: "Generate documents" },
                { id: "data_analysis", label: "Data Analysis", desc: "Analyze data sets" },
                { id: "chart_creation", label: "Chart Creator", desc: "Generate visualizations" },
                { id: "code_execution", label: "Code Runner", desc: "Execute code in sandbox" },
                { id: "email", label: "Email", desc: "Send and read emails" },
                { id: "database", label: "Database", desc: "Query databases" },
                { id: "api_call", label: "API Calls", desc: "Call external APIs" },
                { id: "file_system", label: "File System", desc: "Manage files" },
                { id: "image_generation", label: "Image Gen", desc: "Generate images" },
              ].map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => toggleTool(tool.id)}
                  className={cn(
                    "flex items-start gap-2 p-2 rounded-lg border text-left text-xs transition-colors",
                    form.tools.includes(tool.id)
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border hover:bg-muted"
                  )}
                >
                  <div className={cn("w-2 h-2 rounded-full mt-1 shrink-0", form.tools.includes(tool.id) ? "bg-primary" : "bg-muted-foreground/30")} />
                  <div>
                    <span className="font-medium">{tool.label}</span>
                    <p className="text-muted-foreground">{tool.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl border border-border bg-card">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white text-lg" style={{ backgroundColor: form.color }}>
                {form.icon}
              </div>
              <div>
                <h3 className="font-semibold">{form.name}</h3>
                <p className="text-xs text-muted-foreground">{form.role}</p>
              </div>
            </div>
            {form.description && <p className="text-sm text-muted-foreground mb-3">{form.description}</p>}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div><span className="text-muted-foreground">Model:</span> {form.model}</div>
              <div><span className="text-muted-foreground">Temperature:</span> {form.temperature}</div>
              <div><span className="text-muted-foreground">Skills:</span> {form.skills.length || 0}</div>
              <div><span className="text-muted-foreground">Tools:</span> {form.tools.length || 0}</div>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mt-8">
        <Button variant="outline" onClick={step > 1 ? () => setStep(step - 1) : onCancel}>
          {step > 1 ? <><ArrowLeft className="w-4 h-4 mr-1.5" /> Back</> : "Cancel"}
        </Button>
        {step < 4 ? (
          <Button onClick={() => setStep(step + 1)} disabled={!canProceed()}>
            Next <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>
        ) : (
          <Button onClick={() => onComplete(form)} isLoading={isCreating}>
            <Sparkles className="w-4 h-4 mr-1.5" />
            Create Agent
          </Button>
        )}
      </div>
    </div>
  );
}
