"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { agentsApi } from "@/lib/api-client";
import { toast } from "sonner";
import { AgentCreationWizard } from "@/modules/agents/AgentCreationWizard";
import { PreBuiltAgents } from "@/modules/agents/PreBuiltAgents";

type Mode = "wizard" | "templates";

export default function NewAgentPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("templates");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = async (data: any) => {
    setIsCreating(true);
    try {
      const payload = {
        name: data.name || data.role,
        role: data.role || "Assistant",
        description: data.description,
        system_prompt: data.system_prompt,
        model: data.model || "gpt-4o",
        temperature: data.temperature ?? 0.7,
        icon: data.icon || "🤖",
        color: data.color || "#2563EB",
        skills: (data.skills || []).map((s: any) => typeof s === "string" ? { name: s, proficiency: 5 } : s),
        tools: (data.tools || []).map((t: any) => typeof t === "string" ? { name: t, tool_type: t, enabled: true } : t),
      };
      const res = await agentsApi.create(payload);
      toast.success("Agent created!");
      router.push(`/agents/${res.data.id}`);
    } catch {
      toast.error("Failed to create agent");
    } finally {
      setIsCreating(false);
    }
  };

  const handleTemplateSelect = async (template: any) => {
    setIsCreating(true);
    try {
      const payload = {
        name: template.name,
        role: template.role,
        description: template.description,
        system_prompt: `You are a ${template.role} assistant. ${template.description}`,
        model: "gpt-4o",
        temperature: 0.7,
        icon: template.icon,
        color: template.color,
        skills: template.skills.map((s: string) => ({ name: s, proficiency: 7, category: template.category })),
        tools: [
          { name: "Web Search", tool_type: "web_search", enabled: true, description: "Search the internet" },
          { name: "Document Reader", tool_type: "document_read", enabled: true, description: "Read documents" },
          { name: "Document Writer", tool_type: "document_write", enabled: true, description: "Generate documents" },
        ],
      };
      const res = await agentsApi.create(payload);
      toast.success(`${template.name} created!`);
      router.push(`/agents/${res.data.id}`);
    } catch {
      toast.error("Failed to create agent");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="py-4 animate-fade-in">
      <div className="flex items-center justify-center gap-2 mb-8">
        <button onClick={() => setMode("templates")} className={`px-4 py-2 rounded-lg text-sm transition-colors ${mode === "templates" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"}`}>
          Pre-Built Templates
        </button>
        <button onClick={() => setMode("wizard")} className={`px-4 py-2 rounded-lg text-sm transition-colors ${mode === "wizard" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"}`}>
          Custom Creation Wizard
        </button>
      </div>

      {mode === "templates" ? (
        <PreBuiltAgents onSelect={handleTemplateSelect} />
      ) : (
        <AgentCreationWizard onComplete={handleCreate} onCancel={() => router.push("/agents")} isCreating={isCreating} />
      )}
    </div>
  );
}
